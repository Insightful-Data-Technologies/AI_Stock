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
