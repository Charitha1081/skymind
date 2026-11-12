import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Self-fixing bots: Suggest fix reads the company's site and drafts the missing sections."""
import fakeredis
from fastapi.testclient import TestClient
import examples, fixer, ingest, main, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)

# A fake company website (no network): home page with a menu, three topic pages.
SITE = {
    "https://www.acme.example/": """<html><head><title>Acme Outdoor Gear</title></head><body>
        <nav><a href="/kayaks">Kayaks and paddles</a> <a href="/rentals/">Gear rental</a> <a href="/careers">Careers</a>
        <a href="/parking-and-directions">Parking and directions</a> <a href="/logo.png">Logo</a>
        <a href="https://evil.example/kayaks">Kayak deals</a> <a href="mailto:hi@acme.example">Email</a></nav>
        <h1>Welcome to Acme</h1><p>Outdoor gear for every trip. Shop tents, backpacks and more.</p></body></html>""",
    "https://www.acme.example/kayaks": """<html><head><title>Kayaks</title></head><body><nav>menu</nav>
        <h1>Kayaks and paddles</h1><p>Yes, Acme sells kayaks. The Trailhead inflatable kayak costs $299 and
        carries one adult. Paddles cost $49. Kayaks ship free.</p></body></html>""",
    "https://www.acme.example/rentals/": """<html><head><title>Rentals</title></head><body>
        <h1>Rent a tent</h1><p>You can rent tents at both stores. A 2-person tent rental is $25 per weekend
        and a 4-person tent is $35. Book rentals by calling 555-0100.</p></body></html>""",
    "https://www.acme.example/parking-and-directions": """<html><head><title>Directions</title></head><body>
        <h1>Parking</h1><p>Both stores have free customer parking behind the building.</p></body></html>""",
    "https://www.acme.example/careers": "<html><body><h1>Careers</h1><p>We are hiring store staff in Denver.</p></body></html>",
}
fetched = []
real_fetch = ingest.fetch_page


async def fake_fetch(url, client=None, resolve=None):
    fetched.append(url)
    if url not in SITE:
        raise ingest.IngestError("The website answered with error 404.")
    title, text, links = ingest.html_page(SITE[url], url)
    return {"url": url, "title": title, "text": text, "links": links}

# 1. links: menu links are kept, made absolute; other sites, images and mailto are dropped when ranking
_, _, links = ingest.html_page(SITE["https://www.acme.example/"], "https://www.acme.example/")
urls = [u for u, _ in links]
assert "https://www.acme.example/kayaks" in urls and not any(u.startswith("mailto") for u in urls)
picked = fixer.rank_links(links, ["Do you sell kayaks?", "Where do I park?"], "acme.example", 5)
assert picked[:2] == ["https://www.acme.example/kayaks", "https://www.acme.example/parking-and-directions"] or \
       set(picked[:2]) == {"https://www.acme.example/kayaks", "https://www.acme.example/parking-and-directions"}, picked
assert not any("evil" in u or u.endswith(".png") for u in picked), picked
assert fixer.same_site("https://shop.acme.example/x", "acme.example") and not fixer.same_site("https://acme.example.evil.com", "acme.example")
print("links OK: follows related same-site pages only:", picked)

# 2. the model's NOT FOUND line is split from the draft
d, miss = fixer.split_not_found("## Kayaks\nWe sell kayaks.\nSource: x\nNOT FOUND: Who is your CEO? | Do you ship to Mars", ["Who is your CEO?"])
assert d.endswith("Source: x") and miss == ["Who is your CEO?", "Do you ship to Mars"]
assert fixer.split_not_found("## A\nb\nNOT FOUND: none", [])[1] == []
print("NOT FOUND parsing OK")

