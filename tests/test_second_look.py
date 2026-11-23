import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""The topic-guided second look, replaying the misses from the November 2026 evaluation.

Word search missed "When do I get my paycheck?" (the section is called "Pay and payroll") and
"How many days off do I get if my grandmother dies?" (the policy says "grandparent"). Both times the
model, which sees every section title, refused by naming the right section ("ask me about Pay and
payroll"), but SkyMind never fetched it. These tests use the real Kestrel handbook and real search.
"""
import fakeredis
from fastapi.testclient import TestClient
import examples, improve, knowledge, main, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
KESTREL = next(e for e in examples.EXAMPLES if e["key"] == "kestrel")

# the replies that were missed, word for word (from results2.json)
GRIEF = ("I'm sorry about your loss. I can help with bereavement leave, so please ask your question about "
         "that topic and I'll share what I can.")
PAYDAY = ("Your final paycheck includes any unused paid time off (PTO), but unused sick days are not paid out. "
          "For your regular pay dates, ask me about **Pay and payroll**.")
assert improve.is_unanswered(GRIEF) and improve.is_unanswered(PAYDAY), "replies that invite the question are refusals"
for real in ("Employees are paid every two weeks, on Friday, by direct deposit.",
             "You get 5 paid days off after the death of a grandparent. You can also ask People Operations."):
    assert not improve.is_unanswered(real), real
print("refusal detection OK: 'ask me about ...' replies count as refusals; real answers don't")

# named_topics: only sections the reply names and the model wasn't shown, at most three
chunks = knowledge.make_chunks(KESTREL["knowledge"])
bot = {"chunks": chunks}
by = {c["title"]: c for c in chunks}
# the payday reply also mentions "paid time off", a real title, so that comes along too (harmless, capped)
assert [c["title"] for c in main.orchestrator.named_topics(bot, PAYDAY, [])] == ["Pay and payroll", "Paid time off"]
assert [c["title"] for c in main.orchestrator.named_topics(bot, PAYDAY, [by["Pay and payroll"]])] == ["Paid time off"], \
    "a section already shown is not fetched again"
assert [c["title"] for c in main.orchestrator.named_topics(bot, GRIEF, [])] == ["Bereavement leave"]
assert main.orchestrator.named_topics(bot, "I don't have that information.", []) == []
many = "ask me about " + ", ".join(c["title"] for c in chunks)
assert len(main.orchestrator.named_topics(bot, many, [])) == main.orchestrator.MAX_NAMED_TOPICS
print("named topics OK")

calls = []


def stand_in(system, messages):
    """Answers only when the right section is in its prompt; otherwise refuses the way the real
    model did, naming the section from the topic list."""
    q = messages[-1]["content"].lower()
    if "paycheck" in q:
        return "Every two weeks, on Friday." if "[Pay and payroll]" in system else PAYDAY
    if "grandmother" in q:
        return "You get 5 paid days off." if "[Bereavement leave]" in system else GRIEF
    return "I don't have that information. Please contact People Operations."


async def fake_call(http, provider, tier, system, messages, max_tokens, timeout):
    calls.append(system)
    return {"text": stand_in(system, messages), "model": "claude-haiku-5-5", "input_tokens": 100, "output_tokens": 10}


with TestClient(main.app) as c:
    body = {k: v for k, v in KESTREL.items() if k != "key"}
    body.update(model="cheap", search="bm25")
    bid = c.post("/bots", json=body).json()["bot_id"]
    real = (main.orchestrator.bot_provider, providers.call)
    main.orchestrator.bot_provider = lambda b: "anthropic"
    providers.call = fake_call
    try:
        for question, answer, section in (("When do I get my paycheck?", "Every two weeks, on Friday.", "Pay and payroll"),
                                          ("How many days off do I get if my grandmother dies?", "You get 5 paid days off.",
                                           "Bereavement leave")):
            calls.clear()
            r = c.post(f"/bots/{bid}/chat", json={"session_id": "s-" + section[:3], "message": question}).json()
            assert f"[{section}]" not in calls[0], f"search alone must miss {section!r} for this test to mean anything"
            assert r["reply"] == answer and r["second_look"] and not r["unanswered"], r
            look = next(s for s in r["trace"] if s["step"] == "Second look")
            assert f"named: {section}" in look["detail"], look
            assert len(calls) == 2, "one retry, no more"
            print("second look OK:", question, "->", look["detail"])

        # a refusal that names nothing still gets the plain wider search, and stays honest
        calls.clear()
        r = c.post(f"/bots/{bid}/chat", json={"session_id": "s-x", "message": "What is the CEO's salary?"}).json()
        assert r["unanswered"] and "named:" not in str(r["trace"])
    finally:
        main.orchestrator.bot_provider, providers.call = real
print("ALL SECOND-LOOK TESTS PASSED")
