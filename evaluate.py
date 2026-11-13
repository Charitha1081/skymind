"""SkyMind evaluation: measure answer quality instead of guessing.

Three reports, all from the questions in questions.yaml:

  search    Does each search method find the section that holds the answer, and find
            nothing for questions the documents can't answer? (offline, free, instant)
  routing   Does the router send hard questions to the strong model and easy ones to the
            cheap model? (offline, free, instant)
  answers   Ask a running SkyMind every question with each provider and routing setting,
            grade the answers, and report accuracy, refusals, speed and cost. Then pick the
            cheapest setup that passes the quality bar.

Run inside Docker (the server must be running: docker compose up):
  docker compose run --rm evaluate search routing
  docker compose run --rm evaluate answers --providers mock,gemini --min-accuracy 0.85
Or with Python on your computer:
  python evaluate.py search routing
  python evaluate.py answers --url http://localhost:8000 --providers mock,anthropic
"""
import argparse
import asyncio
import math
import os
import re
import sys
import time

import httpx
import yaml

import embeddings
import examples
import knowledge
import router

HERE = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(HERE, "questions.yaml")

# A correct "refuse" answer says the information isn't available instead of inventing it.
REFUSAL_PHRASES = (
    "don't have", "do not have", "doesn't have", "does not have", "not have that", "not have information",
    "no information", "not in the", "not covered", "isn't covered", "is not covered", "not able to",
    "unable to", "can't find", "cannot find", "couldn't find", "could not find", "not sure",
    "does not quote", "doesn't quote", "not mentioned", "isn't mentioned", "is not mentioned",
    "not provided", "isn't provided", "not available", "i don't know", "i do not know",
    "contact", "reach out", "check with", "please check", "please visit", "visit ",
)


def load_questions(path: str = QUESTIONS_FILE) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        qs = yaml.safe_load(f)
    for i, q in enumerate(qs):
        q.setdefault("level", "easy")
        q["id"] = i + 1
        if not q.get("refuse") and not q.get("must"):
            raise SystemExit(f"Question {i + 1} needs 'must' facts or 'refuse: true'")
    return qs


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‑", "-")
    return re.sub(r"(?<=\d),(?=\d{3})", "", text)  # 43,567 -> 43567


def grade(q: dict, answer: str) -> bool:
    a = normalize(answer)
    if q.get("refuse"):
        return any(p in a for p in REFUSAL_PHRASES)
    return all(any(normalize(alt) in a for alt in str(group).split("|")) for group in q["must"])


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def knowledge_for(bot: str) -> str:
    return next(e["knowledge"] for e in examples.EXAMPLES if e["key"] == bot)


# ---------------------------------------------------------------- search (offline)

async def _embed_all(indexes: dict, qs: list[dict]):
    async with httpx.AsyncClient() as http:
        doc_vecs = {bot: await embeddings.embed_chunks(http, chunks) for bot, (chunks, _) in indexes.items()}
        q_vecs = await embeddings.embed(http, [q["q"] for q in qs], "RETRIEVAL_QUERY")
    return doc_vecs, {q["id"]: v for q, v in zip(qs, q_vecs)}


