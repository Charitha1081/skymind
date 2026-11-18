"""Things every part of SkyMind shares while the server runs.

state holds the live connections, created once at startup (main.py):
  state.redis        Redis client: bots, conversation memory, counters, sessions
  state.http         one HTTP client for all calls to AI providers and websites
  state.bot_cache    bots loaded in the last few seconds (store.load_bot)
  state.admin_token  the operator token for /admin
"""
import logging

from starlette.datastructures import State

state = State()
log = logging.getLogger("skymind")
