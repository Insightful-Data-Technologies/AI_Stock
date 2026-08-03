# How to run the meeting room

## Everything on port 4720

Launch Center, Meeting 41 B, One on One, and dashboards share **one** process:

```bash
export PYTHONPATH=/workspace
bash app_launch_center/run_hub.sh
# or: bash org_platform/deploy/run_meeting_hub.sh
# or: bash org_platform/deploy/run_meeting_3000.sh   # now defaults to 4720
```

Open:

- http://127.0.0.1:4720/apps — **App Launch Center**
- http://127.0.0.1:4720/meeting-41b.html — **Meeting 41 B · Visuals**
- http://127.0.0.1:4720/meeting-simulation.html — Ultra Agent 1:1
- http://127.0.0.1:4720/dashboard — General dashboard
- http://127.0.0.1:4720/ — Org home / War Room

## Meeting 41 B · Visuals (camera + screen share + human avatar)

```bash
export PYTHONPATH=/workspace
bash app_launch_center/run_hub.sh
```

Then open http://127.0.0.1:4720/meeting-41b.html (or Launch Center → **Meeting 41 B**).

In the room:

1. Click **Start meeting with voice** (human female voice for the AI seat).
2. **Camera on** turns your webcam on you.
3. **Share screen** starts screen share.
4. The AI tile uses the girl human avatar (`/static/assets/avatar/agent-girl.mp4`).
5. Optional: **Upload avatar video** and choose  
   `C:\Users\azureuser\Desktop\2026-08-03_01-01-17.mp4`  
   or run `python tools/ingest_41b_avatar.py "C:/Users/azureuser/Desktop/2026-08-03_01-01-17.mp4"`.

## One on One Meeting

From Launch Center on **:4720** → **Meetings → One on One Meeting → Launch / Open Link**, or:

- http://127.0.0.1:4720/dashboard — yellow box → **Launch 1:1**
- http://127.0.0.1:4720/meeting-simulation.html

## Quick start (this environment)

```bash
export PYTHONPATH=/workspace
export ORG_DATA_DIR=/tmp/org_platform_data_srs
export PATH="$HOME/.local/bin:$PATH"
bash org_platform/deploy/run_local.sh
```

Open:

### Google Cloud Enterprise (Cloud Run — production)

- **Org home / Agents:** https://enterprise-org-meeting-184723980511.europe-west2.run.app/
- **One-on-one (green launch box on home):** click **Launch 1:1** or open a live room under `/meeting/{id}`
- **Live 1:1 room (created 2026-07-29):** https://enterprise-org-meeting-184723980511.europe-west2.run.app/meeting/882a60b4-9f97-4a53-9122-405c087faf65
- **Meeting room:** create from home, or open `/meeting/{id}`
- **VP Delivery Studio:** https://enterprise-org-meeting-184723980511.europe-west2.run.app/studio
- **Slack `#devops`:** https://enterprise-org-meeting-184723980511.europe-west2.run.app/slack
- **Dashboards:** https://enterprise-org-meeting-184723980511.europe-west2.run.app/dashboard
- **Domain Publisher:** https://enterprise-org-meeting-184723980511.europe-west2.run.app/publish
- Project: `gen-lang-client-0386540117` · Region: `europe-west2` · Service: `enterprise-org-meeting`

### Local / temporary tunnel

- **Preferred local stack (all on 4720):**
  ```bash
  bash org_platform/deploy/run_meeting_hub.sh
  ```
  Then open http://127.0.0.1:4720/apps and http://127.0.0.1:4720/meeting-41b.html
- Legacy single-service default (also 4720 now): `bash org_platform/deploy/run_meeting_3000.sh`
- If Next.js on Windows still serves an empty `meeting-simulation.html`, copy
  `website/meeting-simulation.html` into that app's `public/` folder (instant redirect to Cloud 1:1).
- Cloudflare quick tunnel (temporary only; prefer Cloud Run URL above)

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
