"""HTTP endpoints for bots: deploy, look up, usage, who can use it, website lookup, delete."""
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field

import auth
import improve
import ingest
import settings
import web
from runtime import state
from security import current_user, is_admin, is_owner, login_required_to_deploy, rate_limited, require_admin, require_owner
from store import (BOTS_SET, _resolve_quiet, all_bots, bot_key, bot_stats, create_bot, latency_key, load_bot, public_info,
                   quality_counts, sessions_key, stats_key, vectors_key)

api = APIRouter(tags=["Bots"])


@api.post("/bots")
async def deploy_bot(
    request: Request,
    body: dict = Body(
        ...,
        examples=[
            {
                "bot_name": "Acme Support",
                "company": "Acme Outdoor Gear",
                "expected_concurrent_users": 100,
                "latency_target_p95": "4s",
                "memory": "window",
                "model": "auto",
                "monthly_budget": "$150",
                "knowledge": "## Returns\nItems can be returned within 30 days for a full refund.",
            }
        ],
    ),
):
    """Deploy a chatbot for a company: plan it, load its documents, and start serving it."""
    user = await current_user(request)
    admin = await is_admin(request)
    if login_required_to_deploy() and not user and not admin:
        raise HTTPException(401, "Sign in with Google to deploy a bot.")
    client_ip = request.client.host if request.client else "unknown"
    # Admins (and evaluate.py / loadtest.py, which use the admin token) are not limited.
    if not admin and await rate_limited(f"deploy:{client_ip}", settings.DEPLOY_LIMIT_PER_IP, window_s=3600):
        raise HTTPException(429, "Too many bots deployed from your address this hour. Please try again later.")
    return await create_bot(body, owner_email=user["email"] if user else "")


@api.get("/bots", dependencies=[Depends(require_admin)])
async def list_bots():
    """Every bot (SkyMind operators only: companies must not see each other's bots)."""
    return [public_info(b) for b in await all_bots()]


@api.get("/featured")
async def featured_bots():
    """Public sample bots shown on the start page."""
    return [public_info(b) for b in await all_bots() if b.get("featured")]


@api.get("/bots/{bot_id}")
async def get_bot(bot_id: str):
    return public_info(await load_bot(bot_id))


@api.get("/bots/{bot_id}/usage")
async def bot_usage(bot_id: str, request: Request):
    """Usage of one bot, for the company that owns it (manage key) or an admin."""
    bot = await load_bot(bot_id)
    if not (await is_owner(request, bot) or await is_admin(request)):
        raise HTTPException(403, "Only the company that deployed this bot can see its usage.")
    stats, _ = await bot_stats(bot_id)
    return {
        "id": bot_id,
        "name": bot["name"],
        "company": bot["company"],
        "requests": stats["requests"],
        "latency": stats["latency"],
        "actual_cost_usd": stats["actual_cost_usd"],
        "saved_percent": stats["saved_percent"],
        "llm_budget_usd": round(bot["llm_budget"], 2),
        "budget_guard": stats["actual_cost_usd"] >= bot["llm_budget"],
        "access": bot.get("access") or {"mode": "public", "allowed_domains": [], "allowed_emails": []},
        "quality": await quality_counts(bot_id),
    }


@api.patch("/bots/{bot_id}/access")
async def update_access(bot_id: str, request: Request, body: dict = Body(...)):
    """Change who can chat with a bot (owner or admin)."""
    bot = await load_bot(bot_id)
    if not (await is_owner(request, bot) or await is_admin(request)):
        raise HTTPException(403, "Only the company that deployed this bot can change who can use it.")
    try:
        access = auth.parse_access(body)
    except ValueError as err:
        raise HTTPException(422, str(err))
    if access["mode"] == "google" and not auth.google_enabled():
        raise HTTPException(422, "Google sign-in is not set up on this server, so the bot can only be public.")
    raw = await state.redis.get(bot_key(bot_id))
    stored = json.loads(raw)
    stored["access"] = access
    await state.redis.set(bot_key(bot_id), json.dumps(stored))
    state.bot_cache.pop(bot_id, None)
    return {"id": bot_id, "access": access}


class WebSettings(BaseModel):
    website: str = Field(default="", max_length=300)
    enabled: bool = True


@api.patch("/bots/{bot_id}/web")
async def update_web(bot_id: str, req: WebSettings, request: Request):
    """Set the company website and turn website lookup on or off (owner or admin)."""
    bot = await load_bot(bot_id)
    await require_owner(request, bot)
    try:
        website = web.normalise_website(req.website)
        if website:
            await ingest.check_public_url(website, resolve=lambda h: _resolve_quiet(h))
    except (ValueError, ingest.IngestError) as err:
        raise HTTPException(422, str(err))
    stored = json.loads(await state.redis.get(bot_key(bot_id)))
    stored["website"] = website
    stored["web_lookup"] = bool(website) and req.enabled
    await state.redis.set(bot_key(bot_id), json.dumps(stored))
    state.bot_cache.pop(bot_id, None)
    return {"website": website, "web_lookup": stored["web_lookup"]}


@api.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str, request: Request):
    """Delete a bot: its owner (manage key) or a SkyMind admin."""
    bot = await load_bot(bot_id)  # 404 if missing
    if not (await is_owner(request, bot) or await is_admin(request)):
        raise HTTPException(401, "Only the company that deployed this bot, or a SkyMind admin, can delete it.")
    r = state.redis
    keys = [bot_key(bot_id), vectors_key(bot_id), stats_key(bot_id), latency_key(bot_id), sessions_key(bot_id)] + improve.bot_keys(bot_id)
    for pattern in (f"chat:{bot_id}:*", f"answer:{bot_id}:*", f"rated:{bot_id}:*"):
        async for key in r.scan_iter(match=pattern):
            keys.append(key)
    await r.delete(*keys)
    await r.srem(BOTS_SET, bot_id)
    state.bot_cache.pop(bot_id, None)
    return {"deleted": bot_id}
