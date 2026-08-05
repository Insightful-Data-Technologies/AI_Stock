"""VP Delivery Studio sessions — screen share frames + briefings + DevOps handoff."""
from __future__ import annotations

import base64
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class StudioStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir = self.data_dir / "studio_frames"
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "studio_sessions.json"
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text(json.dumps({"sessions": {}}, indent=2))

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text())

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def create(self, title: str, host_id: str = "ceo-chanan", vp_id: str = "vp-rd") -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            sid = str(uuid.uuid4())
            session = {
                "id": sid,
                "title": title,
                "host_id": host_id,
                "vp_id": vp_id,
                "status": "live",
                "created_at": _utcnow(),
                "screen_sharing": False,
                "frames": [],
                "messages": [],
                "briefing": None,
                "delivery": None,
            }
            data["sessions"][sid] = session
            self._save(data)
            return session

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._load()["sessions"].get(session_id)

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            items = list(self._load()["sessions"].values())
        items.sort(key=lambda s: s["created_at"], reverse=True)
        return [
            {
                "id": s["id"],
                "title": s["title"],
                "status": s["status"],
                "created_at": s["created_at"],
                "screen_sharing": s.get("screen_sharing"),
                "frame_count": len(s.get("frames", [])),
                "message_count": len(s.get("messages", [])),
                "delivery": s.get("delivery"),
            }
            for s in items
        ]

    def set_sharing(self, session_id: str, active: bool) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            s = data["sessions"][session_id]
            s["screen_sharing"] = active
            s["updated_at"] = _utcnow()
            self._save(data)
            return s

    def add_frame(self, session_id: str, data_url: str, note: str = "") -> Dict[str, Any]:
        """Persist a browser-captured screen frame (data URL)."""
        with self._lock:
            data = self._load()
            s = data["sessions"][session_id]
            fid = str(uuid.uuid4())
            # strip prefix data:image/png;base64,
            raw = data_url
            ext = "png"
            if "," in data_url:
                header, b64 = data_url.split(",", 1)
                if "jpeg" in header or "jpg" in header:
                    ext = "jpg"
                raw_bytes = base64.b64decode(b64)
            else:
                raw_bytes = base64.b64decode(data_url)
            rel = f"studio_frames/{session_id}_{fid}.{ext}"
            abs_path = self.data_dir / rel
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_bytes(raw_bytes)
            frame = {
                "id": fid,
                "ts": _utcnow(),
                "path": f"/api/studio/frames/{session_id}/{fid}.{ext}",
                "file": rel,
                "bytes": len(raw_bytes),
                "note": note,
            }
            s["frames"].append(frame)
            s["screen_sharing"] = True
            s["updated_at"] = _utcnow()
            self._save(data)
            return frame

    def frame_file(self, session_id: str, filename: str) -> Optional[Path]:
        # API filename is <frame_id>.png|jpg — stored as studio_frames/<session>_<frame_id>.ext
        direct = self.data_dir / "studio_frames" / f"{session_id}_{filename}"
        if direct.exists():
            return direct
        with self._lock:
            s = self._load()["sessions"].get(session_id)
            if not s:
                return None
            for f in s.get("frames", []):
                if f["id"] in filename or f["file"].endswith(filename):
                    p = self.data_dir / f["file"]
                    if p.exists():
                        return p
        return None

    def add_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            s = data["sessions"][session_id]
            message = {**message, "id": message.get("id") or str(uuid.uuid4()), "ts": message.get("ts") or _utcnow()}
            s["messages"].append(message)
            s["updated_at"] = _utcnow()
            self._save(data)
            return message

    def set_briefing(self, session_id: str, briefing: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            s = data["sessions"][session_id]
            s["briefing"] = {**briefing, "ts": _utcnow()}
            self._save(data)
            return s["briefing"]

    def set_delivery(self, session_id: str, delivery: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            s = data["sessions"][session_id]
            s["delivery"] = {**delivery, "ts": _utcnow()}
            s["status"] = "delivered"
            self._save(data)
            return s["delivery"]
