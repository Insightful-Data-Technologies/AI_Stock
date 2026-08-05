# AI Capital — Dash 52 / Content Studio

Primary port: **4720** (same Launch Center hub). Optional alias: **8502** (replaces the old Claude stub UI).

## Open
- `http://127.0.0.1:4720/dash52` — Dash 52 command center (top Menu dropdown)
- `http://127.0.0.1:4720/content-studio` — Content Studio (all tools live)
- `http://127.0.0.1:8502/content-studio` — same Content Studio via Dash 52 alias
- Launch Center → **Dash 52** / **Content Studio**

## Run
```bash
bash app_launch_center/run_hub.sh
# optional dedicated alias on 8502 (use this instead of the old Streamlit / Claude stub):
bash dash52/run.sh
# or: python app/gpt52_dashboard_app.py
```

## Content Studio dropdown (fully migrated — no red stub)
Writing · Translate · Articles · Create Text · Create MD Document · Image Creation · Canva Studio · Keyboard Fix
