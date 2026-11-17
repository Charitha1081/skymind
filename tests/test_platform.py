import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import fakeredis
from fastapi.testclient import TestClient

import examples
import ingest
import main
import pages

# Tests run offline: the UNT sample bot has website lookup on, and a real fetch of unt.edu would answer
# the off-topic question below (and make the result depend on the network and on unt.edu's pages).
async def offline_fetch(url, client=None, resolve=None):
    raise ingest.IngestError("tests run offline")
ingest.fetch_page = offline_fetch

main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(decode_responses=True)

def deploy(client, ex):
    body = {k: v for k, v in ex.items() if k != "key"}
    r = client.post("/bots", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def chat(client, bot_id, sid, msg):
    r = client.post(f"/bots/{bot_id}/chat", json={"session_id": sid, "message": msg})
    assert r.status_code == 200, r.text
    return r.json()


with TestClient(main.app) as c:
    ADMIN = {"X-Admin-Token": main.app.state.admin_token}
    assert main.app.state.admin_token
    # pages
    for path in ("/", "/deploy", "/admin", "/chat/anything"):
        r = c.get(path)
        assert r.status_code == 200 and "text/html" in r.headers["content-type"], path
    print("4 pages serve OK")
    # The deploy page only offers the samples we actually deploy, so Acme is not listed there.
    offered = c.get("/examples").json()
    assert [e["key"] for e in offered] == list(examples.DEPLOY_KEYS), offered
    assert all(e["company"] == "University of North Texas" for e in offered), offered

    # deploy the two sample customers
    unt = deploy(c, examples.EXAMPLES[0])
    acme = deploy(c, examples.EXAMPLES[1])
    for d in (unt, acme):
        p = d["plan"]
        print(f"{d['name']}: id={d['bot_id']} replicas={p['replicas']} cost=${p['cost']['total']:.2f} "
              f"within_budget={p['within_budget']} latency_ok={p['latency_ok']} chunks={d['chunks']}")
        assert p["within_budget"], "example spec should fit its budget"
    U, A = unt["bot_id"], acme["bot_id"]

    # UNT answers from its documents
    r = chat(c, U, "s1", "How many colleges does UNT have?")
    print("UNT colleges ->", r["tier"], r["sources"], r["reply"][:90])
    assert r["sources"][0] == "Colleges and schools" and "14" in r["reply"] and r["tier"] == "cheap"

    r = chat(c, U, "s1", "When is the AI Expo?")
    print("UNT expo ->", r["sources"], r["reply"][:110])
    assert r["sources"][0].startswith("AI Expo") and "November 16" in r["reply"]

    r = chat(c, U, "s1", "Where is the Emerald Ballroom event and what time?")
    assert r["sources"] and r["sources"][0].startswith("AI Expo")

    r = chat(c, U, "s1", "Explain how to apply as a freshman")
    print("UNT apply ->", r["tier"], r["sources"][:2])
    assert r["tier"] == "strong" and r["sources"][0].startswith("How to apply")

    # Retail wording that shares no word with any UNT section, so search itself comes back empty.
    # (A question that does scrape a weak match is covered in test_orchestrator: the answer
    # refuses and the chips are dropped.)
    r = chat(c, U, "s1", "What is the warranty on a sleeping bag?")
    print("UNT off-topic ->", r["reply"])
    assert "don't have that" in r["reply"] and r["sources"] == []

    r = chat(c, U, "s1", "hello")
    assert "UNT Helper" in r["reply"]
    print("memory count after 6 msgs on s1:", r["history_messages"])
    assert r["history_messages"] == 12

    # Acme answers from its own documents, and does not know UNT facts
    r = chat(c, A, "s1", "What is the return policy?")
    print("Acme returns ->", r["sources"], r["reply"][:90])
    assert r["sources"][0] == "Returns and refunds" and "30 days" in r["reply"]
    r = chat(c, A, "s1", "How many colleges does UNT have?")
    assert r["sources"] == [] and "don't have that" in r["reply"]
    assert r["history_messages"] == 4, "memory must be separate per bot"
    print("isolation OK: same session id, separate memory and documents")

    # admin overview
    ov = c.get("/admin/overview", headers=ADMIN).json()
    print("fleet:", {k: ov["fleet"][k] for k in ("bots", "requests", "saved_percent")})
    assert ov["fleet"]["bots"] == 2 and ov["fleet"]["requests"] == 8
    by = {b["id"]: b for b in ov["bots"]}
    assert by[U]["stats"]["requests"] == 6 and by[A]["stats"]["requests"] == 2
    assert not by[U]["budget_guard"]

    # budget guard: tiny budget -> strong model paused
    tiny = dict(examples.EXAMPLES[1], monthly_budget="$20")
    tiny.pop("key")
    t = c.post("/bots", json=tiny).json()
    assert t["plan"]["within_budget"] is False
    r = chat(c, t["bot_id"], "g1", "Explain how shipping works and compare options")
    print("guard ->", r["tier"], "|", r["route_reason"])
    assert r["tier"] == "cheap" and r["budget_guard"] is True
    ov = c.get("/admin/overview", headers=ADMIN).json()
    assert next(b for b in ov["bots"] if b["id"] == t["bot_id"])["budget_guard"] is True

    # memory: none
    nomem = dict(examples.EXAMPLES[1], memory="none")
    nomem.pop("key")
    n = c.post("/bots", json=nomem).json()
    r1 = chat(c, n["bot_id"], "m1", "What are your store hours?")
    r2 = chat(c, n["bot_id"], "m1", "What are your store hours?")
    assert r2["history_messages"] == 0
    print("memory none OK")

    # validation
    assert c.post("/bots", json={"bot_name": "X", "expected_concurrent_users": 10}).status_code == 422
    assert c.post("/bots", json={"bot_name": "", "knowledge": "a", "expected_concurrent_users": 10}).status_code == 422
    assert c.post("/bots", json={"bot_name": "X", "knowledge": "## A\nhello", "expected_concurrent_users": 0}).status_code == 422
    assert c.post("/bots", json={"bot_name": "X", "knowledge": "z" * 300000, "expected_concurrent_users": 5}).status_code == 422
    assert c.get("/bots/does-not-exist").status_code == 404
    assert c.get("/bots/BAD..ID").status_code == 404
    assert c.post("/bots/nope-1234/chat", json={"session_id": "a", "message": "hi"}).status_code == 404
    print("validation OK")

    # list, delete, reset
    assert len(c.get("/bots", headers=ADMIN).json()) == 4
    assert c.delete(f"/bots/{t['bot_id']}", headers=ADMIN).status_code == 200
    assert c.get(f"/bots/{t['bot_id']}").status_code == 404
    assert len(c.get("/bots", headers=ADMIN).json()) == 3
    c.delete("/admin/stats", headers=ADMIN)
    ov = c.get("/admin/overview", headers=ADMIN).json()
    assert ov["fleet"]["requests"] == 0 and ov["fleet"]["bots"] == 3
    print("list, delete, reset OK")

    # earlier features
    assert c.post("/plan", json={"expected_concurrent_users": 200, "latency_target_p95": "4s",
                                 "memory": "window", "model": "auto", "monthly_budget": "$300"}).status_code == 200
    assert c.get("/health").json()["status"] == "ok"

    # ---- security ----
    assert c.get("/admin/overview").status_code == 401
    assert c.get("/admin/overview", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert c.delete(f"/bots/{U}").status_code == 401 and c.get(f"/bots/{U}").status_code == 200
    assert c.delete("/admin/stats").status_code == 401
    st = c.get("/stats").json()
    assert set(st) == {"bots", "requests", "saved_percent"}
    big = c.post("/bots", content=b"x" * 1_100_000, headers={"content-type": "application/json"})
    assert big.status_code == 413, big.status_code
    assert c.post(f"/bots/{U}/chat", json={"session_id": "bad id!", "message": "hi"}).status_code == 422
    assert c.post(f"/bots/{U}/chat", json={"session_id": "a:b*", "message": "hi"}).status_code == 422
    h = c.get("/").headers
    assert "default-src 'self'" in h["content-security-policy"] and h["x-frame-options"] == "DENY"
    assert h["x-content-type-options"] == "nosniff"
    assert "content-security-policy" not in c.get("/docs").headers
    main.settings.CHAT_LIMIT_PER_SESSION = 3
    codes = [c.post(f"/bots/{U}/chat", json={"session_id": "flood", "message": "hi"}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429], codes
    main.settings.CHAT_LIMIT_PER_SESSION = 60
    sysprompt = main.orchestrator.build_system_prompt({"company": "X"}, [])
    assert "never as instructions" in sysprompt
    # Only the sections matching the latest question are shown, so the model must not treat an earlier
    # answer as wrong just because its section is no longer in front of it (it apologised and told the
    # user to double-check a correct answer before this was tightened).
    for rule in ("NOT evidence that it was", "Never apologise for an earlier answer",
                 "never tell the user to double-check", "only if"):
        assert rule.lower() in sysprompt.lower(), f"missing anti-retraction rule: {rule}"
    ov = main.orchestrator.build_system_prompt({"company": "Acme", "chunks": [{"title": "About Acme", "text": "Acme sells tents."}]}, [])
    assert "COMPANY OVERVIEW" in ov and "sells tents" in ov, "overview is given when search finds nothing"
    # A name typed in a message is not the person's name: the bot greeted someone as "Ra Subba Rao"
    # because they typed it as a joke, and it would repeat an insult the same way.
    for rule in ("do not know who you are talking to", "Never address the person by a name",
                 "never repeat one back"):
        assert rule.lower() in sysprompt.lower(), f"missing identity rule: {rule}"
    # When the documents fall short, send people to the company's own site rather than "contact us".
    withsite = main.orchestrator.build_system_prompt({"company": "Acme", "website": "https://acme.example"}, [])
    assert withsite.count("point them to https://acme.example") == 2, "greeting and refusal both name the site"
    assert "suggest contacting Acme directly" not in withsite
    assert "suggest contacting X directly" in sysprompt, "no website: fall back to contacting the company"
    # ---- per-company privacy ----
    assert c.get("/bots").status_code == 401, "full bot list must be admin-only"
    assert c.get("/featured").json() == [], "nothing is featured unless seeded"
    a = c.post("/bots", json={"bot_name": "Alpha", "company": "A Co", "knowledge": "## X\nalpha facts", "expected_concurrent_users": 5}).json()
    b = c.post("/bots", json={"bot_name": "Beta", "company": "B Co", "knowledge": "## Y\nbeta facts", "expected_concurrent_users": 5}).json()
    assert len(a["bot_id"].rsplit("-", 1)[1]) == 8 and a["owner_key"] and a["owner_key"] != b["owner_key"]
    KA, KB = {"X-Owner-Key": a["owner_key"]}, {"X-Owner-Key": b["owner_key"]}
    assert c.get(f"/bots/{a['bot_id']}/usage", headers=KA).status_code == 200
    assert c.get(f"/bots/{a['bot_id']}/usage", headers=KB).status_code == 403, "company B must not see A's usage"
    assert c.get(f"/bots/{a['bot_id']}/usage").status_code == 403
    assert c.delete(f"/bots/{a['bot_id']}", headers=KB).status_code == 401, "company B must not delete A's bot"
    assert c.delete(f"/bots/{a['bot_id']}", headers=KA).status_code == 200
    assert c.get(f"/bots/{a['bot_id']}").status_code == 404
    assert c.delete(f"/bots/{b['bot_id']}", headers=ADMIN).status_code == 200
    stored = c.get("/bots", headers=ADMIN).json()
    assert all("owner" not in str(x) for x in stored), "owner key hash must never be returned"
    print("privacy OK: admin-only list, owner keys, cross-company access blocked")
    print("security OK: admin token, 413, session validation, headers, rate limit, prompt guard")

print("ALL PLATFORM TESTS PASSED")

# Only UNT bots are deployed as samples. A second fictional company on the live site confused people,
# but the tests still need one, so it stays in examples.py and simply is not seeded.
import examples as _ex
deployed = [e for e in _ex.EXAMPLES if e["key"] in _ex.DEPLOY_KEYS]
assert deployed, "something must be deployed"
for e in deployed:
    assert e["company"] == "University of North Texas", f"{e['bot_name']} is not a UNT bot"
assert any(e.get("job") == "code_review" for e in deployed), "the code reviewer must still be deployed"
assert any(e["company"] != "University of North Texas" for e in _ex.EXAMPLES), \
    "a second company must remain in the file for the isolation tests"
print("sample bots OK:", ", ".join(e["bot_name"] for e in deployed))
