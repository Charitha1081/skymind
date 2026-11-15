import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""The orchestrator: the trace of every answer, and the second look when the first search finds nothing."""
import json
import fakeredis
from fastapi.testclient import TestClient
import examples, main, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
main.settings.STREAM_MOCK_DELAY_S = 0
REFUSAL = "I don't have that information. Please contact Acme Outdoor Gear directly."
ANSWER = "You can reach a person through Contact support."
calls = []


def reply_for(system, messages):
    """A stand-in model: it answers questions about reaching support, and only when the
    Contact support section is in its prompt. Everything else it honestly refuses."""
    question = messages[-1]["content"].lower()
    about_support = "person" in question or "support" in question
    return ANSWER if about_support and "[Contact support]" in system else REFUSAL


async def fake_call(http, provider, tier, system, messages, max_tokens, timeout):
    calls.append(tier)
    return {"text": reply_for(system, messages), "model": "claude-haiku-5-5", "input_tokens": 100, "output_tokens": 10}


async def fake_stream(http, provider, tier, system, messages, max_tokens, timeout):
    calls.append(tier)
    for word in reply_for(system, messages).split(" "):
        yield "text", word + " "
    yield "done", {"model": "claude-haiku-5-5", "input_tokens": 100, "output_tokens": 10}


def events(text):
    out = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        out.append((lines["event"], json.loads(lines["data"])))
    return out


with TestClient(main.app) as c:
    body = {k: v for k, v in next(e for e in examples.EXAMPLES if e["key"] == "acme").items() if k not in ("key", "website")}
    body["model"] = "cheap"
    bid = c.post("/bots", json=body).json()["bot_id"]
    ask = lambda m, s: c.post(f"/bots/{bid}/chat", json={"session_id": s, "message": m}).json()

    # 1. every answer carries a trace of what SkyMind did (mock provider: no second look)
    r = ask("What is the return policy?", "t1")
    steps = [s["step"] for s in r["trace"]]
    assert steps == ["Checks", "Route", "Search", "Model", "Save and record"], steps
    assert all(s["ms"] >= 0 and s["detail"] for s in r["trace"]) and "document sections" in r["trace"][2]["detail"]
    r = ask("Do you sell kayaks?", "t2")
    assert r["unanswered"] and not r["second_look"] and "Second look" not in [s["step"] for s in r["trace"]]
    print("trace OK:", " > ".join(steps))

    real = (main.orchestrator.bot_provider, providers.call, providers.stream)
    main.orchestrator.bot_provider = lambda b: "anthropic"
    providers.ANTHROPIC_API_KEY = "test-key"  # (calls are replaced; nothing reaches the network)
    providers.call, providers.stream = fake_call, fake_stream
    try:
        # 2. the first search misses the section ("talk to a person" shares no words with it):
        #    the model says it has no answer, SkyMind searches wider and asks once more
        calls.clear()
        r = ask("How can I talk to a person?", "a1")
        assert r["reply"] == ANSWER and r["second_look"] and not r["unanswered"], r
        assert len(calls) == 2 and r["input_tokens"] == 200 and r["output_tokens"] == 20, "both calls are counted"
        assert "Contact support" in r["sources"] and "more widely" in r["route_reason"]
        look = next(s for s in r["trace"] if s["step"] == "Second look")
        assert "found the answer" in look["detail"]
        print("second look OK:", look["detail"])

        # 3. a question the documents really can't answer: still refused, logged as a gap, both calls paid for
        calls.clear()
        r = ask("Do you sell kayaks?", "a2")
        assert r["reply"] == REFUSAL and r["unanswered"] and not r["second_look"] and len(calls) == 2
        assert r["input_tokens"] == 200
        assert "still no answer" in next(s for s in r["trace"] if s["step"] == "Second look")["detail"]
        gaps = [g["question"] for g in c.get(f"/bots/{bid}/improve", headers={"X-Admin-Token": main.app.state.admin_token}).json()["gaps"]]
        assert any("kayaks" in g.lower() for g in gaps) and not any("talk to a person" in g.lower() for g in gaps), gaps
        print("honest refusal OK: a wider search never invents an answer; the gap is logged")

        # 4. answered the first time: one call, no second look
        calls.clear()
        r = ask("What is the support email or phone number in Contact support?", "a3")
        assert r["reply"] == ANSWER and len(calls) == 1 and not r["second_look"]

        # 5. streaming: the refusal streams, then the page is told to replace it with the better answer
        calls.clear()
        ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "a4", "message": "How can I talk to a person?"}).text)
        kinds = [e[0] for e in ev]
        assert kinds[0] == "start" and kinds[-1] == "done" and "searching" in kinds, kinds
        at = kinds.index("searching")
        assert "more widely" in ev[at][1]["note"] and ev[at + 1] == ("text", {"text": ANSWER})
        done = ev[-1][1]
        assert done["reply"] == ANSWER and done["second_look"] and done["streamed"] and len(calls) == 2
        assert [s["step"] for s in done["trace"]] == ["Checks", "Route", "Search", "Model", "Second look", "Save and record"]
        print("streaming OK:", " > ".join(kinds[:2] + ["..."] + kinds[at:]))

        # 6. the second look can be switched off
        main.settings.SECOND_LOOK = False
        calls.clear()
        r = ask("How can I talk to a person?", "a5")
        assert r["reply"] == REFUSAL and len(calls) == 1 and not r["second_look"]
        main.settings.SECOND_LOOK = True
        print("switch OK: SECOND_LOOK=false gives the old behaviour")
    finally:
        main.orchestrator.bot_provider, providers.call, providers.stream = real
        providers.ANTHROPIC_API_KEY = ""
print("ALL ORCHESTRATOR TESTS PASSED")

# 7. the model is told which other topics exist, so it can say what it helps with
#    (it used to describe its whole scope from the two sections search happened to return)
bot = {"company": "UNT", "chunks": [{"title": t, "text": "..."} for t in
       ["About UNT", "Housing", "Meal plans", "Parking permits", "AI Expo by SSAI"]]}
p = main.orchestrator.build_system_prompt(bot, [{"title": "AI Expo by SSAI", "text": "The expo is on Nov 16."}])
assert "Housing; Meal plans; Parking permits" in p, "other topics must be listed"
assert "AI Expo by SSAI;" not in p, "the section already shown must not repeat in the list"
assert "NOT been shown" in p and "from a topic name alone" in p, "must forbid answering from a title"
assert "also cover these topics" not in main.orchestrator.build_system_prompt({"company": "X"}, []), \
    "no topic list when the bot has no other sections"
print("topic list OK: the bot can say what it covers without being shown the text")

# 8. only the sections the answer was really written from are named underneath it.
#    Search returns three sections for a housing question, one of which is the health centre; the
#    answer never mentions it, and because the chips are clickable, naming it is a visible false
#    citation. (Real sections and a real retrieval, not a hand-made example.)
import knowledge
unt = next(e for e in examples.EXAMPLES if "North Texas" in e.get("company", ""))
ch = knowledge.make_chunks(unt["knowledge"])
got = knowledge.retrieve(knowledge.build_index(ch), ch, "What are the housing options available at unt", k=3, method="bm25")
assert [s["title"] for s in got] == ["Housing", "Housing contact", "Student Health and Wellness Center (doctor visits)"], got
housing_answer = ("UNT has 15 residence halls. Living Learning Communities are also available. To apply, use the "
                  "Housing Portal linked from housing.unt.edu; payments go through your myUNT account. Housing and "
                  "Residence Life is in the UNT Welcome Center, 1417 Maple St, Denton, TX 76201, housinginfo@unt.edu.")
named = [s["title"] for s in main.orchestrator.shown_sources({"sources": got}, housing_answer)]
assert named == ["Housing", "Housing contact"], f"the health centre must not be cited: {named}"

# a section quoted for a single fact is still kept, and one source is never filtered away
one_line = got[0]["text"].split(". ")[0]
assert got[0]["title"] in [s["title"] for s in main.orchestrator.shown_sources({"sources": got}, one_line)]
assert len(main.orchestrator.shown_sources({"sources": got[:1]}, "unrelated text")) == 1
# after a second look the wide search saw many loose sections: only the best one is named
assert len(main.orchestrator.shown_sources({"sources": got, "second_look": True}, housing_answer)) == 1
print("sources OK:", " + ".join(named), "(health centre dropped)")
