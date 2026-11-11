"""Tiny knowledge retrieval for SkyMind bots (no outside services needed).

A company's documents are split into chunks. For each question we find the chunks
that share the most meaningful words with it, and the bot answers from those.
Later this can be swapped for embeddings stored in pgvector without changing the
rest of the service.
"""
import difflib
import math
import re

STOPWORDS = set(
    """a an the and or but if of to in on at by for with from as is are was were be been being
    do does did can could should would will may might i me my we our you your it its this that
    these those what when where which who whom how why about into over under than then so not no
    yes there here have has had get got any some tell please""".split()
)


def _stem(word: str) -> str:
    """Very small plural stripper: colleges -> college, policies -> policy."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


def _pieces(text: str, max_chars: int):
    """Yield paragraphs, splitting very long ones by sentence."""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_chars:
            yield para
            continue
        group = ""
        for sentence in re.split(r"(?<=[.!?])\s+", para):
            if group and len(group) + len(sentence) > max_chars:
                yield group.strip()
                group = ""
            group += sentence + " "
        if group.strip():
            yield group.strip()


def make_chunks(text: str, max_chars: int = 900) -> list[dict]:
    """Split documents into chunks. '#' headings become chunk titles."""
    sections = []
    title = "Overview"
    buf: list[str] = []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.append((title, body))
        buf.clear()

    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            flush()
            title = m.group(1).strip() or title
        else:
            buf.append(line)
    flush()

    chunks = []
    for sec_title, body in sections:
        part = ""
        n = 1
        for piece in _pieces(body, max_chars):
            if part and len(part) + len(piece) > max_chars:
                chunks.append({"title": sec_title if n == 1 else f"{sec_title} (part {n})", "text": part.strip()})
                n += 1
                part = ""
            part += piece + "\n\n"
        if part.strip():
            chunks.append({"title": sec_title if n == 1 else f"{sec_title} (part {n})", "text": part.strip()})
    return chunks


def build_index(chunks: list[dict]) -> dict:
    tokens = [set(tokenize(c["title"] + " " + c["text"])) for c in chunks]
    titles = [set(tokenize(c["title"])) for c in chunks]
    df: dict[str, int] = {}
    for s in tokens:
        for t in s:
            df[t] = df.get(t, 0) + 1
    return {"tokens": tokens, "titles": titles, "df": df, "n": len(chunks)}


def retrieve(index: dict, chunks: list[dict], question: str, k: int = 3, min_score: float = 1.0) -> list[dict]:
    """Return up to k chunks that best match the question (rare shared words count more)."""
    query = set()
    vocab = list(index["df"])
    for t in tokenize(question):
        if t not in index["df"] and len(t) >= 4:
            # typo tolerance: 'aplly' -> 'apply', 'freshmen' -> 'freshman'
            close = [w for w in difflib.get_close_matches(t, vocab, n=3, cutoff=0.8) if abs(len(w) - len(t)) <= 1]
            if close:
                t = close[0]
        query.add(t)
    if not query or not chunks:
        return []
    n = index["n"]
    scored = []
    for i, (tok, tit) in enumerate(zip(index["tokens"], index["titles"])):
        score = 0.0
        for t in query:
            if t in tok:
                idf = math.log(1 + n / index["df"][t])
                score += idf * (2 if t in tit else 1)
        if score >= min_score:
            scored.append((score, i))
    scored.sort(reverse=True)
    return [dict(chunks[i], score=round(s, 2)) for s, i in scored[:k]]
