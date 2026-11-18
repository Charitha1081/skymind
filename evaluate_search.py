"""Score search on its own, across every question set, without calling a model.

    python3 evaluate_search.py                     # every bot
    python3 evaluate_search.py fernleaf            # one bot
    python3 evaluate_search.py --min-recall 0.90   # exit with an error below this recall@3 (used by CI)

Two numbers, both standard for retrieval:

  recall@3  the section that holds the answer is among the three search returned. If search
            misses it, the model cannot answer from it, so this is the ceiling on accuracy.
  unanswerable handled
            a question whose answer is not in the documents returns no section, or only the
            section that explains why there is no answer.

evaluate.py grades the whole pipeline on questions.yaml and needs an API key. This grades
search alone, on every set, and runs offline, so the number is cheap to re-check.
"""
import os
import re
import sys

import yaml

import examples
import knowledge

# Held-out sets keep the evaluation honest: write them after the system is built, never tune on
# them, and write the blind one without looking at the code. A set whose file doesn't exist yet is
# skipped (see TODO.md, Phase 2), so add them as you write them.
SETS = {
    "original": ("questions.yaml", "written while building the system"),
    "held-out": ("questions_heldout.yaml", "written after, never used to tune"),
    "blind": ("questions_blind.yaml", "written without looking at the code"),
}


def section_of(item: dict) -> str | None:
    """A section with a comma in it ("Login, passwords and SSO") parses as extra keys unless quoted."""
    s = item.get("section")
    if s is None:
        return None
    extra = [k for k in item if k not in ("bot", "level", "section", "q", "must", "refuse")]
    return (s + ", " + ", ".join(extra)) if extra else s


def main(only: str | None = None, min_recall: float = 0.0) -> int:
    indexes = {}
    for e in examples.EXAMPLES:
        ch = knowledge.make_chunks(e["knowledge"])
        indexes[e["key"]] = (knowledge.build_index(ch), ch)

    rows, misses = [], []
    tot = {"hit": 0, "ans": 0, "ok": 0, "ref": 0}
    for name, (path, note) in SETS.items():
        if not os.path.exists(path):
            continue
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
    recall = h / a if a else 0.0
    if recall < min_recall:
        print(f"\nFAIL: recall@3 is {recall:.1%}, below the floor of {min_recall:.0%}.")
        return 1
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    floor = 0.0
    if "--min-recall" in args:
        i = args.index("--min-recall")
        floor = float(args[i + 1])
        del args[i:i + 2]
    sys.exit(main(args[0] if args else None, floor))
