import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Streaming answers: provider stream parsers, the /chat/stream endpoint, and its fallbacks."""
import asyncio, json
import fakeredis, httpx
from fastapi.testclient import TestClient
import examples, main, providers

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
main.settings.STREAM_MOCK_DELAY_S = 0


def events(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.strip().split("\n\n"):
        name = next(l[6:].strip() for l in block.splitlines() if l.startswith("event:"))
        data = json.loads(next(l[5:] for l in block.splitlines() if l.startswith("data:")))
        out.append((name, data))
    return out


# 1. each provider's streaming format is parsed into pieces + token counts
ANTHROPIC = "".join(f"event: {e}\ndata: {json.dumps(d)}\n\n" for e, d in [
    ("message_start", {"type": "message_start", "message": {"model": "claude-haiku-5-5", "usage": {"input_tokens": 42}}}),
    ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}),
    ("content_block_delta", {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello"}}),
    ("ping", {"type": "ping"}),
    ("content_block_delta", {"type": "content_block_delta", "delta": {"type": "text_delta", "text": " world"}}),
    ("message_delta", {"type": "message_delta", "usage": {"output_tokens": 7}}),
    ("message_stop", {"type": "message_stop"}),
])
GEMINI = "".join(f"data: {json.dumps(d)}\r\n\r\n" for d in [
    {"candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}]}}]},
    {"candidates": [{"content": {"parts": [{"text": "Hel"}]}}], "modelVersion": "gemini-3.1-flash-lite"},
    {"candidates": [{"content": {"parts": [{"text": "lo world"}]}}],
     "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 5, "thoughtsTokenCount": 3}},
])
OLLAMA = "\n".join(json.dumps(d) for d in [
    {"message": {"content": "Hello"}, "done": False},
    {"message": {"content": " world"}, "done": False},
    {"message": {"content": ""}, "done": True, "model": "qwen3.5:0.8b", "prompt_eval_count": 30, "eval_count": 4},
])


def handler(req: httpx.Request) -> httpx.Response:
    host = req.url.host
    body = json.loads(req.content)
    if "anthropic" in host:
        assert body["stream"] is True and req.headers["x-api-key"] == "test-key"
        return httpx.Response(200, text=ANTHROPIC, headers={"content-type": "text/event-stream"})
    if "googleapis" in host:
        assert ":streamGenerateContent" in req.url.path and req.url.params["alt"] == "sse"
        return httpx.Response(200, text=GEMINI, headers={"content-type": "text/event-stream"})
    assert body["stream"] is True
    return httpx.Response(200, text=OLLAMA)


async def collect(provider):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        parts, done = [], None
        async for kind, value in providers.stream(http, provider, "cheap", "sys", [{"role": "user", "content": "hi"}], 100, 10):
            if kind == "text":
                parts.append(value)
            else:
                done = value
        return "".join(parts), done

providers.ANTHROPIC_API_KEY = providers.GEMINI_API_KEY = "test-key"
providers.OLLAMA_URL = "http://ollama.local:11434"
for name, tokens in [("anthropic", (42, 7)), ("gemini", (40, 8)), ("ollama", (30, 4))]:
    text, done = asyncio.run(collect(name))
    assert text == "Hello world", (name, text)
    assert (done["input_tokens"], done["output_tokens"]) == tokens, (name, done)
print("provider streams OK: Claude, Gemini (thinking hidden, thinking tokens billed), Ollama")


async def failing(provider):
    def bad(req):
        return httpx.Response(401, text='{"error": "invalid key"}')
    async with httpx.AsyncClient(transport=httpx.MockTransport(bad)) as http:
        async for _ in providers.stream(http, provider, "cheap", "s", [{"role": "user", "content": "x"}], 10, 5):
            pass
for name in ("anthropic", "gemini", "ollama"):
    try:
        asyncio.run(failing(name))
        raise AssertionError("should fail")
    except providers.ProviderError as err:
        assert err.status == 401 and not err.retryable
print("provider errors OK: bad key is a non-retryable ProviderError")
providers.ANTHROPIC_API_KEY = providers.GEMINI_API_KEY = providers.OLLAMA_URL = ""  # back to no keys

# 2. the endpoint (mock provider): start, many text pieces, done with the same fields as /chat
with TestClient(main.app) as c:
    body = {k: v for k, v in examples.EXAMPLES[1].items() if k != "key"}
    body["provider"] = "mock"
    d = c.post("/bots", json=body).json()
    bid, KEY = d["bot_id"], {"X-Owner-Key": d["owner_key"]}
    r = c.post(f"/bots/{bid}/chat/stream", json={"session_id": "s1", "message": "What is your return policy?"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache" and r.headers["x-accel-buffering"] == "no"
    evs = events(r.text)
    assert evs[0][0] == "start" and evs[0][1]["sources"][0] == "Returns and refunds"
    texts = [e[1]["text"] for e in evs if e[0] == "text"]
    assert len(texts) > 10, "the answer arrives in many pieces"
    name, done = evs[-1]
    assert name == "done" and done["reply"] == "".join(texts) and "30 days" in done["reply"]
    assert done["streamed"] and done["first_token_ms"] is not None and done["answer_id"] and done["history_messages"] == 2
    print("stream OK:", len(texts), "pieces, then done with answer_id, memory and timing")

    # the streamed answer counts like any other: memory, stats, gaps, rating
    r2 = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "s1", "message": "Do you sell kayaks?"}).text)[-1][1]
    assert r2["unanswered"] and r2["history_messages"] == 4
    assert c.get(f"/bots/{bid}/usage", headers=KEY).json()["requests"] == 2
    assert c.post(f"/bots/{bid}/feedback", json={"session_id": "s1", "answer_id": done["answer_id"], "helpful": True}).json()["recorded"]
    assert [g["question"] for g in c.get(f"/bots/{bid}/improve", headers=KEY).json()["gaps"]] == ["Do you sell kayaks?"]
    print("bookkeeping OK: memory, usage, gap log and rating work for streamed answers")

    # 3. problems found before streaming are normal HTTP errors (not half-open streams)
    assert c.post("/bots/nope-12345678/chat/stream", json={"session_id": "s", "message": "hi"}).status_code == 404
    assert c.post(f"/bots/{bid}/chat/stream", json={"session_id": "s", "message": "x" * 4001}).status_code == 422
    assert c.post(f"/bots/{bid}/chat/stream", json={"session_id": "bad id!", "message": "hi"}).status_code == 422
    print("early errors OK: 404 / 422 before any stream starts")

    # 4. a real provider: streaming fails before any text -> the normal call answers instead
    real = (main.orchestrator.bot_provider, providers.stream, providers.call)
    main.orchestrator.bot_provider = lambda b: "anthropic"
    providers.ANTHROPIC_API_KEY = "test-key"  # (calls are replaced below; nothing reaches the network)

    async def stream_fails_early(*a, **k):
        raise providers.ProviderError("overloaded", 529)
        yield  # (makes this an async generator)

    async def call_ok(*a, **k):
        return {"text": "Returns are accepted within 30 days.", "model": "claude-haiku-5-5", "input_tokens": 50, "output_tokens": 9}

    async def stream_fails_halfway(*a, **k):
        yield "text", "Returns are accepted "
        raise providers.ProviderError("connection reset", 0)

    async def call_fails(*a, **k):
        raise providers.ProviderError("down", 503)

    async def stream_ok(*a, **k):
        for piece in ["Returns ", "are ", "accepted ", "within 30 days."]:
            yield "text", piece
        yield "done", {"model": "claude-haiku-5-5", "input_tokens": 50, "output_tokens": 9}
    try:
        providers.stream, providers.call = stream_ok, call_ok
        ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "p0", "message": "Return policy?"}).text)
        assert [e[0] for e in ev] == ["start", "text", "text", "text", "text", "done"]
        assert ev[-1][1]["reply"] == "Returns are accepted within 30 days." and ev[-1][1]["output_tokens"] == 9

        providers.stream = stream_fails_early
        ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "p1", "message": "Return policy?"}).text)
        assert ev[-1][0] == "done" and ev[-1][1]["reply"] == "Returns are accepted within 30 days.", ev
        assert ev[-1][1]["streamed"] is False

        providers.stream = stream_fails_halfway
        ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "p2", "message": "Return policy?"}).text)
        assert ev[-1][0] == "done" and ev[-1][1]["reply"].startswith("Returns are accepted") and "cut off" in ev[-1][1]["reply"]

        providers.stream, providers.call = stream_fails_early, call_fails
        ev = events(c.post(f"/bots/{bid}/chat/stream", json={"session_id": "p3", "message": "Return policy?"}).text)
        assert ev[-1][0] == "error" and "not available" in ev[-1][1]["detail"], ev
        assert "down" not in ev[-1][1]["detail"], "internal errors are not shown to users"
    finally:
        main.orchestrator.bot_provider, providers.stream, providers.call = real
        providers.ANTHROPIC_API_KEY = ""
    print("fallbacks OK: early failure -> normal call; halfway -> partial + note; both down -> error event")
print("ALL STREAMING TESTS PASSED")
