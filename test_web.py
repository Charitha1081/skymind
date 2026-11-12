import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Website lookup: when the documents don't have the answer, check only the company's own website."""
import json
import fakeredis, httpx
from fastapi.testclient import TestClient
import examples, improve, ingest, main, providers, web

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
main.STREAM_MOCK_DELAY_S = 0

# the fake Acme website from the Suggest fix tests (no network)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fix.py")).read()
exec(src[src.index("SITE = {"):src.index("fetched = []")])
fetched = []


async def fake_fetch(url, client=None, resolve=None):
    fetched.append(url)
    if url + "/" in SITE:  # real sites serve https://x.com and https://x.com/ alike
        url += "/"
    if url not in SITE:
        raise ingest.IngestError("The website answered with error 404.")
    title, text, links = ingest.html_page(SITE[url], url)
    return {"url": url, "title": title, "text": text, "links": links}

ingest.fetch_page = fake_fetch


def events(text):
    out = []
    for block in text.strip().split("\n\n"):
        name = next(l[6:].strip() for l in block.splitlines() if l.startswith("event:"))
        out.append((name, json.loads(next(l[5:] for l in block.splitlines() if l.startswith("data:")))))
    return out

# 1. partial answers count as "couldn't answer" (the bug from the UNT screenshot)
assert improve.is_unanswered("UNT offers 126 master's and doctoral degrees. However, I don't have the details of the "
                             "specific computer-related master's programs or their courses.")
assert web.normalise_website("unt.edu") == "https://unt.edu" and web.domain_of("https://www.unt.edu/x") == "unt.edu"
for bad in ("not a site", "ftp://unt.edu", "https://localhost"):
    try:
        web.normalise_website(bad)
        raise AssertionError(bad)
    except ValueError:
        pass
assert improve.is_unanswered("The documents I have don't list courses for individual programs, so I can't tell you how many there are.")
assert not improve.is_unanswered("UNT has 15 residence halls. Living Learning Communities let students live together.")
cut = web.trim_cut_off("Courses:\n- CSCE 1030: Computer Science I\n- CSCE 4600: Operating Systems\n\nFor the full list, see the [UNT Catalog](https://cat")
assert "https://cat" not in cut and cut.startswith("Courses:") and "Shortened" in cut, cut
print("basics OK: partial answers detected, websites normalised, bad ones refused")

ACME = {k: v for k, v in examples.EXAMPLES[1].items() if k != "key"}
ACME["provider"] = "mock"
with TestClient(main.app) as c:
    # 2. deploy with website lookup (and the UNT sample comes with it on)
    d = c.post("/bots", json=dict(ACME, website="https://www.acme.example/", web_lookup=True)).json()
    bid, KEY = d["bot_id"], {"X-Owner-Key": d["owner_key"]}
    strict = c.post("/bots", json=dict(ACME, bot_name="Strict")).json()
    assert c.post("/bots", json=dict(ACME, bot_name="Bad", website="http://127.0.0.1/", web_lookup=True)).status_code == 422
    assert examples.EXAMPLES[0]["website"] == "https://www.unt.edu" and examples.EXAMPLES[0]["web_lookup"]
    print("deploy OK: website saved, private addresses refused")

    ask = lambda b, m, s: c.post(f"/bots/{b}/chat", json={"session_id": s, "message": m}).json()

    # 3. the documents answer: no lookup at all
    fetched.clear()
    r = ask(bid, "What is your return policy?", "a1")
    assert r["answered_from"] == "documents" and fetched == [] and not r["unanswered"]

    # 4. not in the documents but on the website: answered from it, with its source, and logged as a gap
    r = ask(bid, "Do you sell kayaks?", "a2")
    assert r["answered_from"] == "website" and "$299" in r["reply"] and "checked acme.example" in r["reply"], r["reply"]
    assert r["web_sources"][0]["url"] == "https://www.acme.example/kayaks" and r["unanswered"]
    assert r["sources"] == [], "document-section chips are hidden when the website answered"
    gaps = c.get(f"/bots/{bid}/improve", headers=KEY).json()["gaps"]
    assert gaps[0]["question"] == "Do you sell kayaks?" and gaps[0]["web_url"] == "https://www.acme.example/kayaks"
    assert not any("evil" in u for u in fetched), "only the company's own site"
    print("website answer OK:", r["reply"][:70].replace("\n", " "), "...")

    # 5. asked again: served from the cache, no new page reads
    fetched.clear()
    assert ask(bid, "do you sell kayaks?", "a3")["answered_from"] == "website" and fetched == []

    # 6. not on the website either: the honest "I don't have that" stays
    r = ask(bid, "Who is your CEO?", "a4")
    assert r["answered_from"] == "documents" and r["unanswered"] and "don't have" in r["reply"]

    # 7. a strict (documents only) bot never looks anything up
    fetched.clear()
    r = ask(strict["bot_id"], "Do you sell kayaks?", "s1")
    assert r["answered_from"] == "documents" and fetched == []
    print("cache, not found and strict mode OK")

    # 8. streaming: "I don't have that" is never shown; a status, then the website answer
    ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "st1", "message": "Can I rent a tent?"}).text)
    names = [e[0] for e in ev]
    assert names[0] == "start" and "searching" in names and names[-1] == "done", names
    shown = "".join(e[1]["text"] for e in ev if e[0] == "text")
    assert "don't have" not in shown.lower() and "$25 per weekend" in shown, shown
    assert ev[names.index("searching")][1]["site"] == "acme.example"
    assert ev[-1][1]["answered_from"] == "website" and ev[-1][1]["web_sources"]
    ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "st2", "message": "What is your return policy?"}).text)
    assert "searching" not in [e[0] for e in ev] and ev[-1][1]["answered_from"] == "documents"
    print("streaming OK: the refusal is held back, 'searching' status, then the website answer")

    # 9. settings: only the owner, website checked, can be turned off
    assert c.patch(f"/bots/{bid}/web", json={"website": "https://www.acme.example", "enabled": False}).status_code == 403
    assert c.patch(f"/bots/{bid}/web", headers=KEY, json={"website": "http://10.0.0.5", "enabled": True}).status_code == 422
    assert c.patch(f"/bots/{bid}/web", headers=KEY, json={"website": "https://www.acme.example", "enabled": False}).json()["web_lookup"] is False
    main.app.state.bot_cache.clear()
    fetched.clear()
    assert ask(bid, "Where do I park?", "a5")["answered_from"] == "documents" and fetched == []
    c.patch(f"/bots/{bid}/web", headers=KEY, json={"website": "https://www.acme.example", "enabled": True})
    main.app.state.bot_cache.clear()
    print("settings OK: owner only, private address refused, on/off works")

    # 10. Claude bots: Claude's web search, limited to the company's domain, with citations and the search fee
    calls = []

    def claude(req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content)
        calls.append(body)
        if "tools" not in body and "PAGES:" in body["messages"][-1]["content"]:  # SkyMind's reader asks with passages
            return httpx.Response(200, json={"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "Yes: a 4-person tent rents for $35 per weekend."}],
                                             "usage": {"input_tokens": 500, "output_tokens": 15}})
        if "tools" not in body:  # the normal documents answer
            return httpx.Response(200, json={"model": "claude-haiku-5-5", "content": [{"type": "text", "text": "I don't have that information."}],
                                             "usage": {"input_tokens": 300, "output_tokens": 10}})
        if claude.search_off:
            return httpx.Response(400, json={"type": "error", "error": {"type": "invalid_request_error", "message": "web search is not enabled for this organization"}})
        return httpx.Response(200, json={
            "model": "claude-haiku-5-5", "stop_reason": "end_turn",
            "content": [
                {"type": "server_tool_use", "id": "srv1", "name": "web_search", "input": {"query": "acme parking"}},
                {"type": "web_search_tool_result", "tool_use_id": "srv1", "content": [{"type": "web_search_result", "url": "https://www.acme.example/parking-and-directions", "title": "Directions"}]},
                {"type": "text", "text": "Both stores have free customer parking behind the building.",
                 "citations": [{"type": "web_search_result_location", "url": "https://www.acme.example/parking-and-directions",
                                "title": "Directions", "cited_text": "free customer parking"}]}],
            "usage": {"input_tokens": 2000, "output_tokens": 40, "server_tool_use": {"web_search_requests": 1}}})
    claude.search_off = False
    real = (main.bot_provider, main.app.state.http, providers.ANTHROPIC_API_KEY)
    main.bot_provider = lambda b: "anthropic"
    providers.ANTHROPIC_API_KEY = "test-key"
    main.app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(claude))
    try:
        before = c.get(f"/bots/{bid}/usage", headers=KEY).json()["actual_cost_usd"]
        r = ask(bid, "Is there parking at the store?", "c1")
        tool = [b for b in calls if "tools" in b][0]["tools"][0]
        assert tool["type"] == "web_search_20250305" and tool["allowed_domains"] == ["acme.example"] and tool["max_uses"] <= 3
        assert r["answered_from"] == "website" and "free customer parking" in r["reply"]
        assert r["web_sources"] == [{"url": "https://www.acme.example/parking-and-directions", "title": "Directions"}]
        after = c.get(f"/bots/{bid}/usage", headers=KEY).json()["actual_cost_usd"]
        assert after - before >= 0.01, (before, after)  # the $0.01 search fee is counted
        print("Claude web search OK: allowed_domains=['acme.example'], citations as sources, fee counted")

        # web search turned off in the Claude Console: SkyMind's own reader answers instead
        claude.search_off = True
        r = ask(bid, "Can I rent a 4-person tent?", "c2")
        assert r["answered_from"] == "website" and "$35" in r["reply"] and r["web_sources"][0]["url"] == "https://www.acme.example/rentals/", r
        print("fallback OK: Claude web search off -> SkyMind's own reader")
    finally:
        main.bot_provider, main.app.state.http, providers.ANTHROPIC_API_KEY = real
print("ALL WEBSITE TESTS PASSED")