def eval_search(qs: list[dict], tune: bool = False) -> str:
    indexes = {}
    for bot in {q["bot"] for q in qs}:
        chunks = knowledge.make_chunks(knowledge_for(bot))
        indexes[bot] = (chunks, knowledge.build_index(chunks))
    methods = ["keyword", "bm25"]
    doc_vecs, q_vecs, note = {}, {}, ""
    if embeddings.available():
        try:
            doc_vecs, q_vecs = asyncio.run(_embed_all(indexes, qs))
            methods.append("hybrid")
        except embeddings.EmbeddingError as err:
            note = f"Meaning search skipped: {err}"
    else:
        note = "Meaning search (hybrid) skipped: set GEMINI_API_KEY to include it."

    def run(method: str, min_score=None, min_sim=None):
        top1 = top3 = answerable = refused_ok = refuse_n = 0
        misses = []
        for q in qs:
            chunks, index = indexes[q["bot"]]
            found = knowledge.retrieve(index, chunks, q["q"], k=3, method=method, min_score=min_score,
                                       query_vec=q_vecs.get(q["id"]), vectors=doc_vecs.get(q["bot"]), min_sim=min_sim)
            titles = [c["title"].split(" (part")[0] for c in found]
            if q.get("refuse") and not q.get("section"):
                refuse_n += 1
                refused_ok += not found
                if found:
                    misses.append(f"#{q['id']} should find nothing, found '{titles[0]}': {q['q']}")
            else:
                answerable += 1
                top1 += bool(titles) and titles[0] == q["section"]
                top3 += q["section"] in titles
                if q["section"] not in titles:
                    misses.append(f"#{q['id']} missed '{q['section']}': {q['q']}")
        return top1 / answerable, top3 / answerable, refused_ok / max(refuse_n, 1), misses

    rows, report_misses = [], []
    for method in methods:
        t1, t3, rf, misses = run(method)
        rows.append([method, pct(t1), pct(t3), pct(rf)])
        report_misses.append((method, misses))
    n_find = sum(bool(q.get("section")) for q in qs)
    out = ["## Search", "", f"{n_find} questions with a section to find, {len(qs) - n_find} that should find nothing.", "",
           table(["Method", "Right section first", "Right section in top 3", "Finds nothing when it should"], rows)]
    if note:
        out += ["", note]
    for method, misses in report_misses:
        if misses:
            out += ["", f"{method} mistakes:"] + [f"- {m}" for m in misses]
    if tune:
        trows = []
        for floor in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
            t1, t3, rf, _ = run("bm25", floor)
            trows.append([floor, pct(t1), pct(t3), pct(rf)])
        out += ["", "BM25 minimum score (higher = refuses more, may miss answers):", "",
                table(["Min score", "First", "Top 3", "Finds nothing"], trows)]
        if "hybrid" in methods:
            hrows = []
            for sim in (0.5, 0.55, 0.6, 0.62, 0.65, 0.7, 0.75, 0.8):
                t1, t3, rf, _ = run("hybrid", min_sim=sim)
                hrows.append([sim, pct(t1), pct(t3), pct(rf)])
            out += ["", "Hybrid minimum meaning similarity (EMBED_MIN_SIM in knowledge.py):", "",
                    table(["Min similarity", "First", "Top 3", "Finds nothing"], hrows)]
    return "\n".join(out)


# ---------------------------------------------------------------- routing (offline)

def eval_routing(qs: list[dict]) -> str:
    graded = [q for q in qs if not q.get("refuse")]
    right, wrong = 0, []
    confusion = {("easy", "cheap"): 0, ("easy", "strong"): 0, ("hard", "cheap"): 0, ("hard", "strong"): 0}
    for q in graded:
        tier, reason = router.classify(q["q"])
        confusion[(q["level"], tier)] += 1
        ok = (tier == "strong") == (q["level"] == "hard")
        right += ok
        if not ok:
            wrong.append(f"#{q['id']} labelled {q['level']}, routed {tier} ({reason}): {q['q']}")
    rows = [["easy", confusion[("easy", "cheap")], confusion[("easy", "strong")]],
            ["hard", confusion[("hard", "cheap")], confusion[("hard", "strong")]]]
    out = ["## Routing", "", f"Router agrees with the labels on {pct(right / len(graded))} of {len(graded)} questions.", "",
           table(["Question is", "Sent to cheap", "Sent to strong"], rows)]
    if wrong:
        out += ["", "Disagreements:"] + [f"- {w}" for w in wrong]
    return "\n".join(out)


# ---------------------------------------------------------------- answers (live)

async def admin_headers() -> dict:
    try:
        import loadtest  # reuses its admin-token lookup (ADMIN_TOKEN or Redis)
        token = await loadtest.load_admin_token()
    except Exception:
        token = os.getenv("ADMIN_TOKEN", "")
    return {"X-Admin-Token": token} if token else {}


async def deploy(client, base, bot, provider, routing, search):
    ex = next(e for e in examples.EXAMPLES if e["key"] == bot)
    body = {k: v for k, v in ex.items() if k != "key"}
    body.update(bot_name=f"Eval {bot} {provider} {routing}", provider=provider, model=routing, search=search,
                monthly_budget="$100000", memory="none")
    body.pop("website", None)  # measure the documents themselves: no website lookup during the evaluation
    body["web_lookup"] = False
    r = await client.post(f"{base}/bots", json=body)
    if r.status_code != 200:
        raise RuntimeError(f"deploy failed ({r.status_code}): {r.text[:200]}")
    return r.json()["bot_id"]


async def ask(client, base, bot_id, q, pace, attempts=3):
    for attempt in range(attempts):
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{base}/bots/{bot_id}/chat",
                                  json={"session_id": f"eval-{q['id']}-{attempt}", "message": q["q"]})
        except httpx.HTTPError as err:  # dropped connection or timeout: wait and try again
            if attempt < attempts - 1:
                await asyncio.sleep(max(pace, 1) * 4 * (attempt + 1))
                continue
            return {"error": type(err).__name__}, 0.0
        ms = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            return r.json(), ms
        if r.status_code in (429, 502, 503) and attempt < attempts - 1:
            await asyncio.sleep(max(pace, 1) * 4 * (attempt + 1))  # provider or SkyMind rate limit: back off
            continue
        return {"error": f"HTTP {r.status_code}"}, ms
    return {"error": "gave up"}, 0.0


