import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
"""Google sign-in and per-bot access tests (no network: Google's keys are simulated)."""
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
import fakeredis
from fastapi.testclient import TestClient
import auth, main

# ---------- 1. token verification with real RSA signatures ----------
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
class FakeJWKS:
    def __init__(self, k): self.k = k
    def get_signing_key_from_jwt(self, token):
        return type("K", (), {"key": self.k.public_key()})()
J = FakeJWKS(key)
CID = "test-client.apps.googleusercontent.com"
def tok(signer=key, alg="RS256", **over):
    now = int(time.time())
    c = {"iss": "https://accounts.google.com", "aud": CID, "sub": "123", "iat": now, "exp": now + 600,
         "email": "Alice@Gmail.com", "email_verified": True, "name": "Alice"}
    c.update(over)
    c = {k: v for k, v in c.items() if v is not None}
    return jwt.encode(c, signer, algorithm=alg)

u = auth.verify_google_token(tok(), CID, J)
assert u["email"] == "alice@gmail.com" and u["hd"] == ""
assert auth.verify_google_token(tok(hd="unt.edu"), CID, J)["hd"] == "unt.edu"
bad = {
    "forged signature": tok(signer=other),
    "wrong app (aud)": tok(aud="someone-else"),
    "wrong issuer": tok(iss="https://evil.example"),
    "expired": tok(exp=int(time.time()) - 3600, iat=int(time.time()) - 7200),
    "unverified email": tok(email_verified=False),
    "no email": tok(email=None),
    "HS256 (algorithm swap)": jwt.encode({"iss": "accounts.google.com", "aud": CID, "sub": "1", "iat": 1, "exp": 9999999999, "email": "x@y.z", "email_verified": True}, "secret-key-that-is-long-enough-123", algorithm="HS256"),
    "garbage": "not-a-token-" * 3,
}
for label, t in bad.items():
    try:
        auth.verify_google_token(t, CID, J)
        raise SystemExit(f"FAIL: accepted {label}")
    except ValueError:
        pass
print(f"token checks OK: valid accepted, {len(bad)} bad tokens rejected")

# ---------- 2. access rules ----------
pa = auth.parse_access({"mode": "google", "allowed_domains": "@UNT.edu, my.unt.edu", "allowed_emails": "Boss@gmail.com"})
assert pa == {"mode": "google", "allowed_domains": ["unt.edu", "my.unt.edu"], "allowed_emails": ["boss@gmail.com"]}
for badacc in ({"mode": "secret"}, {"mode": "google", "allowed_domains": "not a domain!"}, {"mode": "google", "allowed_emails": "nope"}):
    try: auth.parse_access(badacc); raise SystemExit(f"FAIL parse {badacc}")
    except ValueError: pass
U = lambda e, hd="": {"email": e, "hd": hd}
assert auth.access_allows(pa, None) == (False, "signin")
assert auth.access_allows(pa, U("x@unt.edu"))[0]
assert auth.access_allows(pa, U("x@other.com", hd="unt.edu"))[0]
assert auth.access_allows(pa, U("boss@gmail.com"))[0]
assert auth.access_allows(pa, U("x@fakeunt.edu")) == (False, "not_allowed")
assert auth.access_allows(pa, U("x@unt.edu.evil.com")) == (False, "not_allowed")
assert auth.access_allows({"mode": "google", "allowed_domains": [], "allowed_emails": []}, U("any@gmail.com"))[0]
assert "allowed_emails" not in auth.public_access(pa) and auth.public_access(pa)["invite_list"] is True
print("access rules OK: domains, Workspace hd, invite list, look-alike domains blocked")

# ---------- 3. full app ----------
srv = fakeredis.FakeServer()
main.redis.from_url = lambda *a, **k: fakeredis.FakeAsyncRedis(server=srv, decode_responses=True)
auth.GOOGLE_CLIENT_ID = CID
PEOPLE = {
    "cred-alice-xxxxxxxxxxxxxxxx": {"sub": "1", "email": "alice@acme.com", "name": "Alice", "hd": "acme.com"},
    "cred-bob-xxxxxxxxxxxxxxxxxx": {"sub": "2", "email": "bob@gmail.com", "name": "Bob", "hd": ""},
    "cred-carol-xxxxxxxxxxxxxxxx": {"sub": "3", "email": "carol@unt.edu", "name": "Carol", "hd": ""},
    "cred-dave-xxxxxxxxxxxxxxxxx": {"sub": "4", "email": "dave@outside.org", "name": "Dave", "hd": "unt.edu"},
    "cred-boss-xxxxxxxxxxxxxxxxx": {"sub": "5", "email": "boss@skymind.dev", "name": "Boss", "hd": ""},
}
def fake_verify(t, *a, **k):
    if t not in PEOPLE: raise ValueError("Sign-in token rejected (InvalidSignatureError).")
    return dict(PEOPLE[t])
auth.verify_google_token = fake_verify
H = {"X-Requested-With": "SkyMind"}
def client(): return TestClient(main.app)
def login(c, who):
    r = c.post("/auth/google", json={"credential": f"cred-{who}-" + "x" * (27 - len(who) - 5 - 1)[:0] + PEOPLE_KEY[who]}, headers=H)
    return r
PEOPLE_KEY = {k.split("-")[1]: k for k in PEOPLE}
def login(c, who):
    return c.post("/auth/google", json={"credential": PEOPLE_KEY[who]}, headers=H)
