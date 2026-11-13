import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Improvement loop: unanswered questions, adding information, answer ratings."""
import fakeredis
from fastapi.testclient import TestClient
import examples, improve, main

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)

assert improve.is_unanswered("I don't have that information. Please contact Acme.")
assert improve.is_unanswered("Sorry, I do not have information about kayaks.")
assert not improve.is_unanswered("Call support at 555-0100 or contact us by email.")
assert not improve.is_unanswered("Acme sells tents, backpacks and boots.")

with TestClient(main.app) as c:
    body = {k: v for k, v in examples.EXAMPLES[1].items() if k != "key"}
    d = c.post("/bots", json=body).json()
    bid, KEY = d["bot_id"], {"X-Owner-Key": d["owner_key"]}
    say = lambda m, s="s1": c.post(f"/bots/{bid}/chat", json={"session_id": s, "message": m}).json()

    # 1. gaps are logged and counted; greetings and answered questions are not
    r = say("Do you sell kayaks?")
    assert r["unanswered"] and r["answer_id"]
    say("do you sell KAYAKS", "s2"); say("Do you rent bikes?", "s3"); say("hi", "s4")
    ok = say("What is the return policy?", "s5")
    assert not ok["unanswered"]
    rep = c.get(f"/bots/{bid}/improve", headers=KEY).json()
    gaps = {g["question"].lower().rstrip("?"): g["count"] for g in rep["gaps"]}
    assert gaps == {"do you sell kayaks": 2, "do you rent bikes": 1}, gaps
    assert rep["gaps"][0]["count"] == 2, "most-asked first"
    print("gaps OK:", rep["gaps"])

    # 2. only the owner sees and edits it
    assert c.get(f"/bots/{bid}/improve").status_code == 403
    assert c.post(f"/bots/{bid}/knowledge", json={"text": "## X\nhi"}).status_code == 403

    # 3. adding information makes the bot answer, then the gap is marked fixed
    add = c.post(f"/bots/{bid}/knowledge", headers=KEY,
                 json={"text": "## Kayaks and boats\nAcme sells inflatable kayaks for $299 and paddles for $49."}).json()
    assert add["added"] == 1 and add["sections"] == len(rep["sections"]) + 1
    main.app.state.bot_cache.clear()
    r = say("Do you sell kayaks?", "s6")
    assert not r["unanswered"] and "299" in r["reply"] and r["sources"][0] == "Kayaks and boats", r
    key = next(g["key"] for g in rep["gaps"] if "kayak" in g["key"])
    assert c.delete(f"/bots/{bid}/gaps", params={"question": key}, headers=KEY).status_code == 200
    left = [g["question"] for g in c.get(f"/bots/{bid}/improve", headers=KEY).json()["gaps"]]
    assert left == ["Do you rent bikes?"], left
    too_big = c.post(f"/bots/{bid}/knowledge", headers=KEY, json={"text": "## Big\n" + "word " * 39800})
    assert too_big.status_code == 422
    rep_mode = c.post(f"/bots/{bid}/knowledge", headers=KEY, json={"text": "## Only\nOne section now.", "mode": "replace"}).json()
    assert rep_mode["sections"] == 1
    print("add information OK: bot answers new facts, gap marked fixed, size limit, replace")

    # 4. ratings: only the person who got the answer, once
    a = say("What are your store hours?", "rate")
    fb = lambda s, h, aid=a["answer_id"]: c.post(f"/bots/{bid}/feedback", json={"session_id": s, "answer_id": aid, "helpful": h, "comment": "too vague"})
    assert fb("someone-else", False).status_code == 404
    assert fb("rate", False).json() == {"recorded": True, "already_rated": False}
    assert fb("rate", True).json()["already_rated"] is True
    b = say("Where are you?", "rate")
    assert fb("rate", True, b["answer_id"]).json()["recorded"]
    assert c.post(f"/bots/{bid}/feedback", json={"session_id": "rate", "answer_id": "doesnotexist", "helpful": True}).status_code == 404
    q = c.get(f"/bots/{bid}/improve", headers=KEY).json()["feedback"]
    assert q["helpful"] == 1 and q["not_helpful"] == 1 and q["helpful_percent"] == 50.0
    assert q["recent_not_helpful"][0]["question"] == "What are your store hours?" and q["recent_not_helpful"][0]["comment"] == "too vague"
    ov = c.get("/admin/overview", headers={"X-Admin-Token": main.app.state.admin_token}).json()
    qual = next(x for x in ov["bots"] if x["id"] == bid)["quality"]
    # 3 gaps: "rent bikes", plus two questions asked after the documents were replaced with one section
    assert qual == {"helpful": 1, "not_helpful": 1, "gaps": 3}, qual
    print("ratings OK:", {k: q[k] for k in ("helpful", "not_helpful", "helpful_percent")})

    # 5. deleting the bot removes all of it
    assert c.delete(f"/bots/{bid}", headers=KEY).status_code == 200
    import redis as _r
    left_keys = [k for k in fakeredis.FakeRedis(server=srv, decode_responses=True).keys("*") if bid in k and not k.startswith("rl:")]  # rate-limit counters expire within a minute
    assert left_keys == [], left_keys
    print("delete OK: no keys left for the bot")

# 6. sample bots pick up new documents after a code update (Redis outlives a redeploy)
import json
async def seed_check():
    main.settings.SEED_EXAMPLES = True
    r = main.app.state.redis
    await main.store.seed_examples()
    raw = json.loads(await r.get(main.store.bot_key("unt-helper")))
    assert raw["sample_hash"] and any(c["title"] == "Meal plans" for c in raw["chunks"])
    raw["chunks"], raw["sample_hash"] = [{"title": "Old", "text": "old facts"}], "old"
    await r.set(main.store.bot_key("unt-helper"), json.dumps(raw))
    await r.delete("seed_lock")
    await main.store.seed_examples()
    raw = json.loads(await r.get(main.store.bot_key("unt-helper")))
    assert any(c["title"] == "Meal plans" for c in raw["chunks"]), "sample bot not refreshed"
with TestClient(main.app) as c2:
    c2.portal.call(seed_check)
print("sample refresh OK: old sample documents replaced on startup")
print("ALL IMPROVE TESTS PASSED")
