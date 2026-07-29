"""AI Capital App Launch Center — local hub on port 4720."""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HUB_PORT = int(os.environ.get("HUB_PORT", "4720"))
# Prefer 3000; if taken by something else, fall back to 4050 (then nearby ports).
PREFERRED_PORTS: List[int] = [
    int(p.strip())
    for p in os.environ.get("MEETING_PORTS", "3000,4050,4051,4052,4060").split(",")
    if p.strip()
]
PID_FILE = Path(os.environ.get("MEETING_PID_FILE", "/tmp/ai_capital_meeting.pid"))
PORT_FILE = Path(os.environ.get("MEETING_PORT_FILE", "/tmp/ai_capital_meeting.port"))
LOG_PATH = Path(os.environ.get("MEETING_LOG_FILE", "/tmp/ai_capital_meeting.log"))

app = FastAPI(title="AI Capital App Launch Center", version="1.1.0")

_meeting_proc: Optional[subprocess.Popen] = None
_active_port: Optional[int] = None


class LaunchRequest(BaseModel):
    id: str = "one_on_one"


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.35)
        return sock.connect_ex((host, port)) == 0


def _meeting_healthy_on(port: int) -> bool:
    if not _port_open(port):
        return False
    try:
        with httpx.Client(timeout=1.5) as client:
            res = client.get(f"http://127.0.0.1:{port}/api/health")
            if res.status_code != 200:
                return False
            data = res.json()
            return bool(data.get("ok")) and data.get("service") == "ai-capital-enterprise-team"
    except Exception:
        return False


