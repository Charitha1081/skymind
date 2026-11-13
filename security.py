"""Who may do what: sign-in, admins, bot owners, rate limits and the security middleware.

  - admin endpoints need the admin token (or an admin Google account)
  - a bot's owner is the Google account that deployed it, or whoever holds its manage key
  - chat, deploys, imports and sign-ins are rate limited with counters in Redis
  - every response gets security headers; cookie-authenticated writes need the CSRF header
"""
import hashlib
import hmac
import json
import time

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

import auth
import ingest
import settings
from runtime import state

# Google's sign-in button needs its script, frame, style and endpoints (per Google's CSP guidance).


PAGE_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/client; "
    "style-src 'self' 'unsafe-inline' https://accounts.google.com/gsi/style; "
    "frame-src https://accounts.google.com/gsi/; "
    "connect-src 'self' https://accounts.google.com/gsi/; "
    "img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)


CSRF_HEADER = "x-requested-with"


CSRF_VALUE = "SkyMind"


async def security_layer(request: Request, call_next):
    """Reject oversized requests and add security headers to every response."""
    size = request.headers.get("content-length")
    limit = ingest.MAX_FILE_BYTES + 100_000 if request.url.path == "/import/file" else settings.MAX_BODY_BYTES
    if size and (not size.isdigit() or int(size) > limit):
        return JSONResponse({"detail": "Request is too large."}, status_code=413)
    # CSRF: a request that changes something and relies on the sign-in cookie must carry our custom
    # header. Other websites cannot add it (the browser would need a CORS preflight SkyMind never allows).
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and (
        auth.SESSION_COOKIE in request.cookies or request.url.path.startswith("/auth/")
    ):
        if request.headers.get(CSRF_HEADER) != CSRF_VALUE:
            return JSONResponse({"detail": "Missing X-Requested-With: SkyMind header."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # what Google's sign-in expects
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if response.headers.get("content-type", "").startswith("text/html") and not request.url.path.startswith(("/docs", "/redoc")):
        response.headers["Content-Security-Policy"] = PAGE_CSP
        response.headers["X-Frame-Options"] = "DENY"
    return response


async def current_user(request: Request) -> dict | None:
    """The signed-in Google user for this request, from the session cookie."""
    token = request.cookies.get(auth.SESSION_COOKIE, "")
    if not token or len(token) > 200:
        return None
    raw = await state.redis.get(auth.session_key(token))
    return json.loads(raw) if raw else None


async def is_admin(request: Request) -> bool:
    """Admin = the X-Admin-Token header, or a signed-in Google account listed in ADMIN_EMAILS."""
    given = request.headers.get("x-admin-token", "")
    if given and hmac.compare_digest(given.encode(), str(state.admin_token).encode()):
        return True
    if settings.ADMIN_EMAILS:
        user = await current_user(request)
        return bool(user and user["email"] in settings.ADMIN_EMAILS)
    return False


async def require_admin(request: Request) -> None:
    """Admin endpoints need the X-Admin-Token header (compared in constant time) or an admin Google account."""
    if not await is_admin(request):
        raise HTTPException(401, "Admin token required. Find it in the server window (SkyMind admin token: ...).")


def login_required_to_deploy() -> bool:
    if settings.REQUIRE_LOGIN_TO_DEPLOY in ("true", "1", "yes"):
        return True
    if settings.REQUIRE_LOGIN_TO_DEPLOY in ("false", "0", "no"):
        return False
    return auth.google_enabled()


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def is_owner(request: Request, bot: dict) -> bool:
    """The company that deployed a bot: its signed-in Google account, or the bot's manage key."""
    if bot.get("owner_email"):
        user = await current_user(request)
        if user and user["email"] == bot["owner_email"]:
            return True
    given = request.headers.get("x-owner-key", "")
    stored = bot.get("owner_key_hash", "")
    return bool(given and stored) and hmac.compare_digest(hash_key(given), stored)


async def require_owner(request: Request, bot: dict) -> None:
    if not (await is_owner(request, bot) or await is_admin(request)):
        raise HTTPException(403, "Only the company that deployed this bot can do this.")


async def require_importer(request: Request) -> None:
    """Same rule as deploying: signed in when sign-in is required; limited per visitor."""
    admin = await is_admin(request)
    if login_required_to_deploy() and not admin and not await current_user(request):
        raise HTTPException(401, "Sign in with Google to import documents.")
    client_ip = request.client.host if request.client else "unknown"
    if not admin and await rate_limited(f"import:{client_ip}", settings.IMPORT_LIMIT_PER_HOUR, window_s=3600):
        raise HTTPException(429, "Too many imports from your address this hour. Please try again later.")


async def rate_limited(key: str, limit: int, window_s: int = 60) -> bool:
    """Fixed-window counter in Redis. True when the caller is over the limit."""
    if limit <= 0:
        return False
    bucket = f"rl:{key}:{int(time.time() // window_s)}"
    pipe = state.redis.pipeline()
    pipe.incr(bucket)
    pipe.expire(bucket, window_s + 10)
    count, _ = await pipe.execute()
    return count > limit
