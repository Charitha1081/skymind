"""The web pages and the small read-only endpoints they use (plan, providers, standards, examples, health)."""
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import HTMLResponse

import embeddings
import examples
import pages
import planner
import providers
import settings
import standards
from runtime import state
from store import BOTS_SET

api = APIRouter(tags=["Site"])


@api.post("/plan")
async def plan_endpoint(
    spec: dict = Body(
        ...,
        examples=[
            {
                "expected_concurrent_users": 200,
                "latency_target_p95": "4s",
                "memory": "window",
                "model": "auto",
                "monthly_budget": "$300",
            }
        ],
    ),
):
    """Turn a chatbot spec into a capacity and cost plan."""
    try:
        result = planner.plan(planner.parse_spec(spec))
    except ValueError as err:
        raise HTTPException(422, str(err))
    result["summary"] = planner.format_plan(result)
    return result


@api.get("/standards")
async def list_standards():
    """Ready-made coding standards a code-reviewer bot can start from (OWASP Top 10, PEP 8, clean code)."""
    return standards.STANDARDS


@api.get("/providers")
async def list_providers():
    """AI providers this server can use, their cheap and strong models, and list prices."""
    return {"default": settings.LLM_PROVIDER, "providers": providers.describe(), "embeddings": embeddings.available(),
            "default_search": settings.SEARCH_METHOD}


@api.get("/examples")
async def get_examples():
    """Sample customers the deploy page can load with one click."""
    return examples.EXAMPLES


@api.get("/", response_class=HTMLResponse)
async def home_page():
    return pages.LANDING_HTML


@api.get("/deploy", response_class=HTMLResponse)
async def deploy_page():
    return pages.DEPLOY_HTML


@api.get("/chat/{bot_id}", response_class=HTMLResponse)
async def chat_page(bot_id: str):
    return pages.CHAT_HTML


@api.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return pages.ADMIN_HTML


@api.get("/health")
async def health():
    try:
        await state.redis.ping()
    except Exception:
        raise HTTPException(503, "redis unreachable")
    return {
        "status": "ok",
        "provider": settings.LLM_PROVIDER,
        "bots": await state.redis.scard(BOTS_SET),
        "memory_window": settings.MEMORY_WINDOW,
    }
