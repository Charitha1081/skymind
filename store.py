"""Everything SkyMind keeps in Redis: bots and their documents, conversation memory, usage counters.

Each bot is one JSON document (bot:<id>) plus its own keys for vectors, stats, latency and sessions,
so one company's data never mixes with another's and deleting a bot removes all of it.
"""
import hashlib
import json
import re
import secrets
import time

from fastapi import HTTPException

import auth
import embeddings
import examples
import improve
import ingest
import jobs
import knowledge
import planner
import providers
import router
import settings
import web
from runtime import log, state
from security import hash_key


BOTS_SET = "bots"


ADMIN_TOKEN_KEY = "admin_token"


BOT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,79}$")


# ---------- Redis keys ----------

def bot_key(bot_id: str) -> str:
    return f"bot:{bot_id}"


def chat_key(bot_id: str, session_id: str) -> str:
    return f"chat:{bot_id}:{session_id}"


def vectors_key(bot_id: str) -> str:
    return f"vec:{bot_id}"  # meaning-search vectors, one per chunk (hybrid search only)


def stats_key(bot_id: str) -> str:
    return f"stats:{bot_id}"


def latency_key(bot_id: str) -> str:
    return f"latency:{bot_id}"


def sessions_key(bot_id: str) -> str:
    return f"sessioncost:{bot_id}"


# ---------- Bots ----------

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "bot"


def public_info(bot: dict) -> dict:
    return {
        "id": bot["id"],
        "name": bot["name"],
        "company": bot["company"],
        "greeting": bot["greeting"],
        "access": auth.public_access(bot.get("access")),
        "job": bot.get("job", "answer"),
        "job_label": jobs.get(bot.get("job")).get("label"),
        "max_message": jobs.get(bot.get("job"))["max_message"],
    }


async def load_bot(bot_id: str) -> dict:
    """Load a bot (cached for a few seconds so busy bots do not hit Redis for their documents every time)."""
    if not BOT_ID_RE.match(bot_id):
        raise HTTPException(404, "Bot not found")
    cached = state.bot_cache.get(bot_id)
    now = time.monotonic()
    if cached and now - cached[0] < settings.BOT_CACHE_SECONDS:
        return cached[1]
    raw = await state.redis.get(bot_key(bot_id))
    if raw is None:
        state.bot_cache.pop(bot_id, None)
        raise HTTPException(404, "Bot not found")
    bot = json.loads(raw)
    bot["_index"] = knowledge.build_index(bot["chunks"])
    if bot.get("search") == "hybrid":
        raw_vec = await state.redis.get(vectors_key(bot_id))
        bot["_vectors"] = json.loads(raw_vec) if raw_vec else None
    state.bot_cache[bot_id] = (now, bot)
    return bot


async def all_bots() -> list[dict]:
    bots = []
    for bot_id in await state.redis.smembers(BOTS_SET):
        raw = await state.redis.get(bot_key(bot_id))
        if raw:
            bots.append(json.loads(raw))
    return sorted(bots, key=lambda b: b["created_at"])


async def embed_or_fail(chunks: list[dict]) -> list[list[float]]:
    try:
        return await embeddings.embed_chunks(state.http, chunks)
    except embeddings.EmbeddingError as err:
        log.warning("Embedding failed: %s", err)
        raise HTTPException(502, "Could not prepare meaning search right now (Gemini embeddings). Try again, or use search: bm25.")


async def _resolve_quiet(host: str) -> list[str]:
    """Look up a website name; if DNS can't answer right now, accept it (the fetch checks again later)."""
    try:
        return await ingest._resolve(host)
    except OSError:
        return ["8.8.8.8"]


