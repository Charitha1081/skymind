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

**Still to do:** the fix was designed by looking at these exact misses, so the improvement must be confirmed on a held-out set written before this run (TODO.md, item 5).
