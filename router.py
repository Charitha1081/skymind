"""SkyMind model router.

Decides whether a question needs the cheap model or the strong model, and
turns the usage counters into a savings report.

The rules are deliberately simple and explainable (length, reasoning words,
code, multiple questions). A later version can replace classify() with a
small classifier model without touching the rest of the service.
"""
import difflib
import math
import re

import providers

HARD_KEYWORDS = (
    "why",
    "explain",
    "compare",
    "analyze",
    "analyse",
    "debug",
    "design",
    "step by step",
    "write code",
    "calculate",
    "prove",
    "difference between",
    "trade-off",
    "tradeoff",
    "optimize",
    "optimise",
    "make a plan",  # plain "plan" sent "meal plan prices" to the strong model (found by evaluate.py)
    "create a plan",
    "plan for",
    "summarize",
    "summarise",
)

LONG_MESSAGE_WORDS = 60

GREETINGS = (
    "hi", "hello", "hey", "hiya", "howdy", "yo", "hi there", "hello there", "hey there",
    "good morning", "good afternoon", "good evening", "thanks", "thank you", "thx", "bye",
)


def _squeeze(text: str) -> str:
    """Collapse repeated letters so 'hii', 'hellooo' and 'heyyy' match 'hi', 'hello', 'hey'."""
    return re.sub(r"(.)\1+", r"\1", text)


_GREETING_FORMS = {_squeeze(g) for g in GREETINGS}


def is_greeting(message: str) -> bool:
    """True for short small talk like 'hi', 'hii', 'helo', 'thank you!' (typo tolerant)."""
    words = re.findall(r"[a-z]+", message.lower())
    if not words or len(words) > 3:
        return False
    form = _squeeze(" ".join(words))
    if form in _GREETING_FORMS:
        return True
    return len(form) >= 4 and bool(difflib.get_close_matches(form, _GREETING_FORMS, n=1, cutoff=0.8))


def _has_keyword(text: str, keyword: str) -> bool:
    """Exact match for phrases; typo-tolerant match for single words ('expalin' -> 'explain')."""
    if keyword in text:
        return True
    if " " in keyword or "-" in keyword or len(keyword) < 5:
        return False
    words = re.findall(r"[a-z]+", text)
    return any(
        abs(len(w) - len(keyword)) <= 1 and difflib.get_close_matches(w, [keyword], n=1, cutoff=0.85)
        for w in words
    )


def classify(message: str) -> tuple[str, str]:
    """Return (tier, reason) where tier is 'cheap' or 'strong'."""
    text = message.lower()
    words = len(message.split())

    if words >= LONG_MESSAGE_WORDS:
        return "strong", f"long message ({words} words)"
    if "```" in message or message.count("\n") >= 3:
        return "strong", "contains code or many lines"
    if message.count("?") >= 2:
        return "strong", "several questions in one message"
    for keyword in HARD_KEYWORDS:
        if _has_keyword(text, keyword):
            return "strong", f"needs reasoning ('{keyword}')"
    return "cheap", "short, simple question"


def pick_tier(message: str, mode: str = "auto") -> tuple[str, str]:
    """mode: auto (classify), cheap or strong (force one model for everything)."""
    if mode in ("cheap", "strong"):
        return mode, f"forced to {mode}"
    return classify(message)


def latency_summary(values: list[float]) -> dict:
    """Average and percentile latency (milliseconds) over the recent requests."""
    if not values:
        return {"avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "samples": 0}
    v = sorted(values)
    n = len(v)

    def pct(p: int) -> float:
        return v[min(n - 1, math.ceil(p / 100 * n) - 1)]

    return {
        "avg_ms": round(sum(v) / n, 1),
        "p50_ms": round(pct(50), 1),
        "p95_ms": round(pct(95), 1),
        "max_ms": round(v[-1], 1),
        "samples": n,
    }


def estimate_tokens(text: str) -> int:
    """Rough token count (about 4 characters per token). Used when the API does not report usage."""
    return max(1, len(text) // 4)


def request_cost(tier: str, input_tokens: int, output_tokens: int, provider: str = "anthropic") -> float:
    """Dollar cost of one request at the provider's list price (providers.py)."""
    p_in, p_out = providers.price(provider, tier)
    return input_tokens / 1e6 * p_in + output_tokens / 1e6 * p_out


def summarize(raw: dict) -> dict:
    """Turn the raw Redis counters into a readable savings report."""
    cheap = int(raw.get("cheap_requests", 0))
    strong = int(raw.get("strong_requests", 0))
    total = cheap + strong
    actual = float(raw.get("actual_cost_usd", 0))
    baseline = float(raw.get("all_strong_cost_usd", 0))
    saved = baseline - actual
    return {
        "requests": total,
        "cheap_requests": cheap,
        "strong_requests": strong,
        "cheap_share_percent": round(100 * cheap / total, 1) if total else 0.0,
        "input_tokens": int(float(raw.get("input_tokens", 0))),
        "output_tokens": int(float(raw.get("output_tokens", 0))),
        "actual_cost_usd": round(actual, 6),
        "all_strong_cost_usd": round(baseline, 6),
        "saved_usd": round(saved, 6),
        "saved_percent": round(100 * saved / baseline, 1) if baseline else 0.0,
        "saved_per_1000_requests_usd": round(saved / total * 1000, 4) if total else 0.0,
    }