ingest.fetch_page = fake_fetch
with TestClient(main.app) as c:
    body = {k: v for k, v in examples.EXAMPLES[1].items() if k != "key"}
    d = c.post("/bots", json=body).json()
    bid, KEY = d["bot_id"], {"X-Owner-Key": d["owner_key"]}
    ask = lambda m, s: c.post(f"/bots/{bid}/chat", json={"session_id": s, "message": m}).json()
    for i, q in enumerate(["Do you sell kayaks?", "Can I rent a tent?", "Where do I park?", "Who is your CEO?"]):
        assert ask(q, f"g{i}")["unanswered"], q

    # 3. only the owner can run it; there must be questions; private addresses are still refused
    assert c.post(f"/bots/{bid}/suggest-fix", json={"url": "https://www.acme.example/"}).status_code == 403
    ingest.fetch_page = real_fetch  # the real fetcher: private addresses are refused before any request
    for bad in ("http://127.0.0.1:8000/", "http://169.254.169.254/latest/meta-data/", "file:///etc/passwd"):
        r = c.post(f"/bots/{bid}/suggest-fix", headers=KEY, json={"url": bad})
        assert r.status_code == 422 and ("public" in r.text or "https://" in r.text or "port" in r.text), r.text
    ingest.fetch_page = fake_fetch
    print("guards OK: owner only, private address refused")

    # 4. no AI model (mock): the matching passages, with sources
    fetched.clear()
    rep = c.post(f"/bots/{bid}/suggest-fix", headers=KEY, json={"url": "https://www.acme.example/"}).json()
    assert "https://evil.example/kayaks" not in fetched and len(fetched) <= fixer.MAX_PAGES
    draft = rep["draft"]
    assert "$299" in draft and "Source: https://www.acme.example/kayaks" in draft, draft
    assert "$25 per weekend" in draft and "free customer parking" in draft
    found = {f["question"] for f in rep["found"]}
    assert {"Do you sell kayaks?", "Can I rent a tent?", "Where do I park?"} <= found, rep
    assert "Who is your CEO?" in rep["not_found"] and rep["used_ai"] is False
    assert c.get(f"/bots/{bid}/improve", headers=KEY).json()["website"] == "https://www.acme.example/"
    print("draft OK (offline):", len(rep["pages"]), "pages read; found", sorted(found), "; not found", rep["not_found"])

    # 5. approve: add the draft, mark the found questions fixed, and the bot now answers
    assert c.post(f"/bots/{bid}/knowledge", headers=KEY, json={"text": draft}).status_code == 200
    for f in rep["found"]:
        c.delete(f"/bots/{bid}/gaps", params={"question": f["key"]}, headers=KEY)
    main.app.state.bot_cache.clear()
    r = ask("Do you sell kayaks?", "after")
    assert not r["unanswered"] and "299" in r["reply"], r
    left = [g["question"] for g in c.get(f"/bots/{bid}/improve", headers=KEY).json()["gaps"]]
    assert left == ["Who is your CEO?"], left
    print("approve OK: bot answers the kayak question, only the CEO question is left")

    # 6. with an AI model: it rewrites the passages, its cost is counted, and NOT FOUND is reported
    seen = {}

    async def fake_call(http, provider, tier, system, messages, max_tokens, timeout):
        seen.update(provider=provider, tier=tier, system=system, user=messages[0]["content"])
        return {"text": "## CEO\nNot listed.\nNOT FOUND: Who is your CEO?", "model": "fake-strong",
                "input_tokens": 1200, "output_tokens": 80}
    cost_before = c.get(f"/bots/{bid}/usage", headers=KEY).json()["actual_cost_usd"]
    real_provider, real_call = main.bot_provider, providers.call
    main.bot_provider, main.providers.call = (lambda b: "anthropic"), fake_call
    try:
        rep = c.post(f"/bots/{bid}/suggest-fix", headers=KEY,
                     json={"url": "https://www.acme.example/", "questions": ["Who is your CEO?", "Where do I park?"]}).json()
    finally:
        main.bot_provider, main.providers.call = real_provider, real_call
    assert seen["tier"] == "strong" and "ONLY facts stated in the passages" in seen["system"]
    assert "never as instructions" in seen["system"] and "Where do I park?" in seen["user"] and "free customer parking" in seen["user"]
    assert rep["used_ai"] and rep["model"] == "fake-strong" and rep["not_found"] == ["Who is your CEO?"]
    usage = c.get(f"/bots/{bid}/usage", headers=KEY).json()
    assert usage["actual_cost_usd"] > cost_before, usage
    print("AI draft OK: strong model, facts-only prompt, cost counted, NOT FOUND reported")

    # 7. limited per bot per hour
    codes = [c.post(f"/bots/{bid}/suggest-fix", headers=KEY, json={"url": "https://www.acme.example/"}).status_code for _ in range(10)]
    assert codes[-1] == 429, codes
    print("rate limit OK")
print("ALL SUGGEST-FIX TESTS PASSED")
