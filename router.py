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


# ---------------------------------------------------------------- difficulty signals
#
# classify() adds up a few signals that a message needs the strong model. Each signal is a general
# property of the message (not a list of topics), so the router can explain every decision:
#
#   reasoning   asks to explain, compare, calculate ...                      (HARD_KEYWORDS)
#   several     asks for two or more things at once                          ("..., and what ...?")
#   situation   describes the person's case and asks how the rules apply     ("I'm ... . Can I ...?")
#   specifics   that situation has numbers, times or amounts to work with    ("a $40 tent at 1 PM")
#   working out needs counting or arithmetic over facts                      ("how many days after")
#
# A message goes to the strong model when the signals add up to STRONG_SCORE or more.

STRONG_SCORE = 2

ASK_WORDS = (
    "what", "which", "where", "when", "who", "whom", "whose", "how", "why", "can", "could", "do", "does",
    "did", "is", "are", "was", "will", "would", "should", "may", "must", "tell",
)
# "..., and what ...", "... and can I ...": a second request joined on to the first one.
_JOINED_ASK = re.compile(r"\b(?:and|but|or|also|then|plus)\s+(?:then\s+|also\s+)?(?:" + "|".join(ASK_WORDS) + r")\b")
# The person describes their own case: "I'm ...", "I have ...", "my ...", "if I ...", "it's 9 PM ...".
_SITUATION = re.compile(
    r"(?<!do )(?<!can )(?<!could )(?<!should )(?<!would )(?<!must )(?<!may )(?<!will )(?<!did )\b(?:i'm|i am|i've|i have|i had|i was|i will|i'll|i want|i need|i plan|i missed|i forgot|i lost|i booked|"
    r"i graduated|i live|i study|i work|i drive|i commute|i start|i ordered|i bought|i paid|"
    r"if i|if my|if we|if it|my \w+ (?:is|has|was|did|are|have)|it's \d|it is \d)\b"
)
_NUMBER = re.compile(r"[$€£]\s?\d|\b\d+(?:[.,:]\d+)?\s?(?:am|pm|%|gpa|days?|hours?|weeks?|months?|years?|dollars?)?\b")
_WORKING_OUT = re.compile(
    r"\bhow (?:many|much|long|far|soon) [^?.!]*\b(?:after|before|between|until|since|left|apart|in total|altogether)\b"
    r"|\b(?:in total|altogether|add up|adds up)\b"
)


def _asks(text: str) -> int:
    """How many separate things the message asks for."""
    questions = text.count("?")
    joined = len(_JOINED_ASK.findall(text))
    return max(questions, 1) + joined if (questions or joined) else 0


def signals(message: str) -> list[tuple[str, int, str]]:
    """Every difficulty signal found in the message, as (name, points, explanation)."""
    text = message.lower().replace("\u2019", "'")
    found = []
    for keyword in HARD_KEYWORDS:
        if _has_keyword(text, keyword):
            found.append(("reasoning", 2, f"needs reasoning ('{keyword}')"))
            break
    asks = _asks(text)
    if asks >= 2:
        found.append(("several", 2, f"asks {asks} things at once"))
    if _SITUATION.search(text):
        found.append(("situation", 1, "applies the rules to the person's situation"))
        if _NUMBER.search(text):
            found.append(("specifics", 1, "with specific numbers or times"))
    if _WORKING_OUT.search(text):
        found.append(("working out", 2, "needs counting or arithmetic"))
    return found


def classify(message: str) -> tuple[str, str]:
    """Return (tier, reason) where tier is 'cheap' or 'strong'."""
    words = len(message.split())
    if words >= LONG_MESSAGE_WORDS:
        return "strong", f"long message ({words} words)"
    if "```" in message or message.count("\n") >= 3:
        return "strong", "contains code or many lines"
    found = signals(message)
    score = sum(points for _, points, _ in found)
    if score >= STRONG_SCORE:
        return "strong", "; ".join(why for _, _, why in found)
    if found:
        return "cheap", "simple question (" + found[0][2] + ", not enough for the strong model)"
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
