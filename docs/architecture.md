# SkyMind architecture

## The pieces

```mermaid
flowchart LR
    subgraph Users
        company["Company<br/>/deploy"]
        enduser["End user<br/>/chat/{bot}"]
        operator["Operator<br/>/admin"]
    end

    subgraph SkyMind["SkyMind web service (FastAPI, main.py)"]
        security["security.py<br/>sign-in, owners, admins,<br/>rate limits, headers"]
        routes["routes_*.py<br/>HTTP endpoints"]
        orch["orchestrator.py<br/>one question, end to end"]
        planner["planner.py<br/>capacity and cost plan"]
        knowledge["knowledge.py<br/>sections, BM25 / keyword /<br/>hybrid search"]
        router["router.py<br/>cheap or strong model"]
        providers["providers.py<br/>Claude, Gemini, Ollama, mock"]
        web["web.py + fixer.py<br/>company website lookup"]
        ingest["ingest.py<br/>PDF, Word, web import"]
        improve["improve.py<br/>gaps and ratings"]
        store["store.py<br/>bots, memory, usage"]
    end

    redis[("Redis<br/>bots, documents, memory,<br/>counters, sessions")]
    llm["AI model APIs"]
    site["Company website"]

    company & enduser & operator --> security --> routes
    routes --> planner
    routes --> ingest
    routes --> orch
    orch --> knowledge
    orch --> router
    orch --> providers --> llm
    orch --> web --> site
    orch --> improve
    orch & routes --> store --> redis
```

## What happens to one question

```mermaid
flowchart TD
    q([Question]) --> checks["1. Checks<br/>access rules, rate limits,<br/>monthly budget, hard stop"]
    checks -->|blocked| err([Error: 401 / 403 / 429])
    checks --> route["2. Route<br/>cheap or strong model;<br/>budget used up → cheap only"]
    route --> search["3. Search<br/>best 3 sections of this bot's documents"]
    search --> model["4. Model call<br/>retry once; strong → cheap fallback"]
    model --> ans{Did it answer?}
    ans -->|yes| save
    ans -->|no| second["5. Second look<br/>wider search, ask again"]
    second --> ans2{Answered now?}
    ans2 -->|yes| save
    ans2 -->|no, and the bot has a website| website["6. Website lookup<br/>only the company's own site"]
    ans2 -->|no| save
    website --> save["7. Save and record<br/>memory, cost, latency,<br/>unanswered question logged"]
    save --> reply([Answer + sources + trace])
```

Every answer carries a `trace` with the time each step took, and the chat page shows it under "How this answer was made".

## Where it runs

- **Locally:** `docker compose up --build` starts SkyMind and Redis. Redis is never published outside the containers.
- **On Render:** `render.yaml` creates the web service and a private Redis. `SEED_EXAMPLES` re-creates the sample bots on every start, because the free Redis is wiped on restart. `TRUSTED_PROXY_HOPS` tells SkyMind which `X-Forwarded-For` entry is the real visitor.
