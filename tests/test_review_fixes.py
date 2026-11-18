import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Guards for the security and budget fixes: visitor address, monthly budget, DNS pinning, model fallback,
safe concurrent bot edits, one vector per chunk, and what Suggest fix remembers."""
import asyncio, json
import fakeredis, httpx
from fastapi.testclient import TestClient
import embeddings, examples, ingest, main, orchestrator, providers, security, settings, store

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
R = fakeredis.FakeRedis(server=srv, decode_responses=True)

# ---------- visitor address: read X-Forwarded-For from the right ----------
class FakeRequest:
    def __init__(self, xff):
        self.headers = {"x-forwarded-for": xff} if xff else {}
        self.client = type("Client", (), {"host": "10.0.0.1"})
settings.TRUSTED_PROXY_HOPS = 1
assert security.client_ip(FakeRequest("6.6.6.6, 1.2.3.4")) == "1.2.3.4", "the visitor-written part must be ignored"
assert security.client_ip(FakeRequest("1.2.3.4")) == "1.2.3.4"
assert security.client_ip(FakeRequest("")) == "10.0.0.1", "no header: the connection address"
settings.TRUSTED_PROXY_HOPS = 2
assert security.client_ip(FakeRequest("6.6.6.6, 1.2.3.4, 172.16.0.9")) == "1.2.3.4"
settings.TRUSTED_PROXY_HOPS = 0
assert security.client_ip(FakeRequest("6.6.6.6, 1.2.3.4")) == "10.0.0.1", "hops 0: never trust the header"
print("visitor address OK: X-Forwarded-For read from the right, faked entries ignored")

# ---------- DNS pinning: connect to the checked address, keep the real host for Host and TLS ----------
assert ingest._pinned("https://www.example.edu/a?b=1", "93.184.216.34") == "https://93.184.216.34/a?b=1"
assert ingest._pinned("http://x.org:80/p", "2606:2800::1") == "http://[2606:2800::1]:80/p"
seen = []
def site(request):
    if request.url.host == "2606:2800::1":
        raise httpx.ConnectError("no IPv6 route", request=request)
    seen.append({"url": str(request.url), "host": request.headers["host"],
                 "sni": request.extensions.get("sni_hostname")})
    return httpx.Response(200, headers={"content-type": "text/plain"}, content=b"hello world " * 10)
async def pinning():
    answers = []
    async def dns(host):  # rebinding: public the first time, private afterwards
        answers.append(host)
        return ["2606:2800::1", "93.184.216.34"] if len(answers) == 1 else ["127.0.0.1"]
    async with httpx.AsyncClient(transport=httpx.MockTransport(site)) as client:
        await ingest.fetch_page("https://www.example.edu/x", client, dns)
    assert len(answers) == 1, "the host must be looked up once, then the checked address used"
    assert seen == [{"url": "https://93.184.216.34/x", "host": "www.example.edu", "sni": "www.example.edu"}], seen
    _, ips = await ingest._checked("https://www.example.edu/", resolve=lambda h: asyncio.sleep(0, ["2606:2800::1", "93.184.216.34"]))
    assert ips == ["93.184.216.34", "2606:2800::1"], "IPv4 first"
asyncio.run(pinning())
print("DNS pinning OK: checked address used (IPv4 first, next one if unreachable), Host and SNI keep the real name")

# ---------- strong model refuses -> cheap model answers, and the reason says why ----------
async def fallback():
    calls = []
    async def fake_call(http, provider, tier, *rest):
        calls.append(tier)
        if tier == "strong":
            raise providers.ProviderError("Anthropic 404: model not found", 404)
        return {"text": "ok", "model": "cheap-model", "input_tokens": 1, "output_tokens": 1}
    main.app.state.http = None  # the fake call never uses it; the app sets the real one at startup
    real, providers.call = providers.call, fake_call
    try:
        bot = {"spec": {"provider": "anthropic"}, "company": "X", "chunks": [], "job": "answer"}
        res = await orchestrator.call_llm(bot, [], "q", "strong", [])
    finally:
        providers.call = real
    assert calls == ["strong", "cheap"], calls
    assert res["tier"] == "cheap" and res["fallback"] and res["fallback_why"] == "unavailable", res
asyncio.run(fallback())
print("fallback OK: a strong model that refuses goes straight to the cheap one")

# ---------- the app: monthly budget, per-address limit, concurrent edits, vectors, Suggest fix ----------
providers.GEMINI_API_KEY = "gm-test"
embedded = []
async def fake_embed(http, texts, task):
    embedded.append(len(texts))
    return [[1.0, 0.0] for _ in texts]
embeddings.embed = fake_embed

with TestClient(main.app) as c:
    ADMIN = {"X-Admin-Token": main.app.state.admin_token}
    ex = next(e for e in examples.EXAMPLES if e["key"] in examples.DEPLOY_KEYS)
    body = dict({k: v for k, v in ex.items() if k not in ("key", "website", "web_lookup")}, provider="mock")
    bot = c.post("/bots", json=dict(body, monthly_budget="$100"), headers=ADMIN).json()
    bid, OWNER = bot["bot_id"], {"X-Owner-Key": bot["owner_key"]}
    chat = lambda sid, headers=None: c.post(f"/bots/{bid}/chat", json={"session_id": sid, "message": "hello"},
                                            headers=headers or {})

    # last month's spending doesn't count against this month's budget
    R.hset(f"stats:{bid}", "actual_cost_usd", 1e6)
    assert chat("m1").status_code == 200, "lifetime spending must not stop the bot"
    assert R.get(store.month_cost_key(bid)) is not None, "spending is counted per month"
    R.set(store.month_cost_key(bid), 1e6)
    r = chat("m2")
    assert r.status_code == 429 and "monthly limit" in r.json()["detail"], r.text
    usage = c.get(f"/bots/{bid}/usage", headers=OWNER).json()
    assert usage["month_cost_usd"] == 1e6 and usage["budget_guard"] is True, usage
    row = next(b for b in c.get("/admin/overview", headers=ADMIN).json()["bots"] if b["id"] == bid)
    assert row["month_cost_usd"] == 1e6 and row["budget_guard"] is True
    c.delete("/admin/stats", headers=ADMIN)
    assert R.get(store.month_cost_key(bid)) is None, "reset clears this month's spending"
    assert len(set(store.month_cost_keys(bid))) == 2, "this month and last month"
    print("monthly budget OK: only this month's spending counts; usage and admin show it")

    # a fresh session id per message doesn't get round the per-address limit; admins are not limited
    settings.CHAT_LIMIT_PER_IP = 3
    codes = [chat(f"fresh{i}").status_code for i in range(6)]
    assert 429 in codes, codes
    assert chat("admin-run", ADMIN).status_code == 200
    settings.CHAT_LIMIT_PER_IP = 300
    print("per-address limit OK: new session ids don't help; admin token exempt")

    # a write that lands mid-edit is kept, and the edit is redone on the new copy
    async def conflicting_edit():
        runs = []
        async def change(stored, _read):
            runs.append(1)
            if len(runs) == 1:
                other = json.loads(R.get(f"bot:{bid}"))
                other["greeting"] = "changed elsewhere"
                R.set(f"bot:{bid}", json.dumps(other))
            stored["access"] = {"mode": "public", "allowed_domains": [], "allowed_emails": []}
        stored = await store.update_bot(bid, change)
        assert len(runs) == 2 and stored["greeting"] == "changed elsewhere", (runs, stored["greeting"])
    c.portal.call(conflicting_edit)
    print("concurrent edits OK: the other write survives")

    # hybrid bot whose vectors went missing: an append embeds everything, one vector per chunk
    hy = c.post("/bots", json=dict(body, search="hybrid"), headers=ADMIN).json()
    HKEY = {"X-Owner-Key": hy["owner_key"]}
    R.delete(f"vec:{hy['bot_id']}")
    embedded.clear()
    add = c.post(f"/bots/{hy['bot_id']}/knowledge", headers=HKEY, json={"text": "## Boats\nWe stock kayaks."}).json()
    assert len(json.loads(R.get(f"vec:{hy['bot_id']}"))) == add["sections"], "vectors must match the chunks"
    assert embedded == [1, add["sections"]], embedded  # the new text first, then everything once on the mismatch
    embedded.clear()
    add = c.post(f"/bots/{hy['bot_id']}/knowledge", headers=HKEY, json={"text": "## Paddles\nWooden paddles."}).json()
    assert embedded == [1] and len(json.loads(R.get(f"vec:{hy['bot_id']}"))) == add["sections"], embedded
    print("vectors OK: a mismatch re-embeds everything; a normal append embeds only the new text")

    # Suggest fix remembers the site (not the page), and never replaces a website that is already set
    async def fake_fetch(url, client=None, resolve=None):
        return {"url": url, "title": "Help", "text": "## Opening hours\nWe are open 9 to 5 on weekdays.", "links": []}
    real_fetch, ingest.fetch_page = ingest.fetch_page, fake_fetch
    try:
        fix = lambda: c.post(f"/bots/{bid}/suggest-fix", headers=OWNER,
                             json={"url": "https://help.example.com/a/b?x=1", "questions": ["What are your opening hours?"]})
        assert fix().status_code == 200
        assert json.loads(R.get(f"bot:{bid}"))["website"] == "https://help.example.com", "the site, not the page"
        stored = json.loads(R.get(f"bot:{bid}"))
        stored["website"] = "https://www.owner-set.example"
        R.set(f"bot:{bid}", json.dumps(stored))
        main.app.state.bot_cache.clear()
        assert fix().status_code == 200
        assert json.loads(R.get(f"bot:{bid}"))["website"] == "https://www.owner-set.example", "never replaced"
    finally:
        ingest.fetch_page = real_fetch
    print("Suggest fix OK: remembers the site's address only when none is set")
print("ALL REVIEW-FIX TESTS PASSED")
