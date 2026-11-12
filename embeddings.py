"""Meaning-based search: turn text into embeddings (lists of numbers that capture meaning).

Texts with similar meaning get vectors pointing in similar directions, so "What are your
products?" lands close to "Acme sells tents and backpacks" even with no shared words.
Similarity = cosine of the angle between two vectors (1 = same direction, 0 = unrelated).

Uses Google's gemini-embedding-001 (needs GEMINI_API_KEY; has a free tier):
  - documents are embedded once when a bot is deployed or gets new information
    (task RETRIEVAL_DOCUMENT), questions on every chat (task RETRIEVAL_QUERY)
  - vectors are shortened to EMBED_DIM numbers (768) and re-normalised to length 1,
    which Google requires for any size other than 3072
If anything fails, SkyMind falls back to BM25 word search, so chat never breaks.
"""
import asyncio
import math
import os

import httpx

import providers

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
BATCH = 50              # texts per request (Google suggests staying under 100)
MAX_TEXT_CHARS = 6000   # about 1,500 tokens; the model reads at most 2,048
URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:batchEmbedContents"


class EmbeddingError(RuntimeError):
    pass


def available() -> bool:
    return bool(providers.GEMINI_API_KEY)


def normalise(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [round(x / n, 5) for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both already have length 1


async def _post(http: httpx.AsyncClient, texts: list[str], task: str) -> list[list[float]]:
    model = f"models/{EMBED_MODEL}"
    config = {"taskType": task, "outputDimensionality": EMBED_DIM}
    bodies = (
        {"requests": [{"model": model, "content": {"parts": [{"text": t}]}, "embedContentConfig": config} for t in texts]},
        # older field names, in case the API version in use doesn't accept embedContentConfig
        {"requests": [{"model": model, "content": {"parts": [{"text": t}]}, **config} for t in texts]},
    )
    last = ""
    for attempt in range(4):
        body = bodies[0] if attempt == 0 or "embedContentConfig" not in last else bodies[1]
        try:
            resp = await http.post(URL.format(model=EMBED_MODEL), json=body, timeout=30,
                                   headers={"x-goog-api-key": providers.GEMINI_API_KEY, "content-type": "application/json"})
        except httpx.HTTPError as err:
            last = type(err).__name__
            await asyncio.sleep(1.5 * (attempt + 1))
            continue
        if resp.status_code == 200:
            vectors = [e.get("values") or [] for e in resp.json().get("embeddings", [])]
            if len(vectors) != len(texts) or not all(vectors):
                raise EmbeddingError("embedding response did not match the request")
            return [normalise(v) for v in vectors]
        last = resp.text[:300]
        if resp.status_code in (429, 500, 503):
            await asyncio.sleep(4 * (attempt + 1))  # free tier: back off and retry
        elif resp.status_code != 400 or attempt > 0:
            break
    raise EmbeddingError(f"embedding request failed: {last}")


async def embed(http: httpx.AsyncClient, texts: list[str], task: str) -> list[list[float]]:
    if not available():
        raise EmbeddingError("GEMINI_API_KEY is not set")
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        out += await _post(http, [t[:MAX_TEXT_CHARS] for t in texts[i:i + BATCH]], task)
    return out


async def embed_chunks(http: httpx.AsyncClient, chunks: list[dict]) -> list[list[float]]:
    return await embed(http, [f"{c['title']}\n{c['text']}" for c in chunks], "RETRIEVAL_DOCUMENT")


async def embed_query(http: httpx.AsyncClient, question: str) -> list[float]:
    return (await embed(http, [question], "RETRIEVAL_QUERY"))[0]
