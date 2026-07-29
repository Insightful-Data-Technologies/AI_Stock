"""AI Capital App Launch Center — local hub on port 4720."""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent / "static"
HUB_PORT = int(os.environ.get("HUB_PORT", "4720"))
MEETING_PORT = int(os.environ.get("MEETING_PORT", "3000"))
MEETING_URL = f"http://127.0.0.1:{MEETING_PORT}"
PID_FILE = Path(os.environ.get("MEETING_PID_FILE", "/tmp/ai_capital_meeting_3000.pid"))

app = FastAPI(title="AI Capital App Launch Center", version="1.0.0")

_meeting_proc: Optional[subprocess.Popen] = None


class LaunchRequest(BaseModel):
    id: str = "one_on_one"


def _port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((host, port)) == 0


def _meeting_healthy() -> bool:
    if not _port_open(MEETING_PORT):
        return False
    try:
        with httpx.Client(timeout=1.5) as client:
            res = client.get(f"{MEETING_URL}/api/health")
            if res.status_code != 200:
                return False
            return bool(res.json().get("ok"))
    except Exception:
        return False


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
    if _meeting_healthy():
        return {"started": False, "already_running": True, "port": MEETING_PORT}

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["ORG_DATA_DIR"] = env.get("ORG_DATA_DIR", "/tmp/org_platform_data_launch")
    env["PORT"] = str(MEETING_PORT)
    Path(env["ORG_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "org_platform.api.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(MEETING_PORT),
    ]
    log_path = Path("/tmp/ai_capital_meeting_3000.log")
    log_f = open(log_path, "ab", buffering=0)
    _meeting_proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    _write_pid(_meeting_proc.pid)

    deadline = time.time() + 20
    while time.time() < deadline:
        if _meeting_proc.poll() is not None:
            raise RuntimeError(
                f"Meeting server exited early (code {_meeting_proc.returncode}). See {log_path}"
            )
        if _meeting_healthy():
            return {
                "started": True,
                "already_running": False,
                "port": MEETING_PORT,
                "pid": _meeting_proc.pid,
                "log": str(log_path),
            }
        time.sleep(0.35)

    raise RuntimeError(f"Meeting server did not become healthy on :{MEETING_PORT}. See {log_path}")


@app.get("/api/hub")
def hub_info() -> Dict[str, Any]:
    return {
        "ok": True,
        "name": "AI Capital — App Launch Center",
        "port": HUB_PORT,
        "meeting_port": MEETING_PORT,
        "mode": "local_launch_only",
        "stores_passwords": False,
    }


@app.get("/api/apps/status")
def apps_status() -> Dict[str, Any]:
    healthy = _meeting_healthy()
    return {
        "apps": [
            {
                "id": "one-on-one",
                "title": "One on One Meeting",
                "port": MEETING_PORT,
                "path": "/meeting-simulation.html",
                "on": healthy,
                "url": f"{MEETING_URL}/meeting-simulation.html",
            },
            {
                "id": "war-room",
                "title": "Multi-Agent War Room",
                "port": MEETING_PORT,
                "path": "/",
                "on": healthy,
                "url": f"{MEETING_URL}/",
            },
        ]
    }


@app.post("/api/apps/launch")
def launch_app(body: LaunchRequest) -> Dict[str, Any]:
    key = (body.id or "one_on_one").strip().lower().replace("-", "_")
    if key not in {"one_on_one", "war_room", "one_on_one_meeting"}:
        raise HTTPException(400, f"Unknown app id: {body.id}")
    try:
        start = _start_meeting_server()
    except Exception as exc:
        raise HTTPException(500, str(exc)) from exc

    if key in {"one_on_one", "one_on_one_meeting"}:
        url = f"{MEETING_URL}/meeting-simulation.html"
        message = "One on One Meeting launched on port 3000"
    else:
        url = f"{MEETING_URL}/"
        message = "Multi-Agent War Room launched on port 3000"

    return {
        "ok": True,
        "message": message,
        "url": url,
        "start": start,
        "status": "On" if _meeting_healthy() else "Starting",
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
