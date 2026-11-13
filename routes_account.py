"""HTTP endpoints for accounts: sign in with Google, sign out, who am I, my bots."""
import json
import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

import auth
from runtime import state
from security import current_user, is_admin, login_required_to_deploy, rate_limited
from store import all_bots, bot_stats, public_info, quality_counts

api = APIRouter(tags=["Account"])


class GoogleLogin(BaseModel):
    credential: str = Field(min_length=20, max_length=5000)


@api.post("/auth/google")
async def google_login(req: GoogleLogin, request: Request):
    """Exchange a Google ID token for a SkyMind session cookie."""
    if not auth.google_enabled():
        raise HTTPException(404, "Google sign-in is not set up on this server.")
    client_ip = request.client.host if request.client else "unknown"
    if await rate_limited(f"login:{client_ip}", 20):
        raise HTTPException(429, "Too many sign-in attempts. Please wait a minute.")
    try:
        user = await run_in_threadpool(auth.verify_google_token, req.credential)  # may fetch Google's keys
    except ValueError as err:
        raise HTTPException(401, str(err))
    token = secrets.token_urlsafe(32)
    await state.redis.set(auth.session_key(token), json.dumps(user), ex=auth.SESSION_SECONDS)
    response = JSONResponse({"email": user["email"], "name": user["name"]})
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=auth.SESSION_SECONDS,
        httponly=True,  # page scripts can't read it, so injected scripts can't steal it
        secure=request.url.scheme == "https",
        samesite="lax",
        path="/",
    )
    return response


@api.post("/auth/logout")
async def logout(request: Request):
    token = request.cookies.get(auth.SESSION_COOKIE, "")
    if token:
        await state.redis.delete(auth.session_key(token))
    response = JSONResponse({"signed_out": True})
    response.delete_cookie(auth.SESSION_COOKIE, path="/")
    return response


@api.get("/me")
async def me(request: Request):
    """Who is signed in, and what the pages should offer."""
    user = await current_user(request)
    return {
        "google_enabled": auth.google_enabled(),
        "google_client_id": auth.GOOGLE_CLIENT_ID,
        "login_required_to_deploy": login_required_to_deploy(),
        "user": {"email": user["email"], "name": user["name"]} if user else None,
        "is_admin": await is_admin(request),
    }


@api.get("/my/bots")
async def my_bots(request: Request):
    """Bots owned by the signed-in Google account."""
    user = await current_user(request)
    if not user:
        raise HTTPException(401, "Sign in with Google to see your bots.")
    rows = []
    for bot in await all_bots():
        if bot.get("owner_email") == user["email"]:
            stats, _ = await bot_stats(bot["id"])
            rows.append({
                **public_info(bot),
                "access": bot.get("access") or {"mode": "public", "allowed_domains": [], "allowed_emails": []},
                "requests": stats["requests"],
                "saved_percent": stats["saved_percent"],
                "quality": await quality_counts(bot["id"]),
                "website": bot.get("website", ""),
            })
    return rows
