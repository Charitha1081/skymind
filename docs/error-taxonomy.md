# Error taxonomy

Every wrong answer gets one label, so the miss list becomes a work list: the biggest count is the next thing to fix. Rerun it after every change (TODO.md, item 7).

## Labels

| Label | Meaning | Usual fix |
|---|---|---|
| **search missed** | The right section was not among those the model was shown | Better search (hybrid, the second look), not the model |
| **wrong section first** | The right section was shown, but a weaker one ranked above it and the model used that | Ranking (reranker) |
| **model ignored context** | The right section was shown and the model still got it wrong | Prompt, or the strong model |
| **wrongly refused** | The answer was in what the model was shown, but it said it didn't know | Prompt |
| **made something up** | A fact that is not in the documents | Prompt; this is the most serious label |
| **grader too strict** | The answer was right, but the required words were phrased differently | Fix the question's `must` list, and say so |
| **routing mistake** | Sent to the cheap model, and only the strong model got it right | Router |

## Run 1: 116 questions, Claude, BM25 search (November 2026)

7 misses on 4 questions (cheap and strong models together):

| Question | Corpus | Missed by | Label | What happened |
|---|---|---|---|---|
| When do I get my paycheck? | Kestrel | cheap, strong | search missed | "paycheck" shares no word with "Pay and payroll"; search returned "Leaving Kestrel" (final paycheck) instead |
| How can I talk to a person? | Fernleaf | cheap, strong | search missed | Nothing in the question matches "Customer support hours"; hybrid misses it too |
| How many days off do I get if my grandmother dies? | Kestrel | cheap | search missed | "grandmother" vs "grandparent". The strong model's run found it in the second look |
| Why does a downgrade not take effect right away, and what happens when I upgrade instead? | Fernleaf | cheap, strong | grader too strict | The answer said "end of *your* current billing period"; the grader required "end of *the* current billing period" |

| Label | Count |
|---|---|
| search missed | 5 |
| grader too strict | 2 |
| model ignored context | 0 |
| wrongly refused | 0 |
| made something up | 0 |
| routing mistake | 0 |

### What it showed

- **The weak point is search, not the model.** Given the right section, both models answered every question correctly.
- **The model already knew where the answer was.** It sees every section title, and its refusals named the right one: "ask me about **Pay and payroll**", "please ask your question about **bereavement leave**", "I can help with questions about **customer support hours**". SkyMind wasn't using that.
- **One refusal wasn't recognised as a refusal** ("…so please ask your question about that topic"), so the second look never ran and the question was never logged for the company.

### What changed

1. **Topic-guided second look:** when a refusal names sections from the topic list, those sections are fetched first and the model is asked once more (`orchestrator.named_topics`). Replayed in `tests/test_second_look.py` with the real refusals.
2. **Refusal detection:** replies that invite the question again ("ask me about…", "please ask your question…") count as refusals (`improve.REFUSAL_MARKERS`).
3. **Grader:** the downgrade question now accepts any answer that mentions the billing period. This is a grading change made after seeing the answers, so it is recorded here.

## Run 2: after the fix (116 questions, Claude cheap model, BM25)

115 of 116 correct (before: 112). Fernleaf 42/43, Acme 24/24, Kestrel 49/49. Cost $0.18 per 1,000 answers (before $0.16): the second look adds a model call after a refusal.

| Question | Before | After | Why |
|---|---|---|---|
| When do I get my paycheck? | missed | **correct** | The refusal named "Pay and payroll"; the second look fetched it |
| How many days off do I get if my grandmother dies? | missed (cheap) | **correct** | The refusal is now recognised, and named "Bereavement leave" |
| Why does a downgrade not take effect right away…? | marked wrong | **correct** | Grader fixed. The answer was right before too, so this is not a system improvement |
| How can I talk to a person? | missed | **still missed** | See below |

**The one remaining miss, a known limitation.** The reply was *"I'm not able to connect you to a person directly, but you can contact Fernleaf Software directly… such as company events like the Fernleaf Summit"*. Both safety nets failed:

