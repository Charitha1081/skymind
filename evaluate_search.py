"""Score search on its own, across all four question sets, without calling a model.

    python3 evaluate_search.py

Two numbers, both standard for retrieval:

  recall@3  the section that holds the answer is among the three search returned. If search
            misses it, the model cannot answer from it, so this is the ceiling on accuracy.
  unanswerable handled
            a question whose answer is not in the documents returns no section, or only the
            section that explains why there is no answer.

evaluate.py grades the whole pipeline on questions.yaml and needs an API key. This grades
search alone, on every set, and runs offline, so the number is cheap to re-check.
"""
import re
import sys

import yaml

import examples
import knowledge

SETS = {
    "original": ("questions.yaml", "written while building the system"),
    "held-out": ("questions_heldout.yaml", "written after, to test the rebuilt router"),
    "third": ("questions_third.yaml", "never used to tune anything"),
    "blind": ("questions_blind.yaml", "written without looking at the code"),
}


def section_of(item: dict) -> str | None:
    """A section with a comma in it ("Buses, shuttles and getting around") parses as extra keys."""
    s = item.get("section")
    if s is None:
        return None
    extra = [k for k in item if k not in ("bot", "level", "section", "q", "must", "refuse")]
    return (s + ", " + ", ".join(extra)) if extra else s


def main(only: str | None = None) -> int:
    indexes = {}
    for e in examples.EXAMPLES:
        ch = knowledge.make_chunks(e["knowledge"])
        indexes[e["key"]] = (knowledge.build_index(ch), ch)

    rows, misses = [], []
    tot = {"hit": 0, "ans": 0, "ok": 0, "ref": 0}
    for name, (path, note) in SETS.items():
        hit = ans = ok = ref = 0
        for it in yaml.safe_load(open(path)):
            if only and it.get("bot") != only:
                continue
            index, chunks = indexes[it["bot"]]
            found = [c["title"].split(" (part")[0]
                     for c in knowledge.retrieve(index, chunks, it["q"], method="bm25")]
            want = section_of(it)
            if it.get("refuse"):
                ref += 1
                if not found or (want is not None and want in found):
                    ok += 1
                else:
                    misses.append((name, "answered an unanswerable question", it["q"], found))
            else:
                ans += 1
                if want in found:
                    hit += 1
                else:
                    misses.append((name, f"missed {want!r}", it["q"], found))
        rows.append((name, note, hit, ans, ok, ref))
        tot["hit"] += hit; tot["ans"] += ans; tot["ok"] += ok; tot["ref"] += ref

    who = f" ({only} bot only)" if only else ""
    print(f"# Search, scored on every question set{who}\n")
    print("| Set | What it is | recall@3 | Unanswerable handled |")
    print("|---|---|---|---|")
    for name, note, hit, ans, ok, ref in rows:
        r = f"{hit}/{ans} = {hit / ans:.0%}" if ans else "—"
        f = f"{ok}/{ref}" if ref else "—"
        print(f"| {name} | {note} | {r} | {f} |")
    h, a, o, rf = tot["hit"], tot["ans"], tot["ok"], tot["ref"]
    print(f"| **all** | | **{h}/{a} = {h / a:.1%}** | **{o}/{rf}** |")

    if misses:
        print("\nEvery question search got wrong:\n")
        for setname, what, q, found in misses:
            print(f"- [{setname}] {what}: {q!r} -> {found}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
