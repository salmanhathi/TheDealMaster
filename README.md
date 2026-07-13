# The Deal Outlet Tool Box

Internal - Catalogue and Operations Tool

One landing hub that links out to your other Flask tools, with a live
up/down dot for each (pinged server-side every ~45s, cached), search,
tag filtering, and your logo/branding.

## Setup

1. Edit the `TOOLS` list near the top of `app.py` — replace the
   placeholder URLs with your real Render URLs for PAC, Health Monitor,
   and Lookup. Add more tools by appending to the list; no template
   changes needed.

2. If a tool doesn't have a `/health` route, either add a trivial one
   (`return "ok", 200`) or just delete the `"health"` key for that tool
   — it'll show "no check" instead of a status dot, but the Launch
   button still works fine.

3. Deploy exactly like your other apps (Flask + Render).

## Env vars (set these on Render)

- `TDO_PIN` — same PIN you already use elsewhere
- `SECRET_KEY` — any random string (for session signing)

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
