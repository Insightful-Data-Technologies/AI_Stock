"""Meeting persistence — memory primary, Redis optional, Firestore adapter stub."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MeetingStore:
    def __init__(self, data_dir: Optional[str] = None):
        self._lock = threading.RLock()
        self.data_dir = Path(data_dir or os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.meetings: Dict[str, Dict[str, Any]] = {}
        self._redis = None
        self._init_redis()
        self._load_disk()

    def _init_redis(self) -> None:
        url = os.environ.get("REDIS_URL", "").strip()
        if not url:
            return
        try:
            import redis  # type: ignore

            client = redis.from_url(url, decode_responses=True, socket_connect_timeout=1.5)
            client.ping()
            self._redis = client
        except Exception:
            self._redis = None

    def _load_disk(self) -> None:
        path = self.data_dir / "meetings.json"
        if path.exists():
            try:
                self.meetings = json.loads(path.read_text())
            except Exception:
                self.meetings = {}

    def _persist(self) -> None:
        path = self.data_dir / "meetings.json"
        path.write_text(json.dumps(self.meetings, indent=2))
        if self._redis is not None:
            try:
                self._redis.set("org_platform:meetings", json.dumps(self.meetings))
            except Exception:
                pass

    def create_meeting(
        self,
        title: str,
        chair_id: str,
        participant_ids: List[str],
        created_by: str = "human-operator",
    ) -> Dict[str, Any]:
        with self._lock:
            mid = str(uuid.uuid4())
            meeting = {
                "id": mid,
                "title": title,
                "chair_id": chair_id,
                "participant_ids": participant_ids,
                "created_by": created_by,
                "created_at": _utcnow(),
                "status": "live",
                "messages": [],
                "events": [],
                "frames": [],
                "sense": {"heard": False, "seen": False, "frame_count": 0, "last_heard_at": None, "last_seen_at": None},
            }
            self.meetings[mid] = meeting
            self._persist()
            return meeting

    def list_meetings(self) -> List[Dict[str, Any]]:
        with self._lock:
            items = []
            for m in self.meetings.values():
                items.append(
                    {
                        "id": m["id"],
                        "title": m["title"],
                        "chair_id": m["chair_id"],
                        "status": m["status"],
                        "created_at": m["created_at"],
                        "message_count": len(m.get("messages", [])),
                        "participant_ids": m.get("participant_ids", []),
                    }
                )
            items.sort(key=lambda x: x["created_at"], reverse=True)
            return items

    def get(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.meetings.get(meeting_id)

    def append_message(self, meeting_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            m = self.meetings[meeting_id]
            message = {**message, "id": message.get("id") or str(uuid.uuid4())}
            m["messages"].append(message)
            self._persist()
            return message

    def append_events(self, meeting_id: str, events: List[Dict[str, Any]]) -> None:
        with self._lock:
            m = self.meetings[meeting_id]
            m.setdefault("events", []).extend(events)
            self._persist()

    def mark_heard(self, meeting_id: str) -> Dict[str, Any]:
        with self._lock:
            m = self.meetings[meeting_id]
            sense = m.setdefault(
                "sense",
                {"heard": False, "seen": False, "frame_count": 0, "last_heard_at": None, "last_seen_at": None},
            )
            sense["heard"] = True
            sense["last_heard_at"] = _utcnow()
            self._persist()
            return m

    def add_frame(self, meeting_id: str, data_url: str, note: str = "", source: str = "camera") -> Dict[str, Any]:
        """Persist a browser-captured camera/screen frame (data URL) so the agent can 'see'."""
        import base64
        import re

        with self._lock:
            m = self.meetings[meeting_id]
            frames_dir = self.data_dir / "meeting_frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            match = re.match(r"^data:(image/(png|jpeg|jpg));base64,(.+)$", data_url, re.I | re.S)
            if not match:
                raise ValueError("data_url must be image/png or image/jpeg base64 data URL")
            ext = "jpg" if match.group(2).lower() in {"jpeg", "jpg"} else "png"
            raw = base64.b64decode(match.group(3))
            if len(raw) < 64:
                raise ValueError("frame too small")
            fid = str(uuid.uuid4())
            path = frames_dir / f"{meeting_id}_{fid}.{ext}"
            path.write_bytes(raw)
            frame = {
                "id": fid,
                "path": f"/api/meetings/frames/{meeting_id}/{fid}.{ext}",
                "bytes": len(raw),
                "note": note,
                "source": source,
                "ts": _utcnow(),
            }
            m.setdefault("frames", []).append(frame)
            sense = m.setdefault(
                "sense",
                {"heard": False, "seen": False, "frame_count": 0, "last_heard_at": None, "last_seen_at": None},
            )
            sense["seen"] = True
            sense["frame_count"] = len(m["frames"])
            sense["last_seen_at"] = frame["ts"]
            self._persist()
            return frame

    def frame_file(self, meeting_id: str, filename: str) -> Optional[Path]:
        direct = self.data_dir / "meeting_frames" / f"{meeting_id}_{filename}"
        if direct.exists():
            return direct
        m = self.meetings.get(meeting_id)
        if not m:
            return None
        for f in m.get("frames", []):
            if f.get("id") and filename.startswith(f["id"]):
                candidate = self.data_dir / "meeting_frames" / f"{meeting_id}_{filename}"
                return candidate if candidate.exists() else None
        return None

    def end_meeting(self, meeting_id: str) -> Dict[str, Any]:
        with self._lock:
            m = self.meetings[meeting_id]
            m["status"] = "ended"
            m["ended_at"] = _utcnow()
            self._persist()
            return m

    def backend_info(self) -> Dict[str, Any]:
        return {
            "primary": "memory+disk",
            "disk_path": str(self.data_dir / "meetings.json"),
            "redis_connected": self._redis is not None,
            "firestore": "adapter_ready_requires_adc",
        }


STORE = MeetingStore()
