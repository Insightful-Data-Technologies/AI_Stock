"""Slack-compatible company messaging channels."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


REQUIRED_CHANNELS = [
    ("executive-management", "Executive Management"),
    ("company-announcements", "Company Announcements"),
    ("project-management", "Project Management"),
    ("development", "Development"),
    ("qa", "QA"),
    ("devops", "DevOps"),
    ("it-support", "IT Support"),
    ("production-incidents", "Production Incidents"),
    ("release-approvals", "Release Approvals"),
    ("agent-reports", "Agent Reports"),
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessagingStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            channels = {
                cid: {
                    "id": cid,
                    "name": name,
                    "messages": [],
                }
                for cid, name in REQUIRED_CHANNELS
            }
            self.path.write_text(json.dumps({"channels": channels}, indent=2))

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text())

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def list_channels(self) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._load()
            out = []
            for c in data["channels"].values():
                out.append(
                    {
                        "id": c["id"],
                        "name": c["name"],
                        "message_count": len(c["messages"]),
                    }
                )
            return out

    def post(
        self,
        channel_id: str,
        sender_id: str,
        sender_name: str,
        text: str,
        *,
        thread_id: Optional[str] = None,
        mentions: Optional[List[str]] = None,
        priority: str = "normal",
        attachments: Optional[List[Dict[str, Any]]] = None,
        escalation_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            if channel_id not in data["channels"]:
                raise KeyError(channel_id)
            msg = {
                "id": str(uuid.uuid4()),
                "channel_id": channel_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "text": text,
                "ts": _utcnow(),
                "thread_id": thread_id,
                "mentions": mentions or [],
                "priority": priority,
                "escalation_label": escalation_label,
                "attachments": attachments or [],
                "delivery_status": "delivered",
                "acks": [],
            }
            data["channels"][channel_id]["messages"].append(msg)
            self._save(data)
            return msg

    def ack(self, channel_id: str, message_id: str, agent_id: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            for m in data["channels"][channel_id]["messages"]:
                if m["id"] == message_id:
                    if agent_id not in m["acks"]:
                        m["acks"].append(agent_id)
                    m["delivery_status"] = "acked"
                    self._save(data)
                    return m
            raise KeyError(message_id)

    def history(self, channel_id: str, limit: int = 100, q: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._load()
            msgs = data["channels"][channel_id]["messages"]
            if q:
                ql = q.lower()
                msgs = [m for m in msgs if ql in m["text"].lower() or ql in m["sender_name"].lower()]
            return msgs[-limit:]
