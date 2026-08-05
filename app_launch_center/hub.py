"""AI Capital App Launch Center + Meeting platform — buttons on 4720 or 4600."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HUB_PORT = int(os.environ.get("HUB_PORT", "4720"))
# Accept Launch Center ports the user already uses, plus CMS port 8511.
ALLOWED_PORTS = [4720, 4600, 8511, 8502]

os.environ.setdefault("ORG_DATA_DIR", os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data_launch"))
Path(os.environ["ORG_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

from org_platform.api.app import app as meeting_app  # noqa: E402

app = FastAPI(
    title="AI Capital — Launch Center + Meetings",
    version="3.1.0",
    description="Button-only Launch Center on port 4720 or 4600",
)


class LaunchRequest(BaseModel):
    id: str = "meeting_room"


def _request_port(request: Optional[Request]) -> int:
    if request is None:
        return HUB_PORT
    host = request.headers.get("host") or ""
    if ":" in host:
        try:
            return int(host.rsplit(":", 1)[-1])
        except ValueError:
            pass
    return HUB_PORT


def _base(request: Optional[Request] = None) -> str:
    port = _request_port(request)
    return f"http://127.0.0.1:{port}"


def _app_rows(request: Optional[Request] = None) -> List[Dict[str, Any]]:
    port = _request_port(request)
    base = _base(request)
    # Everything that used to show Off · 3000 (red) is forced On on this port.
    return [
        {
            "id": "general-dashboard",
            "title": "General dashboard",
            "port": port,
            "path": "/dashboard",
            "on": True,
            "url": f"{base}/dashboard",
            "color": "yellow",
        },
        {
            "id": "meeting-room",
            "title": "Meeting Room",
            "port": port,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
            "color": "yellow",
        },
        {
            "id": "one-on-one",
            "title": "One on One Meeting",
            "port": port,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
            "color": "green",
        },
        {
            "id": "forecast-one-on-one",
            "title": "Forecast 1:1 · Hear & See",
            "port": port,
            "path": "/meeting-forecast.html",
            "on": True,
            "url": f"{base}/meeting-forecast.html",
            "color": "yellow",
        },
        {
            "id": "war-room",
            "title": "Multi-Agent War Room",
            "port": port,
            "path": "/meeting-room",
            "on": True,
            "url": f"{base}/meeting-room",
            "color": "green",
        },
        {
            "id": "create-content",
            "title": "Content Manager",
            "port": port,
            "path": "/content-studio",
            "on": True,
            "url": f"{base}/content-studio",
            "color": "yellow",
        },
        {
            "id": "dash52",
            "title": "Dash 52",
            "port": port,
            "path": "/dash52",
            "on": True,
            "url": f"{base}/dash52",
            "color": "yellow",
        },
        {
            "id": "content-studio",
            "title": "Content Manager",
            "port": port,
            "path": "/content-studio",
            "on": True,
            "url": f"{base}/content-studio",
            "color": "yellow",
        },
        {
            "id": "site-editor",
            "title": "Site Editor CMS",
            "port": port,
            "path": "/site-editor",
            "on": True,
            "url": f"{base}/site-editor",
            "color": "yellow",
        },
    ]


def _launch_path(key: str) -> str:
    if key in {"general_dashboard", "dashboard"}:
        return "/dashboard"
    if key in {"dash52", "dash_52"}:
        return "/dash52"
    if key in {"create_content", "createcontent", "content_studio", "contentstudio"}:
        return "/content-studio"
    if key in {"site_editor", "siteeditor", "cms"}:
        return "/site-editor"
    if key in {"forecast", "forecast_one_on_one", "forecast_1_1", "תחזית"}:
        return "/meeting-forecast.html"
    return "/meeting-room"


@app.get("/")
@app.get("/apps")
@app.get("/apps/")
def launch_center() -> FileResponse:
    """Home = button Launch Center (4720 or 4600)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/hub")
def hub_info(request: Request) -> Dict[str, Any]:
    port = _request_port(request)
    return {
        "ok": True,
        "name": "AI Capital — App Launch Center",
        "port": port,
        "meeting_port": port,
        "preferred_ports": ALLOWED_PORTS,
        "fallback_port": 4600 if port == 4720 else 4720,
        "mode": "buttons_only",
        "stores_passwords": False,
        "apps_path": "/",
    }


@app.get("/api/apps/status")
def apps_status(request: Request) -> Dict[str, Any]:
    port = _request_port(request)
    return {
        "apps": _app_rows(request),
        "preferred_ports": ALLOWED_PORTS,
        "active_port": port,
        "next_bind_port": port,
        "embedded": True,
    }


@app.post("/api/apps/launch")
def launch_app(body: LaunchRequest, request: Request) -> Dict[str, Any]:
    key = (body.id or "meeting_room").strip().lower().replace("-", "_")
    if key not in {
        "one_on_one",
        "war_room",
        "one_on_one_meeting",
        "general_dashboard",
        "dashboard",
        "meeting_41b",
        "meeting41b",
        "meeting_room",
        "content_studio",
        "contentstudio",
        "create_content",
        "createcontent",
        "dash52",
        "dash_52",
        "site_editor",
        "siteeditor",
        "cms",
        "forecast",
        "forecast_one_on_one",
        "forecast_1_1",
    }:
        raise HTTPException(400, f"Unknown app id: {body.id}")
    path = _launch_path(key)
    port = _request_port(request)
    url = f"{_base(request)}{path}"
    return {
        "ok": True,
        "message": f"Opening {path}",
        "url": url,
        "path": path,
        "port": port,
        "start": {
            "started": False,
            "already_running": True,
            "port": port,
            "embedded": True,
            "preferred_ports": ALLOWED_PORTS,
        },
        "status": "On",
    }


@app.post("/api/apps/stop")
def stop_meeting() -> Dict[str, Any]:
    return {
        "ok": True,
        "stopped": False,
        "message": "Use the Launch Center buttons. Stop is not needed.",
    }


# Meeting pages + APIs on the same port (after Launch Center routes).
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
