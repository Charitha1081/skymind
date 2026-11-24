# SkyMind

SkyMind is an AI orchestration platform. A company says what it needs ("a chatbot for our customers, around 500 users at a time, answers in under 4 seconds, $600 a month"), adds its documents, and SkyMind works out the capacity and cost, deploys the bot, sends each question to a cheap or a strong model, keeps spending under budget, and reports how it is doing.

## The three pages

| Page | Who it is for | What it does |
|---|---|---|
| `/deploy` | A company | Describe needs (users, latency, memory, model routing, budget), add documents, click Deploy bot. Shows the plan: servers, expected latency, monthly cost. |
| `/chat/{bot_id}` | The company's end users | Chat with the deployed bot. It answers only from that company's documents and shows which model answered. |
| `/admin` | SkyMind operators (us) | Every customer bot: plan vs actual cost, requests, latency (avg and p95), money saved by routing, budget-guard status. Delete a bot or reset counters. |

`/` is a start page that links to all three.

How it fits together: [`docs/architecture.md`](docs/architecture.md) (diagrams). What's next: [`TODO.md`](TODO.md). What we got wrong and fixed: [`docs/reversals.md`](docs/reversals.md).

## Run it

```bash
docker compose up --build
```

Open http://localhost:8000. The server window prints a line like `SkyMind admin token: AbC123...`; you need it to open `/admin`. It starts in mock mode (no API key needed), where answers come straight from the matching document section.

Quick demo:
1. Open `/deploy`, click Load: Fernleaf Assistant, then Deploy bot.
2. Open the bot's chat link and ask a few questions ("How much is the Team plan?", "When is the Fernleaf Summit?", "Is there an Android app?", and something it can't know, like "What is Fernleaf's stock price?").
3. Watch `/admin` update live.

### Use a real model (Claude)

1. At the Claude Console (console.anthropic.com), add a few dollars of credit, set a monthly spend limit (say $10), and create an API key.
2. Locally (Windows):
   ```
   set ANTHROPIC_API_KEY=your-key-here
   docker compose up --build
   ```
   On Render: in the service's Environment tab add `ANTHROPIC_API_KEY`, and delete `LLM_PROVIDER` if it is there (or set it to `anthropic`). With a key and no `LLM_PROVIDER`, SkyMind uses Claude automatically.
3. Never put the key in a file or on GitHub.

Easy questions go to Claude Haiku 5.5 ($0.10 / $0.50 per million input/output tokens) and hard ones to Claude Sonnet 5.5 ($2 / $10). A typical answer costs about $0.0001 on Haiku. If a call fails or is overloaded it is retried once, and if the strong model is still unavailable the cheap model answers (the route reason says so). Bad keys fail fast with a plain message, and the details go only to the server log. `MAX_ANSWER_TOKENS` (512) caps answer length and cost.

Don't run the load test against a real model. It refuses unless you add `--allow-real`, because it would send thousands of paid requests.

## Any AI model (model-agnostic)

Each bot picks its AI provider on the deploy page. Every provider has a cheap and a strong model, so routing works the same way everywhere. Providers without a key show up as "not set up".

| Provider | Easy questions | Hard questions | Price per million tokens (input / output) | Turn it on |
|---|---|---|---|---|
| Mock | document text, no AI | document text, no AI | free (costs shown as if Claude) | always on |
| Claude (Anthropic) | Claude Haiku 5.5 | Claude Sonnet 5.5 | $0.10 / $0.50 and $2 / $10 | `ANTHROPIC_API_KEY` |
| Gemini (Google) | Gemini 3.1 Flash-Lite | Gemini 3.5 Flash | $0.25 / $1.50 and $1.50 / $9 (both have a free tier) | `GEMINI_API_KEY` from Google AI Studio |
| Ollama (open source, your own machine) | qwen3.5:0.8b | qwen3.5:4b | free per answer | `OLLAMA_URL`, e.g. `http://host.docker.internal:11434` |

Prices are list prices from November 2026; check each provider's page. You can change model names with `CHEAP_MODEL` / `STRONG_MODEL` (Claude), `GEMINI_CHEAP_MODEL` / `GEMINI_STRONG_MODEL`, and `OLLAMA_CHEAP_MODEL` / `OLLAMA_STRONG_MODEL`. Every provider gets the same retry and strong-to-cheap fallback, and costs are tracked at that provider's prices.

