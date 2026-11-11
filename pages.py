r"""SkyMind web pages. Each page is one self-contained HTML string (no outside libraries,
fonts or images, so everything works offline).

  LANDING_HTML  /              start page: what SkyMind is, links to the three views
  DEPLOY_HTML   /deploy        page for companies: describe needs, see a live plan, deploy
  CHAT_HTML     /chat/{id}     page for a company's end users: chat with the bot
  ADMIN_HTML    /admin         page for SkyMind operators: every bot, usage, cost, savings

Brand idea ("altitude"): everyday questions take the low, cheap route (sky blue);
hard questions climb to the strong model (indigo). The same two colours mark the
model tier everywhere: chat chips, admin routing bars, the start-page diagram.
"""

LOGO_SVG = r"""<svg class="logo" viewBox="0 0 32 32" aria-hidden="true" focusable="false"><defs><linearGradient id="sm-grad" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#1E9BD7"/><stop offset="1" stop-color="#3A2BA8"/></linearGradient></defs><rect width="32" height="32" rx="9" fill="url(#sm-grad)"/><circle cx="16" cy="11.5" r="4.2" fill="#fff"/><path d="M6 20.5c3.2-3 6.6-3 10 0s6.8 3 10 0" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M6 25.5c3.2-3 6.6-3 10 0s6.8 3 10 0" stroke="#fff" stroke-opacity=".55" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>"""

COMMON_CSS = r"""
:root {
  --bg: #F3F7FC; --surface: #FFFFFF; --ink: #0D1B36; --muted: #56678A; --line: #DCE5F0;
  --sky: #1E8FCB; --zenith: #3A2BA8; --on-zenith: #FFFFFF;
  --sky-soft: #E2F1FA; --zenith-soft: #ECE9FB;
  --good: #13795B; --good-soft: #E1F4EC; --warn: #A35604; --warn-soft: #FCF0DE; --bad: #BE3226; --bad-soft: #FBE7E4;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #08102A; --surface: #0F1937; --ink: #E8EEFC; --muted: #96A6CA; --line: #233259;
    --sky: #4DBDF5; --zenith: #A193FF; --on-zenith: #0B1030;
    --sky-soft: #0E2C47; --zenith-soft: #211C50;
    --good: #45C99A; --good-soft: #0F3029; --warn: #F2B15A; --warn-soft: #3A2A12; --bad: #FF8478; --bad-soft: #3D1A1C;
    color-scheme: dark;
  }
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font-family: "Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Roboto, sans-serif;
  font-size: 15px; line-height: 1.55;
}
.wrap { max-width: 1120px; margin: 0 auto; padding: 0 20px; }
a { color: var(--zenith); text-underline-offset: 3px; }
:focus-visible { outline: 3px solid var(--zenith); outline-offset: 2px; border-radius: 6px; }

/* header */
.site-header { border-bottom: 1px solid var(--line); background: var(--surface); }
.site-header .wrap { display: flex; align-items: center; gap: 24px; min-height: 64px; flex-wrap: wrap; }
.brand { display: inline-flex; align-items: center; gap: 10px; color: var(--ink); text-decoration: none; font-weight: 700; font-size: 19px; letter-spacing: -0.015em; margin-right: auto; }
.brand .logo { width: 30px; height: 30px; flex: none; }
.brand small { font-weight: 500; font-size: 13px; color: var(--muted); letter-spacing: 0; margin-left: 2px; }
.site-nav { display: flex; gap: 22px; align-items: center; flex-wrap: wrap; }
.site-nav a { color: var(--muted); text-decoration: none; font-weight: 550; padding: 20px 0 18px; border-bottom: 2px solid transparent; }
.site-nav a:hover { color: var(--ink); }
.site-nav a[aria-current="page"] { color: var(--ink); border-bottom-color: var(--zenith); }

/* type */
h1 { font-family: "Segoe UI Variable Display", "Segoe UI", system-ui, -apple-system, sans-serif; font-weight: 700; letter-spacing: -0.028em; line-height: 1.06; margin: 0; }
h2 { font-size: 19px; letter-spacing: -0.01em; line-height: 1.3; margin: 0 0 6px; }
h3 { font-size: 15px; margin: 0 0 4px; }
.lead { color: var(--muted); font-size: 17px; max-width: 60ch; margin: 14px 0 0; }
.sub { color: var(--muted); }
.small { font-size: 13px; }
.num { font-variant-numeric: tabular-nums; }
.good { color: var(--good); } .warn { color: var(--warn); } .bad { color: var(--bad); }

/* surfaces */
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; padding: 22px; }
.panel + .panel { margin-top: 16px; }

/* controls */
label { display: block; font-size: 13px; font-weight: 600; margin: 14px 0 6px; }
label .sub { font-weight: 400; }
input, select, textarea {
  width: 100%; font: inherit; font-size: 15px; padding: 10px 12px; border-radius: 10px;
  border: 1px solid var(--line); background: var(--bg); color: var(--ink);
}
input:focus, select:focus, textarea:focus { outline: none; border-color: var(--zenith); box-shadow: 0 0 0 3px var(--zenith-soft); }
input[type="file"] { padding: 8px; background: var(--surface); }
textarea { min-height: 220px; resize: vertical; line-height: 1.5; }
.btn, button {
  font: inherit; font-size: 15px; font-weight: 600; padding: 10px 18px; border-radius: 10px; cursor: pointer;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink);
  text-decoration: none; display: inline-flex; align-items: center; gap: 8px; line-height: 1.2;
}
.btn:hover, button:hover { border-color: var(--muted); }
.btn.primary, button.primary { background: var(--zenith); border-color: var(--zenith); color: var(--on-zenith); }
.btn.primary:hover, button.primary:hover { filter: brightness(1.08); }
button.quiet { border-color: transparent; background: transparent; color: var(--muted); padding: 8px 10px; }
button.quiet:hover { color: var(--bad); border-color: transparent; }
button:disabled { opacity: 0.55; cursor: default; filter: none; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-top: 18px; }

/* chips, pills, bars */
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px; font-size: 12.5px; font-weight: 550; background: var(--bg); border: 1px solid var(--line); color: var(--muted); white-space: nowrap; }
.chip .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
.chip.cheap { background: var(--sky-soft); border-color: transparent; color: var(--ink); }
.chip.cheap .dot { background: var(--sky); }
.chip.strong { background: var(--zenith-soft); border-color: transparent; color: var(--ink); }
.chip.strong .dot { background: var(--zenith); }
.pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12.5px; font-weight: 600; white-space: nowrap; }
.pill.good { background: var(--good-soft); color: var(--good); }
.pill.warn { background: var(--warn-soft); color: var(--warn); }
.pill.bad { background: var(--bad-soft); color: var(--bad); }
.bar { display: flex; height: 8px; border-radius: 999px; overflow: hidden; background: var(--line); }
.bar span { display: block; height: 100%; }
.bar .sky { background: var(--sky); } .bar .zenith { background: var(--zenith); }
.bar .ok { background: var(--good); } .bar .over { background: var(--bad); } .bar .near { background: var(--warn); }
.live { display: inline-flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; font-weight: 550; }
.live i { width: 9px; height: 9px; border-radius: 50%; background: var(--muted); }
.live.on i { background: var(--good); box-shadow: 0 0 0 4px var(--good-soft); }

/* tables */
.table-scroll { overflow-x: auto; margin: 0 -22px; padding: 0 22px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }
th { color: var(--muted); font-weight: 600; font-size: 13px; white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; }

.site-footer { color: var(--muted); font-size: 13px; padding: 36px 0 48px; }
.site-footer .wrap { display: flex; gap: 16px; flex-wrap: wrap; justify-content: space-between; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
"""


