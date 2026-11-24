# SkyMind roadmap

Work still to do, in order. Tick items off as they land and record the result next to them.

Suggested order: 1 → 2 → 4 → 5 → 9 → 7 → 8 → 6 → 3 → 10 → 12 → 11 → 13

## Phase 0: Replace the university sample ✅ done

- [x] The sample company is now **Fernleaf Software** (made up): a support assistant and a code reviewer. Acme Outdoor Gear stays as a hidden second company for the isolation tests.
- [x] The pages, README, comments, tests and evaluation questions were updated. The old measured numbers were removed because they came from the old sample.
- [x] Every test suite passes (`python tests/run_all.py`).
- [x] On the live site: open `/admin` and delete the old `unt-helper`, `unt-code-reviewer` and any `unt-helper-xxxx` bots. The Fernleaf samples appear after the next restart.

## Phase 1: Finish the measurements ✅ done

- [x] **1. Score hybrid vs BM25 vs keyword search, and pick the default on evidence.**
  - Done (116 questions, 3 corpora): hybrid 98% recall@3, bm25 90%, keyword 92%; hybrid and bm25 both handle 8/11 off-topic questions. Hybrid is the default whenever `GEMINI_API_KEY` is set (`settings.py`); `EMBED_MIN_SIM = 0.62` confirmed.
  - Still to do: add `GEMINI_API_KEY` on Render so the live site uses hybrid.
- [x] **2. Measure model latency and replace the planner's placeholders.**
  - Done (116 questions, model time from each answer's trace): cheap 0.87 s avg / 1.18 s p95, strong 1.66 s / 3.51 s, now in `planner.py`.
  - Still to do: the traffic numbers in `ASSUMPTIONS` are placeholders. Measure them with `loadtest.py`, then remove the "placeholder assumptions" note in `planner.py`.
- [x] **3. Keep the CI recall floor matched to the measured number.**
  - `.github/workflows/tests.yml` runs every test suite, then `evaluate_search.py --min-recall 0.88` (BM25 recall@3 is 89.4% over all corpora; CI has no Gemini key, so it measures BM25). Raise the floor to just under the new number whenever search improves.

## Phase 2: Make the evaluation mean something

- [x] **4. A second corpus.** Kestrel Logistics, a 30-section employee handbook (`examples.py`, not deployed). BM25 recall@3 is 97% on Fernleaf but 87% on Kestrel, so one corpus had flattered search.
- [ ] **5. Held-out and blind question sets** (the most important open item). Everything measured so far comes from one tuning set that was used to make decisions.
  - Fernleaf held-out done too: 65 questions (51 answerable, 14 unanswerable). Both corpora now have held-out sets (121 questions).
  - Kestrel held-out done: 56 questions (45 answerable, 11 unanswerable), written by ChatGPT with `questions_kit.py`, reviewed by hand. Still to do: a Fernleaf held-out set, and blind sets (Gemini, and ideally a person).
  - Guide for whoever writes them: [`docs/writing-questions.md`](docs/writing-questions.md).
  - First: a Kestrel held-out set (~40 answerable, ~12 should refuse), written **before** the second-look fix is measured.
  - Then: a blind set for each corpus, by someone who has never seen the code or the section titles.
  - `evaluate_search.py` picks up `questions_heldout.yaml` and `questions_blind.yaml` automatically.
- [ ] **6. Grow to ~300 scored questions.** Targets per corpus are in `docs/writing-questions.md`. Refusals are the thinnest part: only 11 today, so each one is worth 9 points. Add ~8 more to the tuning set per corpus.
- [x] **7. Error taxonomy.** First pass done: [`docs/error-taxonomy.md`](docs/error-taxonomy.md). 7 misses = 5 search misses + 2 grader errors; the model never ignored a section it was shown. It led to the topic-guided second look and better refusal detection.
  - Run 2 done: 112 → 115 of 116 (cheap model). +2 from the second look (both handbook misses), +1 from the grader fix; about 10% more cost per answer. One known limitation remains ("How can I talk to a person?"). Confirm on the held-out set.
- [x] **8. Report per corpus, not pooled.** `evaluate.py answers` and `evaluate_search.py` now print a table per corpus, plus model time from the trace.
- [ ] **9. Score answer accuracy on the held-out sets.** Needs item 5. Then run `evaluate.py answers --questions questions_heldout.yaml` and report it next to the tuning set.
  - Both corpora, after the fixes (run 4): 112/121 overall; answerable 87/96 as graded (90/96 after reviewing grader errors), refusals 25/25. Misses in `docs/error-taxonomy.md`, run 4.
  - Kestrel held-out done: 50/56 (answerable 39/45 = 87%, refusals 11/11), vs 49/49 on the tuning set. Misses in `docs/error-taxonomy.md`, run 3: 1 wrong answer from the wrong section, 2 search misses, 2 grader errors, 1 empty reply.
  - Fixed (defects, not tuning): empty model replies are now asked again and never replace a real answer (`tests/test_empty_reply.py`); the grader accepts "%"/"percent" and contractions (`tests/test_grader.py`). Next: a Fernleaf held-out set, then measure hybrid search on held-out (Eval track).

## Guard track

- [x] **Guard number:** `guard_check.py` blocks 14 of 14 common attacks (11 of 14 before the budget fix); prompt injection reduced, not eliminated. Runs in CI. Next: run it against the live site's settings once more after deploy, and write it up.

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
