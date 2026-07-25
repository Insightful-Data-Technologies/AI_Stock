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
- Meeting room: https://cons-jon-schedules-beaver.trycloudflare.com/meeting/565ea73f-91f2-4dc1-b42c-2c76e7844647

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