1. **Not recognised as a refusal.** "not able to connect you" matches none of the refusal phrases, so the second look never ran.
2. **The wrong topic was named.** The model pointed at "Fernleaf Summit", not "Customer support hours", so even a second look would have fetched the wrong section.

Neither word search nor meaning search links "talk to a person" to "Customer support hours". It is left unfixed on purpose: adding one more phrase would only patch this question. Reported as a limitation.

| Label | Run 1 | Run 2 |
|---|---|---|
| search missed | 5 | 1 |
| grader too strict | 2 | 0 |
| model ignored context | 0 | 0 |
| made something up | 0 | 0 |

## Run 3: held-out (Kestrel, 56 questions, cheap model, BM25)

Questions written by ChatGPT from the handbook text alone (no code, no tuning questions, no section titles), checked by `questions_kit.py` and reviewed by hand (4 "unanswerable" questions that the handbook does answer were removed). 50 of 56 correct: 39/45 answerable, 11/11 refusals. These misses are labelled and reported, **not fixed**.

| Question | What happened | Label |
|---|---|---|
| My paycheck is wrong. Who do I email, and how long do I have? | Search missed "Pay and payroll"; the model gave people@kestrel.example (the general HR address) instead of payroll@kestrel.example, and missed the 30 days | **answered from the wrong section** |
| Who should I contact if someone is treating me unfairly or harassing me? | Search returned "People Operations contact", not "Harassment and discrimination"; the answer was a valid channel but missed the anonymous Speak Up line | search missed (answer incomplete) |
| When is the company's HR department available? | "HR" shares no word with "People Operations"; the model honestly said it didn't have the hours | search missed (honest refusal) |
| Do I have to notify my manager before bereavement leave? | Correct ("doesn't need advance notice"), but the grader required "does not need advance notice" | grader too strict |
| 4% to the 401(k) after 3 years: what's the match, and is it mine? | Correct ("100%", "4%", vested after 2 years), but the grader required "100 percent" and "4 percent" | grader too strict |
| Christmas vacation in the warehouse: what approval and which dates? | The reply was "Sorry, I couldn't put an answer together": the model returned an empty answer | **system error** |

| Label | Run 1 (tuning) | Run 2 (tuning, after fix) | Run 3 (held-out) |
|---|---|---|---|
| search missed | 5 | 1 | 2 |
| answered from the wrong section | 0 | 0 | 1 |
| grader too strict | 2 | 0 | 2 |
| system error | 0 | 0 | 1 |
| made something up | 0 | 0 | 0 |

### What held-out showed that the tuning set could not

- **Accuracy was overstated by about 13 points** (100% → 87% on Kestrel; 91% counting the grader errors as correct).
- **The first wrong answer.** On the tuning set, a search miss always ended in "I don't know". On held-out, the model once answered confidently from a related section. For a company assistant that is the most serious kind of failure, and it is the one to watch in future runs.
- **Search cannot filter on-topic unanswerable questions** (0/11 returned nothing), but the model refused all 11 correctly.
- **An empty model reply reached the user.** This is a reliability defect, not a quality miss; it belongs to the Reliability track.
- **The grader is too literal about symbols and contractions** ("%" vs "percent", "doesn't" vs "does not"). Fixing the grader is allowed (it is not tuning the system), but the held-out figures above stay as measured.

### Fixed after run 3 (defects, not tuning)

1. **Empty replies** (`orchestrator.py`). An empty reply from the model was never retried, and the placeholder "Sorry, I couldn't put an answer together" did not count as a refusal. So it could reach the user, replace an honest first answer during the second look, and go unlogged. Now an empty reply is asked again (in both the normal and the streaming path), and the placeholder counts as a refusal. `tests/test_empty_reply.py` replays it, and fails on the old code.
2. **The grader** (`evaluate.py`). "%" and "percent", and contractions ("doesn't", "can't") and their long forms, now match either way. `tests/test_grader.py` holds both held-out cases and checks for new false passes.

Neither fix was aimed at a held-out question: the first is a reliability defect, the second fixes the measuring tool. Run 3 stays as measured; the next held-out run will show their effect.