def _header(active=""):
    def link(href, key, text):
        cur = ' aria-current="page"' if key == active else ""
        return '<a href="' + href + '"' + cur + ">" + text + "</a>"

    return (
        '<header class="site-header"><div class="wrap">'
        '<a class="brand" href="/">' + LOGO_SVG + "SkyMind</a>"
        '<nav class="site-nav" aria-label="Main">'
        + link("/", "home", "Overview")
        + link("/deploy", "deploy", "Deploy a bot")
        + link("/admin", "admin", "Admin console")
        + "</nav></div></header>"
    )


FOOTER = (
    '<footer class="site-footer"><div class="wrap">'
    "<span>SkyMind: AI helpers, deployed and managed.</span>"
    "<span>Demo build for the UNT AI Expo, November 2026. Costs use placeholder prices.</span>"
    "</div></footer>"
)


def _shell(title, body, script, extra_css=""):
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"theme-color\" content=\"#3A2BA8\">\n"
        "<title>" + title + "</title>\n"
        "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%233A2BA8'/%3E%3Ccircle cx='16' cy='11.5' r='4.2' fill='white'/%3E%3Cpath d='M6 21c3-3 7-3 10 0s7 3 10 0' stroke='white' stroke-width='2.4' fill='none'/%3E%3C/svg%3E\">\n"
        "<style>" + COMMON_CSS + extra_css + "</style>\n</head>\n<body>\n"
        + body + "\n<script>\n" + script + "\n</script>\n</body>\n</html>\n"
    )


# ------------------------------------------------------------------ landing

LANDING_CSS = r"""
.hero { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr); gap: 48px; align-items: center; padding: 56px 0 40px; }
.hero h1 { font-size: clamp(36px, 5vw, 58px); max-width: 14ch; }
.hero .actions { margin-top: 28px; }
.route { background: var(--surface); border: 1px solid var(--line); border-radius: 20px; padding: 18px 18px 14px; }
.route svg { display: block; width: 100%; height: auto; }
.route figcaption { font-size: 13px; color: var(--muted); padding: 4px 4px 0; }
.stats { display: flex; gap: 32px; flex-wrap: wrap; margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.stats div { min-width: 120px; }
.stats b { display: block; font-size: 22px; letter-spacing: -0.01em; }
.stats span { font-size: 13px; color: var(--muted); }

.section { padding: 40px 0 8px; }
.section > h2 { font-size: 24px; letter-spacing: -0.02em; }
.views { margin-top: 18px; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }
.view { display: grid; grid-template-columns: 200px minmax(0, 1fr) auto; gap: 24px; align-items: center; padding: 22px 24px; border-top: 1px solid var(--line); }
.view:first-child { border-top: 0; }
.view .who { font-weight: 700; font-size: 17px; }
.view .who span { display: block; font-weight: 500; font-size: 13px; color: var(--muted); }
.view p { margin: 0; color: var(--muted); }
.botlinks { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.botlinks a { text-decoration: none; }
.botlinks .chip { color: var(--ink); }

.steps { list-style: none; counter-reset: step; margin: 18px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; border: 1px solid var(--line); border-radius: 16px; background: var(--surface); overflow: hidden; }
.steps li { counter-increment: step; padding: 20px 22px; border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.steps li:nth-child(3n) { border-right: 0; }
.steps li:nth-child(n+4) { border-bottom: 0; }
.steps li::before { content: counter(step); display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; background: var(--zenith-soft); color: var(--zenith); font-weight: 700; font-size: 13px; margin-bottom: 10px; }
.steps p { margin: 0; color: var(--muted); font-size: 14px; }

@media (max-width: 860px) {
  .hero { grid-template-columns: 1fr; gap: 28px; padding-top: 36px; }
  .view { grid-template-columns: 1fr; gap: 10px; }
  .steps { grid-template-columns: 1fr; }
  .steps li { border-right: 0; border-bottom: 1px solid var(--line) !important; }
  .steps li:last-child { border-bottom: 0 !important; }
}
"""

ROUTE_SVG = r"""
<svg viewBox="0 0 520 330" role="img" aria-labelledby="route-title">
  <title id="route-title">A question goes to the SkyMind router. Everyday questions take the low route to the cheap model; hard ones climb to the strong model.</title>
  <defs>
    <linearGradient id="altitude" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="var(--zenith)" stop-opacity=".14"/>
      <stop offset="1" stop-color="var(--sky)" stop-opacity=".12"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="520" height="330" rx="14" fill="url(#altitude)"/>
  <text x="16" y="26" font-size="12" fill="var(--muted)">Higher: stronger, slower, costlier</text>
  <text x="16" y="316" font-size="12" fill="var(--muted)">Lower: faster and cheaper</text>

  <g fill="none" stroke-width="2.5" stroke-linecap="round">
    <path id="p-in" d="M92 165 H170" stroke="var(--muted)" stroke-opacity=".6"/>
    <path id="p-strong" d="M226 165 C262 165 262 82 318 82 H372 C412 82 412 165 436 165" stroke="var(--zenith)"/>
    <path id="p-cheap" d="M226 165 C262 165 262 248 318 248 H372 C412 248 412 165 436 165" stroke="var(--sky)"/>
  </g>

  <g class="pulses">
    <circle r="5" fill="var(--muted)"><animateMotion dur="1.2s" repeatCount="indefinite"><mpath href="#p-in"/></animateMotion></circle>
    <circle r="6" fill="var(--sky)"><animateMotion dur="2.4s" repeatCount="indefinite"><mpath href="#p-cheap"/></animateMotion></circle>
    <circle r="6" fill="var(--sky)"><animateMotion dur="2.4s" begin="-0.6s" repeatCount="indefinite"><mpath href="#p-cheap"/></animateMotion></circle>
    <circle r="6" fill="var(--sky)"><animateMotion dur="2.4s" begin="-1.2s" repeatCount="indefinite"><mpath href="#p-cheap"/></animateMotion></circle>
    <circle r="6" fill="var(--sky)"><animateMotion dur="2.4s" begin="-1.8s" repeatCount="indefinite"><mpath href="#p-cheap"/></animateMotion></circle>
    <circle r="6" fill="var(--zenith)"><animateMotion dur="3s" begin="-1.5s" repeatCount="indefinite"><mpath href="#p-strong"/></animateMotion></circle>
  </g>
  <g>
    <rect x="18" y="143" width="74" height="44" rx="12" fill="var(--surface)" stroke="var(--line)"/>
    <text x="55" y="170" font-size="13" font-weight="600" text-anchor="middle" fill="var(--ink)">Question</text>
  </g>
  <g>
    <circle cx="198" cy="165" r="28" fill="var(--surface)" stroke="var(--zenith)" stroke-width="2"/>
    <text x="198" y="161" font-size="11" font-weight="700" text-anchor="middle" fill="var(--ink)">SkyMind</text>
    <text x="198" y="175" font-size="11" text-anchor="middle" fill="var(--muted)">router</text>
  </g>
  <g>
    <rect x="290" y="60" width="112" height="44" rx="12" fill="var(--surface)" stroke="var(--zenith)" stroke-width="1.5"/>
    <text x="346" y="80" font-size="13" font-weight="600" text-anchor="middle" fill="var(--ink)">Strong model</text>
    <text x="346" y="96" font-size="11" text-anchor="middle" fill="var(--muted)">hard questions</text>
  </g>
  <g>
    <rect x="290" y="226" width="112" height="44" rx="12" fill="var(--surface)" stroke="var(--sky)" stroke-width="1.5"/>
    <text x="346" y="246" font-size="13" font-weight="600" text-anchor="middle" fill="var(--ink)">Cheap model</text>
    <text x="346" y="262" font-size="11" text-anchor="middle" fill="var(--muted)">everyday questions</text>
  </g>
  <g>
    <rect x="436" y="143" width="68" height="44" rx="12" fill="var(--surface)" stroke="var(--line)"/>
    <text x="470" y="170" font-size="13" font-weight="600" text-anchor="middle" fill="var(--ink)">Answer</text>
  </g>

</svg>
"""

