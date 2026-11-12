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

### Use a real model (Claude)

1. At the Claude Console (console.anthropic.com), add a few dollars of credit, **set a monthly spend limit** (e.g. $10) and create an API key.
2. Locally (Windows):
   ```
   set ANTHROPIC_API_KEY=your-key-here
   docker compose up --build
   ```
   On Render: in the service's **Environment** tab add `ANTHROPIC_API_KEY`, and delete `LLM_PROVIDER` if it is there (or set it to `anthropic`). With a key and no `LLM_PROVIDER`, SkyMind uses Claude automatically.
3. Never put the key in a file or on GitHub.

Easy questions go to Claude Haiku 5.5 ($0.10 / $0.50 per million input/output tokens) and hard ones to Claude Sonnet 5.5 ($2 / $10). A typical answer costs about $0.0001 on Haiku. Reliability: a failed or overloaded call is retried once, and if the strong model is still unavailable the cheap model answers (shown as the route reason). Bad keys fail fast with a plain message; details go only to the server log. `MAX_ANSWER_TOKENS` (512) caps answer length and cost.

Do not run the load test against a real model: it refuses unless you add `--allow-real`, because it would send thousands of paid requests.

## Any AI model (model-agnostic)

Each bot picks its AI provider on the deploy page. Every provider has a cheap and a strong model, so routing works the same everywhere. Providers without a key are shown as "not set up".

| Provider | Easy questions | Hard questions | Price per million tokens (input / output) | Turn it on |
|---|---|---|---|---|
| Mock | document text, no AI | document text, no AI | free (costs shown as if Claude) | always on |
| Claude (Anthropic) | Claude Haiku 5.5 | Claude Sonnet 5.5 | $0.10 / $0.50 and $2 / $10 | `ANTHROPIC_API_KEY` |
| Gemini (Google) | Gemini 3.1 Flash-Lite | Gemini 3.5 Flash | $0.25 / $1.50 and $1.50 / $9 (both have a free tier) | `GEMINI_API_KEY` from Google AI Studio |
| Ollama (open source, your own machine) | qwen3.5:0.8b | qwen3.5:4b | free per answer | `OLLAMA_URL`, e.g. `http://host.docker.internal:11434` |

Prices are list prices from November 2026; check each provider's page. Model names can be changed with `CHEAP_MODEL` / `STRONG_MODEL` (Claude), `GEMINI_CHEAP_MODEL` / `GEMINI_STRONG_MODEL`, `OLLAMA_CHEAP_MODEL` / `OLLAMA_STRONG_MODEL`. Every provider gets the same retry and strong-to-cheap fallback, and costs are tracked at that provider's prices.

## Evaluation: measured quality, not guesses

`questions.yaml` holds 73 questions about the two sample companies: 66 with the facts a correct answer must contain, and 7 whose answer is *not* in the documents (the bot must say so). Six of them use different words than the documents ("Where do students sleep?" for housing) to test meaning search. `evaluate.py` grades:

- **search**: does each search method find the right section, and find nothing for off-topic questions?
- **routing**: does the router send hard questions to the strong model?
- **answers**: ask a running SkyMind every question with each provider and routing setting; report accuracy, correct refusals, speed and cost, then name the cheapest setup that passes the quality bar.

```bash
docker compose up --build                                   # one window
docker compose run --rm evaluate search routing             # free, instant
docker compose run --rm evaluate answers --providers mock,gemini,anthropic --routing cheap,strong,auto
docker compose run --rm evaluate answers --providers gemini --pace 5 --show   # free tier: go slower, print every answer
```

### Measured results (November 2026)

Search, 66 questions with a section to find and 7 that should find nothing:

| Method | Right section first | Right section in top 3 | Finds nothing when it should |
|---|---|---|---|
| keyword (IDF overlap) | 91% | 94% | 29% |
| **bm25** (default) | 89% | 91% | 57% |
| hybrid (bm25 + embeddings) | _run with GEMINI_API_KEY_ | | |

