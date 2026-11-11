# SkyMind

AI orchestration platform. A company says what it needs ("a chatbot for our customers, about 500 users at a time, answers in under 4 seconds, $600 a month"), adds its documents, and SkyMind plans the capacity and cost, deploys the bot, routes each question to a cheap or a strong model, keeps it under budget, and shows how it is doing.

## The three pages

| Page | Who it is for | What it does |
|---|---|---|
| `/deploy` | A company | Describe needs (users, latency, memory, model routing, budget), add documents, click **Deploy bot**. Shows the plan: servers, expected latency, monthly cost. |
| `/chat/{bot_id}` | The company's end users | Chat with the deployed bot. It answers only from that company's documents and shows which model answered. |
| `/admin` | SkyMind operators (us) | Every customer bot: plan vs actual cost, requests, latency (avg and p95), money saved by routing, budget-guard status. Delete a bot or reset counters. |

`/` is a start page linking to all three.

## Run it

```bash
docker compose up --build
```

Then open http://localhost:8000. The server window prints a line like `SkyMind admin token: AbC123...`. You need it to open **/admin**. It starts in **mock** mode (no API key needed), where answers are taken straight from the matching document section.

Quick demo:
1. Open **/deploy** and click **Load: UNT Helper**, then **Deploy bot**. Do the same for **Acme Support**.
2. Open each bot's chat link and ask questions ("How many colleges does UNT have?", "When is the AI Expo?", "What is the return policy?").
3. Watch **/admin** update live.

### Use a real model

```
set LLM_PROVIDER=anthropic
set ANTHROPIC_API_KEY=your-key-here
docker compose up --build
```

(Windows command prompt. On Mac/Linux use `export` instead of `set`.) Never put the key in a file or on GitHub.

## What happens when a question arrives

1. **Retrieve:** find the sections of that company's documents that best match the question.
2. **Route:** easy questions go to the cheap model, hard ones (long, code, several questions, "explain", "compare", "why") to the strong model.
3. **Budget guard:** once a bot has used its monthly LLM budget, the strong model is paused and everything goes to the cheap model.
4. **Answer** from the retrieved sections only. If the answer is not in the documents, the bot says so.
5. **Remember** the recent messages of that conversation (memory is separate for each bot).
6. **Record** latency, tokens, cost, and what it would have cost with the strong model for everything.

## Put it on the internet (free, on Render)

`render.yaml` describes the whole setup, so Render builds it for you: the SkyMind website plus a private Redis.

1. Put these files in your GitHub repo (including `render.yaml`). Never upload an API key.
2. Go to https://render.com, sign up with GitHub.
3. Click **New**, then **Blueprint**. Pick your `skymind` repo and click **Apply**.
4. Wait for the build (about 3 to 5 minutes). Your site is at `https://skymind-XXXX.onrender.com`.
5. Admin token: in Render, open the **skymind** service, then **Environment**, and copy `ADMIN_TOKEN`.

What the hosted version does differently:
- Starts with the sample bots at stable links: `/chat/unt-helper` and `/chat/acme-support`.
- Per-visitor limits: 30 messages per minute, 10 deploys per hour, 20 bots at most.
- Mock model (no API key, no cost). For real answers add `ANTHROPIC_API_KEY` in the Environment tab and set `LLM_PROVIDER=anthropic`.

Free-plan limits: the site sleeps after 15 minutes with no visitors and takes about a minute to wake, and free Redis is wiped on restart (the sample bots come back automatically). Before a demo, open the site a few minutes early and keep the admin page open (it refreshes every 2 seconds, so the site stays awake).

## Load testing

Simulates many users chatting at once and prints latency, throughput and errors. It runs inside Docker, so you do not need Python on your computer. It refuses to run against a real (paid) model unless you add `--allow-real`.

```bash
docker compose up --build                          # in one window, leave running
docker compose run --rm loadtest --sweep           # in a second window: 100, 500 and 1000 users
docker compose run --rm loadtest --users 200 --duration 60
```

To compare scaling, restart with more server workers and run it again:

```
set WORKERS=2
docker compose up --build
```

The server and the load tester share one machine, so treat the numbers as a lower bound. Paste the Markdown table it prints into this README as your measured results:

| Users | Requests | Req/s | Errors | Avg ms | p95 ms | p99 ms |
|---|---|---|---|---|---|---|
| 100 | _run the load test_ | | | | | |
| 500 | | | | | | |
| 1000 | | | | | | |

## Capacity planner

`/plan` (and `python planner.py spec.yaml`) turns a spec into replicas, a latency check and a monthly cost estimate. The deploy page runs it for every new bot. All token prices, traffic patterns and replica capacity are **placeholder assumptions** at the top of `planner.py`. Replace them with your load-test measurements and your provider's real prices before quoting results.

## API