async def eval_setup(client, base, qs, provider, routing, search, pace, show):
    bots = {}
    try:
        for bot in sorted({q["bot"] for q in qs}):
            bots[bot] = await deploy(client, base, bot, provider, routing, search)
        res = []
        for q in qs:
            data, ms = await ask(client, base, bots[q["bot"]], q, pace)
            ok = "error" not in data and grade(q, data["reply"])
            res.append({"q": q, "ok": ok, "ms": ms, "data": data})
            if show:
                mark = "ok  " if ok else "MISS"
                print(f"    {mark} #{q['id']:<3} {q['q'][:60]:<60} -> {data.get('reply', data.get('error', ''))[:80]!r}")
            if pace:
                await asyncio.sleep(pace)
        return res
    finally:
        for bot_id in bots.values():
            try:
                await client.delete(f"{base}/bots/{bot_id}")
            except httpx.HTTPError:
                pass


def summarize(name, res):
    answerable = [r for r in res if not r["q"].get("refuse")]
    refuse = [r for r in res if r["q"].get("refuse")]
    ok_lat = sorted(r["ms"] for r in res if "error" not in r["data"])
    cost = sum(r["data"].get("cost_usd", 0) for r in res)
    answered = len(ok_lat)
    strong = sum(1 for r in res if r["data"].get("tier") == "strong")
    p95 = ok_lat[min(len(ok_lat) - 1, math.ceil(0.95 * len(ok_lat)) - 1)] if ok_lat else 0
    return {
        "name": name,
        "accuracy": sum(r["ok"] for r in answerable) / max(len(answerable), 1),
        "refusals": sum(r["ok"] for r in refuse) / max(len(refuse), 1),
        "overall": sum(r["ok"] for r in res) / max(len(res), 1),
        "avg_ms": sum(ok_lat) / answered if answered else 0,
        "p95_ms": p95,
        "cost_per_1k": 1000 * cost / answered if answered else 0,
        "strong_share": strong / answered if answered else 0,
        "errors": len(res) - answered,
    }


def outcome_report(by_routing: dict) -> list[str]:
    """Judge the router by results, not labels: which questions did only the strong model get right?"""
    cheap, strong, auto = (by_routing.get(k) for k in ("cheap", "strong", "auto"))
    if not (cheap and strong and auto):
        return []
    rows = list(zip(cheap, strong, auto))
    needed = [(c, s, a) for c, s, a in rows if not c["ok"] and s["ok"]]          # only the strong model got it right
    wasted = [a for c, s, a in rows if c["ok"] and a["data"].get("tier") == "strong"]  # cheap was enough, auto paid for strong
    caught = [a for _, _, a in needed if a["data"].get("tier") == "strong"]
    out = ["", "### Routing judged by results", "",
           f"- Questions only the strong model answered correctly: {len(needed)} of {len(rows)}."
           + (f" The router sent {len(caught)} of them to the strong model." if needed else ""),
           f"- Questions the router sent to the strong model although the cheap model also got them right: {len(wasted)}.",
           f"- Questions neither model got right: {sum(1 for c, s, _ in rows if not c['ok'] and not s['ok'])} "
           "(a document or search problem, not a model problem)."]
    for c, s, a in needed:
        out.append(f"  - needed strong, routed {a['data'].get('tier', '?')} ({a['data'].get('route_reason', '')}): {c['q']['q']}")
    return out


def save_results(path: str, saved: list[dict]) -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=1, ensure_ascii=False)
    print(f"Saved {len(saved)} per-question results to {path}")