BM25 refuses off-topic questions about twice as often as keyword search. Its misses are questions that use different words than the documents ("sleep" vs "residence hall", "money back" vs "refund"), which is what hybrid search is for. Off-topic questions that share a word with the documents ("weather in *Denton*", "football *coach*" vs "career *coach*") still find a section; the model then says it doesn't have the answer, and the question shows up in the bot's "Questions I couldn't answer" list.

To measure hybrid and tune its similarity threshold:

```bash
set GEMINI_API_KEY=your-key
docker compose run --rm -e GEMINI_API_KEY evaluate search --tune
```
Pick the `EMBED_MIN_SIM` with the best balance of found sections and refusals, and set it in `knowledge.py`.

Routing: the router agrees with the easy/hard labels on **97%** of 65 questions (93% before the evaluation exposed "meal *plan*" being treated as a hard question; fixed). The two remaining misses are multi-part questions without a reasoning keyword.

Answers, mock provider (no AI, extractive baseline):

| Setup | Accuracy | Refusals | Overall |
|---|---|---|---|
| mock / keyword search | 93% | 38% | 85% |
| mock / bm25 search | 91% | 88% | 91% |

Add your real-model rows by running `evaluate answers` with Claude and/or Gemini.

## Bot jobs: more than answering questions

When deploying, a company picks what its bot is **for**. The documents are then its knowledge or its rules for that job:

| Job | What users do | What the documents are | Model |
|---|---|---|---|
| **Answer questions** | Ask about policies, products, services | FAQs, policies, product info | Routed: cheap for easy, strong for hard |
| **Code reviewer** | Paste code (up to 12,000 characters) | The company's engineering rules | Always strong |
| **Idea partner** | Describe a goal or problem | Products, customers, goals, limits | Always strong |

The code reviewer gives a summary (ready to merge or not), issues ranked High / Medium / Low with the fix, and **cites the company's own rule** for each one, e.g. `[Security rules]`. A plain chatbot can review code; a SkyMind reviewer reviews it against *your* standards. It never repeats a secret it finds, and flags comments that try to instruct the reviewer (prompt injection) instead of obeying them. Reviews and ideas see every document section when they fit (15,000 characters), otherwise the 6 best matches. Without an AI key, a rule-based checker (secrets, SQL injection, bare except, missing timeouts, money as float, print, TODO, eval) still reviews and cites the rules, so the demo works offline.

Samples: `/chat/acme-code-reviewer` (with a "Try sample code with bugs" button) and `/chat/acme-idea-partner`.

## Improve your bot (the improvement loop)

A bot is only as useful as its documents. SkyMind shows each company what is missing so they can fix it in minutes, without retraining any model:

1. **Questions I couldn't answer.** When the bot says it doesn't have the information, the question is logged (repeats are counted). Owners see the list under **Your bots → Improve** on `/deploy`.
2. **Thumbs up and down.** Every answer on the chat page has *Was this helpful? Yes / No*. Not-helpful answers are kept with the question so the owner can see what went wrong. The admin console shows each bot's helpful percentage.
3. **Let SkyMind fix it.** In **Improve**, enter the company website and click **Suggest fix**. SkyMind reads the page, follows the links that match the unanswered questions (same site only, up to 6 pages), finds the passages that answer each one, and drafts new sections ending in `Source: <page>`. With an AI model the strong model rewrites the passages, using only their facts, and lists what the site doesn't answer. Without one, the passages themselves are used. The owner edits the draft and clicks **Add to documents**, and the answered questions are marked fixed. Nothing is added without approval.
4. **Or add it yourself.** Type the answer (**Answer it**), upload files, or import a web page. The bot uses it on the next question.
5. **More ways to add documents:** PDF, Word (.docx), text, Markdown and CSV files (up to 5 MB each), and public web pages or online PDFs by link.
6. **Embedding search (hybrid).** Choose *Meaning + keywords* when deploying (needs GEMINI_API_KEY, free tier). Documents are embedded once with `gemini-embedding-001`; each question is matched by meaning and by words, and the two rankings are combined (reciprocal rank fusion). If embeddings fail, the bot falls back to BM25 and keeps working.

