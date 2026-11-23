import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""An empty reply from the model must never reach the user as an answer.

Found on the Kestrel held-out set (November 2026): one answer was "Sorry, I couldn't put an answer
together", the placeholder for an empty model reply. Two faults made that possible: an empty reply was
never retried, and the placeholder did not count as a refusal, so in the second look it could replace
the bot's honest first answer and the question was not logged as unanswered.
"""
import json
import asyncio
import fakeredis
from fastapi.testclient import TestClient
import examples, improve, main, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
EMPTY = main.orchestrator.EMPTY_REPLY
REFUSAL = "I don't have that information. Please contact People Operations."
ANSWER = "Warehouse PTO between November 15 and January 5 needs director approval."

assert improve.is_unanswered(EMPTY), "the empty-reply placeholder is not an answer"
print("placeholder counts as a refusal OK")

script: list[str] = []   # what the stand-in model says, call by call ("" = an empty reply)
calls: list[str] = []


async def fake_call(http, provider, tier, system, messages, max_tokens, timeout):
    calls.append(tier)
    text = script.pop(0) if script else REFUSAL
    return {"text": text, "model": "claude-haiku-5-5", "input_tokens": 100, "output_tokens": 0 if not text else 10}


async def fake_stream(http, provider, tier, system, messages, max_tokens, timeout):
    calls.append("stream")
    yield "done", {"model": "claude-haiku-5-5", "input_tokens": 100, "output_tokens": 0}   # no text at all


def events(text):
    out = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        out.append((lines["event"], json.loads(lines["data"])))
    return out


with TestClient(main.app) as c:
    kestrel = next(e for e in examples.EXAMPLES if e["key"] == "kestrel")
    body = {k: v for k, v in kestrel.items() if k != "key"}
    body.update(model="cheap", search="bm25")
    bid = c.post("/bots", json=body).json()["bot_id"]
    ask = lambda m, s: c.post(f"/bots/{bid}/chat", json={"session_id": s, "message": m}).json()
    real = (main.orchestrator.bot_provider, providers.call, providers.stream)
    main.orchestrator.bot_provider = lambda b: "anthropic"
    providers.call, providers.stream = fake_call, fake_stream
    try:
        # 1. an empty reply is asked again, and the real answer is what the user gets
        script[:], calls[:] = ["", ANSWER], []
        r = ask("What approval do I need for vacation in late December?", "e1")
        assert r["reply"] == ANSWER and calls == ["cheap", "cheap"], (r["reply"], calls)
        print("retry OK: empty reply -> asked again -> real answer")

        # 2. a model that never answers: the user gets the placeholder, and it is logged as unanswered
        script[:], calls[:] = ["", "", "", ""], []
        r = ask("What approval do I need for vacation in late December?", "e2")
        assert r["reply"] == EMPTY and r["unanswered"], r
        print("persistent empty reply OK: placeholder shown, logged as unanswered")

        # 3. the second look never swaps an honest refusal for the placeholder
        script[:], calls[:] = [REFUSAL, "", ""], []
        r = ask("When do I get my paycheck?", "e3")
        assert r["reply"] == REFUSAL and r["unanswered"] and not r["second_look"], r
        print("second look OK: an empty second reply keeps the honest first answer")

        # 4. streaming: an empty stream falls back to the normal call (with its retry), not the placeholder
        script[:], calls[:] = [ANSWER], []
        ev = events(c.post(f"/bots/{bid}/chat/stream",
                           json={"session_id": "e4", "message": "What approval do I need for vacation in late December?"}).text)
        done = ev[-1]
        assert done[0] == "done" and done[1]["reply"] == ANSWER and calls[:2] == ["stream", "cheap"], (done, calls)
        print("streaming OK: empty stream -> normal call -> real answer")
    finally:
        main.orchestrator.bot_provider, providers.call, providers.stream = real
print("ALL EMPTY-REPLY TESTS PASSED")
