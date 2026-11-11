"""Google sign-in, sessions and per-bot access rules for SkyMind.

Sign-in flow (Google Identity Services, "Sign in with Google" button):
  1. The page shows Google's button. When someone signs in, Google gives the page a
     signed ID token (a JWT).
  2. The page sends it to POST /auth/google. verify_google_token() checks Google's
     signature and the token's audience, issuer, expiry and verified email.
  3. SkyMind starts its own session: a random token in an HttpOnly cookie. Only a
     SHA-256 hash of that token is stored in Redis, for SESSION_SECONDS.

Access rules (chosen by each company for each bot):
  public  anyone with the link can chat
  google  people must sign in with Google, optionally limited to some email domains
          (e.g. unt.edu) and/or a list of email addresses
"""
import hashlib
import os
import re

import jwt

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}

SESSION_COOKIE = "sm_session"
SESSION_SECONDS = int(os.getenv("SESSION_DAYS", "7")) * 24 * 3600

MAX_DOMAINS = 20
MAX_EMAILS = 200
DOMAIN_RE = re.compile(r"^(?=.{3,253}$)[a-z0-9-]+(\.[a-z0-9-]+)+$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[a-z0-9-]+(\.[a-z0-9-]+)+$")

_jwks_client = None


def google_enabled() -> bool:
    return bool(GOOGLE_CLIENT_ID)


def _jwks():
    global _jwks_client
    if _jwks_client is None:
        # Google's public signing keys; cached and refreshed when they rotate.
        _jwks_client = jwt.PyJWKClient(GOOGLE_CERTS_URL, cache_keys=True, lifespan=3600, timeout=10)
    return _jwks_client


def verify_google_token(token: str, client_id: str | None = None, jwks_client=None) -> dict:
    """Check a Google ID token and return the signed-in person. Raises ValueError if anything is off."""
    client_id = client_id or GOOGLE_CLIENT_ID
    if not client_id:
        raise ValueError("Google sign-in is not configured on this server.")
    if not isinstance(token, str) or not 20 < len(token) < 5000:
        raise ValueError("Malformed sign-in token.")
    try:
        key = (jwks_client or _jwks()).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],  # never accept unsigned or symmetric tokens
            audience=client_id,  # issued for SkyMind, not some other app
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
            leeway=30,
        )
    except jwt.PyJWTError as err:
        raise ValueError(f"Sign-in token rejected ({type(err).__name__}).") from None
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError("Sign-in token was not issued by Google.")
    email = str(claims.get("email", "")).strip().lower()
    if not email or claims.get("email_verified") is not True:
        raise ValueError("Your Google account's email address is not verified.")
    return {
        "sub": str(claims["sub"]),
        "email": email,
        "name": str(claims.get("name") or email)[:100],
        "hd": str(claims.get("hd") or "").lower(),  # Google Workspace domain, when there is one
    }


def session_key(token: str) -> str:
    return "session:" + hashlib.sha256(token.encode()).hexdigest()


# ---------------------------------------------------------------- access rules

def _split(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = re.split(r"[,\s;]+", value)
    if not isinstance(value, list):
        raise ValueError("Use a comma-separated list.")
    return [str(v).strip().lower() for v in value if str(v).strip()]


def parse_access(raw) -> dict:
    """Validate the access settings a company picked for its bot."""
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ValueError("access must be an object.")
    mode = str(raw.get("mode", "public")).strip().lower()
    if mode not in ("public", "google"):
        raise ValueError("access.mode must be 'public' or 'google'.")
    domains = []
    for d in _split(raw.get("allowed_domains")):
        d = d.lstrip("@")
        if not DOMAIN_RE.match(d):
            raise ValueError(f"'{d}' is not a valid email domain (example: unt.edu).")
        if d not in domains:
            domains.append(d)
    emails = []
    for e in _split(raw.get("allowed_emails")):
        if not EMAIL_RE.match(e):
            raise ValueError(f"'{e}' is not a valid email address.")
        if e not in emails:
            emails.append(e)
    if len(domains) > MAX_DOMAINS or len(emails) > MAX_EMAILS:
        raise ValueError(f"At most {MAX_DOMAINS} domains and {MAX_EMAILS} email addresses.")
    if mode == "public":
        domains, emails = [], []
    return {"mode": mode, "allowed_domains": domains, "allowed_emails": emails}


def public_access(access: dict | None) -> dict:
    """What the chat page may show: the mode and domains, never the list of invited emails."""
    access = access or {"mode": "public"}
    return {
        "mode": access.get("mode", "public"),
        "allowed_domains": access.get("allowed_domains", []),
        "invite_list": bool(access.get("allowed_emails")),
    }


def access_allows(access: dict | None, user: dict | None) -> tuple[bool, str]:
    """(allowed, reason). reason is 'signin' when the person must sign in first."""
    access = access or {"mode": "public"}
    if access.get("mode", "public") == "public":
        return True, ""
    if not user:
        return False, "signin"
    domains = access.get("allowed_domains") or []
    emails = access.get("allowed_emails") or []
    if not domains and not emails:
        return True, ""  # any signed-in Google account
    email = user["email"]
    if email in emails:
        return True, ""
    for d in domains:
        # Workspace accounts carry the organisation domain (hd); otherwise use the verified address.
        if user.get("hd") == d or email.endswith("@" + d):
            return True, ""
    return False, "not_allowed"
