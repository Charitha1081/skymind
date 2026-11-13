"""HTTP endpoints for improving a bot: unanswered questions, Suggest fix, adding documents, ratings, imports."""
import json
import time

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import fixer
import improve
import ingest
import knowledge
import orchestrator
import providers
import settings
from runtime import log, state
from security import is_admin, rate_limited, require_importer, require_owner
from store import bot_key, embed_or_fail, load_bot, record_stats, stats_key, vectors_key

api = APIRouter(tags=["Improve"])


@api.get("/bots/{bot_id}/improve")
async def improve_report(bot_id: str, request: Request):
    """What to fix: questions the bot couldn't answer, answers rated not helpful, current sections."""
    bot = await load_bot(bot_id)
    await require_owner(request, bot)
    r = state.redis
    return {
        "gaps": await improve.list_gaps(r, bot_id),
        "feedback": await improve.feedback_summary(r, bot_id, stats_key(bot_id)),
        "sections": [c["title"] for c in bot["chunks"]],
        "characters": sum(len(c["text"]) for c in bot["chunks"]),
        "max_characters": settings.MAX_KNOWLEDGE_CHARS,
        "website": bot.get("website", ""),
        "web_lookup": bool(bot.get("web_lookup")),
        "job": bot.get("job", "answer"),
    }


@api.delete("/bots/{bot_id}/gaps")
async def clear_gaps(bot_id: str, request: Request, question: str | None = None):
    """Mark one question fixed (?question=<key>) or clear the whole list."""
    bot = await load_bot(bot_id)
    await require_owner(request, bot)
    await improve.clear_gap(state.redis, bot_id, question)
    return {"cleared": question or "all"}


class SuggestFix(BaseModel):
    url: str = Field(min_length=8, max_length=2000)
    questions: list[str] | None = Field(default=None, max_length=fixer.MAX_QUESTIONS)


@api.post("/bots/{bot_id}/suggest-fix")
async def suggest_fix(bot_id: str, req: SuggestFix, request: Request):
    """Draft the missing information for the questions a bot couldn't answer, from the company's website.

    Reads the given page and the related pages it links to on the same site, finds passages that answer
    each question and drafts new sections with sources. Nothing is added until the owner approves it.
    """
    bot = await load_bot(bot_id)
    await require_owner(request, bot)
    r = state.redis
    if not await is_admin(request) and await rate_limited(f"fix:{bot_id}", settings.FIX_LIMIT_PER_HOUR, window_s=3600):
        raise HTTPException(429, f"Suggest fix can run {settings.FIX_LIMIT_PER_HOUR} times an hour per bot. Please try again later.")
    gaps = await improve.list_gaps(r, bot_id, fixer.MAX_QUESTIONS)
    questions = req.questions or [g["question"] for g in gaps]
    questions = list(dict.fromkeys(q.strip()[:300] for q in questions if q.strip()))[:fixer.MAX_QUESTIONS]
    if not questions:
        raise HTTPException(422, "There are no unanswered questions to fix yet.")
    start = time.perf_counter()
    try:
        pages, errors = await fixer.gather_pages(req.url, questions)
    except ingest.IngestError as err:
        raise HTTPException(422, str(err))
    evidence = fixer.find_evidence(pages, questions)

    provider, used_ai, model = orchestrator.bot_provider(bot), False, "extractive"
    if provider != "mock" and any(evidence.values()):
        system, user = fixer.draft_prompt(bot["company"], evidence)
        try:
            result = await providers.call(state.http, provider, "strong", system,
                                          [{"role": "user", "content": user}], 1500, max(settings.LLM_TIMEOUT_S, 45))
            draft, missing = fixer.split_not_found(result["text"], questions)
            used_ai, model = bool(draft), result["model"]
            await record_stats(bot_id, "strong", result["input_tokens"], result["output_tokens"],
                               round((time.perf_counter() - start) * 1000, 1), "suggest-fix", provider)
        except providers.ProviderError as err:
            log.warning("Suggest fix: model failed, using passages instead: %s", err)
    if not used_ai:
        draft = fixer.extractive_draft(evidence)
        missing = [q for q, hits in evidence.items() if not hits]

    raw = await r.get(bot_key(bot_id))  # remember the site for next time
    if raw:
        stored = json.loads(raw)
        stored["website"] = req.url.strip()[:2000]
        await r.set(bot_key(bot_id), json.dumps(stored))
        state.bot_cache.pop(bot_id, None)

    keys = {g["question"]: g["key"] for g in gaps}
    missing_set = set(missing)
    return {
        "draft": draft,
        "found": [{"question": q, "key": keys.get(q) or improve._normalise(q)[1]} for q in questions if q not in missing_set],
        "not_found": [q for q in missing],
        "pages": [{"url": p["url"], "title": p["title"]} for p in pages],
        "errors": errors[:5],
        "used_ai": used_ai,
        "model": model,
    }