BOT = {"bot_name": "Acme Help", "company": "Acme", "knowledge": "## Hours\nOpen 9 to 5 on weekdays.", "expected_concurrent_users": 10}

with client() as anon, client() as alice, client() as bob, client() as carol, client() as dave, client() as boss:
    me = anon.get("/me").json()
    assert me["google_enabled"] and me["login_required_to_deploy"] and me["user"] is None
    assert anon.post("/bots", json=BOT).status_code == 401, "deploy needs sign-in when Google is on"
    assert anon.post("/auth/google", json={"credential": PEOPLE_KEY["alice"]}).status_code == 403, "login needs CSRF header"
    assert anon.post("/auth/google", json={"credential": "forged-token-forged-token"}, headers=H).status_code == 401
    for c, w in ((alice, "alice"), (bob, "bob"), (carol, "carol"), (dave, "dave"), (boss, "boss")):
        r = login(c, w); assert r.status_code == 200, r.text
        assert "httponly" in r.headers["set-cookie"].lower() and "samesite=lax" in r.headers["set-cookie"].lower()
    assert alice.get("/me").json()["user"]["email"] == "alice@acme.com"

    # CSRF: cookie-authenticated change without the header is refused
    assert alice.post("/bots", json=BOT).status_code == 403
    pub = alice.post("/bots", json=BOT, headers=H).json()
    restricted = alice.post("/bots", json=dict(BOT, bot_name="UNT Only", access={"mode": "google", "allowed_domains": "unt.edu", "allowed_emails": "bob@gmail.com"}), headers=H).json()
    assert pub["owner_email"] == "alice@acme.com" and restricted["access"]["mode"] == "google"
    assert alice.post("/bots", json=dict(BOT, access={"mode": "google", "allowed_domains": "bad domain"}), headers=H).status_code == 422

    # ownership
    mine = {b["id"] for b in alice.get("/my/bots").json()}
    assert mine == {pub["bot_id"], restricted["bot_id"]}
    assert bob.get("/my/bots").json() == [] and anon.get("/my/bots").status_code == 401
    assert bob.delete(f"/bots/{pub['bot_id']}", headers=H).status_code == 401
    assert bob.patch(f"/bots/{pub['bot_id']}/access", json={"mode": "google"}, headers=H).status_code == 403
    assert bob.get(f"/bots/{pub['bot_id']}/usage").status_code == 403
    assert alice.get(f"/bots/{pub['bot_id']}/usage").status_code == 200

    # public info never reveals the invite list
    info = anon.get(f"/bots/{restricted['bot_id']}").json()
    assert info["access"] == {"mode": "google", "allowed_domains": ["unt.edu"], "invite_list": True}

    # chat access
    say = lambda c, b: c.post(f"/bots/{b}/chat", json={"session_id": "s1", "message": "When are you open?"}, headers=H).status_code
    assert say(anon, pub["bot_id"]) == 200
    assert say(anon, restricted["bot_id"]) == 401
    assert say(alice, restricted["bot_id"]) == 403, "the owner's own account is not on the list"
    assert say(carol, restricted["bot_id"]) == 200, "@unt.edu address"
    assert say(dave, restricted["bot_id"]) == 200, "Workspace hd=unt.edu"
    assert say(bob, restricted["bot_id"]) == 200, "invited email"
    # owner opens it to everyone
    assert alice.patch(f"/bots/{restricted['bot_id']}/access", json={"mode": "public"}, headers=H).status_code == 200
    time.sleep(0.01); main.app.state.bot_cache.clear()
    assert say(anon, restricted["bot_id"]) == 200

    # admins by Google account
    assert boss.get("/admin/overview").status_code == 401
    main.settings.ADMIN_EMAILS = {"boss@skymind.dev"}
    ov = boss.get("/admin/overview").json()
    assert {b["owner_email"] for b in ov["bots"]} == {"alice@acme.com"}
    assert boss.get("/me").json()["is_admin"] and not alice.get("/me").json()["is_admin"]
    assert boss.delete(f"/bots/{pub['bot_id']}", headers=H).status_code == 200
    main.settings.ADMIN_EMAILS = set()

    # owner deletes; sign out ends the session server-side
    assert alice.delete(f"/bots/{restricted['bot_id']}", headers=H).status_code == 200
    cookie = alice.cookies.get("sm_session")
    assert alice.post("/auth/logout", headers=H).status_code == 200
    assert alice.get("/me").json()["user"] is None
    with client() as replay:
        replay.cookies.set("sm_session", cookie)
        assert replay.get("/me").json()["user"] is None, "old session cookie must not work after sign-out"

    # headers for Google's button
    h = anon.get("/deploy").headers
    assert "https://accounts.google.com/gsi/client" in h["content-security-policy"]
    assert "frame-src https://accounts.google.com/gsi/" in h["content-security-policy"]
    assert h["referrer-policy"] == "strict-origin-when-cross-origin"

auth.GOOGLE_CLIENT_ID = ""
with client() as c:
    assert c.post("/bots", json=dict(BOT, access={"mode": "google"})).status_code == 422, "no Google = public only"
    assert c.post("/bots", json=BOT).status_code == 200, "no Google = no login needed"
print("app OK: sign-in, CSRF, ownership, per-bot access, Google admins, sign-out, headers")
print("ALL AUTH TESTS PASSED")
