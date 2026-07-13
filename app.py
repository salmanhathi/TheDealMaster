"""
The Deal Outlet Tool Box — a single landing hub for Salman's internal
Flask tools (Internal - Catalogue and Operations Tool).

Deploy this exactly like the other tools (Flask + Render).
Set env vars:
  TDO_PIN        - shared PIN, same one used by the other tools
  SECRET_KEY     - any random string, for session signing

To add a tool later: just add an entry to the TOOLS list below and redeploy.
Nothing else needs to change.
"""

import os
import time
from datetime import datetime, timezone

import requests
from flask import Flask, request, session, redirect, url_for, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

PIN = os.environ.get("TDO_PIN", "0000")

LOGO_URL = "https://www.thedealoutlet.com/on/demandware.static/Sites-TheDealOutlet_AE-Site/-/default/dwf652137f/images/logo.svg"
BRAND_NAME = "The Deal Outlet Tool Box"
BRAND_EYEBROW = "Internal · Catalogue and Operations Tool"

# ---------------------------------------------------------------------------
# Tool registry — add new tools here. `health` is optional: if the target
# app exposes a lightweight endpoint that returns 200 quickly, point at it
# and the dashboard will show a live status dot. Leave it blank to skip
# the check and just show a static "link" state.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "id": "pac",
        "name": "The Deal - Product Scraper",
        "tag": "SCRAPER",
        "description": "Bulk-scrapes thedealoutlet.com for stock, price and image status across the full catalog. Runs on a daily schedule. Uses Product ID as Input",
        "url": "https://thedealscraper.onrender.com",
        "health": "https://thedealscraper.onrender.com/health",
    },
    {
        "id": "health-monitor",
        "name": "Product Categroy Monitor",
        "tag": "MONITOR",
        "description": "Crawls live categories for data-quality issues — missing images, missing prices, broken listings. Uses live Category link as Input. No Prodduct ID's Needed",
        "url": "https://thedealcategorymonitor.onrender.com",
        "health": "https://thedealcategorymonitor.onrender.com/health",
    },
    {
        "id": "lookup",
        "name": "Product Scanner",
        "tag": "SCANNER",
        "description": "Barcode scan or OCR a physical item and match it to its website product code via the barcode map.",
        "url": "https://deal-product-scanner.onrender.com",
        "health": "https://deal-product-scanner.onrender.com/health",
    },
    {
        "id": "lookup",
        "name": "Price Book Generator",
        "tag": "PRICE BOOK",
        "description": "Generates Price Book XML file for SFCC Import. Both UAE and KSA will work automatically.",
        "url": "https://sfcc-pricebook-tool-updated.onrender.com",
        "health": "https://sfcc-pricebook-tool-updated.onrender.com/health",
    },
]

# very small in-memory cache so the dashboard doesn't re-ping every tool
# on every page view
_status_cache = {}
CACHE_SECONDS = 45


def check_health(tool):
    if not tool.get("health"):
        return "unknown"
    cached = _status_cache.get(tool["id"])
    if cached and (time.time() - cached["ts"]) < CACHE_SECONDS:
        return cached["status"]
    try:
        r = requests.get(tool["health"], timeout=4)
        status = "up" if r.status_code < 400 else "down"
    except requests.RequestException:
        status = "down"
    _status_cache[tool["id"]] = {"status": status, "ts": time.time()}
    return status


# ---------------------------------------------------------------------------
# Auth — same shared-PIN pattern as the lookup tool
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("pin") == PIN:
            session["authed"] = True
            return redirect(url_for("dashboard"))
        error = "Wrong PIN."
    return render_template_string(LOGIN_HTML, error=error, logo=LOGO_URL,
                                   brand=BRAND_NAME, eyebrow=BRAND_EYEBROW)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def require_auth():
    return session.get("authed") is True


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    if not require_auth():
        return redirect(url_for("login"))
    tags = sorted({t["tag"] for t in TOOLS})
    return render_template_string(DASHBOARD_HTML, tools=TOOLS, tags=tags,
                                   logo=LOGO_URL, brand=BRAND_NAME, eyebrow=BRAND_EYEBROW)


@app.route("/api/status")
def api_status():
    if not require_auth():
        return jsonify({"error": "unauthorized"}), 401
    result = {t["id"]: check_health(t) for t in TOOLS}
    return jsonify({"status": result, "checked_at": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ brand }}</title>