async def create_bot(body: dict, fixed_id: str | None = None, featured: bool = False, owner_email: str = "") -> dict:
    """Plan a bot, split its documents and store it. Raises HTTPException on bad input."""
    name = str(body.get("bot_name", "")).strip()
    if not 1 <= len(name) <= 60:
        raise HTTPException(422, "bot_name is required (1 to 60 characters)")
    company = str(body.get("company") or name).strip()[:80]

    text = body.get("knowledge", "")
    if isinstance(text, list):
        text = "\n\n".join(f"## {d.get('title', 'Document')}\n{d.get('text', '')}" for d in text if isinstance(d, dict))
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(422, "Add the documents your bot should answer from (paste text or upload a file).")
    if len(text) > settings.MAX_KNOWLEDGE_CHARS:
        raise HTTPException(422, f"Documents are too long (limit {settings.MAX_KNOWLEDGE_CHARS:,} characters).")

    job = str(body.get("job") or "answer").strip().lower()
    if job not in jobs.JOBS:
        raise HTTPException(422, f"job must be one of: {', '.join(jobs.JOBS)}")
    if jobs.get(job)["tier"]:  # reviews and ideas always use the strong model, so plan the cost for it
        body = {**body, "model": jobs.get(job)["tier"]}
    try:
        spec = planner.parse_spec(body)
        result = planner.plan(spec)
        access = auth.parse_access(body.get("access"))
    except ValueError as err:
        raise HTTPException(422, str(err))
    if access["mode"] == "google" and not auth.google_enabled():
        raise HTTPException(422, "Google sign-in is not set up on this server, so the bot can only be public.")
    search = str(body.get("search") or settings.SEARCH_METHOD).strip().lower()
    if search not in knowledge.SEARCH_METHODS:
        raise HTTPException(422, f"search must be one of: {', '.join(knowledge.SEARCH_METHODS)}")
    if search == "hybrid" and not embeddings.available():
        raise HTTPException(422, "Meaning search needs GEMINI_API_KEY on the server. Use search: bm25.")
    try:
        website = web.normalise_website(str(body.get("website") or ""))
    except ValueError as err:
        raise HTTPException(422, str(err))
    if website:
        try:
            await ingest.check_public_url(website, resolve=lambda h: _resolve_quiet(h))
        except ingest.IngestError as err:
            raise HTTPException(422, str(err))
    if not providers.available(spec["provider"]):
        raise HTTPException(422, f"The {providers.PROVIDERS[spec['provider']]['label']} provider is not set up on this server.")

    if await state.redis.scard(BOTS_SET) >= settings.MAX_BOTS:
        raise HTTPException(409, f"Bot limit reached ({settings.MAX_BOTS}). Delete a bot first.")

    chunks = knowledge.make_chunks(text)
    if not chunks:
        raise HTTPException(422, "Could not read any text from the documents.")

    greeting = str(body.get("greeting") or jobs.get(job)["greeting"].format(name=name, company=company)).strip()[:200]
    bot_id = fixed_id or f"{slugify(name)}-{secrets.token_hex(4)}"  # hard to guess
    owner_key = secrets.token_urlsafe(24)  # shown once to the company that deployed it
    notes = list(result["notes"])
    if any(m in ("summary", "long_term") for m in spec["memory"]):
        notes.insert(0, "Memory types 'summary' and 'long_term' are planned. For now this bot keeps the recent messages of each conversation.")

    bot = {
        "id": bot_id,
        "name": name,
        "company": company,
        "greeting": greeting,
        "created_at": int(time.time()),
        "spec": spec,
        "plan": result,
        "llm_budget": max(spec["budget"] - result["cost"]["infra"], 0.0),
        "chunks": chunks,
        "featured": featured,
        "owner_key_hash": hash_key(owner_key),
        "owner_email": owner_email,
        "access": access,
        "search": search,
        "job": job,
        "website": website,
        "web_lookup": bool(website) and bool(body.get("web_lookup", True)) and job == "answer",
    }
    if search == "hybrid":  # embed before saving, so a failure leaves nothing half-made
        await state.redis.set(vectors_key(bot_id), json.dumps(await embed_or_fail(chunks)))
    await state.redis.set(bot_key(bot_id), json.dumps(bot))
    await state.redis.sadd(BOTS_SET, bot_id)

    return {
        "bot_id": bot_id,
        "name": name,
        "company": company,
        "chat_url": f"/chat/{bot_id}",
        "chunks": len(chunks),
        "plan": result,
        "summary": planner.format_plan(result),
        "notes": notes,
        "owner_key": owner_key,
        "owner_email": owner_email,
        "access": access,
        "job": job,
    }


