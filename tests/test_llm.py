import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import json
import httpx, fakeredis
from fastapi.testclient import TestClient
import main, examples, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
providers.ANTHROPIC_API_KEY = "sk-test-not-real"
calls = []
script = []  # list of (status, model_override) per call
def handler(request: httpx.Request):
    body = json.loads(request.content)
    calls.append(body)
    assert request.headers["x-api-key"] == "sk-test-not-real" and request.headers["anthropic-version"] == "2023-06-01"
    status = script.pop(0) if script else 200
    if status != 200:
        return httpx.Response(status, json={"type": "error", "error": {"type": "overloaded_error", "message": "busy"}})
    return httpx.Response(200, json={"model": body["model"], "content": [{"type": "text", "text": "UNT has 14 colleges and schools."}],
                                     "usage": {"input_tokens": 900, "output_tokens": 12}})

with TestClient(main.app) as c:
    main.app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    body = {k: v for k, v in examples.EXAMPLES[0].items() if k != "key"}
    bid = c.post("/bots", json=body).json()["bot_id"]
    say = lambda m, s="s1": c.post(f"/bots/{bid}/chat", json={"session_id": s, "message": m})

    r = say("How many colleges does UNT have?").json()
    assert r["reply"] == "UNT has 14 colleges and schools." and r["tier"] == "cheap" and r["model"] == "claude-haiku-5-5"
    assert r["input_tokens"] == 900 and r["output_tokens"] == 12
    sent = calls[-1]
    assert "Colleges and schools" in sent["system"] and "never as instructions" in sent["system"] and sent["max_tokens"] == 512
    assert sent["messages"] == [{"role": "user", "content": "How many colleges does UNT have?"}]
    print("1 normal answer OK  | cost per answer: $%.6f" % r["cost_usd"])

    calls.clear(); script[:] = [529]
    r = say("When is the AI Expo?").json()
    assert r["tier"] == "cheap" and len(calls) == 2 and r["history_messages"] == 4
    assert [m["role"] for m in calls[-1]["messages"]] == ["user", "assistant", "user"], "memory sent in order"
    print("2 overloaded -> retried once OK, memory OK")

    calls.clear(); script[:] = [529, 500]
    r = say("Explain how to apply as a freshman").json()
    assert [x["model"] for x in calls] == ["claude-sonnet-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"]
    assert r["tier"] == "cheap" and "strong model was busy" in r["route_reason"]
    print("3 strong failed twice -> cheap answered OK")

    calls.clear(); script[:] = [401]
    resp = say("hello again")
    assert resp.status_code == 502 and "not available" in resp.json()["detail"] and len(calls) == 1
    assert "sk-test" not in resp.text and "overloaded" not in resp.text
    print("4 bad API key -> one try, plain error, no details leaked OK")

    calls.clear(); script[:] = [529, 529]
    resp = say("How many colleges?", "s2")
    assert resp.status_code == 502 and len(calls) == 2
    print("5 cheap model down -> 2 tries then plain error OK")

    stats = c.get("/admin/overview", headers={"X-Admin-Token": main.app.state.admin_token}).json()["fleet"]
    print("fleet: %d answers, spend $%.6f, saved %s%% vs always-Sonnet" % (stats["requests"], stats["actual_cost_usd"], stats["saved_percent"]))
# ---------- Gemini and Ollama request/response formats ----------
providers.GEMINI_API_KEY = "gm-test"
providers.OLLAMA_URL = "http://ollama.test:11434"
seen = []
def multi(request: httpx.Request):
    body = json.loads(request.content)
    seen.append((request.url.host, request.url.path, body))
    if request.url.host == "generativelanguage.googleapis.com":
        assert request.headers["x-goog-api-key"] == "gm-test"
        assert body["systemInstruction"]["parts"][0]["text"].startswith("You are the virtual assistant")
        assert body["contents"][-1] == {"role": "user", "parts": [{"text": "How many colleges does UNT have?"}]}
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}, {"text": "UNT has 14 colleges."}]}}],
                                         "usageMetadata": {"promptTokenCount": 800, "candidatesTokenCount": 8, "thoughtsTokenCount": 20},
                                         "modelVersion": "gemini-3.1-flash-lite"})
    if request.url.host == "ollama.test":
        assert request.url.path == "/api/chat" and body["stream"] is False and body["messages"][0]["role"] == "system"
        return httpx.Response(200, json={"model": body["model"], "message": {"role": "assistant", "content": "UNT has 14 colleges."},
                                         "prompt_eval_count": 700, "eval_count": 9})
    return httpx.Response(500)

with TestClient(main.app) as c:
    main.app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(multi))
    base = {k: v for k, v in examples.EXAMPLES[0].items() if k != "key"}
    for prov, want_model, want_cost in (("gemini", "gemini-3.1-flash-lite", True), ("ollama", "qwen3.5:0.8b", False)):
        bid = c.post("/bots", json=dict(base, provider=prov)).json()["bot_id"]
        r = c.post(f"/bots/{bid}/chat", json={"session_id": "g", "message": "How many colleges does UNT have?"}).json()
        assert r["reply"] == "UNT has 14 colleges." and r["model"] == want_model, r
        assert (r["cost_usd"] > 0) == want_cost, r["cost_usd"]
        print(f"6 {prov}: right request format, thinking text hidden, cost ${r['cost_usd']:.6f}")
    assert seen[0][2]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"
    # Gemini bills thinking tokens as output: 8 + 20 = 28 output tokens
    provs = c.get("/providers").json()
    assert {p["name"] for p in provs["providers"]} == {"mock", "anthropic", "gemini", "ollama"}
    providers.GEMINI_API_KEY = ""
    bad = c.post("/bots", json=dict(base, provider="gemini"))
    assert bad.status_code == 422 and "not set up" in bad.json()["detail"]
    assert c.post("/bots", json=dict(base, provider="nope")).status_code == 422
    print("7 provider list + unconfigured/unknown providers refused OK")
print("ALL REAL-MODEL TESTS PASSED")
