"""AI Capital App Launch Center + Meeting platform — everything on port 4720."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HUB_PORT = int(os.environ.get("HUB_PORT", "4720"))

os.environ.setdefault("ORG_DATA_DIR", os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data_launch"))
Path(os.environ["ORG_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

from org_platform.api.app import app as meeting_app  # noqa: E402

# Parent app owns hub APIs + /apps UI; meeting platform is mounted at "/".
app = FastAPI(
    title="AI Capital — Launch Center + Meetings",
    version="3.0.0",
    description="Single-port stack on 4720: Launch Center, Meeting 41 B, 1:1, dashboards",
)


class LaunchRequest(BaseModel):
    id: str = "one_on_one"


def _base() -> str:
    return f"http://127.0.0.1:{HUB_PORT}"


def _app_rows() -> List[Dict[str, Any]]:
    base = _base()
    return [
        {
            "id": "general-dashboard",
            "title": "General dashboard",
            "port": HUB_PORT,
            "path": "/dashboard",
            "on": True,
            "url": f"{base}/dashboard",
        },
        {
            "id": "meeting-room",
            "title": "Meeting Room",
            "port": HUB_PORT,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
        },
        {
            "id": "meeting-41b",
            "title": "Meeting Room · AI Cinema",
            "port": HUB_PORT,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
        },
        {
            "id": "one-on-one",
            "title": "One on One Meeting",
            "port": HUB_PORT,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
        },
        {
            "id": "war-room",
            "title": "Multi-Agent War Room",
            "port": HUB_PORT,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
        },
    ]


def _launch_url(key: str) -> tuple[str, str]:
    base = _base()
    if key in {"general_dashboard", "dashboard"}:
        return f"{base}/dashboard", f"General dashboard on :{HUB_PORT}"
    if key in {
        "one_on_one",
        "one_on_one_meeting",
        "meeting_41b",
        "meeting41b",
        "meeting_room",
        "war_room",
    }:
        return f"{base}/meeting-room", f"Meeting Room on :{HUB_PORT}"
    return f"{base}/meeting-room", f"Meeting Room on :{HUB_PORT}"


@app.get("/apps")
@app.get("/apps/")
def launch_center() -> FileResponse:
    """App Launch Center UI (same process / port as meetings)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/hub")
def hub_info() -> Dict[str, Any]:
    return {
        "ok": True,
        "name": "AI Capital — App Launch Center",
        "port": HUB_PORT,
        "meeting_port": HUB_PORT,
        "preferred_ports": [HUB_PORT],
        "fallback_port": None,
        "mode": "single_port_embedded",
        "stores_passwords": False,
        "apps_path": "/apps",
    }


@app.get("/api/apps/status")
def apps_status() -> Dict[str, Any]:
    return {
        "apps": _app_rows(),
        "preferred_ports": [HUB_PORT],
        "active_port": HUB_PORT,
        "next_bind_port": HUB_PORT,
        "embedded": True,
    }


@app.post("/api/apps/launch")
def launch_app(body: LaunchRequest) -> Dict[str, Any]:
    key = (body.id or "one_on_one").strip().lower().replace("-", "_")
    if key not in {
        "one_on_one",
        "war_room",
        "one_on_one_meeting",
        "general_dashboard",
        "dashboard",
        "meeting_41b",
        "meeting41b",
        "meeting_room",
    }:
        raise HTTPException(400, f"Unknown app id: {body.id}")
    url, message = _launch_url(key)
    return {
        "ok": True,
        "message": message,
        "url": url,
        "port": HUB_PORT,
        "start": {
            "started": False,
            "already_running": True,
            "port": HUB_PORT,
            "embedded": True,
            "preferred_ports": [HUB_PORT],
        },
        "status": "On",
    }


@app.post("/api/apps/stop")
def stop_meeting() -> Dict[str, Any]:
    return {
        "ok": True,
        "stopped": False,
        "message": f"Meetings are embedded on :{HUB_PORT}. Stop the hub process to shut down.",
    }


# Meeting platform (41 B, 1:1, dashboards, studio, APIs) on the same port.
app.mount("/", meeting_app)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app_launch_center.hub:app",
        host="0.0.0.0",
        port=HUB_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