## Evaluation

`questions.yaml` holds 116 questions about three made-up companies, written as two corpora of different kinds: a product FAQ (Fernleaf Software, plus the small Acme Outdoor Gear set) and a long employee handbook full of rules and exceptions (Kestrel Logistics). 104 have facts a correct answer must contain and 12 have no answer in the documents (the bot has to say so). Some use different words from the documents ("Can I use it on my phone?" for the mobile apps) to test meaning search. `evaluate.py` grades three things:

- search: does each search method find the right section, and find nothing for off-topic questions?
- routing: does the router send hard questions to the strong model?
- answers: ask a running SkyMind every question with each provider and routing setting, then report accuracy, correct refusals, speed and cost, and name the cheapest setup that passes the quality bar.

```bash
docker compose up --build                                   # one window
docker compose run --rm evaluate search routing             # free, instant
docker compose run --rm evaluate answers --providers mock,gemini,anthropic --routing cheap,strong,auto
docker compose run --rm evaluate answers --providers gemini --pace 5 --show   # free tier: go slower, print every answer
python evaluate_search.py                                   # search recall on every question set, offline
```

### Measured results (November 2026)

All 116 questions, three made-up companies, two kinds of corpus: 105 with a section to find and 11 that should find nothing.

**Search** (`evaluate.py search --tune`, offline apart from Gemini embeddings for hybrid):

| Method | Right section first | Right section in top 3 | Finds nothing when it should |
|---|---|---|---|
| keyword (IDF overlap) | 87% | 92% | 36% (4/11) |
| bm25 | 85% | 90% | 73% (8/11) |
| **hybrid (bm25 + embeddings)** | **93%** | **98%** | **73% (8/11)** |

Hybrid finds the right section more often and refuses off-topic questions as well as BM25, so it is the default whenever GEMINI_API_KEY is set. Its advantage grew from 5 points on the product FAQ alone to 8 points once the handbook was added: it fixed every handbook miss caused by different wording ("paid" vs "Pay", "grandmother" vs "grandparent", "stressed" vs "counseling", "shoes" vs "steel-toe boots", "apartment" vs "home"). The similarity threshold `EMBED_MIN_SIM = 0.62` is still the best balance (0.55 finds one more answer but refuses only 36% of off-topic questions). Only 11 questions test refusals, so each one is worth 9 points.

BM25 per corpus (`python evaluate_search.py <bot>`):

| Corpus | Kind | Right section in top 3 | Finds nothing when it should |
|---|---|---|---|
| Fernleaf | product FAQ | 38/39 = 97% | 3/4 |
| Acme | small product FAQ | 16/20 = 80% | 3/4 |
| Kestrel | long policy handbook | 39/45 = 87% | 3/4 |
| **all** | | **93/104 = 89.4%** | **9/12** |

On one product FAQ, word search looked better than it is; the handbook is what exposed it.

**Answers with Claude** (all 116 questions, BM25 search, document answers only, website lookup off, one run each):

| Setup | Fernleaf | Acme | Kestrel | Correct refusals | Model time avg / p95 | $ per 1,000 answers |
|---|---|---|---|---|---|---|
| cheap: claude-haiku-5-5 | 41/43 | 24/24 | 47/49 | 100% | 0.87 s / 1.18 s | 0.16 |
| strong: claude-sonnet-5-5 | 41/43 | 24/24 | 48/49 | 100% | 1.66 s / 3.51 s | 4.42 |

The cheap model got 112 of 116 right and the strong one 113, at 1/27 of the price and half the time, so the cheap model is the recommended setting. The one difference is on the handbook, the first sign that rule-heavy questions may need the strong model, but it is one question. Model time comes from each answer's trace; whole-answer times measured from a laptop include network travel and a Render wake-up, so they are not reported here.

Every miss is explained in [`docs/error-taxonomy.md`](docs/error-taxonomy.md): of 7 misses, 5 were search misses, 2 were the grader being too strict, and none was the model ignoring a section it was shown. The search misses led to the topic-guided second look (`orchestrator.py`, `named_topics`); its effect still has to be measured on the next run.