LANDING_BODY = _header("home") + r"""
<main class="wrap">
  <section class="hero">
    <div>
      <h1>Your company's AI helper, deployed and run for you.</h1>
      <p class="lead">Tell SkyMind how many people will use it, how fast it must answer and what you can spend. It plans the servers, deploys a chatbot on your documents, sends each question to the right model and keeps you inside your budget.</p>
      <div class="actions">
        <a class="btn primary" href="/deploy">Deploy your AI helper</a>
        <a class="btn" href="/admin">Open the admin console</a>
      </div>
      <div class="stats" aria-live="polite">
        <div><b id="s_bots" class="num">-</b><span>bots running</span></div>
        <div><b id="s_requests" class="num">-</b><span>questions answered</span></div>
        <div><b id="s_saved" class="num">-</b><span>saved by routing</span></div>
      </div>
    </div>
    <figure class="route" style="margin:0">
""" + ROUTE_SVG + r"""
      <figcaption>Most questions take the low, cheap route. Hard ones climb to the strong model. When a bot's monthly budget runs out, everything stays low.</figcaption>
    </figure>
  </section>

  <section class="section">
    <h2>One platform, three views</h2>
    <p class="sub">Two pages for customers, one for the team that runs them.</p>
    <div class="views">
      <div class="view">
        <div class="who">Companies<span>/deploy</span></div>
        <p>Describe your users, speed target, memory and budget. Add your documents. See the plan update as you type, then deploy.</p>
        <a class="btn primary" href="/deploy">Deploy a bot</a>
      </div>
      <div class="view">
        <div class="who">Their users<span>/chat</span></div>
        <div>
          <p>Chat with an assistant that answers only from that company's documents.</p>
          <div class="botlinks" id="botlist"><span class="sub small">Loading bots...</span></div>
        </div>
        <span></span>
      </div>
      <div class="view">
        <div class="who">SkyMind team<span>/admin</span></div>
        <p>Watch every customer bot live: traffic, latency, spend against plan, money saved by routing and budget alerts.</p>
        <a class="btn" href="/admin">Open admin</a>
      </div>
    </div>
  </section>

  <section class="section">
    <h2>What happens to every question</h2>
    <ol class="steps">
      <li><h3>Find</h3><p>Pull the three document sections that best match the question.</p></li>
      <li><h3>Route</h3><p>Short, simple questions go to the cheap model. Long, multi-part or "explain why" questions go to the strong one.</p></li>
      <li><h3>Guard</h3><p>If the bot has used its monthly model budget, the strong model is paused.</p></li>
      <li><h3>Answer</h3><p>Reply from the documents only. If the answer is not there, say so.</p></li>
      <li><h3>Remember</h3><p>Keep the last ten exchanges of each conversation, separately for every bot.</p></li>
      <li><h3>Record</h3><p>Log latency, tokens, cost and what an always-strong setup would have cost.</p></li>
    </ol>
  </section>
</main>
""" + FOOTER

LANDING_JS = r"""
if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  document.querySelectorAll(".pulses").forEach(function (g) { g.remove(); });
}
function money(x) {
  x = Number(x) || 0;
  if (x === 0) return "$0";
  if (x < 0.01) return "<$0.01";
  return "$" + x.toLocaleString(undefined, { maximumFractionDigits: 2 });
}
async function loadBots() {
  var box = document.getElementById("botlist");
  try {
    var res = await fetch("/bots");
    var bots = await res.json();
    box.replaceChildren();
    if (!bots.length) {
      var s = document.createElement("span");
      s.className = "sub small";
      s.textContent = "No bots yet. Deploy one and it appears here.";
      box.append(s);
      return;
    }
    bots.forEach(function (b) {
      var a = document.createElement("a");
      a.href = "/chat/" + encodeURIComponent(b.id);
      var chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = b.name + ", " + b.company;
      a.append(chip);
      box.append(a);
    });
  } catch (e) { box.textContent = "Could not load bots."; }
}
async function loadStats() {
  try {
    var res = await fetch("/stats");
    var f = await res.json();
    document.getElementById("s_bots").textContent = f.bots;
    document.getElementById("s_requests").textContent = Number(f.requests).toLocaleString();
    document.getElementById("s_saved").textContent = f.requests ? f.saved_percent + "%" : "-";
  } catch (e) {}
}
loadBots();
loadStats();
"""

LANDING_HTML = _shell("SkyMind: AI helpers, deployed and managed", LANDING_BODY, LANDING_JS, LANDING_CSS)


# ------------------------------------------------------------------ deploy (page 1: companies)