async def eval_answers(qs, base, provider_list, routings, searches, pace, min_accuracy, show, limit, save=""):
    base = base.rstrip("/")
    if limit:
        qs = qs[:limit]
    headers = await admin_headers()
    async with httpx.AsyncClient(timeout=120, headers=headers) as client:
        try:
            info = (await client.get(f"{base}/providers")).json()
        except httpx.HTTPError as err:
            raise SystemExit(f"Cannot reach SkyMind at {base} ({type(err).__name__}). Is docker compose up running?")
        ready = {p["name"]: p for p in info["providers"] if p["available"]}
        rows, saved, outcomes = [], [], []
        for provider in provider_list:
            by_routing = {}
            if provider not in ready:
                print(f"Skipping {provider}: not set up on the server (add its API key or URL).")
                continue
            for routing, search in [(r, s) for r in routings for s in searches]:
                name = f"{provider} / {routing}" + (f" / {search}" if len(searches) > 1 else "")
                p = ready[provider]
                model = {"cheap": p["cheap_model"], "strong": p["strong_model"]}.get(routing, f"{p['cheap_model']} + {p['strong_model']}")
                print(f"Evaluating {name} ({model}) on {len(qs)} questions...")
                res = await eval_setup(client, base, qs, provider, routing, search, pace, show)
                if len(searches) == 1:
                    by_routing[routing] = res
                saved += [{"setup": name, "id": x["q"]["id"], "bot": x["q"]["bot"], "level": x["q"].get("level"),
                           "refuse": bool(x["q"].get("refuse")), "question": x["q"]["q"], "correct": bool(x["ok"]),
                           "tier": x["data"].get("tier"), "model": x["data"].get("model"),
                           "route_reason": x["data"].get("route_reason"), "ms": round(x["ms"]),
                           "cost_usd": x["data"].get("cost_usd"), "reply": x["data"].get("reply", x["data"].get("error"))}
                          for x in res]
                s = summarize(name, res)
                s["model"] = model
                rows.append(s)
                print(f"  accuracy {pct(s['accuracy'])}, refusals {pct(s['refusals'])}, "
                      f"avg {s['avg_ms']:.0f} ms, ${s['cost_per_1k']:.4f} per 1,000 answers, errors {s['errors']}")
            outcomes += outcome_report(by_routing)
    if save and saved:
        save_results(save, saved)
    if not rows:
        return "## Answers\n\nNo provider was available to evaluate."
    out = ["## Answers", "",
           f"{len(qs)} questions, search: {', '.join(searches)}. Accuracy = answerable questions answered with the right facts. "
           "Refusals = questions outside the documents where the bot correctly said it doesn't know.", "",
           table(["Setup", "Models", "Accuracy", "Refusals", "Overall", "Avg ms", "p95 ms", "Strong share", "$ per 1,000 answers", "Errors"],
                 [[r["name"], r["model"], pct(r["accuracy"]), pct(r["refusals"]), pct(r["overall"]), f"{r['avg_ms']:.0f}",
                   f"{r['p95_ms']:.0f}", pct(r["strong_share"]), f"{r['cost_per_1k']:.4f}", r["errors"]] for r in rows])]
    passing = [r for r in rows if r["overall"] >= min_accuracy and r["errors"] == 0 and not r["name"].startswith("mock")]
    out.append("")
    if passing:
        best = min(passing, key=lambda r: (r["cost_per_1k"], -r["overall"]))
        out.append(f"**Cheapest setup that passes the {pct(min_accuracy)} quality bar: {best['name']}** "
                   f"({pct(best['overall'])} overall, ${best['cost_per_1k']:.4f} per 1,000 answers).")
    else:
        out.append(f"No real-model setup reached the {pct(min_accuracy)} quality bar without errors.")
    out += outcomes
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="SkyMind evaluation", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("reports", nargs="*", default=["search", "routing"], help="search, routing, answers, or all")
    ap.add_argument("--questions", default=QUESTIONS_FILE)
    ap.add_argument("--url", default=os.getenv("SKYMIND_URL", "http://chatbot:8000"))
    ap.add_argument("--providers", default="mock", help="comma separated: mock,anthropic,gemini,ollama")
    ap.add_argument("--routing", default="cheap,strong,auto", help="comma separated: cheap,strong,auto")
    ap.add_argument("--search", default="bm25", help="comma separated: keyword,bm25,hybrid (hybrid needs GEMINI_API_KEY on the server)")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds between questions (raise it for free-tier rate limits)")
    ap.add_argument("--min-accuracy", type=float, default=0.85, help="quality bar for the recommendation (0 to 1)")
    ap.add_argument("--limit", type=int, default=0, help="only the first N questions (quick check)")
    ap.add_argument("--tune", action="store_true", help="also show how the BM25 minimum score changes results")
    ap.add_argument("--show", action="store_true", help="print every question and answer")
    ap.add_argument("--save", default="", help="write every question's result (answer, model, correct or not) to this JSON file")
    args = ap.parse_args()

    reports = {"search", "routing", "answers"} if "all" in args.reports else set(args.reports)
    unknown = reports - {"search", "routing", "answers"}
    if unknown:
        raise SystemExit(f"Unknown report: {', '.join(unknown)}")
    qs = load_questions(args.questions)
    parts = [f"# SkyMind evaluation ({len(qs)} questions)"]
    if "search" in reports:
        parts.append(eval_search(qs, args.tune))
    if "routing" in reports:
        parts.append(eval_routing(qs))
    if "answers" in reports:
        parts.append(asyncio.run(eval_answers(
            qs, args.url, [p.strip() for p in args.providers.split(",") if p.strip()],
            [r.strip() for r in args.routing.split(",") if r.strip()],
            [s.strip() for s in args.search.split(",") if s.strip() in knowledge.SEARCH_METHODS] or ["bm25"], args.pace,
            args.min_accuracy, args.show, args.limit, args.save)))
    print()
    print("\n\n".join(parts))
    print()
    print("Paste the tables above into your README as measured results.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
