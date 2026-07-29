"""Company email store — simulated mailboxes explicitly labeled."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmailStore:
    """Simulated mailbox system.

    IMPORTANT: This is a SIMULATED mailbox, not a licensed Google Workspace
    or production SMTP mailbox. Licensing limitations are reported explicitly.
    """

    MODE = "SIMULATED"
    LIMITATION = (
        "No Google Workspace / SMTP credentials available in this environment. "
        "Mailboxes are simulated with full audit records and must not be presented as real mailboxes."
    )

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text(json.dumps({"mailboxes": {}, "messages": []}, indent=2))

    def ensure_mailbox(self, email: str, owner_id: str) -> Dict[str, Any]:
        with self._lock:
            data = json.loads(self.path.read_text())
            mb = data["mailboxes"].setdefault(
                email,
                {
                    "email": email,
                    "owner_id": owner_id,
                    "mode": self.MODE,
                    "limitation": self.LIMITATION,
                },
            )
            self.path.write_text(json.dumps(data, indent=2))
            return mb

    def send(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        *,
        from_id: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            data = json.loads(self.path.read_text())
            msg = {
                "id": str(uuid.uuid4()),
                "mode": self.MODE,
                "limitation": self.LIMITATION,
                "from_email": from_email,
                "from_id": from_id,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "attachments": attachments or [],
                "ts": _utcnow(),
                "status": "delivered_simulated",
            }
            data["messages"].append(msg)
            self.path.write_text(json.dumps(data, indent=2))
            return msg

    def inbox(self, email: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            data = json.loads(self.path.read_text())
            msgs = [m for m in data["messages"] if m["to_email"] == email]
            return msgs[-limit:]

    def status(self) -> Dict[str, Any]:
        with self._lock:
            data = json.loads(self.path.read_text())
            return {
                "mode": self.MODE,
                "limitation": self.LIMITATION,
                "mailbox_count": len(data["mailboxes"]),
                "message_count": len(data["messages"]),
            }