def _read_saved_port() -> Optional[int]:
    try:
        if PORT_FILE.exists():
            return int(PORT_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None
    return None


def _write_active_port(port: int) -> None:
    global _active_port
    _active_port = port
    PORT_FILE.write_text(str(port), encoding="utf-8")


def _clear_port_file() -> None:
    global _active_port
    _active_port = None
    try:
        PORT_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _current_meeting_port() -> Optional[int]:
    """Return port where our meeting service is healthy, if any."""
    candidates: List[int] = []
    if _active_port:
        candidates.append(_active_port)
    saved = _read_saved_port()
    if saved and saved not in candidates:
        candidates.append(saved)
    for port in PREFERRED_PORTS:
        if port not in candidates:
            candidates.append(port)
    for port in candidates:
        if _meeting_healthy_on(port):
            _write_active_port(port)
            return port
    return None


def _pick_bind_port() -> int:
    """
    Choose a free port for binding.
    If preferred port is occupied by a non-meeting process, skip to fallback (4050…).
    """
    existing = _current_meeting_port()
    if existing is not None:
        return existing
    for port in PREFERRED_PORTS:
        if not _port_open(port):
            return port
        # Port is open but not our meeting → occupied (e.g. Next.js on 3000).
        continue
    raise RuntimeError(
        f"No free meeting port among {PREFERRED_PORTS}. Free one of them or set MEETING_PORTS."
    )


def _read_pid() -> Optional[int]:
    try:
        if not PID_FILE.exists():
            return None
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _write_pid(pid: int) -> None:
    PID_FILE.write_text(str(pid), encoding="utf-8")


def _clear_pid() -> None:
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _start_meeting_server() -> Dict[str, Any]:
    global _meeting_proc
    existing = _current_meeting_port()
    if existing is not None:
        return {
            "started": False,
            "already_running": True,
            "port": existing,
            "fallback_used": existing != PREFERRED_PORTS[0],
            "preferred_ports": PREFERRED_PORTS,
        }

    port = _pick_bind_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["ORG_DATA_DIR"] = env.get("ORG_DATA_DIR", "/tmp/org_platform_data_launch")
    env["PORT"] = str(port)
    Path(env["ORG_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "org_platform.api.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
    ]
    log_f = open(LOG_PATH, "ab", buffering=0)
    _meeting_proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _write_pid(_meeting_proc.pid)
    _write_active_port(port)

    deadline = time.time() + 20
    while time.time() < deadline:
        if _meeting_proc.poll() is not None:
            _clear_port_file()
            raise RuntimeError(
                f"Meeting server exited early (code {_meeting_proc.returncode}) on :{port}. See {LOG_PATH}"
            )
        if _meeting_healthy_on(port):
            return {
                "started": True,
                "already_running": False,
                "port": port,
                "fallback_used": port != PREFERRED_PORTS[0],
                "preferred_ports": PREFERRED_PORTS,
                "pid": _meeting_proc.pid,
                "log": str(LOG_PATH),
                "skipped_busy": [p for p in PREFERRED_PORTS if p < port and _port_open(p)],
            }
        time.sleep(0.35)

    raise RuntimeError(f"Meeting server did not become healthy on :{port}. See {LOG_PATH}")


def _app_rows(port: Optional[int], healthy: bool) -> List[Dict[str, Any]]:
    display_port = port or PREFERRED_PORTS[0]
    base = f"http://127.0.0.1:{display_port}"
    return [
        {
            "id": "general-dashboard",
            "title": "General dashboard",
            "port": display_port,
            "path": "/dashboard",
            "on": healthy,
            "url": f"{base}/dashboard",
        },
        {
            "id": "one-on-one",
            "title": "One on One Meeting",
            "port": display_port,
            "path": "/meeting-simulation.html",
            "on": healthy,
            "url": f"{base}/meeting-simulation.html",
        },
        {
            "id": "war-room",
            "title": "Multi-Agent War Room",
            "port": display_port,
            "path": "/",
            "on": healthy,
            "url": f"{base}/",
        },
    ]


@app.get("/api/hub")
def hub_info() -> Dict[str, Any]:
    active = _current_meeting_port()
    return {
        "ok": True,
        "name": "AI Capital — App Launch Center",
        "port": HUB_PORT,
        "meeting_port": active or PREFERRED_PORTS[0],
        "preferred_ports": PREFERRED_PORTS,
        "fallback_port": PREFERRED_PORTS[1] if len(PREFERRED_PORTS) > 1 else None,
        "mode": "local_launch_only",
        "stores_passwords": False,
    }


@app.get("/api/apps/status")
def apps_status() -> Dict[str, Any]:
    port = _current_meeting_port()
    healthy = port is not None
    # When Off, show the next port we would try (skip busy non-meeting listeners).
    display_port = port
    if display_port is None:
        try:
            display_port = _pick_bind_port()
        except RuntimeError:
            display_port = PREFERRED_PORTS[0]
    return {
        "apps": _app_rows(display_port, healthy),
        "preferred_ports": PREFERRED_PORTS,
        "active_port": port,
        "next_bind_port": display_port,
    }


@app.post("/api/apps/launch")
def launch_app(body: LaunchRequest) -> Dict[str, Any]:
    key = (body.id or "one_on_one").strip().lower().replace("-", "_")
    if key not in {"one_on_one", "war_room", "one_on_one_meeting", "general_dashboard", "dashboard"}:
        raise HTTPException(400, f"Unknown app id: {body.id}")
    try:
        start = _start_meeting_server()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

    port = int(start["port"])
    base = f"http://127.0.0.1:{port}"
    if key in {"general_dashboard", "dashboard"}:
        url = f"{base}/dashboard"
        message = f"General dashboard on :{port}"
    elif key in {"one_on_one", "one_on_one_meeting"}:
        url = f"{base}/meeting-simulation.html"
        message = f"One on One Meeting launched on :{port}"
    else:
        url = f"{base}/"
        message = f"Multi-Agent War Room launched on :{port}"

    if start.get("fallback_used"):
        skipped = start.get("skipped_busy") or [PREFERRED_PORTS[0]]
        message += f" (preferred {skipped} busy → fallback)"

    return {
        "ok": True,
        "message": message,
        "url": url,
        "port": port,
        "start": start,
        "status": "On" if _meeting_healthy_on(port) else "Starting",
    }


@app.post("/api/apps/stop")
def stop_meeting() -> Dict[str, Any]:
    global _meeting_proc
    pid = _read_pid()
    stopped = False
    if _meeting_proc and _meeting_proc.poll() is None:
        try:
            os.killpg(os.getpgid(_meeting_proc.pid), signal.SIGTERM)
            stopped = True
        except Exception:
            _meeting_proc.terminate()
            stopped = True
        _meeting_proc = None
    elif pid:
        try:
            os.kill(pid, signal.SIGTERM)
            stopped = True
        except ProcessLookupError:
            pass
        except Exception as exc:
            raise HTTPException(500, str(exc)) from exc
    _clear_pid()
    _clear_port_file()
    return {"ok": True, "stopped": stopped}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


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