DEPLOY_CSS = r"""
.page-head { padding: 36px 0 22px; }
.page-head h1 { font-size: clamp(30px, 3.6vw, 42px); }
.samples { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 18px; }
.samples .sub { margin-right: 4px; }
.samples button { padding: 7px 14px; font-size: 14px; border-radius: 999px; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 24px; align-items: start; }
.step-title { display: flex; gap: 12px; align-items: baseline; }
.step-title b { display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; background: var(--zenith-soft); color: var(--zenith); font-size: 13px; flex: none; }
.row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0 16px; }
.hint { font-size: 12.5px; color: var(--muted); margin-top: 6px; }
.deploybar { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; margin-top: 16px; }
#error { font-size: 14px; }

.plan { position: sticky; top: 16px; }
.plan h2 { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.plan .figure { padding: 16px 0; border-bottom: 1px solid var(--line); }
.plan .figure:last-of-type { border-bottom: 0; }
.plan .big { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.plan .k { font-size: 13px; color: var(--muted); }
.plan .bar { margin-top: 10px; }
.breakdown { width: 100%; font-size: 13.5px; margin-top: 10px; }
.breakdown td { padding: 4px 0; border: 0; }
.breakdown td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
.plan-note { font-size: 12.5px; color: var(--muted); margin-top: 8px; }
.plan.stale .big { opacity: 0.5; }

.success { border-color: var(--good); background: linear-gradient(var(--good-soft), var(--good-soft)) padding-box; }
.success h2 { color: var(--good); }
.linkbox { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.linkbox input { flex: 1 1 260px; font-size: 14px; background: var(--surface); }
.notes { margin: 12px 0 0; padding-left: 18px; color: var(--muted); font-size: 14px; }
.notes li { margin: 4px 0; }

.botrow { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid var(--line); flex-wrap: wrap; }
.botrow:first-child { border-top: 0; }
.botrow .sub { font-size: 13px; }

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .plan { position: static; }
}
"""

DEPLOY_BODY = _header("deploy") + r"""
<main class="wrap">
  <div class="page-head">
    <h1>Deploy your AI helper</h1>
    <p class="lead">Describe what you need. The plan on the right updates as you type, so you see servers, speed and monthly cost before you deploy.</p>
    <div class="samples" id="examples"><span class="sub small">Loading samples...</span></div>
  </div>

  <div class="layout">
    <div>
      <section class="panel" aria-labelledby="needs-title">
        <h2 class="step-title" id="needs-title"><b>1</b>What do you need?</h2>
        <div class="row">
          <div><label for="bot_name">Bot name</label><input id="bot_name" placeholder="Acme Support" maxlength="60"></div>
          <div><label for="company">Company</label><input id="company" placeholder="Acme Outdoor Gear" maxlength="80"></div>
        </div>
        <div class="row">
          <div><label for="users">People chatting at the same time</label><input id="users" type="number" min="1" value="100" inputmode="numeric"></div>
          <div><label for="latency">Answer within (p95)</label><input id="latency" value="4s"><div class="hint">95% of answers faster than this, e.g. 4s</div></div>
          <div><label for="budget">Monthly budget</label><input id="budget" value="$150"></div>
        </div>
        <div class="row">
          <div><label for="memory">Conversation memory</label>
            <select id="memory">
              <option value="window">Recent messages</option>
              <option value="none">None</option>
              <option value="summary">Summary (planned)</option>
              <option value="long_term">Long-term (planned)</option>
              <option value="summary + long_term">Summary and long-term (planned)</option>
            </select></div>
          <div><label for="model">Model routing</label>
            <select id="model">
              <option value="auto">Auto: cheap for easy, strong for hard</option>
              <option value="cheap">Always the cheap model</option>
              <option value="strong">Always the strong model</option>
            </select></div>
        </div>
      </section>

      <section class="panel" aria-labelledby="docs-title">
        <h2 class="step-title" id="docs-title"><b>2</b>What should it know?</h2>
        <p class="sub" style="margin:0">Paste FAQs, policies or product info, or upload a text file. Lines starting with # or ## become section titles.</p>
        <label for="file">Upload a .txt, .md or .csv file</label>
        <input id="file" type="file" accept=".txt,.md,.markdown,.csv">
        <label for="knowledge">Documents <span id="count" class="sub">0 characters</span></label>
        <textarea id="knowledge" placeholder="## Returns&#10;Items can be returned within 30 days of delivery..."></textarea>
        <div class="deploybar">
          <button id="deploy" class="primary" type="button">Deploy bot</button>
          <span id="error" class="bad" role="alert"></span>
        </div>
      </section>

      <section class="panel success" id="result" hidden aria-live="polite">
        <h2>Your bot is live</h2>
        <p class="sub" style="margin:0" id="r_summary"></p>
        <div class="linkbox">
          <input id="chaturl" readonly aria-label="Chat link to share">
          <button id="copy" type="button">Copy link</button>
          <a id="openchat" class="btn primary" href="#" target="_blank" rel="noopener">Open chat</a>
        </div>
        <ul class="notes" id="r_notes"></ul>
      </section>

    </div>

    <aside class="panel plan" id="plan" aria-live="polite" aria-labelledby="plan-title">
      <h2 id="plan-title">Your plan <span class="chip" id="p_state">estimate</span></h2>
      <div class="figure">
        <div class="k">Monthly cost</div>
        <div class="big num" id="p_cost">-</div>
        <div class="bar" aria-hidden="true"><span id="p_costbar" class="ok" style="width:0"></span></div>
        <div class="small" id="p_budget" style="margin-top:6px">&nbsp;</div>
        <table class="breakdown"><tbody id="p_breakdown"></tbody></table>
      </div>
      <div class="figure">
        <div class="k">Servers</div>
        <div class="big num" id="p_replicas">-</div>
        <div class="small sub" id="p_load">&nbsp;</div>
      </div>
      <div class="figure">
        <div class="k">Expected answer time (p95)</div>
        <div class="big num" id="p_p95">-</div>
        <div class="small" id="p_p95_hint">&nbsp;</div>
      </div>
      <div class="figure">
        <div class="k">Questions routed to the strong model</div>
        <div class="bar" aria-hidden="true" style="margin-top:8px"><span class="sky" id="p_cheapbar" style="width:80%"></span><span class="zenith" id="p_strongbar" style="width:20%"></span></div>
        <div class="small sub" id="p_mix" style="margin-top:6px">&nbsp;</div>
      </div>
      <div class="plan-note">Estimates use placeholder prices and traffic assumptions until calibrated with load tests.</div>
    </aside>
  </div>

  <section class="panel" style="margin-top:16px">
    <h2>Deployed bots</h2>
    <div id="bots"><span class="sub">Loading...</span></div>
  </section>
</main>
""" + FOOTER

