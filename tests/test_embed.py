import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Meaning (hybrid) search, with simulated embeddings so no network is needed."""
import asyncio, json, math
import fakeredis, httpx
from fastapi.testclient import TestClient
import embeddings, examples, knowledge, main, providers

# ---------- 1. the real request format, simulated Google server ----------
providers.GEMINI_API_KEY = "gm-test"
calls = []
def google(request):
    body = json.loads(request.content)
    calls.append(body)
    assert request.headers["x-goog-api-key"] == "gm-test" and request.url.path.endswith("gemini-embedding-001:batchEmbedContents")
    if len(calls) == 1:
        return httpx.Response(429, json={"error": "busy"})
    return httpx.Response(200, json={"embeddings": [{"values": [3.0, 4.0] + [0.0] * 766} for _ in body["requests"]]})
async def fmt():
    real_sleep = asyncio.sleep
    asyncio.sleep = lambda s: real_sleep(0)  # no real waiting in tests
    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(google)) as http:
            v = await embeddings.embed(http, ["a", "b"], "RETRIEVAL_DOCUMENT")
    finally:
        asyncio.sleep = real_sleep
    req = calls[-1]["requests"][0]
    assert req["model"] == "models/gemini-embedding-001" and req["content"]["parts"][0]["text"] == "a"
    assert req["embedContentConfig"] == {"taskType": "RETRIEVAL_DOCUMENT", "outputDimensionality": 768}
    assert len(v) == 2 and abs(v[0][0] - 0.6) < 1e-6 and abs(v[0][1] - 0.8) < 1e-6, "re-normalised to length 1"
asyncio.run(fmt())
print("request format OK: model, task type, 768 dimensions, retry after 429, vectors normalised")

# ---------- 2. fake 'meaning': words that mean the same thing share a dimension ----------
CONCEPTS = [
    {"product", "products", "sell", "sells", "tents", "backpacks", "boots", "gear", "equipment", "items"},
    {"return", "returns", "refund", "refunds", "money", "back"},
    {"ship", "shipping", "delivery", "deliver", "arrive", "express"},
    {"hours", "open", "store", "stores", "closed", "sunday"},
    {"phone", "call", "email", "contact", "support"},
    {"kayak", "kayaks", "boat", "paddle"},
]
def fake_vec(text):
    words = {w.strip(".,?!:()").lower() for w in text.split()}
    v = [float(len(words & c)) for c in CONCEPTS] + [0.05]  # tiny shared dimension so nothing is all-zero
    return embeddings.normalise(v)
async def fake_embed(http, texts, task):
    return [fake_vec(t) for t in texts]
embeddings.embed = fake_embed

srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
with TestClient(main.app) as c:
    body = dict({k: v for k, v in examples.EXAMPLES[1].items() if k != "key"}, provider="mock")
    hy = c.post("/bots", json=dict(body, search="hybrid")).json()
    bm = c.post("/bots", json=dict(body, search="bm25")).json()
    vecs = json.loads(fakeredis.FakeRedis(server=srv, decode_responses=True).get(f"vec:{hy['bot_id']}"))
    assert len(vecs) == hy["chunks"], "one vector per chunk"
    ask = lambda b, m: c.post(f"/bots/{b}/chat", json={"session_id": "s", "message": m}).json()

    q = "What are your products?"
    assert ask(bm["bot_id"], q)["sources"] == [], "word search can't match 'products'"
    assert ask(hy["bot_id"], q)["sources"][0] == "About Acme Outdoor Gear", "meaning search finds it"
    assert ask(hy["bot_id"], "How do I get my money back?")["sources"][0] == "Returns and refunds"
    assert ask(hy["bot_id"], "What is the capital of France?")["sources"] == [], "off-topic still finds nothing"
    print("hybrid OK: 'products' finds 'sells tents', 'money back' finds refunds, off-topic finds nothing")

    # embedding service down during chat -> falls back to BM25, chat still works
    async def broken(http, q): raise embeddings.EmbeddingError("down")
    real_query, embeddings.embed_query = embeddings.embed_query, broken
    main.app.state.bot_cache.clear()
    r = ask(hy["bot_id"], "What is the return policy?")
    assert r["sources"][0] == "Returns and refunds"
    embeddings.embed_query = real_query
    print("fallback OK: embeddings down -> word search, chat keeps working")

    # adding information keeps one vector per chunk; deleting removes vectors
    KEY = {"X-Owner-Key": hy["owner_key"]}
    add = c.post(f"/bots/{hy['bot_id']}/knowledge", headers=KEY, json={"text": "## Boats\nWe stock inflatable kayaks and paddles."}).json()
    vecs = json.loads(fakeredis.FakeRedis(server=srv, decode_responses=True).get(f"vec:{hy['bot_id']}"))
    assert len(vecs) == add["sections"]
    main.app.state.bot_cache.clear()
    assert ask(hy["bot_id"], "Can I buy a boat?")["sources"][0] == "Boats"
    c.delete(f"/bots/{hy['bot_id']}", headers=KEY)
    assert fakeredis.FakeRedis(server=srv, decode_responses=True).get(f"vec:{hy['bot_id']}") is None
    print("updates OK: new information gets vectors, delete removes them")

    providers.GEMINI_API_KEY = ""
    r = c.post("/bots", json=dict(body, search="hybrid"))
    assert r.status_code == 422 and "GEMINI_API_KEY" in r.json()["detail"]
    assert c.get("/providers").json()["embeddings"] is False
print("ALL EMBEDDING TESTS PASSED")