**After the fix** (same 116 questions, cheap model, BM25, one run):

| Run | Fernleaf | Acme | Kestrel | Total | $ per 1,000 answers |
|---|---|---|---|---|---|
| Before (cheap) | 41/43 | 24/24 | 47/49 | 112/116 | 0.16 |
| After (cheap) | 42/43 | 24/24 | 49/49 | 115/116 | 0.18 |

Of the 3 extra points, 2 come from the second look (both handbook search misses now answered) and 1 from correcting the grader on the downgrade question, so the system itself improved by 2 questions. It costs about 10% more per answer, because a refusal now triggers a second model call. The one remaining miss ("How can I talk to a person?") is a known limitation: the refusal was phrased in a way SkyMind does not recognise, and it named the wrong topic. The fix was designed from these exact misses, so it still has to be confirmed on a held-out set.

**On questions it was never tuned on** (`questions_heldout.yaml`: 121 questions written by ChatGPT from each company's documents alone, without SkyMind's code, the tuning questions or the section titles, then checked by `questions_kit.py` and reviewed by hand; cheap model, BM25):

| | Fernleaf | Kestrel | Both |
|---|---|---|---|
| Search: right section in top 3 (BM25) | 43/51 = 84% | 36/45 = 80% | 79/96 = 82% |
| Answerable, as graded | 46/51 | 41/45 | 87/96 = 91% |
| Answerable, after reviewing the grader's 3 errors by hand | 48/51 | 42/45 | 90/96 = 94% |
| Unanswerable, correctly refused | 14/14 | 11/11 | 25/25 = 100% |
| Overall | 60/65 | 52/56 | 112/121 = 93% |

The tuning set had scored 100% on Kestrel; the first held-out run scored 87% there (before the empty-reply and grader fixes), and this run 91%. Of the 9 misses, 4 were search misses, 2 were answers from the wrong section, 3 were the grader being too literal ("no card required" against a required "no credit card"), and none was an invented fact. Every unanswerable question was refused even though search returned a section for each of them: they are on-topic ("Is Fernleaf HIPAA-compliant?"), so search cannot filter them out, and the model is what said it didn't know. The most serious miss repeated in both runs: for "My paycheck is wrong, who do I email?", search missed the payroll section and the model gave the general HR address. 15 questions in this run never reached the bot (connection errors while the hosted service restarted); they were run once more and all connected. All misses are in [`docs/error-taxonomy.md`](docs/error-taxonomy.md), runs 3 and 4. Held-out misses are reported, not fixed: changing code because of them would turn the held-out set into a tuning set.

Routing: the router agrees with the easy/hard labels on all 104 labelled questions. Treat that as a sanity check, not a result: these questions were written by people who knew how the router works. All numbers above come from one tuning set that was used to make decisions, so they need confirming on held-out and blind sets (see [`docs/writing-questions.md`](docs/writing-questions.md)). How the router was rebuilt after failing on new questions is in `docs/reversals.md`.

To measure hybrid and tune its similarity threshold:

```bash
set GEMINI_API_KEY=your-key
docker compose run --rm -e GEMINI_API_KEY evaluate search --tune
```
Pick the `EMBED_MIN_SIM` with the best balance of found sections and refusals, and set it in `knowledge.py`.

To compare models by results (which questions only the strong model got right, and what each setup costs):

```bash
python evaluate.py answers --url https://your-service --providers anthropic --routing cheap,strong,auto --pace 4 --save results.json
```

## Website lookup

Each question-answering bot has a knowledge source, chosen on `/deploy` and changeable under Improve:

- Documents only (strict): if the documents don't have it, the bot says so.
- Documents, then our website: if the documents don't answer (including partial answers like "However, I don't have the details..."), SkyMind looks the question up on the company's own site, for example `example.com` and its subdomains, and nowhere else on the internet. The answer starts "That isn't in Acme's documents, so I checked acme.example:", shows a "From the company website" chip, and links its source pages.