async def seed_examples() -> None:
    """Make sure the sample bots exist at stable links (free hosting wipes Redis on restart)."""
    if not await state.redis.set("seed_lock", "1", nx=True, ex=60):
        return  # another worker is seeding
    created = []
    for ex in examples.EXAMPLES:
        bot_id = slugify(ex["bot_name"])
        raw = await state.redis.get(bot_key(bot_id))
        if raw is None:
            body = {k: v for k, v in ex.items() if k != "key"}
            await create_bot(body, fixed_id=bot_id, featured=True)
            bot = json.loads(await state.redis.get(bot_key(bot_id)))
            bot["sample_hash"] = hashlib.sha256(ex["knowledge"].encode()).hexdigest()[:16]
            await state.redis.set(bot_key(bot_id), json.dumps(bot))
            created.append("/chat/" + bot_id)
        else:
            bot = json.loads(raw)
            changed = not bot.get("featured")
            bot["featured"] = True
            # Redis outlives a code update on hosting, so bring a sample bot's documents up to date
            # when examples.py changes (only for unowned sample bots).
            sample_hash = hashlib.sha256(ex["knowledge"].encode()).hexdigest()[:16]
            if not bot.get("owner_email") and (bot.get("website", "") != ex.get("website", "")
                                               or bool(bot.get("web_lookup")) != bool(ex.get("web_lookup"))):
                bot["website"], bot["web_lookup"] = ex.get("website", ""), bool(ex.get("web_lookup"))
                changed = True
            if not bot.get("owner_email") and bot.get("sample_hash") != sample_hash:
                bot["chunks"] = knowledge.make_chunks(ex["knowledge"])
                bot["sample_hash"] = sample_hash
                if bot.get("search") == "hybrid":
                    bot["search"] = "bm25"
                    await state.redis.delete(vectors_key(bot_id))
                changed = True
                created.append("/chat/" + bot_id + " (documents updated)")
            if changed:
                await state.redis.set(bot_key(bot_id), json.dumps(bot))
                state.bot_cache.pop(bot_id, None)
    if created:
        print("SkyMind: sample bots deployed (" + ", ".join(created) + ")", flush=True)


# ---------- Conversation memory ----------

async def load_history(bot_id: str, session_id: str) -> list[dict]:
    raw = await state.redis.lrange(chat_key(bot_id, session_id), 0, -1)
    return [json.loads(item) for item in raw]


async def save_turn(bot_id: str, session_id: str, user_msg: str, bot_msg: str) -> int:
    key = chat_key(bot_id, session_id)
    pipe = state.redis.pipeline()
    pipe.rpush(key, json.dumps({"role": "user", "content": user_msg}))
    pipe.rpush(key, json.dumps({"role": "assistant", "content": bot_msg}))
    pipe.ltrim(key, -2 * settings.MEMORY_WINDOW, -1)  # keep only the last N exchanges
    pipe.expire(key, settings.MEMORY_TTL_SECONDS)
    pipe.llen(key)
    results = await pipe.execute()
    return results[-1]


# ---------- Usage, cost and quality counters ----------

async def record_stats(
    bot_id: str, tier: str, input_tokens: int, output_tokens: int, latency_ms: float, session_id: str,
    provider: str = "anthropic",
) -> float:
    """Count the request and compare its cost with sending everything to the strong model."""
    actual = router.request_cost(tier, input_tokens, output_tokens, provider)
    all_strong = router.request_cost("strong", input_tokens, output_tokens, provider)
    key = stats_key(bot_id)
    pipe = state.redis.pipeline()
    pipe.hincrby(key, f"{tier}_requests", 1)
    pipe.hincrby(key, "input_tokens", input_tokens)
    pipe.hincrby(key, "output_tokens", output_tokens)
    pipe.hincrbyfloat(key, "actual_cost_usd", actual)
    pipe.hincrbyfloat(key, "all_strong_cost_usd", all_strong)
    pipe.lpush(latency_key(bot_id), latency_ms)
    pipe.ltrim(latency_key(bot_id), 0, 999)  # keep the last 1000 requests
    pipe.zincrby(sessions_key(bot_id), actual, session_id)
    await pipe.execute()
    return actual


async def bot_stats(bot_id: str) -> tuple[dict, list[float]]:
    r = state.redis
    report = router.summarize(await r.hgetall(stats_key(bot_id)))
    latencies = [float(x) for x in await r.lrange(latency_key(bot_id), 0, -1)]
    report["latency"] = router.latency_summary(latencies)
    report["sessions"] = await r.zcard(sessions_key(bot_id))
    top = await r.zrevrange(sessions_key(bot_id), 0, 4, withscores=True)
    report["top_sessions"] = [{"session_id": s, "cost_usd": round(c, 8)} for s, c in top]
    return report, latencies


async def quality_counts(bot_id: str) -> dict:
    r = state.redis
    up, down = await r.hmget(stats_key(bot_id), ["thumbs_up", "thumbs_down"])
    return {"helpful": int(up or 0), "not_helpful": int(down or 0), "gaps": await r.zcard(improve.gaps_key(bot_id))}
