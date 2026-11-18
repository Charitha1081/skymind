"""SkyMind: deploy and manage AI chatbots for companies.

Three pages:
  /deploy        a company describes what it needs and adds its documents
  /chat/{bot_id} that company's end users chat with the deployed bot
  /admin         SkyMind operators see every bot: usage, latency, cost, savings

This file only starts the service and connects its parts:

  settings.py        every setting that an environment variable can change
  runtime.py         the shared Redis and HTTP connections
  security.py        sign-in, admins, bot owners, rate limits, security headers
  store.py           bots, documents, conversation memory and usage counters in Redis
  orchestrator.py    what happens to one question: access, limits, budget, routing, search,
                     model call with retry and fallback, website lookup, cost and gap logging
  routes_*.py        the HTTP endpoints, grouped by area (bots, chat, improve, admin, account, site)

  router.py          cheap model or strong model?        planner.py     capacity and cost plan from a spec
  providers.py       Claude, Gemini, Ollama, mock        knowledge.py   splitting and searching documents
  jobs.py            answer / code reviewer / ideas      improve.py     gaps and ratings
  web.py, fixer.py   the company's own website           ingest.py      PDF, Word and web page import
"""
import secrets
from contextlib import asynccontextmanager

import httpx
import redis.asyncio as redis
from fastapi import FastAPI

import orchestrator
import routes_account
import routes_admin
import routes_bots
import routes_chat
import routes_improve
import routes_site
import runtime
import security
import settings
import store
from runtime import log


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = runtime.state
    # Each worker needs enough Redis connections for all requests it has in flight at once.
    state.redis = redis.from_url(settings.REDIS_URL, decode_responses=True, max_connections=settings.REDIS_MAX_CONNECTIONS)
    state.http = httpx.AsyncClient(timeout=60)
    state.bot_cache = {}
    # One admin token shared by every worker: from ADMIN_TOKEN, or generated once and kept in Redis.
    if settings.ADMIN_TOKEN:
        state.admin_token = settings.ADMIN_TOKEN
    else:
        await state.redis.set(store.ADMIN_TOKEN_KEY, secrets.token_urlsafe(18), nx=True)
        state.admin_token = await state.redis.get(store.ADMIN_TOKEN_KEY)
        print(f"SkyMind admin token: {state.admin_token}  (enter it on /admin)", flush=True)
    if settings.SEED_EXAMPLES:
        try:
            await store.seed_examples()
        except Exception as err:  # seeding is a convenience; never block startup
            log.warning("Could not seed sample bots: %s", err)
    yield
    await state.http.aclose()
    await state.redis.aclose()


app = FastAPI(title="SkyMind", lifespan=lifespan)
app.state = runtime.state  # one shared state object: the modules use runtime.state, tests use app.state
app.middleware("http")(security.security_layer)
for part in (routes_site, routes_bots, routes_chat, routes_improve, routes_admin, routes_account):
    app.include_router(part.api)

__all__ = ["app", "orchestrator"]
