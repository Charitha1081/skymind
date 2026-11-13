"""SkyMind settings: every value that can be changed with an environment variable, in one place.

The rest of the code reads these as settings.NAME, so a test (or an operator) can change one value
and every part of the service sees it.
"""
import os

import providers

# --- storage ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "1000"))  # per worker process
BOT_CACHE_SECONDS = 5  # how long a worker keeps a bot's documents in memory
MAX_BOTS = int(os.getenv("MAX_BOTS", "50"))
MAX_KNOWLEDGE_CHARS = 200_000
SEED_EXAMPLES = os.getenv("SEED_EXAMPLES", "false").lower() in ("1", "true", "yes")  # deploy sample bots on an empty start

# --- models and answers ---
# Default provider for new bots: LLM_PROVIDER if set, else the first one with a key (Claude, Gemini), else mock.
LLM_PROVIDER = providers.default_provider()
SEARCH_METHOD = os.getenv("SEARCH_METHOD", "bm25").strip().lower()  # default search for new bots (keyword | bm25)
MAX_ANSWER_TOKENS = int(os.getenv("MAX_ANSWER_TOKENS", "512"))  # caps cost and length of each answer
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "25"))
SECOND_LOOK = os.getenv("SECOND_LOOK", "true").lower() in ("1", "true", "yes")  # no answer found: search wider, ask once more
STREAM_MOCK_DELAY_S = float(os.getenv("STREAM_MOCK_DELAY_S", "0.02"))  # mock provider: pause between words

# --- conversation memory ---
MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", "10"))  # last N exchanges kept per conversation
MEMORY_TTL_SECONDS = int(os.getenv("MEMORY_TTL_SECONDS", "3600"))

# --- spending ---
HARD_STOP_FACTOR = float(os.getenv("HARD_STOP_FACTOR", "1.2"))  # stop answering at 120% of the model budget

# --- security and rate limits ---
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()  # empty: one is generated and printed in the logs
ADMIN_EMAILS = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}  # Google accounts that are admins
REQUIRE_LOGIN_TO_DEPLOY = os.getenv("REQUIRE_LOGIN_TO_DEPLOY", "auto").lower()  # auto = yes when Google sign-in is on
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "1000000"))  # reject requests larger than ~1 MB
SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{1,128}$"
CHAT_LIMIT_PER_SESSION = int(os.getenv("CHAT_LIMIT_PER_SESSION", "60"))  # messages per minute per conversation (0 = off)
CHAT_LIMIT_PER_IP = int(os.getenv("CHAT_LIMIT_PER_IP", "0"))  # messages per minute per client address (0 = off)
DEPLOY_LIMIT_PER_IP = int(os.getenv("DEPLOY_LIMIT_PER_IP", "20"))  # bot deploys per hour per client address (0 = off)
IMPORT_LIMIT_PER_HOUR = int(os.getenv("IMPORT_LIMIT_PER_HOUR", "30"))  # document imports per hour per client address
FIX_LIMIT_PER_HOUR = int(os.getenv("FIX_LIMIT_PER_HOUR", "10"))  # Suggest fix runs per bot per hour
WEB_LOOKUPS_PER_HOUR = int(os.getenv("WEB_LOOKUPS_PER_HOUR", "30"))  # website lookups per bot per hour
