# How to run the meeting room

## Quick start (this environment)

```bash
export PYTHONPATH=/workspace
export ORG_DATA_DIR=/tmp/org_platform_data_srs
export PATH="$HOME/.local/bin:$PATH"
bash org_platform/deploy/run_local.sh
```

Open:

- Local: http://127.0.0.1:8080
- Public tunnel (temporary; refreshes if it drops): https://cons-jon-schedules-beaver.trycloudflare.com
- **VP Delivery Studio (screen share → DevOps):** https://cons-jon-schedules-beaver.trycloudflare.com/studio
- **Domain Publisher (Google Studio → GoDaddy):** https://cons-jon-schedules-beaver.trycloudflare.com/publish
- Slack `#devops`: https://cons-jon-schedules-beaver.trycloudflare.com/slack
- Meeting room: https://cons-jon-schedules-beaver.trycloudflare.com/meeting/565ea73f-91f2-4dc1-b42c-2c76e7844647

## Domain Publisher (Google Studio site → GoDaddy domain)

1. Open `/publish`.
2. Paste your **Google Studio / Firebase** site URL (e.g. `https://your-app.web.app`).
3. Enter the **GoDaddy domain** you already own.
4. Click **Build DNS plan** (always safe) or uncheck dry-run and **Publish to GoDaddy**.
5. Provide GoDaddy API key/secret in the form, or set server env:
   - `GODADDY_API_KEY`
   - `GODADDY_API_SECRET`

The app writes `www` CNAME → Studio host, optionally forwards apex → `www`, and can add a verification TXT. You must also add the custom domain inside Google Studio / Firebase so SSL can issue.

## VP Delivery Studio (share screen in a meeting)

Use this when you sit with VP R&D (You), share your screen, explain a DevOps task, and have the VP deliver it.

1. Open `/studio` and click **Start studio session** (unlocks voice).
2. Click **Share screen** and pick the window/tab to share.
3. Frames are captured automatically so the VP has visual evidence.
4. Type or hold the mic and explain the DevOps task (you are **Me / CEO**).
5. Click **VP: Deliver to DevOps** (or say “deliver now”).
6. The VP creates an assigned task, attaches the latest screen frame as evidence, and posts to `#devops`.

Honest limit: without a live vision LLM key, the VP “sees” via stored screen frames + your spoken/typed briefing (frames are attached as task evidence).

## Use the meeting

1. Open the portal and click **Enter meeting room**.
2. Click **Start meeting with voice** (required once — browsers block autoplay).
3. Choose **Speak as**:
   - **Me (CEO Chanan)** — you speak as the CEO
   - **You (VP R&D)** — speak as VP R&D Super Admin
4. Type a message or hold **Hold to talk**.
5. Agents reply live with **human neural voices** and professional portraits.
6. Click **Test voice** to hear Sofia Marchetti (Executive Assistant).

## Why voice was silent before

Chrome/Safari block speech until the user clicks once. The new unlock screen fixes that.

## Portraits

Professional photoreal portraits are served from `/static/assets/portraits/` for every agent, including:

- Chanan Zevin (CEO / Me)
- Sofia Marchetti (Executive Assistant)
- VP R&D (You)