How it works (`web.py`):
1. Claude bots use Claude's web search tool with `allowed_domains` set to the company's domain, and its citations become the source links. Each search costs $0.01 ($10 per 1,000) and is counted in the bot's spend. At most 3 searches per question.
2. Other providers, or an Anthropic organisation that has web search turned off, fall back to SkyMind's own reader (the Suggest fix crawler), which reads the site, follows related same-site links (SSRF-safe) and answers from the best passages.

A few guards keep this cheap and honest: answers are cached for a day per question, `WEB_LOOKUPS_PER_HOUR` (default 30) per bot caps the bill, and while streaming the first 300 characters are held back so a "not in my documents" answer is never shown before the lookup runs. Every website answer is still logged under "Questions it couldn't answer", marked "answered from your website", so the company can add it to its documents (or click Suggest fix) and skip the lookup next time.

Turn it on per bot on the deploy page (Company website) or in the bot's Improve panel.

## Streaming answers

Answers appear word by word, like ChatGPT. `POST /bots/{id}/chat/stream` sends Server-Sent Events: a `start` event (model tier, sources), many `text` pieces as the model writes, then a `done` event with the same fields as `/chat` plus `first_token_ms` (time to the first word, shown as a chip). Claude, Gemini and Ollama each stream in their own format, and `providers.stream()` parses all three behind one async generator.

- Access, rate limits, budget and message length are all checked before the first byte, so those stay normal HTTP errors.
- If the stream fails before any text, SkyMind uses the normal call (retry plus strong-to-cheap fallback) and sends the answer in one piece. If it fails halfway, the user keeps the words already shown plus a short note.
- Memory, cost, the unanswered-question log and ratings work exactly as with `/chat` (both share `prepare_chat()` and `finish_chat()`).
- `Cache-Control: no-cache` and `X-Accel-Buffering: no` stop proxies from holding the pieces back. The chat page falls back to `/chat` if the browser can't stream.

## Bot jobs

When deploying, a company picks what its bot is for. The documents are then its knowledge, or its rules, for that job:

| Job | What users do | What the documents are | Model |
|---|---|---|---|
| Answer questions | Ask about policies, products, services | FAQs, policies, product info | Routed: cheap for easy, strong for hard |
| Code reviewer | Paste code (up to 12,000 characters) | The company's engineering rules | Always strong |
| Idea partner | Describe a goal or problem | Products, customers, goals, limits | Always strong |

The code reviewer gives a summary (ready to merge or not), issues ranked High / Medium / Low with the fix, and cites the company's own rule for each one, for example `[Security rules]`. A plain chatbot can review code; a SkyMind reviewer reviews it against your standards. It never repeats a secret it finds, and it flags comments that try to instruct the reviewer (prompt injection) rather than obeying them. Reviews and ideas see every document section when they fit (15,000 characters), otherwise the 6 best matches. Without an AI key, a rule-based checker (secrets, SQL injection, bare except, missing timeouts, money as float, print, TODO, eval) still reviews and cites the rules, so the demo works offline.

Ready-made standards: a company doesn't have to write rules from scratch. On `/deploy`, a code reviewer can start from OWASP Top 10:2025 (security), PEP 8 (Python style) or clean code basics in one click (`GET /standards`, written in `standards.py` as short review rules that summarise the public standards). The company adds its own rules on top. The reviewer cites both, for example `[Security rules] [OWASP A05: Injection]`, and the company's rules win when they disagree.