DEPLOY_JS = r"""
var $ = function (id) { return document.getElementById(id); };
var examples = [];
var planTimer = null;
var planSeq = 0;

function money(x) {
  return "$" + Number(x).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function updateCount() {
  $("count").textContent = $("knowledge").value.length.toLocaleString() + " characters";
}
function spec() {
  return {
    expected_concurrent_users: Number($("users").value),
    latency_target_p95: $("latency").value,
    memory: $("memory").value,
    model: $("model").value,
    monthly_budget: $("budget").value
  };
}
function fill(ex) {
  $("bot_name").value = ex.bot_name;
  $("company").value = ex.company;
  $("users").value = ex.expected_concurrent_users;
  $("latency").value = ex.latency_target_p95;
  $("memory").value = ex.memory;
  $("model").value = ex.model;
  $("budget").value = ex.monthly_budget;
  $("knowledge").value = ex.knowledge;
  updateCount();
  schedulePlan(0);
}

function renderPlan(p) {
  var budget = p.spec.budget;
  var total = p.cost.total;
  $("p_cost").textContent = money(total);
  var ratio = budget > 0 ? total / budget : 1;
  var bar = $("p_costbar");
  bar.style.width = Math.min(100, Math.round(ratio * 100)) + "%";
  bar.className = ratio > 1 ? "over" : (ratio > 0.85 ? "near" : "ok");
  if (p.within_budget) {
    $("p_budget").textContent = "Within your " + money(budget) + " budget (" + Math.round(ratio * 100) + "% used)";
    $("p_budget").className = "small good";
  } else {
    var tip = p.max_users_in_budget ? " Fits about " + p.max_users_in_budget.toLocaleString() + " users." : "";
    $("p_budget").textContent = "Over your " + money(budget) + " budget." + tip;
    $("p_budget").className = "small bad";
  }
  var rows = [["Servers", p.cost.replicas], ["Memory store (Redis)", p.cost.redis]];
  if (p.cost.pgvector) rows.push(["Long-term memory store", p.cost.pgvector]);
  rows.push(["Model usage", p.cost.llm]);
  var tb = $("p_breakdown");
  tb.replaceChildren();
  rows.forEach(function (r) {
    var tr = document.createElement("tr");
    var a = document.createElement("td"); a.className = "sub"; a.textContent = r[0];
    var b = document.createElement("td"); b.textContent = money(r[1]);
    tr.append(a, b);
    tb.append(tr);
  });
  $("p_replicas").textContent = p.replicas;
  $("p_load").textContent = "About " + p.peak_rps.toFixed(1) + " questions per second at peak";
  $("p_p95").textContent = p.p95_estimate_s.toFixed(2) + " s";
  $("p_p95_hint").textContent = p.latency_ok ? "Meets your " + p.spec.latency_target_s + " s target" : "Slower than your " + p.spec.latency_target_s + " s target";
  $("p_p95_hint").className = "small " + (p.latency_ok ? "good" : "warn");
  var strong = Math.round(p.strong_share * 100);
  $("p_cheapbar").style.width = (100 - strong) + "%";
  $("p_strongbar").style.width = strong + "%";
  $("p_mix").textContent = strong + "% strong, " + (100 - strong) + "% cheap";
  $("plan").classList.remove("stale");
  $("p_state").textContent = "estimate";
}

function schedulePlan(delay) {
  clearTimeout(planTimer);
  $("plan").classList.add("stale");
  planTimer = setTimeout(refreshPlan, delay === undefined ? 350 : delay);
}
async function refreshPlan() {
  var seq = ++planSeq;
  try {
    var res = await fetch("/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spec())
    });
    var data = await res.json();
    if (seq !== planSeq) return;
    if (!res.ok) {
      $("p_state").textContent = "check the fields";
      $("p_budget").textContent = typeof data.detail === "string" ? data.detail : "Some fields are not valid yet.";
      $("p_budget").className = "small warn";
      return;
    }
    renderPlan(data);
  } catch (e) {
    if (seq === planSeq) { $("p_state").textContent = "offline"; }
  }
}

async function loadExamples() {
  var box = $("examples");
  try {
    var res = await fetch("/examples");
    examples = await res.json();
    box.replaceChildren();
    var s = document.createElement("span");
    s.className = "sub small";
    s.textContent = "Try a sample customer:";
    box.append(s);
    examples.forEach(function (ex) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = ex.bot_name;
      b.title = ex.company;
      b.onclick = function () { fill(ex); };
      box.append(b);
    });
  } catch (e) { box.textContent = "Could not load samples."; }
}

async function refreshBots() {
  var box = $("bots");
  try {
    var res = await fetch("/bots");
    var bots = await res.json();
    box.replaceChildren();
    if (!bots.length) { box.textContent = "No bots deployed yet. Fill in the form and press Deploy bot."; return; }
    bots.forEach(function (b) {
      var row = document.createElement("div");
      row.className = "botrow";
      var left = document.createElement("div");
      var name = document.createElement("b");
      name.textContent = b.name;
      var sub = document.createElement("div");
      sub.className = "sub";
      sub.textContent = b.company + "  /chat/" + b.id;
      left.append(name, sub);
      var a = document.createElement("a");
      a.className = "btn";
      a.href = "/chat/" + encodeURIComponent(b.id);
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = "Open chat";
      row.append(left, a);
      box.append(row);
    });
  } catch (e) { box.textContent = "Could not load bots."; }
}

function showResult(data) {
  renderPlan(data.plan);
  $("p_state").textContent = "deployed";
  $("r_summary").textContent = data.name + " is answering from " + data.chunks + " document sections. Share this link with your users.";
  var list = $("r_notes");
  list.replaceChildren();
  data.notes.forEach(function (n) {
    var li = document.createElement("li");
    li.textContent = n;
    list.append(li);
  });
  $("openchat").href = data.chat_url;
  $("chaturl").value = location.origin + data.chat_url;
  $("result").hidden = false;
  $("result").scrollIntoView({ behavior: "smooth", block: "center" });
}

["users", "latency", "budget"].forEach(function (id) { $(id).addEventListener("input", function () { schedulePlan(); }); });
["memory", "model"].forEach(function (id) { $(id).addEventListener("change", function () { schedulePlan(0); }); });
$("knowledge").oninput = updateCount;
$("file").onchange = function () {
  var f = $("file").files[0];
  if (!f) return;
  if (f.size > 400000) { $("error").textContent = "That file is too large. Keep documents under about 200,000 characters."; return; }
  var reader = new FileReader();
  reader.onload = function () { $("knowledge").value = reader.result; updateCount(); };
  reader.readAsText(f);
};
$("copy").onclick = async function () {
  try { await navigator.clipboard.writeText($("chaturl").value); $("copy").textContent = "Copied"; }
  catch (e) { $("chaturl").select(); $("copy").textContent = "Press Ctrl+C"; }
  setTimeout(function () { $("copy").textContent = "Copy link"; }, 1800);
};

$("deploy").onclick = async function () {
  $("error").textContent = "";
  if (!$("bot_name").value.trim()) { $("error").textContent = "Give your bot a name."; $("bot_name").focus(); return; }
  if (!$("knowledge").value.trim()) { $("error").textContent = "Add some documents so the bot has something to answer from."; $("knowledge").focus(); return; }
  $("result").hidden = true;
  var body = spec();
  body.bot_name = $("bot_name").value;
  body.company = $("company").value;
  body.knowledge = $("knowledge").value;
  $("deploy").disabled = true;
  $("deploy").textContent = "Deploying...";
  try {
    var res = await fetch("/bots", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    var data = await res.json();
    if (!res.ok) {
      $("error").textContent = typeof data.detail === "string" ? data.detail : "Check the fields: users must be a number above 0 and documents can't be empty.";
    } else {
      showResult(data);
      refreshBots();
    }
  } catch (e) {
    $("error").textContent = "Could not reach the SkyMind server. Is docker compose up still running?";
  }
  $("deploy").disabled = false;
  $("deploy").textContent = "Deploy bot";
};

loadExamples();
refreshBots();
schedulePlan(0);
"""

