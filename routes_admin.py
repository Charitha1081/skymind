"""HTTP endpoints for SkyMind operators: every bot's usage, latency, cost and savings."""
import json

from fastapi import APIRouter, Depends

import router
from runtime import state
from security import require_admin
from store import BOTS_SET, bot_key, bot_stats, latency_key, quality_counts, sessions_key, stats_key

api = APIRouter(tags=["Admin"])


@api.get("/admin/overview", dependencies=[Depends(require_admin)])
async def admin_overview():
    """Every bot with its plan, usage, latency, cost and budget status, plus fleet totals."""
    r = state.redis
    rows = []
    all_latencies: list[float] = []
    for bot_id in sorted(await r.smembers(BOTS_SET)):
        raw = await r.get(bot_key(bot_id))
        if raw is None:
            await r.srem(BOTS_SET, bot_id)
            continue
        bot = json.loads(raw)
        stats, latencies = await bot_stats(bot_id)
        all_latencies += latencies
        plan = bot["plan"]
        rows.append(
            {
                "id": bot_id,
                "name": bot["name"],
                "company": bot["company"],
                "created_at": bot["created_at"],
                "spec": bot["spec"],
                "planned": {
                    "replicas": plan["replicas"],
                    "monthly_cost_usd": round(plan["cost"]["total"], 2),
                    "within_budget": plan["within_budget"],
                    "latency_ok": plan["latency_ok"],
                },
                "llm_budget_usd": round(bot["llm_budget"], 2),
                "budget_guard": stats["actual_cost_usd"] >= bot["llm_budget"],
                "stats": stats,
                "owner_email": bot.get("owner_email", ""),
                "access": (bot.get("access") or {}).get("mode", "public"),
                "quality": await quality_counts(bot_id),
            }
        )
    rows.sort(key=lambda b: b["created_at"])
    actual = sum(b["stats"]["actual_cost_usd"] for b in rows)
    baseline = sum(b["stats"]["all_strong_cost_usd"] for b in rows)
    fleet = {
        "bots": len(rows),
        "requests": sum(b["stats"]["requests"] for b in rows),
        "actual_cost_usd": round(actual, 6),
        "all_strong_cost_usd": round(baseline, 6),
        "saved_usd": round(baseline - actual, 6),
        "saved_percent": round(100 * (baseline - actual) / baseline, 1) if baseline else 0.0,
        "latency": router.latency_summary(all_latencies),
        "planned_monthly_total_usd": round(sum(b["planned"]["monthly_cost_usd"] for b in rows), 2),
    }
    return {"fleet": fleet, "bots": rows}


@api.delete("/admin/stats", dependencies=[Depends(require_admin)])
async def reset_all_stats():
    """Clear the usage counters of every bot (bots and their documents stay)."""
    r = state.redis
    for bot_id in await r.smembers(BOTS_SET):
        await r.delete(stats_key(bot_id), latency_key(bot_id), sessions_key(bot_id))
    return {"cleared": True}


@api.get("/stats")
async def public_stats():
    """Fleet totals for the public start page (no per-bot or per-customer details)."""
    r = state.redis
    requests = 0
    actual = baseline = 0.0
    bot_ids = await r.smembers(BOTS_SET)
    for bot_id in bot_ids:
        s = router.summarize(await r.hgetall(stats_key(bot_id)))
        requests += s["requests"]
        actual += s["actual_cost_usd"]
        baseline += s["all_strong_cost_usd"]
    saved = round(100 * (baseline - actual) / baseline, 1) if baseline else 0.0
    return {"bots": len(bot_ids), "requests": requests, "saved_percent": saved}