Samples: `/chat/acme-code-reviewer` (with a "Try sample code with bugs" button; it has Acme's rules plus OWASP Top 10) and `/chat/acme-idea-partner`.

## Improving a bot

A bot is only as good as its documents, so SkyMind shows each company what is missing and lets them fix it in minutes, without retraining any model.

1. Questions I couldn't answer. When the bot says it doesn't have the information, the question is logged and repeats are counted. Owners see the list under Your bots → Improve on `/deploy`.
2. Thumbs up and down. Every answer on the chat page has "Was this helpful? Yes / No". Not-helpful answers are kept with the question so the owner can see what went wrong, and the admin console shows each bot's helpful percentage.
3. Let SkyMind fix it. In Improve, enter the company website and click Suggest fix. SkyMind reads the page, follows the links that match the unanswered questions (same site only, up to 6 pages), finds the passages that answer each one, and drafts new sections that end in `Source: <page>`. With an AI model the strong model rewrites the passages using only their facts and lists what the site doesn't answer; without one, the passages themselves are used. The owner edits the draft, clicks Add to documents, and the answered questions are marked fixed. Nothing is added without approval.
4. Or add it yourself. Type the answer (Answer it), upload files, or import a web page. The bot uses it on the next question.
5. More ways to add documents: PDF, Word (.docx), text, Markdown and CSV files (up to 5 MB each), and public web pages or online PDFs by link.
6. Embedding search (hybrid). Choose "Meaning + keywords" when deploying (needs GEMINI_API_KEY, free tier). Documents are embedded once with `gemini-embedding-001`, each question is matched by meaning and by words, and the two rankings are combined with reciprocal rank fusion. If embeddings fail, the bot falls back to BM25 and keeps working.

Demo: deploy a bot with only the "About Fernleaf" paragraph, ask "Is there an Android app?" (it can't answer), open Improve, upload `fernleaf_help_center.md` (or type the answer), approve, and ask again.

Web import safety: SkyMind only fetches `http(s)` pages on ports 80/443 whose addresses are all public, re-checks every redirect, and refuses localhost, private networks and cloud metadata addresses (SSRF protection). Imports are limited to 30 per hour per account.

## Tests

```bash
pip install -r requirements-dev.txt
python tests/run_all.py
```

Thirteen suites, none of which touch the network or make paid calls:

- the orchestrator (the trace of every answer, the second look, honest refusals)
- the model router (each signal, how they add up, forced modes)
- website lookup (strict mode, cache, Claude search with allowed_domains and the fee, fallback when search is off, refusal held back while streaming)
- streaming (Claude, Gemini and Ollama stream parsers, event order, fallbacks)
- bot jobs (code reviewer cites rules, never echoes secrets, strong model, size limits)
- Suggest fix (follows only related same-site links, refuses private addresses, drafts with sources, approval clears the questions)
- the improvement loop (gaps, ratings, adding information)
- document import (PDF, Word, web pages, blocked private addresses)
- embeddings (hybrid search, fallback)
- the platform (deploy, chat, memory, isolation, budget guard, validation, admin, privacy, security headers, rate limits)
- sign-in (real RSA-signed tokens: forged, expired, wrong app, wrong issuer, unverified email and algorithm-swap tokens are all rejected; CSRF; ownership; per-bot access; sign-out)
- model providers (Claude, Gemini and Ollama request formats, retry, fallback, bad keys, cost)
- the security and budget fixes (visitor address, monthly budget, DNS pinning, strong-to-cheap fallback, safe concurrent edits)

## What happens when a question arrives

1. Retrieve: find the sections of that company's documents that best match the question (BM25 by default).
2. Route: easy questions go to the cheap model. A question goes to the strong model when it is long, contains code, or shows enough signs of difficulty, meaning it asks for reasoning, asks several things at once, or describes a situation with numbers to work through. The answer says why (`route_reason`).
3. Budget guard: once a bot has used its monthly LLM budget, the strong model is paused and everything goes to the cheap model.
4. Answer from the retrieved sections only. If the answer isn't in the documents, the bot says so.
   - Second look: word search can miss a section that uses other words ("When do I get my paycheck?" vs "Pay and payroll"). When the model says it has no answer, SkyMind gives it the sections its refusal named from the topic list ("ask me about Pay and payroll"), then the best sections of a wider search, and asks once more. A real answer replaces the refusal; otherwise the refusal stands and the question is logged. Turn it off with `SECOND_LOOK=false`.
5. Remember the recent messages of that conversation (memory is separate for each bot).
6. Record latency, tokens, cost, and what the request would have cost on the strong model.
7. Show its work: every answer carries a `trace` (checks, route, search, model, second look, website, save) with the time each step took. The chat page shows it under "How this answer was made".

## Deploying on Render

`render.yaml` describes the whole setup, so Render builds it for you: the SkyMind website plus a private Redis.

1. Put these files in your GitHub repo, including `render.yaml`. Never upload an API key.
2. Go to https://render.com and sign up with GitHub.
3. Click New, then Blueprint. Pick your `skymind` repo and click Apply.
4. Wait for the build (about 3 to 5 minutes). Your site is at `https://skymind-XXXX.onrender.com`.
5. For the admin token, open the skymind service in Render, go to Environment, and copy `ADMIN_TOKEN`.

The hosted version differs in a few ways:
- It starts with the sample bots at stable links: `/chat/fernleaf-assistant` and `/chat/fernleaf-code-reviewer`.
- Per-visitor limits apply: 30 messages per minute, 10 deploys per hour, 20 bots at most.
- It runs the mock model (no API key, no cost). For real answers, add `ANTHROPIC_API_KEY` in the Environment tab and set `LLM_PROVIDER=anthropic`.

On the free plan the site sleeps after 15 minutes with no visitors and takes about a minute to wake, and free Redis is wiped on restart (the sample bots come back automatically). Before a demo, open the site a few minutes early and keep the admin page open, since it refreshes every 2 seconds and that keeps the site awake.

## Sign in with Google and bot access

When `GOOGLE_CLIENT_ID` is set:
- Companies sign in with Google to deploy. Their bots belong to their Google account, so they can manage them from any device under Your bots on `/deploy`.
- Each company chooses who can use each bot, when deploying or later under Access:
  - Anyone with the link (public)
  - Only people who sign in with Google, optionally limited to email domains (`yourcompany.com`) and/or invited addresses
- Admins can sign in with a Google account listed in `ADMIN_EMAILS` instead of typing the admin token.

Without `GOOGLE_CLIENT_ID` everything still works: bots are public and owned through a manage key kept in the browser.

### Get a Google client ID (about 10 minutes, free)

1. Open https://console.cloud.google.com and create a project (e.g. "SkyMind").
2. Go to Google Auth Platform (APIs & Services). Click Get started: app name SkyMind, your support email, audience External, your contact email.
3. Go to Clients, then Create client, type Web application. Under Authorized JavaScript origins add your site and local address, scheme and host only:
   - `https://skymind-XXXX.onrender.com`
   - `http://localhost` and `http://localhost:8000`
   No redirect URIs are needed. Click Create and copy the Client ID (it ends in `.apps.googleusercontent.com`). There is no secret to keep.
4. Audience: while the app is in Testing, only the test users you add can sign in. Click Publish app to let anyone sign in (SkyMind only asks for name and email, the basic scopes).
5. In Render, open the skymind service, go to Environment, and add:
   - `GOOGLE_CLIENT_ID` = the client ID
   - `ADMIN_EMAILS` = your Gmail address (comma-separate several)
   Save. Render redeploys in a few minutes.

Locally: `set GOOGLE_CLIENT_ID=...` and `set ADMIN_EMAILS=you@gmail.com` before `docker compose up --build`.

### How it is kept safe
- Google's ID token is checked on the server: Google's signature (RS256 only), audience equal to your client ID, issuer equal to Google, not expired, email verified.
- SkyMind then uses its own session: a random token in an `HttpOnly`, `SameSite=Lax` cookie (`Secure` on HTTPS). Only a SHA-256 hash is stored in Redis, and signing out deletes it.
- Every change made with the sign-in cookie has to carry an `X-Requested-With: SkyMind` header, which other websites can't add, so cross-site request forgery is blocked.
- Domain rules check Google Workspace's organisation claim (`hd`) when it's present, otherwise the verified email address. Google only fully vouches for Gmail and Workspace addresses; for other providers it confirms the address was verified when the account was made, so use invited addresses for anything sensitive.
- The chat page shows which domains are allowed, never the invite list.

## Load testing

The load tester simulates many users chatting at once and prints latency, throughput and errors. It runs inside Docker, so you don't need Python on your computer. It refuses to run against a real (paid) model unless you add `--allow-real`.

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

`/plan` (and `python planner.py spec.yaml`) turns a spec into replicas, a latency check and a monthly cost estimate. The deploy page runs it for every new bot. All token prices, traffic patterns and replica capacity are placeholder assumptions at the top of `planner.py`. Replace them with your load-test measurements and your provider's real prices before quoting results.

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
| `PATCH /bots/{id}/web` | Set the company website and turn website lookup on or off (owner or admin) |
| `POST /bots/{id}/chat/stream` | Same, streamed as Server-Sent Events (`start`, `text`..., `done` or `error`) |
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
| `GET /examples` | Sample bots shown on the deploy page (Fernleaf Assistant, Fernleaf Code Reviewer) |
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
| WEB_LOOKUPS_PER_HOUR | 30 | Website lookups per bot per hour (each Claude web search costs $0.01) |
| FIX_LIMIT_PER_HOUR | 10 | Suggest fix runs per bot per hour |
| IMPORT_LIMIT_PER_HOUR | 30 | File and web-page imports per account or address per hour |
| MAX_ANSWER_TOKENS | 512 | Longest answer, caps cost |
| STREAM_MOCK_DELAY_S | 0.02 | Mock provider: pause between streamed words (demo only) |
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
| SECOND_LOOK | true | When the model says it has no answer, search the documents more widely and ask once more |
| REDIS_MAX_CONNECTIONS | 1000 | Redis connections per worker (raised after a load test hit "Too many connections" at 500 users) |

## Files

The service, in the order a request passes through it:

| File | What it holds |
|---|---|
| `main.py` | Starts the service and connects the parts below (about 70 lines) |
| `settings.py` | Every setting an environment variable can change |
| `runtime.py` | The shared Redis and HTTP connections |
| `security.py` | Sign-in, admins, bot owners, rate limits, security headers |
| `routes_bots.py`, `routes_chat.py`, `routes_improve.py`, `routes_admin.py`, `routes_account.py`, `routes_site.py` | The HTTP endpoints, grouped by area |
| `orchestrator.py` | What happens to one question: access, limits, budget, routing, search, model call with retry and fallback, website lookup, cost and gap logging, streaming |
| `store.py` | Bots, documents, conversation memory and usage counters in Redis |

The parts the orchestrator uses: `router.py` (cheap or strong model, savings), `providers.py` (Claude, Gemini, Ollama behind one interface), `knowledge.py` (splitting and searching documents), `embeddings.py` (meaning search), `jobs.py` (answer, code reviewer, idea partner), `standards.py` (OWASP, PEP 8, clean code rule sets), `web.py` (website lookup), `improve.py` (unanswered questions and ratings), `fixer.py` (Suggest fix), `ingest.py` (PDF, Word and web page import), `auth.py` (Google sign-in, sessions, bot access rules), `planner.py` (capacity and cost), `pages.py` (the web pages), `examples.py` (sample customers).

Quality and testing: `evaluate.py` with `questions.yaml`, `questions_heldout.yaml`, `questions_third.yaml` and `questions_blind.yaml` (evaluation), `tests/` (twelve test suites), `loadtest.py` (load tester).

Other: `fernleaf_help_center.md` (sample document to upload), `TODO.md` (roadmap), `docs/` (architecture and reversals), `Dockerfile`, `docker-compose.yml`, `render.yaml`, `requirements.txt`, `spec.yaml` and `spec_demo.yaml` (example specs for the planner).

## Limitations

- "Deploy" currently creates an isolated bot (its own documents, memory, routing, budget and stats) inside one running service. A separate Kubernetes deployment per customer, with autoscaling, is the next step.
- Memory types `summary` and `long_term` are planned. For now every bot keeps the recent messages of each conversation.
- The router is rule based. It scored 89% on questions it was never tuned to, and "hard" is a human label. On document questions the cheap model was nearly as accurate as the strong one, so how much the router adds over just using the cheap model is still being measured (`evaluate.py answers` reports it). A small classifier model, or escalating only when the cheap answer looks weak, are the next steps.
- BM25 and keyword search can miss questions worded differently from the documents. Hybrid search fixes this but needs a Gemini key, and its threshold is only tuned once you run `evaluate search --tune`.
- Vectors are stored in Redis next to the bot. For very large document sets a vector database (pgvector) would be the next step.
- Pages that need JavaScript to show text, and scanned PDFs (images), import as almost no text. Suggest fix reads links in the page's HTML; menus built by JavaScript aren't followed, so give it a more specific page (for example the FAQ).
- The offline code checker only knows a handful of patterns; real reviews need an AI model.
- Answers are graded by required facts, which is strict and explainable but can mark a correct paraphrase as wrong ("fourteen" vs "14"). Check misses with `--show`.
- Accounts are individual Google sign-ins. Teams (several people managing one company's bots) aren't built yet.
- The deploy page is open to anyone who can reach the server, limited by MAX_BOTS. Keep BIND_ADDRESS at 127.0.0.1 unless you need others to connect.
- Costs are estimates from placeholder prices until calibrated.
- The sample companies (Fernleaf Software, Acme Outdoor Gear) are made up.

## Security

| Risk | Protection |
|---|---|
| Someone on the same Wi-Fi opens your SkyMind | Port 8000 is published to `127.0.0.1` only. Redis is never published. |
| One company sees or changes another company's bots | Each bot gets a secret manage key (only its SHA-256 hash is stored). Usage and delete need that key. The full bot list is admin-only, the deploy page shows only "Your bots" from this browser, and bot links carry 8 random hex characters. |
| Someone deletes bots or reads admin data | `/admin/overview`, `DELETE /admin/stats` and `DELETE /bots/{id}` need the `X-Admin-Token` header (constant-time check). The public start page uses `/stats`, which has totals only. |
| Spam runs up a real API bill | Per-conversation rate limit, optional per-address limit, budget guard (strong model paused), then a hard stop at 120% of the model budget. |
| Huge or malformed requests | 1 MB request limit, 200,000-character document limit, 4,000-character messages, session IDs restricted to letters, digits, `-` and `_`. |
| Prompt injection ("ignore your rules...") | The system prompt treats documents and messages as data, never as instructions, and never reveals the prompt or keys. This reduces the risk but no prompt removes it completely. |
| Script injection in the pages | All text is inserted with `textContent`, plus a Content-Security-Policy, `X-Frame-Options: DENY`, `nosniff` and `no-referrer`. |
| Leaked secrets | The API key comes only from an environment variable, model errors are logged on the server and not sent to the browser, and `.gitignore` blocks `.env` files. |
| Container break-out damage | The app runs as a non-root user with `no-new-privileges`. Dependencies are pinned to tested major versions. |

The load tester reads the admin token automatically (from ADMIN_TOKEN or Redis). For a load test, raise or turn off the per-conversation limit if you lower the think time: `set CHAT_LIMIT_PER_SESSION=0`.

### Guard check: common attacks, tested

`python guard_check.py` tries a well-known list of attacks on quickly built apps against a private in-memory copy of SkyMind (no network, no cost), and CI runs it on every push:

| Result | Attacks |
|---|---|
| Blocked (14) | type /admin; change the ID in the URL; API key in the browser; edit the price (a $99,999,999,999 budget); negative or absurd numbers; redeem it 100 times; admin at signup; guess the login code; script in your username; upload a non-photo or fetch a private address; .env in Git; query the database; over budget (one bot, then the whole server); cross-site request (CSRF) |
| Reduced, not eliminated | prompt injection: documents and messages are treated as data and the prompt holds no secrets, but a model can still be talked off-script |
| Not applicable | fake a payment (SkyMind takes no payments) |

The first run blocked 11 of 14. The gap: whoever deploys a bot picks its budget, but whoever runs the server pays the model bill, so a visitor could deploy a bot with an enormous budget and chat on the owner's credits, and a negative budget was accepted. Now every bot not deployed with the admin token (sample bots included) gets at most `MAX_BOT_LLM_BUDGET` ($5 by default) of model spending a month, all bots together stop at `MAX_FLEET_LLM_BUDGET` ($20 by default; admins exempt so evaluations still run), and nonsense budgets are refused. Also set a monthly spend limit in the model provider's console: it is the last line of defence.

## Roadmap

Built so far: the chatbot service with Redis memory, the capacity planner, cheap/strong model routing with savings tracking, the multi-customer platform (deploy, chat and admin pages), the load tester, the evaluation set with model-agnostic providers, the improvement loop (unanswered questions, ratings, file and web import, hybrid search), and Google sign-in with per-bot access.

What comes next, in order, is in [`TODO.md`](TODO.md): finish the measurements, make the evaluation meaningful (a second document set, held-out questions, an error taxonomy), then the technical report. Longer term: per-customer Kubernetes deployments with autoscaling, long-term memory, and teams for companies.