DEPLOY_HTML = _shell("Deploy your AI helper | SkyMind", DEPLOY_BODY, DEPLOY_JS, DEPLOY_CSS)


# ------------------------------------------------------------------ chat (page 2: end users)

CHAT_CSS = r"""
html, body { height: 100%; }
body { background: var(--bg); }
.chat { display: flex; flex-direction: column; height: 100%; max-width: 780px; margin: 0 auto; }
.top { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-bottom: 1px solid var(--line); background: var(--surface); }
.avatar { width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center; font-weight: 700; font-size: 18px; color: #fff; background: linear-gradient(160deg, #3A2BA8, #1E9BD7); flex: none; }
.top .grow { flex: 1; min-width: 0; }
.top .name { font-weight: 700; font-size: 17px; line-height: 1.2; }
.top .company { color: var(--muted); font-size: 13.5px; }
.top .status { display: inline-flex; align-items: center; gap: 6px; }
.top .status i { width: 8px; height: 8px; border-radius: 50%; background: var(--good); }
.top button { padding: 8px 14px; font-size: 14px; }
.log { flex: 1; overflow-y: auto; padding: 20px; scroll-behavior: smooth; }
.msg { display: flex; margin: 0 0 14px; }
.msg.user { justify-content: flex-end; }
.bubble { max-width: min(82%, 600px); padding: 11px 15px; border-radius: 18px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 15px; }
.msg.user .bubble { background: var(--zenith); color: var(--on-zenith); border-bottom-right-radius: 6px; }
.msg.bot .bubble { background: var(--surface); border: 1px solid var(--line); border-bottom-left-radius: 6px; }
.meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; white-space: normal; }
.meta .chip { font-size: 12px; padding: 2px 9px; }
.typing { display: inline-flex; gap: 5px; padding: 4px 2px; }
.typing i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: blink 1.2s infinite ease-in-out; }
.typing i:nth-child(2) { animation-delay: 0.15s; }
.typing i:nth-child(3) { animation-delay: 0.3s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }
.composer { padding: 12px 20px 8px; border-top: 1px solid var(--line); background: var(--surface); }
.inputrow { display: flex; gap: 8px; }
.inputrow input { flex: 1; font-size: 15px; padding: 12px 14px; border-radius: 12px; }
.inputrow button { border-radius: 12px; padding: 0 20px; }
.powered { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; color: var(--muted); padding: 8px 0 4px; }
.powered .logo { width: 14px; height: 14px; }
.powered a { color: var(--muted); }
.tierkey { text-align: center; font-size: 12px; color: var(--muted); margin-top: 4px; }
"""

CHAT_BODY = r"""
<div class="chat">
  <header class="top">
    <div class="avatar" id="avatar" aria-hidden="true">?</div>
    <div class="grow">
      <div class="name" id="title">Assistant</div>
      <div class="company"><span class="status" id="status"><i></i><span id="sub">Connecting...</span></span></div>
    </div>
    <button id="newchat" type="button">New chat</button>
  </header>
  <div class="log" id="log" aria-live="polite"></div>
  <div class="composer">
    <form class="inputrow" id="form">
      <label for="msg" style="position:absolute;left:-9999px">Your question</label>
      <input id="msg" placeholder="Ask a question..." autocomplete="off" maxlength="4000">
      <button id="send" class="primary" type="submit">Send</button>
    </form>
    <div class="powered">""" + LOGO_SVG + r"""Powered by <a href="/" target="_blank" rel="noopener">SkyMind</a></div>
  </div>
</div>
"""

CHAT_JS = r"""
var $ = function (id) { return document.getElementById(id); };
var botId = decodeURIComponent(location.pathname.split("/").filter(Boolean).pop() || "");
var greeting = "Hello! How can I help?";
var busy = false;

function newSession() {
  var s = "s-" + Math.random().toString(36).slice(2, 10);
  try { sessionStorage.setItem("sm_" + botId, s); } catch (e) {}
  return s;
}
var session = null;
try { session = sessionStorage.getItem("sm_" + botId); } catch (e) {}
if (!session) { session = newSession(); }

function chip(text, cls) {
  var c = document.createElement("span");
  c.className = "chip" + (cls ? " " + cls : "");
  if (cls === "cheap" || cls === "strong") {
    var d = document.createElement("span");
    d.className = "dot";
    c.append(d);
  }
  c.append(document.createTextNode(text));
  return c;
}

function addMessage(text, who, data) {
  var row = document.createElement("div");
  row.className = "msg " + who;
  var b = document.createElement("div");
  b.className = "bubble";
  b.textContent = text;
  if (data) {
    var meta = document.createElement("div");
    meta.className = "meta";
    meta.append(chip(data.tier === "strong" ? "Strong model" : "Cheap model", data.tier));
    meta.append(chip(data.latency_ms < 1000 ? Math.round(data.latency_ms) + " ms" : (data.latency_ms / 1000).toFixed(1) + " s"));
    if (data.history_messages) { meta.append(chip("remembers " + data.history_messages + " messages")); }
    (data.sources || []).forEach(function (s) { meta.append(chip("Source: " + s)); });
    if (data.budget_guard) { meta.append(chip("Budget guard on")); }
    b.append(meta);
  }
  row.append(b);
  $("log").append(row);
  $("log").scrollTop = $("log").scrollHeight;
  return row;
}

function addTyping() {
  var row = document.createElement("div");
  row.className = "msg bot";
  var b = document.createElement("div");
  b.className = "bubble";
  b.setAttribute("aria-label", "Assistant is typing");
  var t = document.createElement("span");
  t.className = "typing";
  t.append(document.createElement("i"), document.createElement("i"), document.createElement("i"));
  b.append(t);
  row.append(b);
  $("log").append(row);
  $("log").scrollTop = $("log").scrollHeight;
  return row;
}

async function init() {
  try {
    var res = await fetch("/bots/" + encodeURIComponent(botId));
    if (!res.ok) {
      $("title").textContent = "Assistant not found";
      $("sub").textContent = "This chatbot does not exist or was removed.";
      $("status").querySelector("i").style.background = "var(--bad)";
      $("send").disabled = true;
      $("msg").disabled = true;
      return;
    }
    var bot = await res.json();
    document.title = bot.name + " | " + bot.company;
    $("title").textContent = bot.name;
    $("sub").textContent = bot.company;
    $("avatar").textContent = (bot.name || "?").trim().charAt(0).toUpperCase();
    greeting = bot.greeting;
    addMessage(greeting, "bot", null);
    $("msg").focus();
  } catch (e) {
    $("sub").textContent = "Could not reach the server.";
    $("status").querySelector("i").style.background = "var(--bad)";
  }
}

async function send() {
  var text = $("msg").value.trim();
  if (!text || busy) return;
  busy = true;
  $("msg").value = "";
  addMessage(text, "user", null);
  var wait = addTyping();
  $("send").disabled = true;
  try {
    var res = await fetch("/bots/" + encodeURIComponent(botId) + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: session, message: text })
    });
    var data = await res.json();
    wait.remove();
    if (!res.ok) {
      addMessage(typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.", "bot", null);
    } else {
      addMessage(data.reply, "bot", data);
    }
  } catch (e) {
    wait.remove();
    addMessage("Could not reach the server. Check your connection and try again.", "bot", null);
  }
  busy = false;
  $("send").disabled = false;
  $("msg").focus();
}

$("form").onsubmit = function (e) { e.preventDefault(); send(); };
$("newchat").onclick = function () {
  session = newSession();
  $("log").replaceChildren();
  addMessage(greeting, "bot", null);
  $("msg").focus();
};

init();
"""

