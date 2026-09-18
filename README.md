# The Deal Outlet Tool Box

Internal - Catalogue and Operations Tool

One landing hub that links out to your other Flask tools, with a live
up/down dot for each (pinged server-side every ~45s, cached), search,
tag filtering, and your logo/branding. Each tool is locked behind a PIN
before launching — most tools share one PIN, but any tool can be given
its own separate PIN.

## Setup

1. Edit the `TOOLS` list near the top of `app.py` — replace the
   placeholder URLs with your real Render URLs (Scraper, Category
   Monitor, Scanner, Price Book Generator, etc.). Add more tools by
   appending to the list; no template changes needed.

2. If a tool doesn't have a `/health` route, either add a trivial one
   (`return "ok", 200`) or just delete the `"health"` key for that tool
   — it'll show "no check" instead of a status dot, but the Launch
   button still works fine.

3. To disable a tool without removing it, set `"enabled": False` on its
   entry — it disappears from the dashboard and status checks but stays
   in the list for later.

4. To give a tool its own PIN instead of the shared one, add
   `"pin": "your-pin"` to that tool's entry. Any tool without a `"pin"`
   key falls back to the shared `TDO_PIN`.

5. Deploy exactly like your other apps (Flask + Render).

## Structure

There is no `templates/` folder and no `config.json`. The dashboard and
PIN-unlock pages are rendered from HTML strings inside `app.py`
(`DASHBOARD_HTML`, `UNLOCK_HTML`), and the tool registry lives in the
`TOOLS` list near the top of that same file. Everything lives in one file
on purpose — one place to edit, one file to redeploy.

## Env vars (set these on Render)

- `TDO_PIN` — the shared PIN, used by any tool that doesn't define its
  own `"pin"`
- `SECRET_KEY` — any random string (for session signing). Set once and
  keep it stable — changing it logs everyone out of every tool.

## Local run

Windows cmd:
    set TDO_PIN=1234
    set SECRET_KEY=dev
    python app.py

PowerShell:
    $env:TDO_PIN="1234"
    $env:SECRET_KEY="dev"
    python app.py

Mac/Linux:
    TDO_PIN=1234 SECRET_KEY=dev python app.py

Then open http://127.0.0.1:5000

## Deployment (Render)

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Set `TDO_PIN` and `SECRET_KEY` under Environment
