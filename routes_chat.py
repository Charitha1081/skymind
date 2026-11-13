"""HTTP endpoints for chatting with a bot. All the work happens in orchestrator.py."""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

import orchestrator
from orchestrator import ChatRequest, ChatResponse

api = APIRouter(tags=["Chat"])


@api.post("/bots/{bot_id}/chat", response_model=ChatResponse)
async def bot_chat(bot_id: str, req: ChatRequest, request: Request):
    """Ask a question and get the whole answer at once."""
    return await orchestrator.answer(bot_id, req, request)


@api.post("/bots/{bot_id}/chat/stream")
async def bot_chat_stream(bot_id: str, req: ChatRequest, request: Request):
    """Like /chat, but streams the answer as Server-Sent Events:

      event: start  {tier, route_reason, sources, job, context_sections}   once, right away
      event: text   {"text": "piece"}                                       many times
      event: done   {the same fields /chat returns}                         once, at the end
      event: error  {"detail": "..."}                                       if the answer failed
    Access, limits and budget are checked first, so those errors are normal HTTP errors.
    """
    ctx = await orchestrator.prepare_chat(bot_id, req, request)
    # no-cache and X-Accel-Buffering: no stop proxies (like Render's) from holding the pieces back
    return StreamingResponse(orchestrator.answer_events(ctx), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