| Method and path | Purpose |
|---|---|
| `POST /bots` | Deploy a bot from a spec and documents |
| `GET /bots`, `GET /bots/{id}` | List bots, or get one bot's public info |
| `DELETE /bots/{id}` | Remove a bot, its memory and its stats |
| `POST /bots/{id}/chat` | Chat with a bot |
| `GET /admin/overview` | All bots with plan, usage, latency, cost, budget status |
| `DELETE /admin/stats` | Reset usage counters |
| `POST /plan` | Capacity and cost plan for a spec |
| `GET /examples` | Sample customers (UNT Helper, Acme Support) |
| `GET /health` | Health check |

Interactive docs: http://localhost:8000/docs

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| LLM_PROVIDER | mock | `mock` or `anthropic` |
| CHEAP_MODEL | claude-haiku-5-5 | Model for easy questions |
| STRONG_MODEL | claude-sonnet-5-5 | Model for hard questions |
| MEMORY_WINDOW | 10 | Recent exchanges kept per conversation |
| MEMORY_TTL_SECONDS | 3600 | Conversation memory expiry |
| WORKERS | 1 | Server processes inside the container |
| MAX_BOTS | 50 | Maximum number of deployed bots |
| ADMIN_TOKEN | generated | Token for /admin and admin API calls. If empty, one is generated, stored in Redis and printed at startup |
| BIND_ADDRESS | 127.0.0.1 | Who can open SkyMind. `127.0.0.1` = only this computer; `0.0.0.0` = every device on your network |
| CHAT_LIMIT_PER_SESSION | 60 | Messages per minute per conversation (0 = off) |
| CHAT_LIMIT_PER_IP | 0 | Messages per minute per client address (0 = off; turn on for public servers) |
| HARD_STOP_FACTOR | 1.2 | Bot stops answering at 120% of its monthly model budget |
| MAX_BODY_BYTES | 1000000 | Largest request accepted (bytes) |
| REDIS_MAX_CONNECTIONS | 1000 | Redis connections per worker (raised after a load test hit "Too many connections" at 500 users) |

## Files

`main.py` (service and API), `router.py` (cheap vs strong routing, savings), `planner.py` (capacity and cost), `knowledge.py` (document retrieval), `examples.py` (sample customers), `pages.py` (the three pages), `loadtest.py` (load tester), `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `spec.yaml` and `spec_demo.yaml` (example specs for the planner).

## Honest limits

- "Deploy" currently creates an isolated bot (own documents, memory, routing, budget and stats) inside one running service. Giving each customer a separate Kubernetes deployment with autoscaling is the next step.
- Memory types `summary` and `long_term` are planned. Today every bot keeps the recent messages of each conversation.
- Document retrieval uses keyword matching. Embeddings in pgvector are planned.
- Admin actions are protected by one shared admin token. Customer accounts (each company sees only its own bots) are not built yet.
- The deploy page is open to anyone who can reach the server, limited by MAX_BOTS. Keep BIND_ADDRESS at 127.0.0.1 unless you need others to connect.
- Costs are estimates from placeholder prices until calibrated.
- The UNT Helper sample uses facts collected from official UNT pages in November 2026. Verify details on unt.edu.

## Security

| Risk | Protection |
|---|---|
| Someone on the same Wi-Fi opens your SkyMind | Port 8000 is published to `127.0.0.1` only. Redis is never published. |
| Someone deletes bots or reads admin data | `/admin/overview`, `DELETE /admin/stats` and `DELETE /bots/{id}` need the `X-Admin-Token` header (constant-time check). The public start page uses `/stats`, which has totals only. |
| Spam runs up a real API bill | Per-conversation rate limit, optional per-address limit, budget guard (strong model paused), then a hard stop at 120% of the model budget. |
| Huge or malformed requests | 1 MB request limit, 200,000-character document limit, 4,000-character messages, session IDs restricted to letters, digits, `-` and `_`. |
| Prompt injection ("ignore your rules...") | The system prompt treats documents and messages as data, never as instructions, and never reveals the prompt or keys. This reduces the risk but no prompt fully removes it. |
| Script injection in the pages | All text is inserted with `textContent`, plus a Content-Security-Policy, `X-Frame-Options: DENY`, `nosniff` and `no-referrer`. |
| Leaked secrets | The API key comes only from an environment variable, model errors are logged on the server and not sent to the browser, and `.gitignore` blocks `.env` files. |
| Container break-out damage | The app runs as a non-root user with `no-new-privileges`. Dependencies are pinned to tested major versions. |

Load testing reads the admin token automatically (from ADMIN_TOKEN or Redis). For a load test, raise or turn off the per-conversation limit if you lower the think time: `set CHAT_LIMIT_PER_SESSION=0`.

## Roadmap

1. Chatbot service with Redis memory (done)
2. Capacity planner: spec to replicas and cost (done, placeholder assumptions)
3. Model routing, cheap vs strong, with savings tracking (done)
4. Multi-customer platform: deploy page, end-user chat page, admin console (done)
5. Load test tool (done). Next: run it at 100 / 500 / 1,000 users and record the real numbers above
6. Long-term memory with pgvector and embeddings
7. Per-customer Kubernetes deployment with autoscaling
8. Customer accounts and per-company access (admin token protection is done)