<link rel="icon" href="{{ logo }}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;1,500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#14151A; --bg2:#0F1013; --panel:#1D1F26; --line:#2C2E37;
    --gold:#C9A66B; --gold-dim:#8E7A54; --ink:#F2EFE8; --dim:#B0B2BD;
    --err:#C4695F;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; min-height:100vh; color:var(--ink);
    font-family:'IBM Plex Mono',monospace;
    display:flex; align-items:center; justify-content:center;
    background:
      radial-gradient(60% 50% at 50% 0%, rgba(201,166,107,.10), transparent 70%),
      linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
  }
  .card{
    width:min(380px,90vw); background:var(--panel); border:1px solid var(--line);
    border-radius:10px; padding:40px 36px; position:relative; overflow:hidden;
    box-shadow:0 30px 60px -20px rgba(0,0,0,.6);
    animation:rise .5s cubic-bezier(.2,.8,.2,1);
  }
  @keyframes rise{ from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:translateY(0);} }
  .card::before{
    content:""; position:absolute; top:0; left:-100%; width:60%; height:2px;
    background:linear-gradient(90deg, transparent, var(--gold), transparent);
    animation:sweep 3.2s ease-in-out infinite;
  }
  @keyframes sweep{ 0%{left:-60%;} 55%{left:100%;} 100%{left:100%;} }
  .logo-wrap{ display:inline-flex; align-items:center; background:#fff; border-radius:8px; padding:8px 14px; margin:0 0 22px; }
  .logo{ display:block; height:22px; }
  h1{
    font-family:'Fraunces',serif; font-weight:600; font-size:22px; margin:0 0 4px;
    letter-spacing:.005em;
  }
  .eyebrow{
    color:var(--gold); font-size:10.5px; letter-spacing:.14em; text-transform:uppercase;
    margin:0 0 26px;
  }
  input[type=password]{
    width:100%; padding:13px 14px; background:var(--bg); border:1px solid var(--line);
    color:var(--ink); border-radius:6px; font-family:inherit; font-size:15px;
    letter-spacing:.3em; margin-bottom:16px; transition:border-color .15s;
  }
  input[type=password]:focus{ outline:none; border-color:var(--gold); }
  button{
    width:100%; padding:13px; background:var(--gold); color:#181913; border:none;
    border-radius:6px; font-family:'IBM Plex Mono',monospace; font-weight:500; letter-spacing:.06em;
    text-transform:uppercase; font-size:12.5px; cursor:pointer; transition:filter .15s, transform .1s;
  }
  button:hover{ filter:brightness(1.1); }
  button:active{ transform:scale(.98); }
  .err{ color:var(--err); font-size:12px; margin:-8px 0 14px; }
</style>
</head>
<body>
  <form class="card" method="POST">
    <div class="logo-wrap"><img class="logo" src="{{ logo }}" alt="{{ brand }}"></div>
    <h1>{{ brand }}</h1>
    <p class="eyebrow">{{ eyebrow }}</p>
    {% if error %}<p class="err">{{ error }}</p>{% endif %}
    <input type="password" name="pin" placeholder="PIN" autofocus>
    <button type="submit">Enter</button>
  </form>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ brand }}</title>
