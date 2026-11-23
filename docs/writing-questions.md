# Writing held-out and blind questions

SkyMind's numbers are only as honest as its question sets. `questions.yaml` is the **tuning set**: it was written while building the system, and its misses were used to design fixes. So it flatters the system. Two more sets keep the results honest.

| Set | File | Who writes it | Rule |
|---|---|---|---|
| Tuning | `questions.yaml` | Whoever builds SkyMind | Use it freely to find and fix problems |
| Held-out | `questions_heldout.yaml` | Anyone, **before** the change being measured is tested | Only for reporting. Never change code because of a held-out miss without writing a new held-out set afterwards |
| Blind | `questions_blind.yaml` | Someone who has **never seen** the code, `questions.yaml` or the section titles | Only for reporting |

`evaluate_search.py` picks up these files automatically once they exist. For answers, run `evaluate.py answers --questions questions_heldout.yaml`.

## For the person writing a blind set

You get only the plain documents (for Kestrel, the handbook text from `examples.py`, with the `## ` titles removed) and these instructions:

1. Read the documents the way an employee or customer would.
2. Write questions the way **real people** would ask them, not by copying the document's words. "When do I get paid?" not "What is the payroll frequency?"
3. For each question, note the answer and **the words a correct answer must contain**. Keep them short: a number, a name, a date.
4. **About one in four questions should have no answer** in the documents but sound plausible ("Do we get a company car?", "What is the dress code on Fridays?"). Those test whether the bot admits it doesn't know.
5. Mark questions **hard** if they need two facts combined, a calculation, or applying a rule to a situation ("I joined 4 months ago, can I take parental leave?"). Everything else is **easy**.
6. Don't look at `questions.yaml`.

## Format

One question per line in YAML, like this:

```yaml
- {bot: kestrel, level: easy, section: Pay and payroll, q: "When do I get paid?", must: ["friday"]}
- {bot: kestrel, level: hard, section: Parental leave, q: "I joined 4 months ago. Can I take parental leave next month?", must: ["6|six"]}
- {bot: kestrel, refuse: true, level: easy, q: "Do we get a company car?"}
```

- `section`: the `## ` title that holds the answer. The person running the evaluation fills this in afterwards, so the blind writer never sees the titles.
- `must`: every item must appear in the answer (case doesn't matter). `"a|b"` means a or b. Commas in numbers are ignored.
- `refuse: true`: the answer is not in the documents.

## How many

Per corpus (Fernleaf, Kestrel), aim for:

| | Tuning | Held-out | Blind |
|---|---|---|---|
| Answerable | ~45 | ~40 | ~25 |
| Should refuse | ~12 | ~12 | ~8 |

That's about 300 questions in all. With ~40 answerable questions, one question is about 2.5 points, so differences smaller than about 5 points between two setups are noise. Say so when reporting.
