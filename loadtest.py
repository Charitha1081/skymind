"""SkyMind load test.

Deploys a test customer bot, simulates many users chatting at the same time, and
prints latency, throughput and errors. Run it inside Docker (see README):

    docker compose run --rm loadtest --users 100 --duration 30
    docker compose run --rm loadtest --sweep

Each virtual user sends a message, waits a short "think time", and sends the next.
The server and the load tester share your laptop's CPU, so treat the numbers as a
lower bound for what the service can do on its own machine.
"""
import argparse
import asyncio
import math
import random
import sys
import os
import time

import httpx

import examples

EASY = [
    "What are your store hours?",
    "Do you offer free shipping?",
    "How long does shipping take?",
    "How do I contact support?",
    "Is there a warranty?",
    "Do gift cards expire?",
]
HARD = [
    "Explain how your return policy works and compare it with the warranty",
    "Why would an order be delayed, and can I change the shipping address?",
    "Compare standard and express shipping and tell me which is better for a tent",
    "Explain what is covered by the warranty and what is not",
]


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    return sorted_values[min(n - 1, math.ceil(p / 100 * n) - 1)]


async def wait_for_server(client: httpx.AsyncClient, base: str, timeout: float = 90) -> dict:
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            r = await client.get(f"{base}/health")
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except httpx.HTTPError as err:
            last = type(err).__name__
        await asyncio.sleep(1)
    raise SystemExit(f"Server at {base} did not become ready ({last}). Is `docker compose up` running?")


ADMIN_HEADERS: dict = {}


async def load_admin_token() -> str:
    """Admin token from ADMIN_TOKEN, or the one SkyMind generated and stored in Redis."""
    token = os.getenv("ADMIN_TOKEN", "").strip()
    if token:
        return token
    try:
        import redis.asyncio as redis

        r = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
        token = await r.get("admin_token") or ""
        await r.aclose()
    except Exception:
        token = ""
    return token


async def deploy_test_bot(client: httpx.AsyncClient, base: str) -> str:
    ex = next(e for e in examples.EXAMPLES if e["key"] == "acme")
    body = {k: v for k, v in ex.items() if k != "key"}
    body["bot_name"] = "Load Test Bot"
    r = await client.post(f"{base}/bots", json=body)
    if r.status_code != 200:
        raise SystemExit(f"Could not deploy the test bot: {r.text[:200]}")
    return r.json()["bot_id"]


async def virtual_user(i, client, base, bot_id, start_delay, stop_at, think, hard_share, results):
    await asyncio.sleep(start_delay)
    session = f"load-{i}"
    while time.monotonic() < stop_at:
        message = random.choice(HARD if random.random() < hard_share else EASY)
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{base}/bots/{bot_id}/chat", json={"session_id": session, "message": message})
            elapsed_ms = (time.perf_counter() - t0) * 1000
            if r.status_code == 200:
                results["latencies"].append(elapsed_ms)
                tier = r.json()["tier"]
                results["tiers"][tier] = results["tiers"].get(tier, 0) + 1
            else:
                key = f"HTTP {r.status_code}"
                results["errors"][key] = results["errors"].get(key, 0) + 1
        except httpx.HTTPError as err:
            key = type(err).__name__
            results["errors"][key] = results["errors"].get(key, 0) + 1
        await asyncio.sleep(think * random.uniform(0.5, 1.5))


async def run_stage(base, bot_id, users, duration, think, hard_share):
    limits = httpx.Limits(max_connections=users + 20, max_keepalive_connections=users + 20)
    async with httpx.AsyncClient(limits=limits, timeout=30, headers=ADMIN_HEADERS) as client:
        await client.delete(f"{base}/admin/stats")  # server-side numbers for this stage only
        results = {"latencies": [], "errors": {}, "tiers": {}}
        ramp = min(5.0, duration * 0.2)
        started = time.monotonic()
        stop_at = started + duration
        tasks = [
            asyncio.create_task(
                virtual_user(i, client, base, bot_id, ramp * i / users, stop_at, think, hard_share, results)
            )
            for i in range(users)
        ]
        await asyncio.gather(*tasks)
        elapsed = time.monotonic() - started

        server = {}
        try:
            overview = (await client.get(f"{base}/admin/overview")).json()
            mine = next(b for b in overview["bots"] if b["id"] == bot_id)
            server = mine["stats"]
        except Exception:
            pass

    lat = sorted(results["latencies"])
    ok = len(lat)
    errors = sum(results["errors"].values())
    total = ok + errors
    return {
        "users": users,
        "duration_s": round(elapsed, 1),
        "requests": ok,
        "errors": errors,
        "error_detail": results["errors"],
        "error_rate": errors / total if total else 0.0,
        "rps": ok / elapsed if elapsed else 0.0,
        "avg_ms": sum(lat) / ok if ok else 0.0,
        "p50_ms": percentile(lat, 50),
        "p95_ms": percentile(lat, 95),
        "p99_ms": percentile(lat, 99),
        "max_ms": lat[-1] if lat else 0.0,
        "cheap_share": results["tiers"].get("cheap", 0) / ok if ok else 0.0,
        "server_cost_usd": server.get("actual_cost_usd", 0.0),
        "server_saved_percent": server.get("saved_percent", 0.0),
    }


