"""Immutable-style append-only audit trail."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text("[]")

    def append(self, event_type: str, actor_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "ts": _utcnow(),
            "event_type": event_type,
            "actor_id": actor_id,
            "payload": payload,
        }
        with self._lock:
            data = json.loads(self.path.read_text() or "[]")
            data.append(event)
            self.path.write_text(json.dumps(data, indent=2))
        return event

    def list(self, limit: int = 200, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            data = json.loads(self.path.read_text() or "[]")
        if event_type:
            data = [e for e in data if e.get("event_type") == event_type]
        return list(reversed(data[-limit:]))
