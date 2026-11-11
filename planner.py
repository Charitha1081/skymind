"""SkyMind capacity planner.

Turns a simple spec (users, latency, memory, model, budget) into a plan:
replica count, a latency check, and an estimated monthly cost.

IMPORTANT: model prices in MODELS are Claude Haiku 5.5 / Sonnet 5.5 list prices (Nov 2026).
Traffic numbers in ASSUMPTIONS and model latencies are still placeholder estimates:
replace them with values measured in your load tests before quoting results as fact.

Run from the command line:   python planner.py spec.yaml
"""
import math

import providers
import re
import sys

import yaml

# ---- Assumptions (edit these; later, fill them from load-test results) ----
ASSUMPTIONS = {
    "msgs_per_user_per_min": 0.5,       # how often a connected user sends a message at peak
    "duty_cycle": 0.02,                 # share of the month spent at peak load
    "avg_input_tokens": 500,            # prompt tokens before memory is added
    "avg_output_tokens": 250,           # reply tokens
    "hard_question_share": 0.20,        # share of questions routed to the strong model (model: auto)
    "replica_inflight_capacity": 40,    # concurrent requests one replica can hold
    "target_utilization": 0.70,         # keep replicas at 70% so there is headroom
    "min_replicas": 2,                  # at least 2 so one can fail
    "replica_cost_month": 15.0,         # $ per replica per month
    "redis_cost_month": 15.0,           # $ for short-term memory store
    "pgvector_cost_month": 25.0,        # $ for long-term memory database
    "overhead_s": 0.15,                 # time spent outside the LLM call
}

# Model tiers: average and p95 latency in seconds (placeholders: replace with measurements).
# Prices per provider live in providers.py; the price fields here are the Claude defaults.
MODELS = {
    "cheap": {"input_per_m": 0.10, "output_per_m": 0.50, "avg_s": 0.6, "p95_s": 1.2},
    "strong": {"input_per_m": 2.00, "output_per_m": 10.00, "avg_s": 2.0, "p95_s": 3.5},
}

# Extra prompt tokens each memory type adds per request.
MEMORY_EXTRA_INPUT_TOKENS = {"none": 0, "window": 400, "summary": 250, "long_term": 300}

SECONDS_PER_MONTH = 30 * 24 * 3600


def parse_duration(value) -> float:
    """'2s' -> 2.0, '800ms' -> 0.8, 2 -> 2.0"""
    if isinstance(value, (int, float)):
        return float(value)
    m = re.fullmatch(r"\s*([\d.]+)\s*(ms|s)?\s*", str(value).lower())
    if not m:
        raise ValueError(f"Cannot read latency '{value}' (use something like 2s or 800ms)")
    num = float(m.group(1))
    return num / 1000 if m.group(2) == "ms" else num


def parse_money(value) -> float:
    """'$50' -> 50.0"""
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        raise ValueError(f"Cannot read budget '{value}' (use something like $50)")