Demo: deploy a bot with only the *About UNT* paragraph, ask "Do I need a meal plan?" (it can't answer), open **Improve**, click **Suggest fix** with `https://dining.unt.edu` (or upload `unt_student_services.md`), approve, and ask again.

Web import safety: SkyMind only fetches `http(s)` pages on ports 80/443 whose addresses are all public, re-checks every redirect, and refuses localhost, private networks and cloud metadata addresses (SSRF protection). Imports are limited to 30 per hour per account.

## Tests

```bash
pip install -r requirements-dev.txt
python tests/run_all.py
```

Eight suites with no network or paid calls: bot jobs (code reviewer cites rules, never echoes secrets, strong model, size limits), Suggest fix (follows only related same-site links, refuses private addresses, drafts with sources, approval clears the questions), the improvement loop (gaps, ratings, adding information), document import (PDF, Word, web pages, blocked private addresses) and embeddings (hybrid search, fallback), plus the platform (deploy, chat, memory, isolation, budget guard, validation, admin, privacy, security headers, rate limits), sign-in (real RSA-signed tokens: forged, expired, wrong app, wrong issuer, unverified email and algorithm-swap tokens are rejected; CSRF; ownership; per-bot access; sign-out), and model providers (Claude, Gemini and Ollama request formats, retry, fallback, bad keys, cost).

## What happens when a question arrives

1. **Retrieve:** find the sections of that company's documents that best match the question (BM25 by default).
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

## Sign in with Google and bot access

When `GOOGLE_CLIENT_ID` is set:
- **Companies sign in with Google to deploy.** Their bots belong to their Google account, so they can manage them from any device under **Your bots** on `/deploy`.
- **Each company chooses who can use each bot** (when deploying, or later with **Access**):
  - *Anyone with the link* (public)
  - *Only people who sign in with Google*, optionally limited to email domains (`unt.edu`) and/or invited addresses
- **Admins** can sign in with a Google account listed in `ADMIN_EMAILS` instead of typing the admin token.

Without `GOOGLE_CLIENT_ID` everything still works: bots are public and owned through a manage key kept in the browser.

### Get a Google client ID (about 10 minutes, free)

1. Open https://console.cloud.google.com and create a project (e.g. "SkyMind").
2. Go to **Google Auth Platform** (APIs & Services). Click **Get started**: app name *SkyMind*, your support email, audience **External**, your contact email.
3. **Clients**, then **Create client**: type **Web application**. Under **Authorized JavaScript origins** add your site and local address, scheme and host only:
   - `https://skymind-XXXX.onrender.com`
   - `http://localhost` and `http://localhost:8000`
   No redirect URIs are needed. Click **Create** and copy the **Client ID** (ends in `.apps.googleusercontent.com`). There is no secret to keep.
4. **Audience**: while the app is in *Testing*, only the test users you add can sign in. Click **Publish app** to let anyone sign in (SkyMind only asks for name and email, the basic scopes).
5. In Render, open the **skymind** service, then **Environment**, and add:
   - `GOOGLE_CLIENT_ID` = the client ID
   - `ADMIN_EMAILS` = your Gmail address (comma-separate several)
   Save. Render redeploys in a few minutes.

Locally: `set GOOGLE_CLIENT_ID=...` and `set ADMIN_EMAILS=you@gmail.com` before `docker compose up --build`.

### How it is kept safe
- Google's ID token is checked on the server: Google's signature (RS256 only), audience = your client ID, issuer = Google, not expired, email verified.
- SkyMind then uses its own session: a random token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` on HTTPS). Only a SHA-256 hash is stored in Redis, and signing out deletes it.
- Every change made with the sign-in cookie must carry an `X-Requested-With: SkyMind` header, which other websites cannot add, so cross-site request forgery is blocked.
- Domain rules check Google Workspace's organisation claim (`hd`) when present, otherwise the verified email address. Google only fully vouches for Gmail and Workspace addresses. For other providers it confirms the address was verified when the account was made, so use invited addresses for anything sensitive.
- The chat page shows which domains are allowed, never the invite list.

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
| `POST /bots` | Deploy a bot from a spec and documents. Returns a secret `owner_key` (shown once) |
| `GET /bots/{id}` | One bot's public info (name, company, greeting) |
| `GET /bots/{id}/usage` | That bot's usage. Needs its `X-Owner-Key` (or the admin token) |
| `DELETE /bots/{id}` | Remove a bot, its memory and its stats. Needs its `X-Owner-Key` (or the admin token) |
| `GET /featured` | Public sample bots for the start page |
| `POST /auth/google`, `POST /auth/logout`, `GET /me` | Sign in with a Google ID token, sign out, who is signed in |
| `GET /my/bots` | Bots owned by the signed-in Google account |
| `PATCH /bots/{id}/access` | Change who can chat with a bot (owner or admin) |
| `GET /bots` | Every bot (admin token only) |
| `POST /bots/{id}/chat` | Chat with a bot. Returns `answer_id` (for rating) and `unanswered` |
| `POST /bots/{id}/feedback` | Rate an answer helpful or not (only the conversation that got it) |
| `GET /bots/{id}/improve` | Questions it couldn't answer, ratings, not-helpful answers (owner or admin) |
| `DELETE /bots/{id}/gaps?question=` | Mark a question fixed (owner or admin) |
| `POST /bots/{id}/suggest-fix` | Read the company's site and draft the missing sections for the unanswered questions (owner or admin) |
| `POST /bots/{id}/knowledge` | Add (`append`) or replace (`replace`) a bot's documents (owner or admin) |
| `POST /import/file` | Turn a PDF, Word, text, Markdown or CSV file into text |
| `POST /import/url` | Turn a public web page or online PDF into text |
| `GET /admin/overview` | All bots with plan, usage, latency, cost, budget status |
| `DELETE /admin/stats` | Reset usage counters |
| `POST /plan` | Capacity and cost plan for a spec |
| `GET /examples` | Sample customers (UNT Helper, Acme Support) |
| `GET /providers` | AI providers this server can use, their models and prices |
| `GET /health` | Health check |

Interactive docs: http://localhost:8000/docs

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| LLM_PROVIDER | auto | Default provider for new bots: Claude if ANTHROPIC_API_KEY is set, else Gemini if GEMINI_API_KEY is set, else mock |
| ANTHROPIC_API_KEY, GEMINI_API_KEY, OLLAMA_URL | (empty) | Turn on Claude, Gemini, Ollama |
| CHEAP_MODEL / STRONG_MODEL | claude-haiku-5-5 / claude-sonnet-5-5 | Claude models (Gemini and Ollama have their own, see "Any AI model") |
| SEARCH_METHOD | bm25 | Default search for new bots: `bm25`, `keyword` or `hybrid` |
| EMBED_MODEL / EMBED_DIM | gemini-embedding-001 / 768 | Embedding model and vector size for hybrid search (needs GEMINI_API_KEY) |
| FIX_LIMIT_PER_HOUR | 10 | Suggest fix runs per bot per hour |
| IMPORT_LIMIT_PER_HOUR | 30 | File and web-page imports per account or address per hour |
| MAX_ANSWER_TOKENS | 512 | Longest answer, caps cost |
| MEMORY_WINDOW | 10 | Recent exchanges kept per conversation |
| MEMORY_TTL_SECONDS | 3600 | Conversation memory expiry |
| WORKERS | 1 | Server processes inside the container |
| MAX_BOTS | 50 | Maximum number of deployed bots |
| GOOGLE_CLIENT_ID | (empty) | Turns on Sign in with Google and per-bot access rules |
| ADMIN_EMAILS | (empty) | Google accounts that are admins (comma separated) |
| REQUIRE_LOGIN_TO_DEPLOY | auto | `auto` = sign-in required to deploy when Google is on; or `true` / `false` |
| SESSION_DAYS | 7 | How long a sign-in lasts |
| ADMIN_TOKEN | generated | Token for /admin and admin API calls. If empty, one is generated, stored in Redis and printed at startup |
| BIND_ADDRESS | 127.0.0.1 | Who can open SkyMind. `127.0.0.1` = only this computer; `0.0.0.0` = every device on your network |
| CHAT_LIMIT_PER_SESSION | 60 | Messages per minute per conversation (0 = off) |
| CHAT_LIMIT_PER_IP | 0 | Messages per minute per client address (0 = off; turn on for public servers) |
| HARD_STOP_FACTOR | 1.2 | Bot stops answering at 120% of its monthly model budget |
| MAX_BODY_BYTES | 1000000 | Largest request accepted (bytes) |
| REDIS_MAX_CONNECTIONS | 1000 | Redis connections per worker (raised after a load test hit "Too many connections" at 500 users) |

## Files

`main.py` (service and API), `providers.py` (Claude, Gemini, Ollama behind one interface), `auth.py` (Google sign-in, sessions, bot access rules), `evaluate.py` and `questions.yaml` (quality evaluation), `tests/` (test suites), `router.py` (cheap vs strong routing, savings), `planner.py` (capacity and cost), `knowledge.py` (document retrieval), `embeddings.py` (meaning search), `jobs.py` (answer, code reviewer, idea partner), `fixer.py` (Suggest fix), `improve.py` (unanswered questions and ratings), `ingest.py` (PDF, Word and web page import), `unt_student_services.md` (sample document to upload), `examples.py` (sample customers), `pages.py` (the three pages), `loadtest.py` (load tester), `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `spec.yaml` and `spec_demo.yaml` (example specs for the planner).

## Honest limits

- "Deploy" currently creates an isolated bot (own documents, memory, routing, budget and stats) inside one running service. Giving each customer a separate Kubernetes deployment with autoscaling is the next step.
- Memory types `summary` and `long_term` are planned. Today every bot keeps the recent messages of each conversation.
- BM25 and keyword search can miss questions that use different words than the documents. Hybrid search fixes this but needs a Gemini key, and its threshold is only tuned once you run `evaluate search --tune`.
- Vectors are stored in Redis next to the bot; for very large document sets a vector database (pgvector) would be the next step.
- Pages that need JavaScript to show text, and scanned PDFs (images), import as almost no text. Suggest fix reads links in the page's HTML; menus built by JavaScript are not followed, so give it a more specific page (e.g. the FAQ).
- The offline code checker only knows a handful of patterns; real reviews need an AI model.
- Answers are graded by required facts, which is strict and explainable but can mark a correct paraphrase as wrong (e.g. "fourteen" vs "14"). Check misses with `--show`.
- Accounts are individual Google sign-ins. Teams (several people managing one company's bots) are not built yet.
- The deploy page is open to anyone who can reach the server, limited by MAX_BOTS. Keep BIND_ADDRESS at 127.0.0.1 unless you need others to connect.
- Costs are estimates from placeholder prices until calibrated.
- The UNT Helper sample uses facts collected from official UNT pages in November 2026. Verify details on unt.edu.

## Security

| Risk | Protection |
|---|---|
| Someone on the same Wi-Fi opens your SkyMind | Port 8000 is published to `127.0.0.1` only. Redis is never published. |
| One company sees or changes another company's bots | Each bot gets a secret manage key (only its SHA-256 hash is stored). Usage and delete need that key. The full bot list is admin-only, the deploy page shows only "Your bots" from this browser, and bot links carry 8 random hex characters. |
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
6. Evaluation set and model-agnostic providers (done). Next: run it on Claude and Gemini and record the numbers above
7. Improvement loop: unanswered questions, ratings, file and web import, hybrid embedding search (done). Next: tune with a Gemini key; long-term memory and pgvector
8. Per-customer Kubernetes deployment with autoscaling
9. Teams and roles for companies (Google sign-in and per-bot access are done)