def print_stage(s: dict) -> None:
    print(
        f"  {s['users']:>5} users | {s['requests']:>7,} requests | {s['rps']:>7.1f} req/s | "
        f"errors {s['errors']} ({s['error_rate']:.1%}) | avg {s['avg_ms']:.0f} ms | "
        f"p95 {s['p95_ms']:.0f} ms | p99 {s['p99_ms']:.0f} ms | max {s['max_ms']:.0f} ms"
    )


def print_summary(stages: list[dict], p95_limit: float) -> None:
    print()
    print("Results")
    print("=======")
    print(f"{'Users':>6} {'Requests':>9} {'Req/s':>8} {'Errors':>7} {'Avg ms':>8} {'p95 ms':>8} {'p99 ms':>8} {'Max ms':>8}")
    for s in stages:
        print(
            f"{s['users']:>6} {s['requests']:>9,} {s['rps']:>8.1f} {s['errors']:>7} "
            f"{s['avg_ms']:>8.0f} {s['p95_ms']:>8.0f} {s['p99_ms']:>8.0f} {s['max_ms']:>8.0f}"
        )
    print()
    print("Markdown table (paste into your README):")
    print()
    print("| Users | Requests | Req/s | Errors | Avg ms | p95 ms | p99 ms |")
    print("|---|---|---|---|---|---|---|")
    for s in stages:
        print(
            f"| {s['users']} | {s['requests']:,} | {s['rps']:.1f} | {s['errors']} | "
            f"{s['avg_ms']:.0f} | {s['p95_ms']:.0f} | {s['p99_ms']:.0f} |"
        )
    healthy = [s for s in stages if s["p95_ms"] <= p95_limit and s["error_rate"] < 0.01]
    print()
    if healthy:
        best = max(healthy, key=lambda s: s["users"])
        print(f"Healthy up to {best['users']} simulated users (p95 under {p95_limit:.0f} ms and under 1% errors).")
    else:
        print(f"No tested level stayed under p95 {p95_limit:.0f} ms with under 1% errors. Try fewer users or more WORKERS.")
    print("Note: the server and the load tester shared one machine, so real capacity on separate servers should be higher.")


async def main() -> None:
    ap = argparse.ArgumentParser(description="SkyMind load test")
    ap.add_argument("--url", default="http://chatbot:8000", help="server address (default works inside docker compose)")
    ap.add_argument("--users", type=int, default=100, help="simultaneous virtual users")
    ap.add_argument("--duration", type=float, default=30, help="seconds per stage")
    ap.add_argument("--think", type=float, default=2.0, help="average seconds between a user's messages")
    ap.add_argument("--hard-share", type=float, default=0.2, help="share of questions that are hard (0 to 1)")
    ap.add_argument("--sweep", action="store_true", help="run several user levels one after another")
    ap.add_argument("--levels", default="100,500,1000", help="user levels for --sweep, comma separated")
    ap.add_argument("--p95-limit", type=float, default=1000, help="p95 (ms) counted as healthy")
    ap.add_argument("--keep", action="store_true", help="keep the test bot afterwards")
    ap.add_argument("--allow-real", action="store_true", help="allow running against a real (paid) LLM")
    args = ap.parse_args()

    levels = [int(x) for x in args.levels.split(",") if x.strip()] if args.sweep else [args.users]
    if not levels or min(levels) < 1 or max(levels) > 5000:
        raise SystemExit("User levels must be between 1 and 5000.")

    base = args.url.rstrip("/")
    ADMIN_HEADERS["X-Admin-Token"] = await load_admin_token()
    async with httpx.AsyncClient(timeout=30, headers=ADMIN_HEADERS) as client:
        health = await wait_for_server(client, base)
        if health.get("provider") != "mock" and not args.allow_real:
            raise SystemExit(
                f"The server uses the real model provider '{health.get('provider')}'. "
                "A load test would spend real money. Restart in mock mode, or add --allow-real."
            )
        bot_id = await deploy_test_bot(client, base)

    print(f"SkyMind load test against {base} (provider: {health.get('provider')})")
    print(f"Each stage runs {args.duration:g}s; users send a message about every {args.think:g}s; {args.hard_share:.0%} of questions are hard.")
    print()

    stages = []
    try:
        for users in levels:
            print(f"Running {users} users...")
            stage = await run_stage(base, bot_id, users, args.duration, args.think, args.hard_share)
            print_stage(stage)
            stages.append(stage)
    finally:
        if not args.keep:
            async with httpx.AsyncClient(timeout=30, headers=ADMIN_HEADERS) as client:
                try:
                    await client.delete(f"{base}/bots/{bot_id}")
                except httpx.HTTPError:
                    pass

    print_summary(stages, args.p95_limit)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