def parse_spec(raw: dict) -> dict:
    """Validate the user's spec and convert it to plain numbers."""
    if not isinstance(raw, dict):
        raise ValueError("The spec must be a set of key: value lines")
    try:
        users = int(raw["expected_concurrent_users"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("expected_concurrent_users is required and must be a number")
    if users < 1:
        raise ValueError("expected_concurrent_users must be at least 1")

    memory = [p.strip() for p in str(raw.get("memory", "window")).split("+") if p.strip()]
    bad = [p for p in memory if p not in MEMORY_EXTRA_INPUT_TOKENS]
    if bad or not memory:
        raise ValueError(
            f"memory must use: {', '.join(MEMORY_EXTRA_INPUT_TOKENS)} (join with +). Got: {raw.get('memory')}"
        )

    model = str(raw.get("model", "auto")).strip().lower()
    if model not in ("auto", "cheap", "strong"):
        raise ValueError("model must be auto, cheap or strong")

    provider = str(raw.get("provider") or providers.default_provider()).strip().lower()
    if provider not in providers.PROVIDERS:
        raise ValueError(f"provider must be one of: {', '.join(providers.PROVIDERS)}")

    return {
        "users": users,
        "provider": provider,
        "latency_target_s": parse_duration(raw.get("latency_target_p95", "2s")),
        "memory": memory,
        "model": model,
        "budget": parse_money(raw.get("monthly_budget", 50)),
    }


def _request_cost(tier: str, in_tokens: int, out_tokens: int, provider: str = "anthropic") -> float:
    p_in, p_out = providers.price(provider, tier)
    return in_tokens / 1e6 * p_in + out_tokens / 1e6 * p_out


def plan(spec: dict) -> dict:
    a = ASSUMPTIONS
    users = spec["users"]
    peak_rps = users * a["msgs_per_user_per_min"] / 60

    # Share of questions that go to the strong model.
    share = {"auto": a["hard_question_share"], "strong": 1.0, "cheap": 0.0}[spec["model"]]

    # Capacity: Little's law (requests in flight = arrival rate x time per request).
    avg_latency = (
        a["overhead_s"] + (1 - share) * MODELS["cheap"]["avg_s"] + share * MODELS["strong"]["avg_s"]
    )
    inflight = peak_rps * avg_latency
    per_replica = a["replica_inflight_capacity"] * a["target_utilization"]
    replicas = max(a["min_replicas"], math.ceil(inflight / per_replica))

    # Cost per request and per month.
    in_tokens = a["avg_input_tokens"] + sum(MEMORY_EXTRA_INPUT_TOKENS[m] for m in spec["memory"])
    out_tokens = a["avg_output_tokens"]
    prov = spec.get("provider", "anthropic")
    cheap_cost = _request_cost("cheap", in_tokens, out_tokens, prov)
    strong_cost = _request_cost("strong", in_tokens, out_tokens, prov)
    cost_per_request = (1 - share) * cheap_cost + share * strong_cost
    monthly_requests = peak_rps * SECONDS_PER_MONTH * a["duty_cycle"]

    cost = {
        "replicas": replicas * a["replica_cost_month"],
        "redis": a["redis_cost_month"] if any(m in ("window", "summary") for m in spec["memory"]) else 0.0,
        "pgvector": a["pgvector_cost_month"] if "long_term" in spec["memory"] else 0.0,
        "llm": monthly_requests * cost_per_request,
    }
    cost["infra"] = cost["replicas"] + cost["redis"] + cost["pgvector"]
    cost["total"] = cost["infra"] + cost["llm"]

    # Latency check: the slowest model used decides the p95.
    cheap_p95 = a["overhead_s"] + MODELS["cheap"]["p95_s"]
    strong_p95 = a["overhead_s"] + MODELS["strong"]["p95_s"]
    p95 = strong_p95 if share >= 0.05 else cheap_p95
    latency_ok = p95 <= spec["latency_target_s"]

    notes = []
    if not latency_ok:
        if share >= 0.05 and cheap_p95 <= spec["latency_target_s"]:
            notes.append(
                f"About {share:.0%} of questions go to the strong model, which takes ~{strong_p95:.1f}s at p95, "
                f"above your {spec['latency_target_s']:g}s target. Use model: cheap, or raise the target to {strong_p95:.1f}s."
            )
        else:
            notes.append(
                f"Expected p95 (~{p95:.1f}s) is above your {spec['latency_target_s']:g}s target. "
                "Stream the reply or raise the target."
            )

    within_budget = cost["total"] <= spec["budget"]
    max_strong_share = None
    max_users = None
    if not within_budget:
        llm_budget = spec["budget"] - cost["infra"]
        if llm_budget <= 0:
            notes.append(
                f"Servers and memory alone cost ${cost['infra']:,.2f}, more than the ${spec['budget']:,.2f} budget. "
                "Reduce users or memory options."
            )
        else:
            affordable = llm_budget / monthly_requests  # $ available per request
            if spec["model"] != "cheap" and affordable >= cheap_cost:
                s = (affordable - cheap_cost) / (strong_cost - cheap_cost)
                max_strong_share = min(1.0, s)
                notes.append(
                    f"To fit the budget, send at most {max_strong_share:.0%} of questions to the strong model (or use model: cheap)."
                )
            else:
                max_users = int(users * llm_budget / (monthly_requests * cheap_cost))
                notes.append(
                    f"Even with only the cheap model this is over budget. Roughly {max_users} concurrent users fit in "
                    f"${spec['budget']:,.2f}/month (approximate)."
                )

    notes.append("All figures use placeholder assumptions. Replace them with your load-test measurements.")

    return {
        "spec": spec,
        "peak_rps": peak_rps,
        "inflight": inflight,
        "replicas": replicas,
        "strong_share": share,
        "p95_estimate_s": p95,
        "latency_ok": latency_ok,
        "monthly_requests": monthly_requests,
        "cost_per_request": cost_per_request,
        "cost": cost,
        "within_budget": within_budget,
        "max_strong_share": max_strong_share,
        "max_users_in_budget": max_users,
        "notes": notes,
    }


def format_plan(p: dict) -> str:
    s, c = p["spec"], p["cost"]
    lines = [
        "SkyMind capacity plan",
        "=====================",
        f"Spec: {s['users']} concurrent users | p95 target {s['latency_target_s']:g}s | "
        f"memory {'+'.join(s['memory'])} | model {s['model']} | budget ${s['budget']:,.2f}/month",
        "",
        f"Replicas:            {p['replicas']}   (peak {p['peak_rps']:.1f} req/s, ~{p['inflight']:.1f} requests in flight)",
        f"Expected p95:        {p['p95_estimate_s']:.2f}s   ({'OK' if p['latency_ok'] else 'AT RISK'} vs {s['latency_target_s']:g}s target)",
        f"Strong-model share:  {p['strong_share']:.0%} of questions",
        f"Requests per month:  {p['monthly_requests']:,.0f}",
        "",
        "Estimated monthly cost",
        f"  App replicas ({p['replicas']}):  ${c['replicas']:,.2f}",
        f"  Redis memory:        ${c['redis']:,.2f}",
        f"  pgvector memory:     ${c['pgvector']:,.2f}",
        f"  LLM tokens:          ${c['llm']:,.2f}",
        f"  TOTAL:               ${c['total']:,.2f}   ({'within budget' if p['within_budget'] else 'OVER BUDGET'})",
        "",
        "Notes",
    ]
    lines += [f"  - {n}" for n in p["notes"]]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python planner.py spec.yaml")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        raw_spec = yaml.safe_load(f)
    try:
        print(format_plan(plan(parse_spec(raw_spec))))
    except ValueError as err:
        print(f"Spec problem: {err}")
        sys.exit(1)
