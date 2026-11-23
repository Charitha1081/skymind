"""Write held-out and blind question sets with an outside AI (or person), without showing it SkyMind.

    python questions_kit.py export kestrel              -> kestrel_documents.txt (plain text, no section titles)
    python questions_kit.py import kestrel answers.jsonl questions_heldout.yaml

export  writes the bot's documents as plain paragraphs, without the "## " titles, so the writer
        can't phrase questions to match them.
import  reads the writer's JSON lines, finds the section each answer came from (using the quoted
        evidence), checks every required word really is in that section, and appends the questions
        to a question file in SkyMind's format. Anything it can't verify is listed, not added.
"""
import json
import re
import sys

import examples
import knowledge


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("“", '"').replace("”", '"')).strip().lower()


def bot_chunks(bot: str) -> list[dict]:
    ex = next((e for e in examples.EXAMPLES if e["key"] == bot), None)
    if ex is None:
        sys.exit(f"Unknown bot {bot!r}. Bots: " + ", ".join(e["key"] for e in examples.EXAMPLES))
    return knowledge.make_chunks(ex["knowledge"])


def export(bot: str) -> None:
    path = f"{bot}_documents.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(c["text"].strip() for c in bot_chunks(bot)) + "\n")
    print(f"Wrote {path}. Give the writer this file and the prompt, nothing else.")


def find_section(chunks: list[dict], evidence: str) -> str | None:
    """The section whose text contains the evidence sentence; if it was paraphrased, the one sharing most words."""
    ev = norm(evidence)
    if not ev:
        return None
    for c in chunks:
        if ev in norm(c["text"]):
            return c["title"]
    words = set(re.findall(r"[a-z0-9$.,%-]+", ev))
    best, score = None, 0.0
    for c in chunks:
        overlap = len(words & set(re.findall(r"[a-z0-9$.,%-]+", norm(c["text"])))) / max(len(words), 1)
        if overlap > score:
            best, score = c["title"], overlap
    return best if score >= 0.8 else None


def line(item: dict) -> str:
    parts = [f"bot: {item['bot']}"]
    if item.get("refuse"):
        parts.append("refuse: true")
    parts.append(f"level: {item['level']}")
    if item.get("section"):
        parts.append(f"section: {json.dumps(item['section'])}")
    parts.append(f"q: {json.dumps(item['q'])}")
    if item.get("must"):
        parts.append("must: " + json.dumps(item["must"]))
    return "- {" + ", ".join(parts) + "}"


def import_(bot: str, source: str, target: str) -> None:
    chunks = bot_chunks(bot)
    text_of = {c["title"]: norm(c["title"] + " " + c["text"]).replace(",", "") for c in chunks}
    good, problems, seen = [], [], set()
    for n, raw in enumerate(open(source, encoding="utf-8"), 1):
        raw = raw.strip().rstrip(",")
        if not raw or raw.startswith(("```", "[", "]")):
            continue
        try:
            q = json.loads(raw)
        except json.JSONDecodeError:
            problems.append(f"line {n}: not valid JSON: {raw[:80]}")
            continue
        question = str(q.get("question", "")).strip()
        if not question or norm(question) in seen:
            problems.append(f"line {n}: empty or duplicate question")
            continue
        level = "hard" if str(q.get("difficulty", "")).lower() == "hard" else "easy"
        if q.get("answerable") is False:
            seen.add(norm(question))
            good.append({"bot": bot, "refuse": True, "level": level, "q": question})
            continue
        section = find_section(chunks, str(q.get("evidence", "")))
        if section is None:
            problems.append(f"line {n}: evidence not found in the documents: {question!r}")
            continue
        must = [str(m).strip() for m in q.get("must_contain", []) if str(m).strip()]
        if not must:
            problems.append(f"line {n}: no must_contain words: {question!r}")
            continue
        missing = [m for m in must if not any(norm(alt).replace(",", "") in text_of[section] for alt in m.split("|"))]
        if missing and level == "easy":
            problems.append(f"line {n}: {missing} not in section {section!r} (a hard question may compute it; mark it hard): {question!r}")
            continue
        seen.add(norm(question))
        good.append({"bot": bot, "level": level, "section": section, "q": question, "must": must})

    with open(target, "a", encoding="utf-8") as f:
        f.write(f"\n# ---- {bot}: {len(good)} questions imported from {source}\n")
        f.write("\n".join(line(g) for g in good) + "\n")
    answerable = sum(1 for g in good if not g.get("refuse"))
    print(f"Added {len(good)} questions to {target}: {answerable} answerable "
          f"({sum(1 for g in good if g['level'] == 'hard' and not g.get('refuse'))} hard), {len(good) - answerable} should refuse.")
    if problems:
        print(f"\nNot added ({len(problems)}). Fix them in {source} and import again, or drop them:")
        print("\n".join("- " + p for p in problems))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "export":
        export(a[1])
    elif len(a) == 4 and a[0] == "import":
        import_(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)
