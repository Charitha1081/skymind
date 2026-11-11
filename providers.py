"""Model providers for SkyMind: one interface, several AI companies (model-agnostic design).

Each provider has a cheap and a strong model, so SkyMind's routing (easy questions to the
cheap model, hard ones to the strong one) works the same with every provider.

  mock       no AI: answers with the matching document text (free, for demos and load tests).
             Billed at Claude's prices so dashboards show what real use would cost.
  anthropic  Claude Haiku 5.5 (cheap) and Claude Sonnet 5.5 (strong)       ANTHROPIC_API_KEY
  gemini     Gemini 3.1 Flash-Lite (cheap) and Gemini 3.5 Flash (strong)    GEMINI_API_KEY
  ollama     open-source models on your own machine (free per answer)       OLLAMA_URL

Prices are list prices in USD per million tokens (November 2026). Check each provider's
pricing page before quoting them. Model names can be changed with environment variables.
"""
import os

import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "").strip().rstrip("/")  # e.g. http://host.docker.internal:11434

PROVIDERS = {
    "mock": {
        "label": "Mock (no AI, free)",
        "models": {"cheap": "mock-cheap", "strong": "mock-strong"},
        "prices": {"cheap": (0.10, 0.50), "strong": (2.00, 10.00)},  # billed as if Claude
    },
    "anthropic": {
        "label": "Claude (Anthropic)",
        "models": {
            "cheap": os.getenv("CHEAP_MODEL", "claude-haiku-5-5"),
            "strong": os.getenv("STRONG_MODEL", "claude-sonnet-5-5"),
        },
        "prices": {"cheap": (0.10, 0.50), "strong": (2.00, 10.00)},
    },
    "gemini": {
        "label": "Gemini (Google)",
        "models": {
            "cheap": os.getenv("GEMINI_CHEAP_MODEL", "gemini-3.1-flash-lite"),
            "strong": os.getenv("GEMINI_STRONG_MODEL", "gemini-3.5-flash"),
        },
        "prices": {"cheap": (0.25, 1.50), "strong": (1.50, 9.00)},
    },
    "ollama": {
        "label": "Open-source via Ollama (self-hosted)",
        "models": {
            "cheap": os.getenv("OLLAMA_CHEAP_MODEL", "qwen3.5:0.8b"),
            "strong": os.getenv("OLLAMA_STRONG_MODEL", "qwen3.5:4b"),
        },
        "prices": {"cheap": (0.0, 0.0), "strong": (0.0, 0.0)},  # you pay for the machine, not per answer
    },
}

# Errors where trying again cannot help (bad key, unknown model, bad request).
FATAL_STATUSES = {400, 401, 403, 404}


class ProviderError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status
        self.retryable = status not in FATAL_STATUSES


def available(name: str) -> bool:
    if name == "mock":
        return True
    if name == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    if name == "gemini":
        return bool(GEMINI_API_KEY)
    if name == "ollama":
        return bool(OLLAMA_URL)
    return False


def default_provider() -> str:
    """LLM_PROVIDER if set, otherwise the first provider with a key: Claude, then Gemini, else mock."""
    forced = os.getenv("LLM_PROVIDER", "").strip().lower()
    if forced:
        return forced
    for name in ("anthropic", "gemini"):
        if available(name):
            return name
    return "mock"


def model_name(provider: str, tier: str) -> str:
    return PROVIDERS[provider]["models"][tier]


def price(provider: str, tier: str) -> tuple[float, float]:
    return PROVIDERS.get(provider, PROVIDERS["anthropic"])["prices"][tier]


def describe() -> list[dict]:
    """What the deploy page shows in its model picker."""
    return [
        {
            "name": name,
            "label": p["label"],
            "available": available(name),
            "cheap_model": p["models"]["cheap"],
            "strong_model": p["models"]["strong"],
            "cheap_price": p["prices"]["cheap"],
            "strong_price": p["prices"]["strong"],
        }
        for name, p in PROVIDERS.items()
    ]


# ---------------------------------------------------------------- calls
# Each call returns {"text", "model", "input_tokens", "output_tokens"} or raises ProviderError.

async def _anthropic(http, model, system, messages, max_tokens, timeout):
    resp = await http.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens, "system": system, "messages": messages},
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise ProviderError(f"Anthropic {resp.status_code}: {resp.text[:300]}", resp.status_code)
    data = resp.json()
    usage = data.get("usage", {})
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    return {"text": text, "model": data.get("model", model),
            "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}


async def _gemini(http, model, system, messages, max_tokens, timeout, tier):
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]
    config = {"maxOutputTokens": max_tokens * 2}  # Gemini 3 thinking tokens share this allowance
    # Keep "thinking" short: minimal for the cheap model, low for the strong one.
    config["thinkingConfig"] = {"thinkingLevel": "minimal" if tier == "cheap" else "low"}
    body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents, "generationConfig": config}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"x-goog-api-key": GEMINI_API_KEY, "content-type": "application/json"}
    resp = await http.post(url, headers=headers, json=body, timeout=timeout)
    if resp.status_code == 400 and "thinking" in resp.text.lower():
        body["generationConfig"].pop("thinkingConfig")  # this model doesn't take that setting
        resp = await http.post(url, headers=headers, json=body, timeout=timeout)
    if resp.status_code != 200:
        raise ProviderError(f"Gemini {resp.status_code}: {resp.text[:300]}", resp.status_code)
    data = resp.json()
    cands = data.get("candidates") or []
    parts = (cands[0].get("content") or {}).get("parts", []) if cands else []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    usage = data.get("usageMetadata", {})
    out = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)  # thinking is billed as output
    return {"text": text, "model": data.get("modelVersion", model),
            "input_tokens": usage.get("promptTokenCount", 0), "output_tokens": out}


async def _ollama(http, model, system, messages, max_tokens, timeout):
    body = {"model": model, "stream": False, "think": False,
            "messages": [{"role": "system", "content": system}] + messages,
            "options": {"num_predict": max_tokens}}
    url = f"{OLLAMA_URL}/api/chat"
    resp = await http.post(url, json=body, timeout=timeout * 4)  # local CPUs are slow
    if resp.status_code == 400 and "think" in resp.text.lower():
        body.pop("think")  # older models don't take the setting
        resp = await http.post(url, json=body, timeout=timeout * 4)
    if resp.status_code != 200:
        raise ProviderError(f"Ollama {resp.status_code}: {resp.text[:300]}", resp.status_code)
    data = resp.json()
    return {"text": (data.get("message") or {}).get("content", ""), "model": data.get("model", model),
            "input_tokens": data.get("prompt_eval_count", 0), "output_tokens": data.get("eval_count", 0)}


async def call(http, provider: str, tier: str, system: str, messages: list[dict], max_tokens: int, timeout: float) -> dict:
    """One request to one model. Network failures become retryable ProviderErrors."""
    if not available(provider):
        raise ProviderError(f"{provider} is not configured on this server", 400)
    model = model_name(provider, tier)
    try:
        if provider == "anthropic":
            return await _anthropic(http, model, system, messages, max_tokens, timeout)
        if provider == "gemini":
            return await _gemini(http, model, system, messages, max_tokens, timeout, tier)
        if provider == "ollama":
            return await _ollama(http, model, system, messages, max_tokens, timeout)
    except httpx.HTTPError as err:
        raise ProviderError(f"{provider} network error: {type(err).__name__}", 0) from None
    raise ProviderError(f"Unknown provider {provider}", 400)