<link rel="icon" href="{{ logo }}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;1,500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#14151A; --bg2:#0F1013; --panel:#1D1F26; --panel-hi:#22242D; --line:#2C2E37;
    --gold:#C9A66B; --gold-dim:#8E7A54; --ink:#F2EFE8; --dim:#B0B2BD;
    --up:#7BAE93; --down:#C4695F; --unknown:#54565F;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; min-height:100vh; color:var(--ink);
    font-family:'IBM Plex Mono',monospace;
    background:
      radial-gradient(50% 30% at 50% 0%, rgba(201,166,107,.07), transparent 70%),
      linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
  }
  header{
    display:flex; align-items:center; justify-content:space-between; gap:20px;
    padding:22px clamp(20px,4vw,48px); border-bottom:1px solid var(--line);
    position:sticky; top:0; backdrop-filter:blur(10px); background:rgba(20,21,26,.82); z-index:10;
  }
  .brand{ display:flex; align-items:center; gap:14px; }
  .brand-logo{ display:inline-flex; align-items:center; background:#fff; border-radius:6px; padding:6px 10px; }
  .brand img{ height:18px; display:block; }
  .brand-text h1{
    font-family:'Fraunces',serif; font-weight:600; font-size:18px; margin:0; letter-spacing:.005em;
  }
  .brand-text p{ margin:2px 0 0; color:var(--gold); font-size:10px; letter-spacing:.12em; text-transform:uppercase; }
  .right{ display:flex; align-items:center; gap:18px; }
  .summary{ font-size:11px; color:var(--dim); display:flex; align-items:center; gap:6px; }
  .summary .up-count{ color:var(--up); }
  .refresh{
    background:transparent; border:1px solid var(--line); color:var(--dim); border-radius:5px;
    padding:7px 10px; font-family:inherit; font-size:11px; cursor:pointer; display:flex; align-items:center; gap:6px;
    transition:border-color .15s, color .15s;
  }
  .refresh:hover{ border-color:var(--gold); color:var(--gold); }
  .refresh svg{ width:12px; height:12px; transition:transform .5s; }
  .refresh.spinning svg{ transform:rotate(360deg); }
  a.logout{ color:var(--dim); font-size:12px; text-decoration:none; border-bottom:1px solid transparent; }
  a.logout:hover{ color:var(--ink); border-bottom-color:var(--dim); }

  main{ padding:30px clamp(20px,4vw,48px) 60px; max-width:1200px; margin:0 auto; }

  .controls{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:26px; }
  .search{ position:relative; flex:1; min-width:220px; }
  .search input{
    width:100%; padding:11px 14px 11px 36px; background:var(--panel); border:1px solid var(--line);
    color:var(--ink); border-radius:7px; font-family:inherit; font-size:13px; transition:border-color .15s;
  }
  .search input:focus{ outline:none; border-color:var(--gold); }
  .search svg{ position:absolute; left:12px; top:50%; transform:translateY(-50%); width:14px; height:14px; color:var(--dim); }
  .chips{ display:flex; gap:8px; flex-wrap:wrap; }
  .chip{
    padding:7px 13px; border-radius:20px; border:1px solid var(--line); background:var(--panel);
    color:var(--dim); font-size:11px; letter-spacing:.06em; text-transform:uppercase; cursor:pointer;
    transition:all .15s; user-select:none;
  }
  .chip:hover{ border-color:var(--gold-dim); color:var(--ink); }
  .chip.active{ background:var(--gold); border-color:var(--gold); color:#181913; }

  .grid{
    display:grid; grid-template-columns:repeat(auto-fill,minmax(290px,1fr)); gap:16px;
  }
  .tool{
    background:var(--panel); border:1px solid var(--line); border-radius:10px;
    padding:22px; display:flex; flex-direction:column; gap:11px;
    transition:transform .18s cubic-bezier(.2,.8,.2,1), border-color .18s, box-shadow .18s;
    opacity:0; animation:fadein .4s ease forwards;
  }
  @keyframes fadein{ from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:translateY(0);} }
  .tool:hover{
    transform:translateY(-3px); border-color:var(--gold-dim);
    box-shadow:0 16px 30px -16px rgba(0,0,0,.55);
  }
  .tool.hidden{ display:none; }
  .tool-top{ display:flex; align-items:center; justify-content:space-between; }
  .tag{
    font-size:10px; letter-spacing:.14em; color:var(--gold); text-transform:uppercase;
  }
  .status{ display:flex; align-items:center; gap:6px; font-size:11px; color:var(--dim); }
  .dot{ width:7px; height:7px; border-radius:50%; background:var(--unknown); flex:none; transition:background .2s; }
  .dot.up{ background:var(--up); box-shadow:0 0 0 3px rgba(123,174,147,.15); }
  .dot.down{ background:var(--down); box-shadow:0 0 0 3px rgba(196,105,95,.15); }
  .dot.pulse{ animation:pulse 1.5s ease-in-out infinite; }
  @keyframes pulse{ 0%,100%{opacity:1;} 50%{opacity:.35;} }

  .tool h2{
    font-family:'Fraunces',serif; font-weight:600; font-size:17px; margin:0;
    letter-spacing:.002em;
  }
  .tool p{ color:var(--dim); font-size:12.5px; line-height:1.55; margin:0; flex:1; }
  .launch{
    align-self:flex-start; margin-top:4px; padding:9px 16px; background:transparent;
    border:1px solid var(--gold); color:var(--gold); border-radius:6px; text-decoration:none;
    font-size:11px; letter-spacing:.08em; text-transform:uppercase; font-family:inherit;
    font-weight:500; transition:background .15s, color .15s, transform .1s;
  }
  .launch:hover{ background:var(--gold); color:#181913; }
  .launch:active{ transform:scale(.97); }

  .empty{ text-align:center; padding:60px 20px; color:var(--dim); font-size:13px; display:none; }
  .empty.show{ display:block; }

  footer{ padding:0 clamp(20px,4vw,48px) 40px; color:var(--dim); font-size:11px; max-width:1200px; margin:0 auto; }

  @media (prefers-reduced-motion: reduce){
    *{ animation:none !important; transition:none !important; }
  }
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="brand-logo"><img src="{{ logo }}" alt=""></div>
    <div class="brand-text">
      <h1>{{ brand }}</h1>
      <p>{{ eyebrow }}</p>
    </div>
  </div>
  <div class="right">
    <div class="summary" id="summary">checking status…</div>
    <button class="refresh" id="refreshBtn" title="Refresh status">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
      refresh
    </button>
    <a class="logout" href="{{ url_for('logout') }}">Log out</a>
  </div>
</header>
<main>
  <div class="controls">
    <div class="search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
      <input type="text" id="searchInput" placeholder="Search tools…">
    </div>
    <div class="chips" id="chips">
      <span class="chip active" data-tag="all">All</span>
      {% for tag in tags %}
      <span class="chip" data-tag="{{ tag }}">{{ tag }}</span>
      {% endfor %}
    </div>
  </div>

  <div class="grid" id="grid">
    {% for t in tools %}
    <div class="tool" data-id="{{ t.id }}" data-tag="{{ t.tag }}" data-name="{{ t.name|lower }}" style="animation-delay:{{ loop.index0 * 0.05 }}s">
      <div class="tool-top">
        <span class="tag">{{ t.tag }}</span>
        <span class="status"><span class="dot pulse" id="dot-{{ t.id }}"></span><span id="label-{{ t.id }}">checking</span></span>
      </div>
      <h2>{{ t.name }}</h2>
      <p>{{ t.description }}</p>
      <a class="launch" href="{{ t.url }}" target="_blank" rel="noopener">Launch →</a>
    </div>
    {% endfor %}
  </div>
  <div class="empty" id="emptyState">No tools match that search.</div>
</main>
<footer>Add new tools by editing TOOLS in app.py — no template changes needed.</footer>

<script>
async function refreshStatus(manual){
  const btn = document.getElementById('refreshBtn');
  if (manual) btn.classList.add('spinning');
  try{
    const res = await fetch('/api/status');
    const data = await res.json();
    let up = 0, down = 0, unknown = 0;
    for (const [id, status] of Object.entries(data.status)){
      const dot = document.getElementById('dot-' + id);
      const label = document.getElementById('label-' + id);
      if (!dot) continue;
      dot.classList.remove('up','down','pulse');
      if (status === 'up'){ dot.classList.add('up'); label.textContent = 'online'; up++; }
      else if (status === 'down'){ dot.classList.add('down'); label.textContent = 'offline'; down++; }
      else { label.textContent = 'no check'; unknown++; }
    }
    const parts = [];
    if (up) parts.push(up + ' online');
    if (down) parts.push(down + ' offline');
    if (unknown) parts.push(unknown + ' unmonitored');
    document.getElementById('summary').innerHTML =
      '<span class="up-count">' + (parts.join(' · ') || 'no tools configured') + '</span>';
  } catch(e){
    document.getElementById('summary').textContent = 'status unavailable';
  }
  if (manual) setTimeout(() => btn.classList.remove('spinning'), 500);
}
document.getElementById('refreshBtn').addEventListener('click', () => refreshStatus(true));
refreshStatus(false);
setInterval(() => refreshStatus(false), 60000);

// search + filter
const cards = Array.from(document.querySelectorAll('.tool'));
const searchInput = document.getElementById('searchInput');
const chips = document.querySelectorAll('.chip');
const emptyState = document.getElementById('emptyState');
let activeTag = 'all';

function applyFilters(){
  const q = searchInput.value.trim().toLowerCase();
  let visible = 0;
  cards.forEach(c => {
    const matchesTag = activeTag === 'all' || c.dataset.tag === activeTag;
    const matchesSearch = !q || c.dataset.name.includes(q);
    const show = matchesTag && matchesSearch;
    c.classList.toggle('hidden', !show);
    if (show) visible++;
  });
  emptyState.classList.toggle('show', visible === 0);
}

searchInput.addEventListener('input', applyFilters);
chips.forEach(chip => {
  chip.addEventListener('click', () => {
    chips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    activeTag = chip.dataset.tag;
    applyFilters();
  });
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
