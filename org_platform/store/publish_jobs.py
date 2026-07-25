"""Persist domain publish jobs (no secrets stored)."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PublishJobStore:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.data_dir / "publish_jobs.json"
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text(json.dumps({"jobs": {}}, indent=2))

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text())

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            job = {
                "id": str(uuid.uuid4()),
                "created_at": _utcnow(),
                **payload,
            }
            data["jobs"][job["id"]] = job
            self._save(data)
            return job

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._load()["jobs"].get(job_id)

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = list(self._load()["jobs"].values())
        jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
        return jobs