CHAT_HTML = _shell("Chat | SkyMind", CHAT_BODY, CHAT_JS, CHAT_CSS)


# ------------------------------------------------------------------ admin (page 3: us)

ADMIN_CSS = r"""
.page-head { display: flex; justify-content: space-between; align-items: end; gap: 16px; flex-wrap: wrap; padding: 32px 0 20px; }
.page-head h1 { font-size: clamp(28px, 3.4vw, 38px); }
.fleet { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }
.fleet > div { padding: 20px 22px; border-left: 1px solid var(--line); }
.fleet > div:first-child { border-left: 0; }
.fleet .k { font-size: 13px; color: var(--muted); font-weight: 550; }
.fleet .v { font-size: 30px; font-weight: 700; letter-spacing: -0.02em; margin-top: 4px; font-variant-numeric: tabular-nums; line-height: 1.15; }
.fleet .h { font-size: 12.5px; color: var(--muted); margin-top: 2px; }
.fleet .saved .v { color: var(--good); }
.tablehead { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.legend { display: flex; gap: 8px; }
.botname { min-width: 180px; }
.botname b { display: block; }
.botname .sub { font-size: 12.5px; }
.mini { min-width: 110px; }
td.num { white-space: nowrap; }
.mini .bar { margin-top: 6px; }
.mini .small { color: var(--muted); }
td.rowactions { white-space: nowrap; text-align: right; }
td.rowactions a { font-weight: 600; font-size: 14px; }
.empty { padding: 28px 0; text-align: center; color: var(--muted); }
.signin { max-width: 560px; }
.tokenrow { display: flex; gap: 8px; }
.tokenrow input { flex: 1; }
@media (max-width: 900px) {
  .fleet { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fleet > div { border-left: 0; border-top: 1px solid var(--line); }
  .fleet > div:nth-child(-n+2) { border-top: 0; }
  .fleet > div:nth-child(even) { border-left: 1px solid var(--line); }
  .fleet > div:last-child { grid-column: 1 / -1; }
}
"""

ADMIN_BODY = _header("admin") + r"""
<main class="wrap">
  <div class="page-head">
    <div>
      <h1>Fleet overview</h1>
      <p class="sub" style="margin:6px 0 0">Every customer bot SkyMind is running, refreshed every 2 seconds.</p>
    </div>
    <div class="actions" style="margin:0">
      <span class="live" id="live"><i></i><span id="status">Connecting</span></span>
      <button id="reset" type="button">Reset counters</button>
      <button id="signout" type="button" class="quiet">Sign out</button>
    </div>
  </div>

  <form class="panel signin" id="signin" hidden>
    <h2>Sign in to the admin console</h2>
    <p class="sub" style="margin:0">Enter the admin token. It is printed in the server window as <b>SkyMind admin token: ...</b> when SkyMind starts, unless you set your own with ADMIN_TOKEN.</p>
    <label for="token">Admin token</label>
    <div class="tokenrow">
      <input id="token" type="password" autocomplete="current-password" required>
      <button class="primary" type="submit">Sign in</button>
    </div>
    <div id="signin_error" class="bad small" role="alert" style="margin-top:8px"></div>
  </form>

  <div id="console">
  <div class="fleet" aria-live="polite">
    <div><div class="k">Bots</div><div class="v" id="f_bots">0</div><div class="h" id="f_planned">planned $0 / month</div></div>
    <div><div class="k">Questions answered</div><div class="v" id="f_requests">0</div><div class="h" id="f_mix">&nbsp;</div></div>
    <div><div class="k">Answer time (p95)</div><div class="v" id="f_p95">0 ms</div><div class="h" id="f_avg">avg 0 ms</div></div>
    <div><div class="k">Model spend</div><div class="v" id="f_cost">$0</div><div class="h">this month, estimated</div></div>
    <div class="saved"><div class="k">Saved by routing</div><div class="v" id="f_saved">$0</div><div class="h" id="f_saved_pct">0% vs always strong</div></div>
  </div>

  <section class="panel" style="margin-top:16px">
    <div class="tablehead">
      <h2 style="margin:0">Customer bots</h2>
      <div class="legend"><span class="chip cheap"><span class="dot"></span>Cheap model</span><span class="chip strong"><span class="dot"></span>Strong model</span></div>
    </div>
    <div class="table-scroll">
      <table>
        <thead><tr>
          <th>Bot</th><th>Plan</th><th class="num">Questions</th><th class="num">Avg</th><th class="num">p95</th>
          <th>Routing mix</th><th>Budget used</th><th class="num">Saved</th><th>Status</th><th><span style="position:absolute;left:-9999px">Actions</span></th>
        </tr></thead>
        <tbody id="rows"><tr><td colspan="10" class="empty">Loading...</td></tr></tbody>
      </table>
    </div>
  </section>
  <p class="sub small" style="margin-top:14px">Costs use placeholder token prices from planner.py until calibrated. Admin actions need the admin token; customer accounts and logins are on the roadmap.</p>
  </div>
</main>
""" + FOOTER

