# Prompt for the question-writing AI

Paste everything below the line into ChatGPT or Gemini (not Claude: SkyMind answers with Claude), then attach or paste the documents file (for example `kestrel_documents.txt`). Use a **new chat for every set**. Ask for 20 questions at a time and say "20 more, all different from the ones above" until you reach the target.

---

You are writing test questions for an AI assistant that answers questions using only the document I'm giving you. Your questions will be used to measure how often the assistant finds the right information and answers correctly. Realistic, varied questions make the test honest. Questions that copy the document's wording make it too easy.

**The document is the only source of truth.** Never use outside knowledge.

## What to write

Write **20 questions** now. Across all batches, aim for this mix:

- **About 60% easy:** one fact, asked the way a real person would ask it.
- **About 15% hard:** they need two facts combined, a small calculation, or applying a rule to someone's situation (for example: "I've worked here 4 years and have 8 days left in December, what happens to them?").
- **About 25% unanswerable:** questions a real user might plausibly ask that the document does **not** answer, such as a policy, number or benefit it never mentions. Most should be on-topic for this kind of document, not general trivia. The assistant should reply that it doesn't know.

## How to write them

1. **Write like real people, not like the document.** Use everyday words, synonyms and short forms: "paycheck" not "pay run", "grandpa" not "grandparent", "work from my apartment" not "remote work". About one question in five can be casual, with lowercase, no question mark, or a small typo.
2. **Vary the form:** direct questions, situations ("My mom is in hospital, can I..."), yes/no questions, "how do I...", "what happens if...".
3. **Cover the whole document**, not just the first pages. No two questions should ask for the same fact.
4. **Don't put the answer in the question.**

## For every answerable question, also give

- **answer:** the correct answer in one short sentence.
- **must_contain:** 1–3 short items that any correct answer must include, in **lowercase**, such as a number, name, date or key word. Use `|` between acceptable alternatives: `"5|five"`, `"two weeks|every 2 weeks|biweekly"`. Keep each item short: `"friday"`, not `"paid every friday"`.
- **evidence:** one sentence **copied exactly, word for word** from the document, that proves the answer. For a hard question, copy the sentence holding the main rule.

For unanswerable questions, use `"answerable": false`, and leave `answer`, `must_contain` and `evidence` empty.

## Output format

Output **only** JSON lines: one JSON object per line, no other text, no numbering. Exactly these keys:

{"question": "...", "answerable": true, "difficulty": "easy", "answer": "...", "must_contain": ["..."], "evidence": "..."}
{"question": "...", "answerable": false, "difficulty": "easy", "answer": "", "must_contain": [], "evidence": ""}

`difficulty` is `"easy"` or `"hard"`.

## Check before you answer

- Is every `evidence` sentence copied exactly from the document?
- Does every `must_contain` item actually appear in the document (or follow from it, for hard questions)?
- Is each "unanswerable" question truly not answered anywhere in the document?
- Do most questions use different words from the document?
