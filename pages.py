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
.authbox { display: flex; align-items: center; gap: 8px; min-height: 36px; }
.authbox:empty { display: none; }
.userchip { display: inline-flex; align-items: center; gap: 8px; font-size: 13.5px; color: var(--muted); max-width: 260px; }
.userchip .av { width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 13px; color: #fff; background: linear-gradient(160deg, #3A2BA8, #1E9BD7); flex: none; }
.userchip .em { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.autherr { font-size: 12.5px; color: var(--bad); }

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
        + '</nav><div class="authbox" id="authbox"></div></div></header>'
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


AUTH_JS = r"""
// ---- Sign in with Google (shared by every page) ----
var SKY = { me: { google_enabled: false, user: null, is_admin: false }, googleReady: false };
function skyHeaders(extra) { return Object.assign({ "X-Requested-With": "SkyMind" }, extra || {}); }
function skyLoadGoogle(done) {
  if (window.google && google.accounts && google.accounts.id) { done(); return; }
  var s = document.createElement("script");
  s.src = "https://accounts.google.com/gsi/client";
  s.async = true;
  s.onload = done;
  document.head.append(s);
}
function skyRenderButton(el, text) {
  if (!el || !SKY.me.google_enabled) return;
  skyLoadGoogle(function () {
    if (!SKY.googleReady) {
      google.accounts.id.initialize({ client_id: SKY.me.google_client_id, callback: skyOnCredential, auto_select: false, cancel_on_tap_outside: true });
      SKY.googleReady = true;
    }
    el.replaceChildren();
    google.accounts.id.renderButton(el, { type: "standard", theme: "outline", size: "medium", shape: "pill", text: text || "signin_with" });
  });
}
async function skyOnCredential(resp) {
  try {
    var r = await fetch("/auth/google", { method: "POST", headers: skyHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ credential: resp.credential }) });
    if (!r.ok) {
      var d = {};
      try { d = await r.json(); } catch (e) {}
      skyAuthError(typeof d.detail === "string" ? d.detail : "Sign-in failed. Please try again.");
      return;
    }
    location.reload();
  } catch (e) { skyAuthError("Could not reach SkyMind to finish signing in."); }
}
function skyAuthError(msg) {
  var box = document.getElementById("authbox");
  if (!box) return;
  var s = document.createElement("span");
  s.className = "autherr";
  s.textContent = msg;
  box.append(s);
}
async function skySignOut() {
  try { await fetch("/auth/logout", { method: "POST", headers: skyHeaders() }); } catch (e) {}
  try { google.accounts.id.disableAutoSelect(); } catch (e) {}
  location.reload();
}
function skyRenderAuthBox() {
  var box = document.getElementById("authbox");
  if (!box) return;
  box.replaceChildren();
  if (!SKY.me.google_enabled) return;
  if (SKY.me.user) {
    var chip = document.createElement("span");
    chip.className = "userchip";
    chip.title = SKY.me.user.email;
    var av = document.createElement("span");
    av.className = "av";
    av.textContent = (SKY.me.user.name || SKY.me.user.email).trim().charAt(0).toUpperCase();
    var em = document.createElement("span");
    em.className = "em";
    em.textContent = SKY.me.user.email;
    chip.append(av, em);
    var out = document.createElement("button");
    out.type = "button";
    out.className = "quiet";
    out.textContent = "Sign out";
    out.onclick = skySignOut;
    box.append(chip, out);
  } else {
    var holder = document.createElement("div");
    box.append(holder);
    skyRenderButton(holder);
  }
}
var skyReady = (async function () {
  try { SKY.me = await (await fetch("/me")).json(); } catch (e) {}
  skyRenderAuthBox();
  return SKY.me;
})();
"""


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
      <p class="lead">Tell SkyMind what your bot should do (answer questions, review code or brainstorm ideas), who will use it and what you can spend. It plans the servers, deploys the bot on your documents, sends each request to the right model and keeps you inside your budget. When the bot can't answer, SkyMind finds the fix on your website.</p>
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
          <p>Chat with assistants that answer questions, review code or brainstorm, using only that company's documents and rules. Try the samples:</p>
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
      <li><h3>Answer</h3><p>Reply from the documents only. If the answer is not there, say so and log the question so the company can fix it.</p></li>
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
    var res = await fetch("/featured");
    var bots = await res.json();
    var mine = [];
    try { mine = JSON.parse(localStorage.getItem("sm_my_bots") || "[]"); } catch (e) {}
    var seen = {};
    bots.forEach(function (b) { seen[b.id] = true; });
    mine.forEach(function (b) { if (!seen[b.id]) { bots.push({ id: b.id, name: b.name + " (yours)", company: b.company }); } });
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

LANDING_HTML = _shell("SkyMind: AI helpers, deployed and managed", LANDING_BODY, AUTH_JS + LANDING_JS, LANDING_CSS)


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

.urlrow { display: flex; gap: 8px; }
.urlrow input { flex: 1; min-width: 0; }
.loginnote { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-top: 18px; border-color: var(--zenith); background: var(--zenith-soft); }
.accessedit { margin-top: 10px; padding: 14px; border: 1px solid var(--line); border-radius: 12px; background: var(--bg); width: 100%; }
.accessedit .row { gap: 0 12px; }
.botrow .meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.improve { margin-top: 10px; padding: 16px; border: 1px solid var(--line); border-radius: 12px; background: var(--bg); width: 100%; }
.improve h3 { font-size: 14px; margin: 14px 0 6px; }
.improve h3:first-child { margin-top: 0; }
.gap { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 7px 0; border-top: 1px solid var(--line); font-size: 14px; }
.gap:first-of-type { border-top: 0; }
.gap .n { color: var(--muted); font-size: 12.5px; white-space: nowrap; }
.badans { font-size: 13.5px; padding: 8px 0; border-top: 1px solid var(--line); }
.badans .q { font-weight: 600; }
.badans .a { color: var(--muted); margin-top: 2px; }
.improve textarea { min-height: 110px; }
.webset { display: grid; gap: 8px; margin: 0 0 14px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; background: var(--surface); }
.webset .check { display: flex; gap: 8px; align-items: center; font-weight: 600; font-size: 14px; }
.webset .check input { width: auto; }
.stdrow { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0 0 10px; }
.stdrow button { font-size: 13px; padding: 6px 12px; border-radius: 999px; }
.fixbox { margin: 14px 0 6px; padding: 14px; border-radius: 14px; border: 1px solid var(--zenith); background: var(--zenith-soft); }
.fixtitle { font-weight: 700; margin-bottom: 4px; }
.fixbox .urlrow { margin-top: 10px; }
.fixout { margin-top: 10px; display: grid; gap: 6px; }
.improve textarea.flash { box-shadow: 0 0 0 4px var(--zenith-soft); border-color: var(--zenith); transition: box-shadow .3s; }
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
    <div class="panel loginnote" id="loginNote" hidden>
      <div><b>Sign in with Google to deploy.</b> Your bots are saved to your account, so you can manage them from any device.</div>
      <div id="loginBtn"></div>
    </div>
  </div>

  <div class="layout">
    <div>
      <section class="panel" aria-labelledby="needs-title">
        <h2 class="step-title" id="needs-title"><b>1</b>What do you need?</h2>
        <div class="row">
          <div><label for="job">What should it do?</label>
            <select id="job">
              <option value="answer">Answer questions from your documents</option>
              <option value="code_review">Review code against your engineering rules</option>
              <option value="ideas">Brainstorm ideas that fit your company</option>
            </select>
            <div class="hint" id="job_hint">For customers or staff: FAQs, policies, products.</div></div>
        </div>
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
          <div><label for="provider">AI provider</label>
            <select id="provider"><option value="">Loading...</option></select>
            <div class="hint" id="provider_hint"></div></div>
          <div><label for="search">Search method</label>
            <select id="search">
              <option value="bm25">Words (BM25)</option>
              <option value="hybrid">Words + meaning (needs Gemini key)</option>
              <option value="keyword">Simple keywords</option>
            </select>
            <div class="hint" id="search_hint">Meaning search also finds answers phrased differently.</div></div>
          <div><label for="model">Model routing</label>
            <select id="model">
              <option value="auto">Auto: cheap for easy, strong for hard</option>
              <option value="cheap">Always the cheap model</option>
              <option value="strong">Always the strong model</option>
            </select></div>
        </div>
      </section>

      <section class="panel" aria-labelledby="access-title">
        <h2 class="step-title" id="access-title"><b>2</b>Who can use it?</h2>
        <div class="row">
          <div><label for="access_mode">Access</label>
            <select id="access_mode">
              <option value="public">Anyone with the link</option>
              <option value="google">Only people who sign in with Google</option>
            </select></div>
        </div>
        <div id="access_more" hidden>
          <div class="row">
            <div><label for="access_domains">Allowed email domains <span class="sub">(optional)</span></label><input id="access_domains" placeholder="unt.edu, my.unt.edu"></div>
            <div><label for="access_emails">Allowed people <span class="sub">(optional)</span></label><input id="access_emails" placeholder="dean@unt.edu, alex@gmail.com"></div>
          </div>
          <div class="hint">Leave both empty to let any Google account in. Fill either one to allow only those domains or people.</div>
        </div>
        <div class="hint" id="access_note"></div>
      </section>

      <section class="panel" aria-labelledby="docs-title">
        <h2 class="step-title" id="docs-title"><b>3</b>What should it know?</h2>
        <div class="row" id="webrow">
          <div><label for="web_mode">When the documents don't have the answer</label>
            <select id="web_mode">
              <option value="docs">Say so (documents only, strict)</option>
              <option value="site">Look it up on our website</option>
            </select>
            <div class="hint">Only your own site is searched, never the rest of the internet. Answers link their source pages.</div></div>
          <div id="website_box" hidden><label for="website">Your website</label>
            <input id="website" type="url" placeholder="https://www.yourcompany.com">
            <div class="hint">Its subdomains count too (unt.edu covers dining.unt.edu).</div></div>
        </div>
        <div class="stdrow" id="stdrow" hidden><span class="sub small">Start from a standard:</span></div>
        <p class="sub" id="docs-intro" style="margin:0">Paste FAQs, policies or product info, upload files, or import web pages. Each adds to the documents below. Lines starting with # or ## become section titles.</p>
        <div class="row">
          <div><label for="file">Upload PDF, Word, text or CSV files</label>
            <input id="file" type="file" multiple accept=".pdf,.docx,.txt,.md,.markdown,.csv"></div>
          <div><label for="url">Import a web page</label>
            <div class="urlrow"><input id="url" type="url" placeholder="https://www.example.com/faq"><button id="urlbtn" type="button">Import</button></div></div>
        </div>
        <div id="import_msg" class="small" role="status" style="margin-top:6px"></div>
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
    <h2>Your bots</h2>
    <p class="sub small" style="margin:0 0 4px" id="bots_note">Only your bots appear here. Other companies can't see them, and you can't see theirs.</p>
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
var providerInfo = {};
function spec() {
  return {
    provider: $("provider").value || undefined,
    expected_concurrent_users: Number($("users").value),
    latency_target_p95: $("latency").value,
    memory: $("memory").value,
    model: $("model").value,
    monthly_budget: $("budget").value,
    job: $("job").value
  };
}
var JOB_TEXT = {
  answer: ["For customers or staff: FAQs, policies, products.", "What should it know?",
           "Paste FAQs, policies or product info, upload files, or import web pages. Each adds to the documents below. Lines starting with # or ## become section titles.",
           "## Returns\nItems can be returned within 30 days of delivery..."],
  code_review: ["Your developers paste code; the bot reviews it against your rules and cites them. Always uses the strong model.",
                "What are your engineering rules?",
                "Paste your coding standards, security rules and review checklist, or upload them. Each ## heading becomes a rule the review can cite.",
                "## Security rules\nNever write API keys in code; read them from environment variables..."],
  ideas: ["Your team describes a goal; the bot brainstorms ideas that fit your products, customers and limits. Always uses the strong model.",
          "What should it know about your company?",
          "Paste what you sell, who your customers are, your goals and your limits. Ideas will cite these sections.",
          "## Goals for 2027\nGrow repeat customers by 20%..."]
};
function applyJob() {
  var job = $("job").value, t = JOB_TEXT[job];
  $("job_hint").textContent = t[0];
  $("docs-title").lastChild.textContent = t[1];
  $("docs-intro").textContent = t[2];
  $("knowledge").placeholder = t[3];
  if (job !== "answer") { $("model").value = "strong"; }
  $("model").disabled = job !== "answer";
  $("stdrow").hidden = job !== "code_review";
  $("webrow").hidden = job !== "answer";
}
$("web_mode").addEventListener("change", function () {
  $("website_box").hidden = $("web_mode").value !== "site";
  if (!$("website_box").hidden) $("website").focus();
});
// Ready-made coding standards (OWASP Top 10, PEP 8, clean code) for code reviewers: one click adds them.
(async function loadStandards() {
  try {
    var list = await (await fetch("/standards")).json();
    list.forEach(function (st) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = "+ " + st.label;
      b.title = st.description;
      b.onclick = function () {
        var ta = $("knowledge");
        var first = st.text.split("\n")[0];
        if (ta.value.indexOf(first) >= 0) { $("import_msg").className = "small"; $("import_msg").textContent = st.label + " is already in your rules."; return; }
        ta.value = (ta.value.trim() ? ta.value.trim() + "\n\n" : "") + st.text;
        updateCount();
        schedulePlan(0);
        $("import_msg").className = "small good";
        $("import_msg").textContent = "Added " + st.label + ". Add your own rules too: the reviewer cites both, and yours win when they disagree.";
      };
      $("stdrow").append(b);
    });
  } catch (e) {}
})();
$("job").addEventListener("change", function () { applyJob(); schedulePlan(0); });
function fill(ex) {
  $("bot_name").value = ex.bot_name;
  $("company").value = ex.company;
  $("users").value = ex.expected_concurrent_users;
  $("latency").value = ex.latency_target_p95;
  $("memory").value = ex.memory;
  $("model").value = ex.model;
  $("budget").value = ex.monthly_budget;
  $("knowledge").value = ex.knowledge;
  $("job").value = ex.job || "answer";
  applyJob();
  $("web_mode").value = ex.web_lookup && ex.website ? "site" : "docs";
  $("website").value = ex.website || "";
  $("website_box").hidden = $("web_mode").value !== "site";
  if (ex.provider) { $("provider").value = ex.provider; }
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
      headers: skyHeaders({ "Content-Type": "application/json" }),
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

function providerHint() {
  var p = providerInfo[$("provider").value];
  if (!p) { $("provider_hint").textContent = ""; return; }
  var free = p.cheap_price[0] === 0 && p.strong_price[0] === 0;
  $("provider_hint").textContent = "Easy questions: " + p.cheap_model + ". Hard: " + p.strong_model + "." +
    (free ? " No per-answer cost." : " $" + p.cheap_price[0] + " / $" + p.strong_price[0] + " per million input tokens.");
}
async function loadProviders() {
  try {
    var d = await (await fetch("/providers")).json();
    var sel = $("provider");
    sel.replaceChildren();
    d.providers.forEach(function (p) {
      providerInfo[p.name] = p;
      var o = document.createElement("option");
      o.value = p.name;
      o.textContent = p.label + (p.available ? "" : " (not set up)");
      o.disabled = !p.available;
      sel.append(o);
    });
    sel.value = d.default;
    var hy = $("search").querySelector('option[value="hybrid"]');
    hy.disabled = !d.embeddings;
    if (!d.embeddings) { $("search_hint").textContent = "Meaning search needs GEMINI_API_KEY on the server."; }
    $("search").value = d.embeddings && d.default_search === "hybrid" ? "hybrid" : (d.default_search === "keyword" ? "keyword" : "bm25");
    providerHint();
    schedulePlan(0);
  } catch (e) { $("provider_hint").textContent = "Could not load providers."; }
}
$("provider").addEventListener("change", function () { providerHint(); schedulePlan(0); });

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

function myBots() {
  try { return JSON.parse(localStorage.getItem("sm_my_bots") || "[]"); } catch (e) { return []; }
}
function saveMyBots(list) {
  try { localStorage.setItem("sm_my_bots", JSON.stringify(list)); } catch (e) {}
}
function ownerHeaders(bot, extra) {
  var h = skyHeaders(extra);
  if (bot.key) h["X-Owner-Key"] = bot.key;
  return h;
}
function accessLabel(a) {
  a = a || { mode: "public" };
  if (a.mode !== "google") return "Public link";
  var parts = (a.allowed_domains || []).map(function (d) { return "@" + d; });
  if ((a.allowed_emails || []).length) parts.push(a.allowed_emails.length + " invited");
  return "Google sign-in" + (parts.length ? ": " + parts.join(", ") : "");
}
function readAccess(prefix) {
  return {
    mode: $(prefix + "mode").value,
    allowed_domains: $(prefix + "domains").value,
    allowed_emails: $(prefix + "emails").value
  };
}

async function deleteMine(bot) {
  if (!confirm("Delete " + bot.name + "? Its documents, memory and stats will be removed.")) return;
  try {
    var res = await fetch("/bots/" + encodeURIComponent(bot.id), { method: "DELETE", headers: ownerHeaders(bot) });
    if (res.ok || res.status === 404) { saveMyBots(myBots().filter(function (b) { return b.id !== bot.id; })); }
  } catch (e) {}
  refreshBots();
}

async function improvePanel(bot, row) {
  var old = row.querySelector(".improve");
  if (old) { old.remove(); return; }
  var box = document.createElement("div");
  box.className = "improve";
  box.textContent = "Loading...";
  row.append(box);
  var rep;
  try {
    var res = await fetch("/bots/" + encodeURIComponent(bot.id) + "/improve", { headers: ownerHeaders(bot) });
    rep = await res.json();
    if (!res.ok) { box.textContent = typeof rep.detail === "string" ? rep.detail : "Could not load."; return; }
  } catch (e) { box.textContent = "Could not reach the server."; return; }
  box.replaceChildren();
  function h(text) { var e = document.createElement("h3"); e.textContent = text; box.append(e); }
  function note(text) { var e = document.createElement("div"); e.className = "sub small"; e.textContent = text; box.append(e); }

  var lineByKey = {}, pendingFix = [];
  if (!rep.job || rep.job === "answer") {
    var wb = document.createElement("div");
    wb.className = "webset";
    var wl = document.createElement("label");
    wl.className = "check";
    var wc = document.createElement("input");
    wc.type = "checkbox";
    wc.checked = !!rep.web_lookup;
    wl.append(wc, document.createTextNode(" When the documents don't have the answer, look it up on"));
    var wu = document.createElement("input");
    wu.type = "url";
    wu.placeholder = "https://www.yourcompany.com";
    wu.value = rep.website || "";
    wu.setAttribute("aria-label", "Your website");
    var ws = document.createElement("button");
    ws.type = "button";
    ws.textContent = "Save";
    var wm = document.createElement("span");
    wm.className = "small";
    ws.onclick = async function () {
      wm.className = "small"; wm.textContent = "Saving...";
      try {
        var res = await fetch("/bots/" + encodeURIComponent(bot.id) + "/web", {
          method: "PATCH",
          headers: ownerHeaders(bot, { "Content-Type": "application/json" }),
          body: JSON.stringify({ website: wu.value.trim(), enabled: wc.checked })
        });
        var d = await res.json();
        if (!res.ok) { wm.className = "small bad"; wm.textContent = typeof d.detail === "string" ? d.detail : "Could not save."; return; }
        wm.className = "small good";
        wm.textContent = d.web_lookup ? "On: unanswered questions are looked up on your website." : "Off: documents only.";
      } catch (e) { wm.className = "small bad"; wm.textContent = "Could not reach the server."; }
    };
    var wrow = document.createElement("div");
    wrow.className = "urlrow";
    wrow.append(wu, ws);
    wb.append(wl, wrow, wm);
    box.append(wb);
  }
  h("Questions it couldn't answer (" + rep.gaps.length + ")");
  if (!rep.gaps.length) note(rep.job && rep.job !== "answer"
    ? "Reviews and idea sessions are not logged here. Use the ratings below to see what to improve."
    : "None yet. When a customer asks something your documents don't cover, it appears here.");
  rep.gaps.forEach(function (g) {
    var line = document.createElement("div");
    line.className = "gap";
    lineByKey[g.key] = line;
    var q = document.createElement("span");
    q.textContent = g.question;
    var right = document.createElement("span");
    right.style.display = "flex";
    right.style.gap = "8px";
    right.style.alignItems = "center";
    var n = document.createElement("span");
    n.className = "n";
    n.textContent = "asked " + g.count + (g.count === 1 ? " time" : " times");
    var fix = document.createElement("button");
    fix.type = "button";
    fix.className = "quiet";
    fix.textContent = "Mark fixed";
    fix.onclick = async function () {
      await fetch("/bots/" + encodeURIComponent(bot.id) + "/gaps?question=" + encodeURIComponent(g.key), { method: "DELETE", headers: ownerHeaders(bot) });
      line.remove();
    };
    var use = document.createElement("button");
    use.type = "button";
    use.className = "quiet";
    use.textContent = "Answer it";
    use.onclick = function () { ta.value += (ta.value ? "\n\n" : "") + "## " + g.question + "\n"; ta.focus(); };
    if (g.web_url && /^https?:\/\//i.test(g.web_url)) {
      var src = document.createElement("a");
      src.href = g.web_url; src.target = "_blank"; src.rel = "noopener noreferrer";
      src.className = "small";
      src.textContent = "answered from your website";
      src.title = g.web_url + " (add it to your documents to answer without a lookup)";
      right.prepend(src);
    }
    right.append(n, use, fix);
    line.append(q, right);
    box.append(line);
  });

  // Self-fixing: SkyMind reads the company's website and drafts the missing answers, with sources.
  if (rep.gaps.length) {
    var fixBox = document.createElement("div");
    fixBox.className = "fixbox";
    var ft = document.createElement("div");
    ft.className = "fixtitle";
    ft.textContent = "Let SkyMind fix it";
    var fn = document.createElement("div");
    fn.className = "sub small";
    fn.textContent = "Give your website. SkyMind reads it and the related pages it links to, finds the answers to these questions, and drafts new sections with sources. You check the draft before anything is added.";
    var fr = document.createElement("div");
    fr.className = "urlrow";
    var site = document.createElement("input");
    site.type = "url";
    site.placeholder = "https://www.yourcompany.com";
    site.value = rep.website || "";
    site.setAttribute("aria-label", "Your website");
    var go = document.createElement("button");
    go.type = "button";
    go.className = "primary";
    go.textContent = "Suggest fix";
    fr.append(site, go);
    var out = document.createElement("div");
    out.className = "fixout small";
    out.setAttribute("role", "status");
    fixBox.append(ft, fn, fr, out);
    box.append(fixBox);
    go.onclick = async function () {
      if (!/^https?:\/\//i.test(site.value.trim())) { out.className = "fixout small bad"; out.textContent = "Enter your website address, starting with https://"; return; }
      go.disabled = true;
      go.textContent = "Reading your website...";
      out.className = "fixout small";
      out.textContent = "Reading pages and looking for answers. This can take up to 30 seconds.";
      try {
        var res = await fetch("/bots/" + encodeURIComponent(bot.id) + "/suggest-fix", {
          method: "POST",
          headers: ownerHeaders(bot, { "Content-Type": "application/json" }),
          body: JSON.stringify({ url: site.value.trim() })
        });
        var d = await res.json();
        if (!res.ok) { out.className = "fixout small bad"; out.textContent = typeof d.detail === "string" ? d.detail : "Could not suggest a fix."; return; }
        out.replaceChildren();
        function line(label, items, cls) {
          if (!items.length) return;
          var p = document.createElement("div");
          if (cls) p.className = cls;
          var b = document.createElement("strong"); b.textContent = label + " ";
          p.append(b, document.createTextNode(items.join("; ")));
          out.append(p);
        }
        var pages = document.createElement("div");
        var pb = document.createElement("strong"); pb.textContent = "Read " + d.pages.length + (d.pages.length === 1 ? " page: " : " pages: ");
        pages.append(pb);
        d.pages.forEach(function (pg, i) {
          var a = document.createElement("a");
          a.href = pg.url; a.target = "_blank"; a.rel = "noopener noreferrer";
          a.textContent = pg.title || pg.url;
          pages.append(a);
          if (i < d.pages.length - 1) pages.append(document.createTextNode(", "));
        });
        out.append(pages);
        line("Found answers for:", d.found.map(function (f) { return f.question; }), "good");
        line("Not on these pages:", d.not_found, "warn");
        if (d.draft) {
          ta.value = (ta.value ? ta.value + "\n\n" : "") + d.draft;
          ta.style.minHeight = "280px";
          pendingFix = d.found.map(function (f) { return f.key; });
          var tip = document.createElement("div");
          tip.textContent = (d.used_ai ? "Drafted by " + d.model + " from these pages. " : "Matching passages from these pages. ") +
            "Check the draft in the box below, edit anything, then click Add to documents.";
          out.append(tip);
          ta.scrollIntoView({ behavior: "smooth", block: "center" });
          ta.classList.add("flash");
          setTimeout(function () { ta.classList.remove("flash"); }, 1600);
        } else {
          var none = document.createElement("div");
          none.textContent = "No answers found on those pages. Try a more specific page, like your FAQ or help page.";
          out.append(none);
        }
      } catch (e) { out.className = "fixout small bad"; out.textContent = "Could not reach the server."; }
      finally { go.disabled = false; go.textContent = "Suggest fix"; }
    };
  }

  var fb = rep.feedback;
  h("Answers rated not helpful (" + fb.not_helpful + " of " + (fb.helpful + fb.not_helpful) + " ratings)");
  if (!fb.recent_not_helpful.length) note("No not-helpful ratings yet.");
  fb.recent_not_helpful.forEach(function (x) {
    var d = document.createElement("div");
    d.className = "badans";
    var q = document.createElement("div"); q.className = "q"; q.textContent = x.question;
    var a = document.createElement("div"); a.className = "a"; a.textContent = x.answer.slice(0, 300);
    d.append(q, a);
    if (x.comment) { var cm = document.createElement("div"); cm.className = "a"; cm.textContent = "Comment: " + x.comment; d.append(cm); }
    box.append(d);
  });

  h("Add information");
  note("Write the missing answers, upload files or import web pages, then check the text below. Start each topic with ## and a title. Your bot uses it on the next question. Now: " + rep.sections.length + " sections, " + rep.characters.toLocaleString() + " of " + rep.max_characters.toLocaleString() + " characters.");
  var imp = document.createElement("div");
  imp.className = "row";
  imp.style.marginTop = "8px";
  var fileIn = document.createElement("input");
  fileIn.type = "file";
  fileIn.multiple = true;
  fileIn.accept = ".pdf,.docx,.txt,.md,.markdown,.csv";
  fileIn.setAttribute("aria-label", "Upload files to add");
  var urlWrap = document.createElement("div");
  urlWrap.className = "urlrow";
  var urlIn = document.createElement("input");
  urlIn.type = "url";
  urlIn.placeholder = "https://www.example.com/faq";
  urlIn.setAttribute("aria-label", "Web page to import");
  var urlBtn = document.createElement("button");
  urlBtn.type = "button";
  urlBtn.textContent = "Import";
  urlWrap.append(urlIn, urlBtn);
  imp.append(fileIn, urlWrap);
  var impMsg = document.createElement("div");
  impMsg.className = "small";
  box.append(imp, impMsg);
  fileIn.onchange = async function () { await importFiles(fileIn.files, ta, impMsg); fileIn.value = ""; };
  urlBtn.onclick = async function () { if (await importUrl(urlIn.value, ta, impMsg)) urlIn.value = ""; };
  var ta = document.createElement("textarea");
  ta.style.marginTop = "8px";
  ta.placeholder = "## Kayaks\nWe sell inflatable kayaks for $299.";
  ta.setAttribute("aria-label", "Information to add");
  var act = document.createElement("div");
  act.className = "actions";
  act.style.marginTop = "10px";
  var add = document.createElement("button");
  add.type = "button";
  add.className = "primary";
  add.textContent = "Add to documents";
  var msg = document.createElement("span");
  msg.className = "small";
  add.onclick = async function () {
    if (!ta.value.trim()) { msg.className = "small bad"; msg.textContent = "Write something to add first."; return; }
    try {
      var res = await fetch("/bots/" + encodeURIComponent(bot.id) + "/knowledge", {
        method: "POST",
        headers: ownerHeaders(bot, { "Content-Type": "application/json" }),
        body: JSON.stringify({ text: ta.value, mode: "append" })
      });
      var d = await res.json();
      if (!res.ok) { msg.className = "small bad"; msg.textContent = typeof d.detail === "string" ? d.detail : "Could not add."; return; }
      ta.value = "";
      var fixedNow = pendingFix.slice();
      pendingFix = [];
      for (var i = 0; i < fixedNow.length; i++) {
        try {
          await fetch("/bots/" + encodeURIComponent(bot.id) + "/gaps?question=" + encodeURIComponent(fixedNow[i]), { method: "DELETE", headers: ownerHeaders(bot) });
          if (lineByKey[fixedNow[i]]) lineByKey[fixedNow[i]].remove();
        } catch (e) {}
      }
      msg.className = "small good";
      msg.textContent = "Added " + d.added + (d.added === 1 ? " section" : " sections") + ". The bot now has " + d.sections + "." +
        (fixedNow.length ? " Marked " + fixedNow.length + " question" + (fixedNow.length === 1 ? "" : "s") + " fixed." : "") + " Ask it again to check.";
    } catch (e) { msg.className = "small bad"; msg.textContent = "Could not reach the server."; }
  };
  act.append(add, msg);
  box.append(ta, act);
}

function accessEditor(bot, row) {
  var old = row.querySelector(".accessedit");
  if (old) { old.remove(); return; }
  var a = bot.access || { mode: "public", allowed_domains: [], allowed_emails: [] };
  var box = document.createElement("div");
  box.className = "accessedit";
  var id = "ae_" + bot.id + "_";
  function field(labelText, el) {
    var w = document.createElement("div");
    var l = document.createElement("label");
    l.htmlFor = el.id;
    l.textContent = labelText;
    w.append(l, el);
    return w;
  }
  var sel = document.createElement("select");
  sel.id = id + "mode";
  [["public", "Anyone with the link"], ["google", "Only people who sign in with Google"]].forEach(function (o) {
    var op = document.createElement("option");
    op.value = o[0];
    op.textContent = o[1];
    if (!SKY.me.google_enabled && o[0] === "google") op.disabled = true;
    sel.append(op);
  });
  sel.value = a.mode;
  var dom = document.createElement("input");
  dom.id = id + "domains";
  dom.placeholder = "unt.edu";
  dom.value = (a.allowed_domains || []).join(", ");
  var em = document.createElement("input");
  em.id = id + "emails";
  em.placeholder = "dean@unt.edu";
  em.value = (a.allowed_emails || []).join(", ");
  var r1 = document.createElement("div");
  r1.className = "row";
  r1.append(field("Access", sel), field("Allowed email domains", dom), field("Allowed people", em));
  var save = document.createElement("button");
  save.type = "button";
  save.className = "primary";
  save.textContent = "Save access";
  var msg = document.createElement("span");
  msg.className = "small";
  save.onclick = async function () {
    msg.textContent = "";
    try {
      var res = await fetch("/bots/" + encodeURIComponent(bot.id) + "/access", {
        method: "PATCH",
        headers: ownerHeaders(bot, { "Content-Type": "application/json" }),
        body: JSON.stringify(readAccess(id))
      });
      var d = await res.json();
      if (!res.ok) { msg.className = "small bad"; msg.textContent = typeof d.detail === "string" ? d.detail : "Could not save."; return; }
      refreshBots();
    } catch (e) { msg.className = "small bad"; msg.textContent = "Could not reach the server."; }
  };
  var act = document.createElement("div");
  act.className = "actions";
  act.style.marginTop = "12px";
  act.append(save, msg);
  box.append(r1, act);
  row.append(box);
}

async function refreshBots() {
  await skyReady;
  var box = $("bots");
  var list = [];
  var seen = {};
  if (SKY.me.user) {
    $("bots_note").textContent = "Bots owned by " + SKY.me.user.email + ", plus any deployed from this browser. Other companies can't see them.";
    try {
      var res = await fetch("/my/bots");
      if (res.ok) {
        (await res.json()).forEach(function (b) { seen[b.id] = true; list.push(b); });
      }
    } catch (e) {}
  }
  var mine = myBots();
  var alive = [];
  for (var i = 0; i < mine.length; i++) {
    var b = mine[i];
    if (seen[b.id]) { alive.push(b); list.forEach(function (x) { if (x.id === b.id) x.key = b.key; }); continue; }
    try {
      var r = await fetch("/bots/" + encodeURIComponent(b.id) + "/usage", { headers: ownerHeaders(b) });
      if (r.status === 404) continue;  // removed, or wiped by a restart
      alive.push(b);
      if (r.ok) {
        var u = await r.json();
        list.push({ id: b.id, name: b.name, company: b.company, key: b.key, access: u.access, requests: u.requests, saved_percent: u.saved_percent, quality: u.quality });
      } else {
        list.push({ id: b.id, name: b.name, company: b.company, key: b.key });
      }
    } catch (e) { alive.push(b); }
  }
  if (alive.length !== mine.length) saveMyBots(alive);

  box.replaceChildren();
  if (!list.length) {
    box.textContent = "No bots yet. Fill in the form and press Deploy bot.";
    return;
  }
  list.forEach(function (bot) {
    var row = document.createElement("div");
    row.className = "botrow";
    var left = document.createElement("div");
    var name = document.createElement("b");
    name.textContent = bot.name;
    var sub = document.createElement("div");
    sub.className = "sub";
    sub.textContent = bot.company + "  /chat/" + bot.id + (bot.requests !== undefined ? "  |  " + bot.requests + " questions, " + bot.saved_percent + "% saved" : "");
    var meta = document.createElement("div");
    meta.className = "meta";
    var chipEl = document.createElement("span");
    chipEl.className = "chip" + (bot.access && bot.access.mode === "google" ? " strong" : "");
    chipEl.textContent = accessLabel(bot.access);
    meta.append(chipEl);
    if (bot.quality) {
      var q = bot.quality, rated = q.helpful + q.not_helpful;
      var qc = document.createElement("span");
      qc.className = "chip";
      qc.textContent = (rated ? Math.round(100 * q.helpful / rated) + "% helpful" : "no ratings yet") + ", " + q.gaps + " unanswered";
      meta.append(qc);
    }
    left.append(name, sub, meta);
    var right = document.createElement("div");
    right.style.display = "flex";
    right.style.gap = "8px";
    right.style.flexWrap = "wrap";
    var a = document.createElement("a");
    a.className = "btn";
    a.href = "/chat/" + encodeURIComponent(bot.id);
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "Open chat";
    var acc = document.createElement("button");
    acc.type = "button";
    acc.textContent = "Access";
    acc.onclick = function () { accessEditor(bot, row); };
    var imp = document.createElement("button");
    imp.type = "button";
    imp.textContent = "Improve";
    imp.onclick = function () { improvePanel(bot, row); };
    var del = document.createElement("button");
    del.type = "button";
    del.className = "quiet";
    del.textContent = "Delete";
    del.setAttribute("aria-label", "Delete " + bot.name);
    del.onclick = function () { deleteMine(bot); };
    right.append(a, imp, acc, del);
    row.append(left, right);
    box.append(row);
  });
}

function showResult(data) {
  var mine = myBots();
  mine.push({ id: data.bot_id, name: data.name, company: data.company, key: data.owner_key });
  saveMyBots(mine);
  renderPlan(data.plan);
  $("p_state").textContent = "deployed";
  $("r_summary").textContent = data.name + " is answering from " + data.chunks + " document sections. " + accessLabel(data.access) + ". " + (data.owner_email ? "Saved to " + data.owner_email + "." : "Only this browser can manage or delete it.");
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
// ---- importing files and web pages (shared by the deploy form and the Improve panel) ----
function appendText(ta, text) {
  ta.value = ta.value.trim() ? ta.value.replace(/\s+$/, "") + "\n\n" + text : text;
  if (ta === $("knowledge")) updateCount();
}
function showImport(el, ok, text) { el.className = "small " + (ok ? "good" : "bad"); el.textContent = text; }
async function importFiles(files, ta, msgEl) {
  for (var i = 0; i < files.length; i++) {
    var f = files[i];
    if (f.size > 5000000) { showImport(msgEl, false, f.name + " is larger than 5 MB."); continue; }
    showImport(msgEl, true, "Reading " + f.name + "...");
    try {
      var form = new FormData();
      form.append("file", f);
      var res = await fetch("/import/file", { method: "POST", headers: skyHeaders(), body: form });
      var d = await res.json();
      if (!res.ok) { showImport(msgEl, false, f.name + ": " + (typeof d.detail === "string" ? d.detail : "could not import.")); continue; }
      appendText(ta, d.text);
      showImport(msgEl, true, "Added " + f.name + " (" + d.characters.toLocaleString() + " characters" + (d.truncated ? ", shortened to fit" : "") + ").");
    } catch (e) { showImport(msgEl, false, "Could not reach the server."); }
  }
}
async function importUrl(url, ta, msgEl) {
  url = (url || "").trim();
  if (!url) { showImport(msgEl, false, "Paste a web address first."); return false; }
  showImport(msgEl, true, "Fetching " + url + "...");
  try {
    var res = await fetch("/import/url", { method: "POST", headers: skyHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ url: url }) });
    var d = await res.json();
    if (!res.ok) { showImport(msgEl, false, typeof d.detail === "string" ? d.detail : "Could not import that page."); return false; }
    appendText(ta, d.text);
    showImport(msgEl, true, "Added \u201c" + d.title + "\u201d (" + d.characters.toLocaleString() + " characters). Check the text before deploying.");
    return true;
  } catch (e) { showImport(msgEl, false, "Could not reach the server."); return false; }
}
$("file").onchange = async function () {
  await importFiles($("file").files, $("knowledge"), $("import_msg"));
  $("file").value = "";
};
$("urlbtn").onclick = async function () {
  if (await importUrl($("url").value, $("knowledge"), $("import_msg"))) $("url").value = "";
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
  body.access = readAccess("access_");
  body.search = $("search").value;
  body.bot_name = $("bot_name").value;
  body.company = $("company").value;
  body.knowledge = $("knowledge").value;
  if ($("job").value === "answer" && $("web_mode").value === "site") {
    if (!$("website").value.trim()) { $("error").textContent = "Add your website, or choose documents only."; $("website").focus(); return; }
    body.website = $("website").value.trim();
    body.web_lookup = true;
  }
  $("deploy").disabled = true;
  $("deploy").textContent = "Deploying...";
  try {
    var res = await fetch("/bots", {
      method: "POST",
      headers: skyHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body)
    });
    var data = await res.json();
    if (res.status === 401) { showLoginNote(); }
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

function showLoginNote() {
  $("loginNote").hidden = false;
  skyRenderButton($("loginBtn"), "continue_with");
}
$("access_mode").onchange = function () { $("access_more").hidden = $("access_mode").value !== "google"; };
skyReady.then(function (me) {
  if (!me.google_enabled) {
    $("access_mode").querySelector('option[value="google"]').disabled = true;
    $("access_note").textContent = "Google sign-in isn't set up on this server, so bots are public. Set GOOGLE_CLIENT_ID to turn it on.";
  }
  if (me.login_required_to_deploy && !me.user) showLoginNote();
});

loadProviders();
loadExamples();
refreshBots();
schedulePlan(0);
"""

DEPLOY_HTML = _shell("Deploy your AI helper | SkyMind", DEPLOY_BODY, AUTH_JS + DEPLOY_JS, DEPLOY_CSS)


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
.rate { display: flex; align-items: center; gap: 4px; margin-top: 8px; font-size: 12px; color: var(--muted); white-space: normal; }
.rate button { padding: 3px 8px; font-size: 12px; font-weight: 550; border-radius: 999px; background: transparent; color: var(--muted); gap: 4px; }
.rate button svg { width: 14px; height: 14px; }
.rate button:hover { color: var(--ink); border-color: var(--muted); }
.typing { display: inline-flex; gap: 5px; padding: 4px 2px; }
.typing i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: blink 1.2s infinite ease-in-out; }
.typing i:nth-child(2) { animation-delay: 0.15s; }
.typing i:nth-child(3) { animation-delay: 0.3s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.25; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-3px); } }
.composer { padding: 12px 20px 8px; border-top: 1px solid var(--line); background: var(--surface); }
.inputrow { display: flex; gap: 8px; }
.inputrow textarea { flex: 1; font-size: 15px; padding: 12px 14px; border-radius: 12px; min-height: 48px; max-height: 40vh; resize: none; overflow-y: auto; }
.inputrow textarea.code { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 13.5px; min-height: 150px; resize: vertical; }
.inputrow button { align-self: flex-end; min-height: 48px; }
.starters { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 10px; }
.starters button { font-size: 13px; padding: 6px 12px; border-radius: 999px; }
.hint { font-size: 12px; color: var(--muted); margin-top: 6px; }
.jobtag { display: inline-block; margin-left: 8px; font-size: 11.5px; font-weight: 650; padding: 2px 8px; border-radius: 999px; background: var(--zenith-soft); color: var(--zenith); vertical-align: 2px; }
.chat.wide .bubble { max-width: 100%; }
.bubble.streaming::after { content: ""; display: inline-block; width: 7px; height: 1.05em; margin-left: 2px; vertical-align: -2px; background: var(--zenith); animation: caret 1s steps(1) infinite; }
@keyframes caret { 50% { opacity: 0; } }
.websrc { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: baseline; margin-top: 10px; font-size: 13px; white-space: normal; }
.websrc span { color: var(--muted); }
.websrc a { overflow-wrap: anywhere; }
.chip.web { background: var(--good-soft); color: var(--good); border-color: transparent; }
@media (prefers-reduced-motion: reduce) { .bubble.streaming::after { animation: none; } }
.bubble pre { white-space: pre; overflow-x: auto; margin: 8px 0; padding: 10px 12px; border-radius: 10px; background: var(--bg); border: 1px solid var(--line); font-size: 13px; line-height: 1.45; }
.msg.user .bubble pre { background: rgba(0,0,0,.18); border-color: transparent; color: inherit; }
.bubble code { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: .92em; }
.bubble :not(pre) > code { padding: 1px 5px; border-radius: 5px; background: var(--bg); }
.inputrow button { border-radius: 12px; padding: 0 20px; }
.powered { display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 12px; color: var(--muted); padding: 8px 0 4px; }
.powered .logo { width: 14px; height: 14px; }
.powered a { color: var(--muted); }
.tierkey { text-align: center; font-size: 12px; color: var(--muted); margin-top: 4px; }
.top .authbox .em { display: none; }
.gate { margin: 4px 0 14px; padding: 18px; border: 1px solid var(--zenith); background: var(--zenith-soft); border-radius: 16px; }
.gate p { margin: 0 0 12px; }
@media (min-width: 640px) { .top .authbox .em { display: inline; } }
"""

CHAT_BODY = r"""
<div class="chat" id="chatbox">
  <header class="top">
    <div class="avatar" id="avatar" aria-hidden="true">?</div>
    <div class="grow">
      <div class="name" id="title">Assistant</div>
      <div class="company"><span class="status" id="status"><i></i><span id="sub">Connecting...</span></span></div>
    </div>
    <div class="authbox" id="authbox"></div>
    <button id="newchat" type="button">New chat</button>
  </header>
  <div class="log" id="log" aria-live="polite"></div>
  <div class="composer">
    <div class="starters" id="starters" hidden></div>
    <form class="inputrow" id="form">
      <label for="msg" style="position:absolute;left:-9999px">Your question</label>
      <textarea id="msg" rows="1" placeholder="Ask a question..." autocomplete="off" maxlength="4000"></textarea>
      <button id="send" class="primary" type="submit">Send</button>
    </form>
    <div class="hint" id="hint" hidden></div>
    <div class="powered">""" + LOGO_SVG + r"""Powered by <a href="/" target="_blank" rel="noopener">SkyMind</a></div>
  </div>
</div>
"""

CHAT_JS = r"""
var $ = function (id) { return document.getElementById(id); };
var botId = decodeURIComponent(location.pathname.split("/").filter(Boolean).pop() || "");
var greeting = "Hello! How can I help?";
var JOB = "answer";
var SAMPLE_CODE = [
  "import requests",
  "",
  "API_KEY = \"sk-live-4f9a8b7c6d5e4f3a2b1c\"",
  "",
  "def get_order(db, order_id):",
  "    cur = db.cursor()",
  "    cur.execute(f\"SELECT * FROM orders WHERE id = {order_id}\")",
  "    return cur.fetchone()",
  "",
  "def total_with_discount(price: float, discount_pct):",
  "    # TODO: support coupon codes",
  "    try:",
  "        rate = requests.get(\"https://partner.example/rates\").json()",
  "        return price * (1 - discount_pct / 100) * rate[\"tax\"]",
  "    except:",
  "        print(\"something failed\")"
].join("\n");
var STARTERS = {
  code_review: [["Try sample code with bugs", SAMPLE_CODE, false], ["What are the security rules?", "What are the security rules?", true]],
  ideas: [["Get more first-time campers", "How can we sell more to first-time campers?", true],
          ["Cut tent returns", "Give me ideas to reduce tent returns.", true],
          ["Bring customers back", "How do we get customers to buy again?", true]]
};
function setupJob(bot) {
  JOB = bot.job || "answer";
  var box = $("msg");
  box.maxLength = bot.max_message || 4000;
  if (JOB !== "answer") {
    var tag = document.createElement("span");
    tag.className = "jobtag";
    tag.textContent = bot.job_label;
    $("title").append(tag);
  }
  if (JOB === "code_review") {
    $("chatbox").classList.add("wide");
    box.classList.add("code");
    box.rows = 8;
    box.placeholder = "Paste code to review...";
    $("hint").textContent = "Ctrl+Enter (or Cmd+Enter) to send. Enter adds a new line.";
    $("hint").hidden = false;
  } else if (JOB === "ideas") {
    box.placeholder = "Describe a goal or problem...";
  }
  var list = STARTERS[JOB] || [];
  list.forEach(function (s) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = s[0];
    btn.onclick = function () { box.value = s[1]; grow(); if (s[2]) { send(); } else { box.focus(); } };
    $("starters").append(btn);
  });
  $("starters").hidden = list.length === 0;
}
function grow() {
  var box = $("msg");
  if (JOB === "code_review") return;  // fixed tall box, user can resize
  box.style.height = "auto";
  box.style.height = Math.min(box.scrollHeight + 2, window.innerHeight * 0.4) + "px";
}
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

// Safe formatting for replies: ```code blocks```, **bold**, `code` and # headings.
// Everything is built with text nodes (never innerHTML), so model output can't inject HTML.
function inline(parent, text) {
  text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/).forEach(function (part) {
    if (!part) return;
    if (part.slice(0, 2) === "**" && part.slice(-2) === "**" && part.length > 4) {
      var st = document.createElement("strong"); st.textContent = part.slice(2, -2); parent.append(st);
    } else if (part.charAt(0) === "`" && part.slice(-1) === "`" && part.length > 2) {
      var c = document.createElement("code"); c.textContent = part.slice(1, -1); parent.append(c);
    } else {
      parent.append(document.createTextNode(part));
    }
  });
}
function renderRich(el, text) {
  var parts = text.split(/```[\w+-]*\n?/);
  parts.forEach(function (part, i) {
    if (i % 2 === 1) {
      var pre = document.createElement("pre"), code = document.createElement("code");
      code.textContent = part.replace(/\n$/, "");
      pre.append(code); el.append(pre);
    } else {
      part = part.replace(/^\n+|\n+$/g, "");
      part.split("\n").forEach(function (line, j, all) {
        var h = line.match(/^#{1,4}\s+(.*)/);
        if (h) { var st = document.createElement("strong"); st.textContent = h[1]; el.append(st); }
        else { inline(el, line); }
        if (j < all.length - 1) el.append(document.createTextNode("\n"));
      });
    }
  });
}
function addMessage(text, who, data) {
  var row = document.createElement("div");
  row.className = "msg " + who;
  var b = document.createElement("div");
  b.className = "bubble";
  if (who === "bot" && data) { renderRich(b, text); }
  else if (who === "user" && JOB === "code_review" && text.indexOf("\n") >= 0) {
    var pre = document.createElement("pre"), code = document.createElement("code");
    code.textContent = text; pre.append(code); b.append(pre);
  } else { b.textContent = text; }
  if (data) {
    var meta = document.createElement("div");
    meta.className = "meta";
    meta.append(chip(data.tier === "strong" ? "Strong model" : "Cheap model", data.tier));
    var ms = function (v) { return v < 1000 ? Math.round(v) + " ms" : (v / 1000).toFixed(1) + " s"; };
    if (data.streamed && data.first_token_ms) { meta.append(chip("first words in " + ms(data.first_token_ms))); }
    meta.append(chip((data.streamed ? "done in " : "") + ms(data.latency_ms)));
    if (data.history_messages) { meta.append(chip("remembers " + data.history_messages + " messages")); }
    (data.sources || []).forEach(function (s) { meta.append(chip("Source: " + s)); });
    if (data.job && data.job !== "answer" && data.context_sections) {
      meta.append(chip((data.job === "code_review" ? "Checked against " : "Used ") + data.context_sections + " document sections"));
    }
    if (data.budget_guard) { meta.append(chip("Budget guard on")); }
    if (data.answered_from === "website") { meta.append(chip("From the company website", "web")); }
    b.append(meta);
    if (data.answered_from === "website" && data.web_sources && data.web_sources.length) {
      var srcs = document.createElement("div");
      srcs.className = "websrc";
      var lab = document.createElement("span");
      lab.textContent = "Sources:";
      srcs.append(lab);
      data.web_sources.forEach(function (s) {
        if (!/^https?:\/\//i.test(s.url || "")) return;  // only real web links
        var a = document.createElement("a");
        a.href = s.url; a.target = "_blank"; a.rel = "noopener noreferrer";
        a.textContent = s.title || s.url;
        a.title = s.url;
        srcs.append(a);
      });
      b.append(srcs);
    }
    if (data.answer_id) { b.append(rateRow(data.answer_id)); }
  }
  row.append(b);
  $("log").append(row);
  $("log").scrollTop = $("log").scrollHeight;
  return row;
}

var THUMB = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 10v12"/><path d="M15 5.9 14 10h5.8a2 2 0 0 1 2 2.3l-1.4 8A2 2 0 0 1 18.4 22H7V10l4.4-7.5A1.9 1.9 0 0 1 15 5.9Z"/></svg>';
function rateRow(answerId) {
  var row = document.createElement("div");
  row.className = "rate";
  var label = document.createElement("span");
  label.textContent = "Was this helpful?";
  row.append(label);
  [[true, "Yes"], [false, "No"]].forEach(function (opt) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.innerHTML = THUMB;  // fixed icon markup, no user text
    if (!opt[0]) { btn.querySelector("svg").style.transform = "rotate(180deg)"; }
    btn.append(document.createTextNode(opt[1]));
    btn.setAttribute("aria-label", opt[0] ? "Helpful" : "Not helpful");
    btn.onclick = async function () {
      row.replaceChildren(document.createTextNode("Thanks for the feedback."));
      try {
        await fetch("/bots/" + encodeURIComponent(botId) + "/feedback", {
          method: "POST",
          headers: skyHeaders({ "Content-Type": "application/json" }),
          body: JSON.stringify({ session_id: session, answer_id: answerId, helpful: opt[0] })
        });
      } catch (e) {}
    };
    row.append(btn);
  });
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
    currentBot = bot;
    document.title = bot.name + " | " + bot.company;
    $("title").textContent = bot.name;
    $("sub").textContent = bot.company;
    $("avatar").textContent = (bot.name || "?").trim().charAt(0).toUpperCase();
    greeting = bot.greeting;
    setupJob(bot);
    var me = await skyReady;
    var restricted = bot.access && bot.access.mode === "google";
    if (!restricted && !me.user) { $("authbox").hidden = true; }
    if (restricted && !me.user) { showGate(bot); return; }
    addMessage(greeting, "bot", null);
    $("msg").focus();
  } catch (e) {
    $("sub").textContent = "Could not reach the server.";
    $("status").querySelector("i").style.background = "var(--bad)";
  }
}

function showGate(bot) {
  var a = bot.access || {};
  var who = (a.allowed_domains || []).map(function (d) { return "@" + d; }).join(", ");
  var g = document.createElement("div");
  g.className = "gate";
  var p = document.createElement("p");
  p.textContent = bot.company + "'s assistant is only for signed-in " + (who ? who + " " : "") + "Google accounts" + (a.invite_list ? " and invited people" : "") + ". Sign in to continue.";
  var holder = document.createElement("div");
  g.append(p, holder);
  $("log").replaceChildren(g);
  $("send").disabled = true;
  $("msg").disabled = true;
  $("msg").placeholder = "Sign in to ask a question";
  if (SKY.me.google_enabled) { skyRenderButton(holder, "signin_with"); }
  else { holder.textContent = "Sign-in is not available on this server."; }
}
var currentBot = null;

// Streaming: the server sends the answer as Server-Sent Events while the model writes it.
// Each event is "event: <name>" + "data: <json>" followed by a blank line.
function parseEvent(block) {
  var ev = { event: "message", data: null };
  block.split("\n").forEach(function (line) {
    if (line.indexOf("event:") === 0) ev.event = line.slice(6).trim();
    else if (line.indexOf("data:") === 0) { try { ev.data = JSON.parse(line.slice(5)); } catch (e) {} }
  });
  return ev;
}

async function askStreaming(text, wait) {
  // Returns true when handled; false when streaming isn't possible (then the caller uses /chat).
  var res;
  try {
    res = await fetch("/bots/" + encodeURIComponent(botId) + "/chat/stream", {
      method: "POST",
      headers: skyHeaders({ "Content-Type": "application/json", "Accept": "text/event-stream" }),
      body: JSON.stringify({ session_id: session, message: text })
    });
  } catch (e) { return false; }
  if (res.status === 401 && currentBot) { wait.remove(); showGate(currentBot); return true; }
  if (!res.ok) {
    var err = {};
    try { err = await res.json(); } catch (e) {}
    wait.remove();
    addMessage(typeof err.detail === "string" ? err.detail : "Something went wrong. Please try again.", "bot", null);
    return true;
  }
  if (!res.body || (res.headers.get("content-type") || "").indexOf("text/event-stream") !== 0) return false;

  var reader = res.body.getReader(), decoder = new TextDecoder(), buf = "", got = "";
  var row = null, bubble = null, done = null, failure = null;
  try {
    while (true) {
      var chunk = await reader.read();
      if (chunk.done) break;
      buf += decoder.decode(chunk.value, { stream: true });
      var cut;
      while ((cut = buf.indexOf("\n\n")) >= 0) {
        var ev = parseEvent(buf.slice(0, cut));
        buf = buf.slice(cut + 2);
        if (ev.event === "text" && ev.data) {
          if (!row) {
            wait.remove();
            row = document.createElement("div");
            row.className = "msg bot";
            bubble = document.createElement("div");
            bubble.className = "bubble streaming";
            row.append(bubble);
            $("log").append(row);
          }
          got += ev.data.text;
          bubble.replaceChildren();
          renderRich(bubble, got);  // formatted as it grows (bold, code blocks)
          $("log").scrollTop = $("log").scrollHeight;
        } else if (ev.event === "searching" && ev.data) {
          wait.remove();
          if (!row) {
            row = document.createElement("div");
            row.className = "msg bot";
            bubble = document.createElement("div");
            bubble.className = "bubble streaming";
            row.append(bubble);
            $("log").append(row);
          }
          got = "";
          bubble.textContent = "That isn't in my documents. Checking " + ev.data.site + "...";
          $("log").scrollTop = $("log").scrollHeight;
        } else if (ev.event === "done") { done = ev.data; }
        else if (ev.event === "error") { failure = ev.data && ev.data.detail; }
      }
    }
  } catch (e) { failure = failure || "The connection was interrupted. Please ask again."; }
  wait.remove();
  if (row) row.remove();
  if (done) { addMessage(done.reply, "bot", done); }
  else {
    if (got) addMessage(got, "bot", null);
    addMessage(failure || "The answer didn't finish. Please ask again.", "bot", null);
  }
  return true;
}

async function askWhole(text, wait) {
  try {
    var res = await fetch("/bots/" + encodeURIComponent(botId) + "/chat", {
      method: "POST",
      headers: skyHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ session_id: session, message: text })
    });
    var data = await res.json();
    wait.remove();
    if (res.status === 401 && currentBot) { showGate(currentBot); return; }
    if (!res.ok) {
      addMessage(typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.", "bot", null);
    } else {
      addMessage(data.reply, "bot", data);
    }
  } catch (e) {
    wait.remove();
    addMessage("Could not reach the server. Check your connection and try again.", "bot", null);
  }
}

async function send() {
  var text = $("msg").value.trim();
  if (!text || busy) return;
  busy = true;
  $("msg").value = "";
  grow();
  addMessage(text, "user", null);
  var wait = addTyping();
  $("send").disabled = true;
  if (!(await askStreaming(text, wait))) { await askWhole(text, wait); }
  busy = false;
  $("send").disabled = false;
  $("msg").focus();
}

$("form").onsubmit = function (e) { e.preventDefault(); send(); };
$("msg").addEventListener("input", grow);
$("msg").addEventListener("keydown", function (e) {
  if (e.key !== "Enter" || e.isComposing) return;
  var sendNow = JOB === "code_review" ? (e.ctrlKey || e.metaKey) : !e.shiftKey;
  if (sendNow) { e.preventDefault(); send(); }
});
$("newchat").onclick = function () {
  session = newSession();
  $("log").replaceChildren();
  addMessage(greeting, "bot", null);
  $("msg").focus();
};

init();
"""

CHAT_HTML = _shell("Chat | SkyMind", CHAT_BODY, AUTH_JS + CHAT_JS, CHAT_CSS)


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
    <p class="sub" style="margin:0">Enter the admin token. It is printed in the server window as <b>SkyMind admin token: ...</b> when SkyMind starts, unless you set your own with ADMIN_TOKEN. Google accounts listed in ADMIN_EMAILS can sign in with Google instead.</p>
    <div id="adminGoogle" style="margin-top:12px"></div>
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
          <th>Routing mix</th><th>Budget used</th><th class="num">Saved</th><th>Quality</th><th>Status</th><th><span style="position:absolute;left:-9999px">Actions</span></th>
        </tr></thead>
        <tbody id="rows"><tr><td colspan="11" class="empty">Loading...</td></tr></tbody>
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
  opts.headers = Object.assign({}, opts.headers || {}, skyHeaders(token ? { "X-Admin-Token": token } : {}));
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
  skyReady.then(function (me) {
    if (me.google_enabled && !me.user) skyRenderButton($("adminGoogle"), "signin_with");
    else if (me.user && !me.is_admin) $("adminGoogle").textContent = me.user.email + " is not an admin account.";
  });
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
      c.colSpan = 11;
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
      sub.textContent = b.company + ", " + (b.spec.provider || "anthropic") + ", " + (b.owner_email || "no account") + ", " + (b.access === "google" ? "Google sign-in" : "public link");
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
      var qd = b.quality || { helpful: 0, not_helpful: 0, gaps: 0 }, qr = qd.helpful + qd.not_helpful;
      tr.append(mini((qr ? Math.round(100 * qd.helpful / qr) + "% helpful" : "no ratings") + ", " + qd.gaps + " gaps", bar([["ok", qr ? 100 * qd.helpful / qr : 0], ["over", qr ? 100 * qd.not_helpful / qr : 0]])));

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

refresh();  // works with a saved token, or an admin Google account; otherwise shows sign-in
"""

ADMIN_HTML = _shell("Admin console | SkyMind", ADMIN_BODY, AUTH_JS + ADMIN_JS, ADMIN_CSS)
