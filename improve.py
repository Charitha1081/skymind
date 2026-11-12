"""Helping companies improve their bots: the questions a bot couldn't answer, and answer ratings.

The improvement loop:
  1. A customer asks something the documents don't cover. The bot says "I don't have that",
     and SkyMind logs the question (log_gap). Repeated questions are counted.
  2. Customers rate answers helpful or not (record_feedback). Not-helpful answers are kept.
  3. The company opens "Improve" on /deploy, sees the gaps and bad answers, adds the missing
     information, and marks the gaps fixed. The evaluation set measures the improvement.

Redis keys (all per bot, removed with the bot):
  gaps:{bot}         sorted set: normalised question -> times asked
  gaptext:{bot}      hash: normalised question -> the question as first asked
  answer:{bot}:{id}  string (JSON): an answer that can be rated, kept 7 days
  rated:{bot}:{id}   marker: this answer was already rated (one rating per answer)
  feedback:{bot}     list (JSON): the latest not-helpful answers
"""
import json
import secrets
import time

MAX_GAPS = 500          # distinct questions kept per bot
MAX_BAD_ANSWERS = 200   # not-helpful answers kept per bot
ANSWER_TTL = 7 * 24 * 3600

# Phrases that mean "I could not answer". Kept specific so a normal answer that says
# "contact support at 555-0100" is not counted as a gap.
REFUSAL_MARKERS = (
    "don't have that", "do not have that", "don't have information", "do not have information",
    "don't have any information", "do not have any information", "don't have details",
    "do not have details", "not able to find", "unable to find", "couldn't find", "could not find",
    "can't find", "cannot find", "no information about", "not in my documents", "isn't in my documents",
    "is not in my documents", "not covered in", "isn't covered", "i don't know", "i do not know",
)


def gaps_key(bot_id: str) -> str:
    return f"gaps:{bot_id}"


def gaptext_key(bot_id: str) -> str:
    return f"gaptext:{bot_id}"


def answer_key(bot_id: str, answer_id: str) -> str:
    return f"answer:{bot_id}:{answer_id}"


def rated_key(bot_id: str, answer_id: str) -> str:
    return f"rated:{bot_id}:{answer_id}"


def feedback_key(bot_id: str) -> str:
    return f"feedback:{bot_id}"


def bot_keys(bot_id: str) -> list[str]:
    """Fixed-name keys to delete with the bot (answer:/rated: keys expire on their own)."""
    return [gaps_key(bot_id), gaptext_key(bot_id), feedback_key(bot_id)]


def is_unanswered(reply: str) -> bool:
    """True when the bot said it couldn't answer (checked near the start of the reply)."""
    head = reply[:300].lower().replace("’", "'")
    return any(m in head for m in REFUSAL_MARKERS)


def _normalise(question: str) -> tuple[str, str]:
    text = " ".join(question.split())[:300]
    return text, text.lower().strip(" ?!.")


async def log_gap(redis, bot_id: str, question: str) -> None:
    text, norm = _normalise(question)
    if not norm:
        return
    pipe = redis.pipeline()
    pipe.zincrby(gaps_key(bot_id), 1, norm)
    pipe.hsetnx(gaptext_key(bot_id), norm, text)
    pipe.zcard(gaps_key(bot_id))
    _, _, size = await pipe.execute()
    if size > MAX_GAPS:  # forget the least-asked questions
        dropped = await redis.zrange(gaps_key(bot_id), 0, size - MAX_GAPS - 1)
        if dropped:
            await redis.zrem(gaps_key(bot_id), *dropped)
            await redis.hdel(gaptext_key(bot_id), *dropped)


async def list_gaps(redis, bot_id: str, limit: int = 50) -> list[dict]:
    rows = await redis.zrevrange(gaps_key(bot_id), 0, limit - 1, withscores=True)
    if not rows:
        return []
    texts = await redis.hmget(gaptext_key(bot_id), [q for q, _ in rows])
    return [{"question": t or q, "key": q, "count": int(n)} for (q, n), t in zip(rows, texts)]


async def clear_gap(redis, bot_id: str, key: str | None = None) -> None:
    if key is None:
        await redis.delete(gaps_key(bot_id), gaptext_key(bot_id))
    else:
        await redis.zrem(gaps_key(bot_id), key)
        await redis.hdel(gaptext_key(bot_id), key)


async def remember_answer(redis, bot_id: str, session_id: str, question: str, reply: str, model: str) -> str:
    """Keep an answer for 7 days so the person who got it can rate it."""
    answer_id = secrets.token_urlsafe(9)
    record = {"session_id": session_id, "question": question[:1000], "answer": reply[:4000],
              "model": model, "at": int(time.time())}
    await redis.set(answer_key(bot_id, answer_id), json.dumps(record), ex=ANSWER_TTL)
    return answer_id


async def record_feedback(redis, bot_id: str, session_id: str, answer_id: str, helpful: bool,
                          stats_key: str, comment: str = "") -> str:
    """Returns 'ok', 'unknown' (no such answer for this conversation) or 'duplicate'."""
    raw = await redis.get(answer_key(bot_id, answer_id))
    if not raw:
        return "unknown"
    record = json.loads(raw)
    if record["session_id"] != session_id:
        return "unknown"  # only the person who got the answer can rate it
    if not await redis.set(rated_key(bot_id, answer_id), "1", nx=True, ex=ANSWER_TTL):
        return "duplicate"
    pipe = redis.pipeline()
    pipe.hincrby(stats_key, "thumbs_up" if helpful else "thumbs_down", 1)
    if not helpful:
        entry = {k: record[k] for k in ("question", "answer", "model", "at")}
        entry["comment"] = comment[:500]
        pipe.lpush(feedback_key(bot_id), json.dumps(entry))
        pipe.ltrim(feedback_key(bot_id), 0, MAX_BAD_ANSWERS - 1)
    await pipe.execute()
    return "ok"


async def feedback_summary(redis, bot_id: str, stats_key: str, limit: int = 20) -> dict:
    up, down = await redis.hmget(stats_key, ["thumbs_up", "thumbs_down"])
    up, down = int(up or 0), int(down or 0)
    recent = [json.loads(x) for x in await redis.lrange(feedback_key(bot_id), 0, limit - 1)]
    return {
        "helpful": up,
        "not_helpful": down,
        "helpful_percent": round(100 * up / (up + down), 1) if up + down else None,
        "recent_not_helpful": recent,
    }