ADMIN_JS = r"""
var $ = function (id) { return document.getElementById(id); };
var token = "";
try { token = sessionStorage.getItem("sm_admin") || ""; } catch (e) {}

function api(path, opts) {
  opts = opts || {};
  opts.headers = Object.assign({}, opts.headers || {}, { "X-Admin-Token": token });
  return fetch(path, opts).then(function (res) {
    if (res.status === 401) { showSignin("That token was not accepted."); throw new Error("unauthorized"); }
    return res;
  });
}
function showSignin(msg) {
  clearTimeout(timer);
  $("console").hidden = true;
  $("signin").hidden = false;
  $("signin_error").textContent = token ? (msg || "") : "";
  $("reset").hidden = true;
  $("signout").hidden = true;
  $("live").className = "live";
  $("status").textContent = "Signed out";
  $("token").focus();
}
function showConsole() {
  $("signin").hidden = true;
  $("console").hidden = false;
  $("reset").hidden = false;
  $("signout").hidden = false;
}

function money(x) {
  x = Number(x) || 0;
  if (!x) return "$0";
  if (Math.abs(x) < 0.01) return "$" + x.toFixed(4);
  return "$" + x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function ms(x) {
  x = Number(x) || 0;
  return x >= 1000 ? (x / 1000).toFixed(2) + " s" : x.toFixed(0) + " ms";
}
function cell(text, cls) {
  var td = document.createElement("td");
  td.textContent = text;
  if (cls) td.className = cls;
  return td;
}
function bar(parts) {
  var b = document.createElement("div");
  b.className = "bar";
  parts.forEach(function (p) {
    var s = document.createElement("span");
    s.className = p[0];
    s.style.width = Math.max(0, Math.min(100, p[1])) + "%";
    b.append(s);
  });
  return b;
}
function mini(caption, barEl) {
  var td = document.createElement("td");
  var d = document.createElement("div");
  d.className = "mini";
  var c = document.createElement("div");
  c.className = "small";
  c.textContent = caption;
  d.append(c, barEl);
  td.append(d);
  return td;
}

async function removeBot(id, name) {
  if (!confirm("Delete " + name + "? Its documents, memory and stats will be removed.")) return;
  try { await api("/bots/" + encodeURIComponent(id), { method: "DELETE" }); } catch (e) { return; }
  refresh(true);
}

var timer = null;
async function refresh(once) {
  clearTimeout(timer);
  try {
    var res = await api("/admin/overview");
    var data = await res.json();
    showConsole();
    var f = data.fleet;
    $("f_bots").textContent = f.bots;
    $("f_planned").textContent = "planned " + money(f.planned_monthly_total_usd) + " / month";
    $("f_requests").textContent = Number(f.requests).toLocaleString();
    $("f_p95").textContent = ms(f.latency.p95_ms);
    $("f_avg").textContent = "avg " + ms(f.latency.avg_ms);
    $("f_cost").textContent = money(f.actual_cost_usd);
    $("f_saved").textContent = money(f.saved_usd);
    $("f_saved_pct").textContent = f.saved_percent + "% vs always strong";

    var body = $("rows");
    body.replaceChildren();
    if (!data.bots.length) {
      var empty = document.createElement("tr");
      var c = document.createElement("td");
      c.colSpan = 10;
      c.className = "empty";
      var a = document.createElement("a");
      a.href = "/deploy";
      a.textContent = "Deploy the first bot";
      c.append(document.createTextNode("No bots yet. "), a);
      empty.append(c);
      body.append(empty);
    }
    data.bots.forEach(function (b) {
      var s = b.stats;
      var tr = document.createElement("tr");

      var name = document.createElement("td");
      name.className = "botname";
      var strong = document.createElement("b");
      strong.textContent = b.name;
      var sub = document.createElement("div");
      sub.className = "sub";
      sub.textContent = b.company + ", " + b.spec.users + " users, " + b.spec.model + " routing";
      name.append(strong, sub);
      tr.append(name);

      var plan = document.createElement("td");
      plan.style.whiteSpace = "nowrap";
      var pb = document.createElement("b");
      pb.style.fontWeight = "500";
      pb.textContent = b.planned.replicas + " servers";
      var ps = document.createElement("div");
      ps.className = "sub";
      ps.textContent = money(b.planned.monthly_cost_usd) + " / month";
      plan.append(pb, ps);
      tr.append(plan);
      tr.append(cell(Number(s.requests).toLocaleString(), "num"));
      tr.append(cell(ms(s.latency.avg_ms), "num"));
      tr.append(cell(ms(s.latency.p95_ms), "num"));

      var cheap = s.requests ? s.cheap_share_percent : 0;
      var strongPct = s.requests ? 100 - cheap : 0;
      tr.append(mini(s.requests ? cheap + "% cheap" : "no traffic yet", bar([["sky", cheap], ["zenith", strongPct]])));

      var used = b.llm_budget_usd > 0 ? (s.actual_cost_usd / b.llm_budget_usd) * 100 : 100;
      var cls = used >= 100 ? "over" : (used >= 85 ? "near" : "ok");
      tr.append(mini(money(s.actual_cost_usd) + " / " + money(b.llm_budget_usd), bar([[cls, used]])));

      tr.append(cell(s.saved_percent + "%", "num good"));

      var status = document.createElement("td");
      var pill = document.createElement("span");
      if (b.budget_guard) { pill.textContent = "Budget guard on"; pill.className = "pill warn"; }
      else if (!b.planned.within_budget) { pill.textContent = "Plan over budget"; pill.className = "pill bad"; }
      else { pill.textContent = "Healthy"; pill.className = "pill good"; }
      status.append(pill);
      tr.append(status);

      var actions = document.createElement("td");
      actions.className = "rowactions";
      var open = document.createElement("a");
      open.href = "/chat/" + encodeURIComponent(b.id);
      open.textContent = "Open chat";
      open.target = "_blank";
      open.rel = "noopener";
      var del = document.createElement("button");
      del.type = "button";
      del.className = "quiet";
      del.textContent = "Delete";
      del.setAttribute("aria-label", "Delete " + b.name);
      del.onclick = function () { removeBot(b.id, b.name); };
      actions.append(open, del);
      tr.append(actions);
      body.append(tr);
    });

    var total = data.bots.reduce(function (n, b) { return n + (b.stats.requests || 0); }, 0);
    $("f_mix").textContent = total ? "across " + data.bots.length + " bots" : "no traffic yet";
    $("live").className = "live on";
    $("status").textContent = "Live";
  } catch (e) {
    if (e.message === "unauthorized") return;
    $("live").className = "live";
    $("status").textContent = "Disconnected, retrying";
  }
  timer = setTimeout(refresh, 2000);
}

$("reset").onclick = async function () {
  if (!confirm("Reset usage counters for every bot? Bots and their documents stay.")) return;
  try { await api("/admin/stats", { method: "DELETE" }); } catch (e) { return; }
  refresh(true);
};
$("signin").onsubmit = function (e) {
  e.preventDefault();
  token = $("token").value.trim();
  try { sessionStorage.setItem("sm_admin", token); } catch (err) {}
  $("token").value = "";
  refresh();
};
$("signout").onclick = function () {
  token = "";
  try { sessionStorage.removeItem("sm_admin"); } catch (err) {}
  showSignin("");
};

if (token) { refresh(); } else { showSignin(""); }
"""

ADMIN_HTML = _shell("Admin console | SkyMind", ADMIN_BODY, ADMIN_JS, ADMIN_CSS)