class KnowledgeUpdate(BaseModel):
    text: str = Field(min_length=1, max_length=settings.MAX_KNOWLEDGE_CHARS)
    mode: str = Field(default="append", pattern="^(append|replace)$")


@api.post("/bots/{bot_id}/knowledge")
async def update_knowledge(bot_id: str, req: KnowledgeUpdate, request: Request):
    """Add information to a bot (or replace all of it). Takes effect on the next question."""
    bot = await load_bot(bot_id)
    await require_owner(request, bot)
    new_chunks = knowledge.make_chunks(req.text)
    if not new_chunks:
        raise HTTPException(422, "Could not read any text to add.")
    raw = await state.redis.get(bot_key(bot_id))
    stored = json.loads(raw)
    chunks = new_chunks if req.mode == "replace" else stored["chunks"] + new_chunks
    total = sum(len(c["text"]) for c in chunks)
    if total > settings.MAX_KNOWLEDGE_CHARS:
        raise HTTPException(422, f"Documents would be too long ({total:,} of {settings.MAX_KNOWLEDGE_CHARS:,} characters).")
    if stored.get("search") == "hybrid":  # keep one vector per chunk
        if req.mode == "replace":
            vectors = await embed_or_fail(chunks)
        else:
            old = json.loads(await state.redis.get(vectors_key(bot_id)) or "[]")
            vectors = old + await embed_or_fail(new_chunks)
        await state.redis.set(vectors_key(bot_id), json.dumps(vectors))
    stored["chunks"] = chunks
    await state.redis.set(bot_key(bot_id), json.dumps(stored))
    state.bot_cache.pop(bot_id, None)
    return {"sections": len(chunks), "added": len(new_chunks), "characters": total}


class Feedback(BaseModel):
    session_id: str = Field(min_length=1, max_length=128, pattern=settings.SESSION_ID_PATTERN)
    answer_id: str = Field(min_length=6, max_length=40, pattern=r"^[A-Za-z0-9_-]+$")
    helpful: bool
    comment: str = Field(default="", max_length=500)


@api.post("/bots/{bot_id}/feedback")
async def rate_answer(bot_id: str, req: Feedback):
    """A customer rates an answer they received (one rating per answer)."""
    await load_bot(bot_id)
    if await rate_limited(f"fb:{bot_id}:{req.session_id}", 30):
        raise HTTPException(429, "Too many ratings. Please wait a minute.")
    result = await improve.record_feedback(
        state.redis, bot_id, req.session_id, req.answer_id, req.helpful, stats_key(bot_id), req.comment
    )
    if result == "unknown":
        raise HTTPException(404, "That answer can't be rated (it is older than 7 days or from another conversation).")
    return {"recorded": result == "ok", "already_rated": result == "duplicate"}


# ---------- Importing documents: PDF, Word, text files and web pages ----------

def import_result(title: str, text: str) -> dict:
    return {"title": title, "text": text[:settings.MAX_KNOWLEDGE_CHARS], "characters": len(text),
            "truncated": len(text) > settings.MAX_KNOWLEDGE_CHARS}


@api.post("/import/file")
async def import_file(request: Request, file: UploadFile = File(...)):
    """Read a PDF, Word (.docx), text, Markdown or CSV file and return its text, ready to add to a bot."""
    await require_importer(request)
    data = await file.read(ingest.MAX_FILE_BYTES + 1)
    try:
        text = await run_in_threadpool(ingest.extract_file, file.filename or "document", data)
    except ingest.IngestError as err:
        raise HTTPException(422, str(err))
    return import_result(file.filename or "document", text)


class UrlImport(BaseModel):
    url: str = Field(min_length=8, max_length=2000)


@api.post("/import/url")
async def import_url(req: UrlImport, request: Request):
    """Fetch a public web page (or PDF link) and return its text. Private addresses are refused (SSRF)."""
    await require_importer(request)
    try:
        title, text = await ingest.fetch_url(req.url)
    except ingest.IngestError as err:
        raise HTTPException(422, str(err))
    return import_result(title, text)
