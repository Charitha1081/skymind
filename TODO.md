# SkyMind roadmap

Work still to do, in order. Tick items off as they land and record the result next to them.

Suggested order: 1 → 2 → 4 → 5 → 9 → 7 → 8 → 6 → 3 → 10 → 12 → 11 → 13

## Phase 0: Replace the university sample ✅ done

- [x] The sample company is now **Fernleaf Software** (made up): a support assistant and a code reviewer. Acme Outdoor Gear stays as a hidden second company for the isolation tests.
- [x] The pages, README, comments, tests and evaluation questions were updated. The old measured numbers were removed because they came from the old sample.
- [x] Every test suite passes (`python tests/run_all.py`).
- [ ] On the live site: open `/admin` and delete the old `unt-helper`, `unt-code-reviewer` and any `unt-helper-xxxx` bots. The Fernleaf samples appear after the next restart.

## Phase 1: Finish the measurements

The code for all of this exists; it has never been run with real API keys.

- [ ] **1. Score hybrid vs BM25 vs keyword search, and pick the default on evidence.**
  - Search only, free: `python evaluate.py search`. Add `GEMINI_API_KEY` to include hybrid, and `--tune` to tune its threshold.
  - Full answers: `python evaluate.py answers --url <your-service> --providers anthropic --search keyword,bm25,hybrid --pace 4 --save results.json`
  - Then set `SEARCH_METHOD` in `settings.py` to the winner and write down why.
  - Today (offline, 60 questions): keyword 93% / bm25 92% recall@3; bm25 handles off-topic questions far better (71% vs 29%). Hybrid not measured yet.
- [ ] **2. Measure model latency and replace the planner's placeholders.**
  - Run the answers evaluation with a real key and read average and p95 time per model (cheap and strong).
  - Put them in `planner.py` (the model latency table near line 36, marked "placeholders").
  - Remove the "All figures use placeholder assumptions" note (near line 190) once the traffic assumptions are measured too (`loadtest.py`).
- [ ] **3. Raise the CI recall floor to match.**
  - CI exists now: `.github/workflows/tests.yml` runs every test suite, then `evaluate_search.py --min-recall 0.90`.
  - Today's recall@3 is 91.5%, so the floor is 0.90. Each time search improves, raise the floor to just under the new number.

## Phase 2: Make the evaluation mean something

- [ ] **4. A second corpus** (the highest-value item). Every number today could be an artifact of one document set.
  - Pick a document set that is different in kind: an HR policy handbook, a clinic FAQ, or an API reference. Make it 30+ sections.
  - Add it to `examples.py` as a third company (not deployed, like Acme).
- [ ] **5. Question sets for the second corpus, with the same held-out discipline.**
  - Three files per corpus: a tuning set (`questions.yaml`), a held-out set (`questions_heldout.yaml`) and a blind set (`questions_blind.yaml`).
  - Never tune search or the router on the held-out or blind sets.
  - Have someone who hasn't seen the code write the blind set.
  - `evaluate_search.py` picks up these files automatically once they exist.
  - Fernleaf needs its held-out and blind sets too. The routing score (100%) only counts once it is measured on questions written without knowing the router.
- [ ] **6. Grow to ~300–400 scored questions** across both corpora and all sets. Mix easy, hard, refusals (answer not in the documents) and reworded questions ("Can I use it on my phone?").
- [ ] **7. Error taxonomy: turn the miss list into a work list.**
  - Label every miss: search missed it / wrong section ranked first / model ignored the context / wrongly refused / made something up / routing mistake.
  - Count each label. The biggest count is the next thing to fix.
- [ ] **8. Report per corpus, not pooled.** Make `evaluate.py` and `evaluate_search.py` print one table per corpus (`evaluate_search.py fernleaf` already filters by bot).
- [ ] **9. Score answer accuracy on the held-out sets.** Recall is scored on every set, but accuracy only on `questions.yaml`. Run `evaluate.py answers --questions <set>` on each held-out and blind set and report them.

## Phase 3: Make it legible

- [ ] **10. Technical report** (the headline deliverable), in `docs/report.md`:
  - problem, architecture, method (corpora, question sets, metrics)
  - results per corpus, error taxonomy, cost and latency
  - limitations, and the reversals (item 13)
- [x] **11. A README a stranger can run in one command.** `docker compose up --build` is at the top. Next: move the long reference sections into `docs/`.
- [x] **12. Architecture diagram.** See `docs/architecture.md`; GitHub draws it automatically. Keep it in step with the code.
- [ ] **13. Record the reversals.** Started in `docs/reversals.md`; fill in the coverage guard entry.

## Later

- Prompt caching for Claude: the fixed part of the instructions is the same on every question, so caching it makes answers cheaper and faster.
- An answer cache for repeated questions.
- A reranking step after search, and a one-line summary added to each section before it is indexed.
- Per-customer Kubernetes deployments with autoscaling; long-term memory; teams for companies.
