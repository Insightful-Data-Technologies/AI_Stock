"""Central platform state hub."""
from __future__ import annotations

import os
from pathlib import Path

from org_platform.store.audit import AuditLog
from org_platform.store.email_store import EmailStore
from org_platform.store.meetings import MeetingStore
from org_platform.store.messaging import MessagingStore
from org_platform.store.tasks import TaskStore


class Platform:
    def __init__(self, data_dir: str | None = None):
        self.data_dir = Path(data_dir or os.environ.get("ORG_DATA_DIR", "/tmp/org_platform_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(self.data_dir / "audit.json")
        self.messages = MessagingStore(self.data_dir / "messages.json")
        self.email = EmailStore(self.data_dir / "email.json")
        self.tasks = TaskStore(self.data_dir / "tasks.json")
        self.meetings = MeetingStore(str(self.data_dir))
        self.comm_results: dict = {}

    def reset_comm_results(self) -> None:
        self.comm_results = {}


PLATFORM = Platform()


def get_platform() -> Platform:
    return PLATFORM


def rebind(data_dir: str) -> Platform:
    global PLATFORM
    PLATFORM = Platform(data_dir)
    return PLATFORM
