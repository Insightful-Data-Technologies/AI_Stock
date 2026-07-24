"""Task lifecycle store per SRS §13."""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path


ACTIVE = {
    "created",
    "assigned",
    "acknowledged",
    "in_progress",
    "review",
    "qa",
    "approved",
    "blocked",
    "rejected",
    "needs_clarification",
    "escalated",
}
TERMINAL = {"completed", "rolled_back", "cancelled"}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self.path.write_text(json.dumps({"tasks": {}}, indent=2))

    def _load(self) -> Dict[str, Any]:
        return json.loads(self.path.read_text())

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            tid = payload.get("id") or f"TASK-{uuid.uuid4().hex[:8].upper()}"
            task = {
                "id": tid,
                "title": payload["title"],
                "description": payload.get("description", ""),
                "business_objective": payload.get("business_objective", ""),
                "acceptance_criteria": payload.get("acceptance_criteria", []),
                "owner": payload.get("owner"),
                "team_leader": payload.get("team_leader"),
                "priority": payload.get("priority", "P2"),
                "dependencies": payload.get("dependencies", []),
                "target_environment": payload.get("target_environment", "staging"),
                "status": "created",
                "progress_updates": [],
                "evidence": [],
                "qa_decision": None,
                "final_approval": None,
                "created_at": _utcnow(),
                "updated_at": _utcnow(),
                "completed_at": None,
                "created_by": payload.get("created_by", "system"),
            }
            data["tasks"][tid] = task
            self._save(data)
            return task

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._load()["tasks"].get(task_id)

    def list(self, status: Optional[str] = None, owner: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            tasks = list(self._load()["tasks"].values())
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if owner:
            tasks = [t for t in tasks if t.get("owner") == owner]
        tasks.sort(key=lambda t: t["updated_at"], reverse=True)
        return tasks

    def transition(self, task_id: str, status: str, actor_id: str, note: str = "") -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            task = data["tasks"][task_id]
            task["status"] = status
            task["updated_at"] = _utcnow()
            task["progress_updates"].append(
                {"ts": _utcnow(), "actor_id": actor_id, "status": status, "note": note}
            )
            if status == "completed":
                task["completed_at"] = _utcnow()
            self._save(data)
            return task

    def assign(self, task_id: str, owner: str, team_leader: str, actor_id: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            task = data["tasks"][task_id]
            task["owner"] = owner
            task["team_leader"] = team_leader
            task["status"] = "assigned"
            task["updated_at"] = _utcnow()
            task["progress_updates"].append(
                {
                    "ts": _utcnow(),
                    "actor_id": actor_id,
                    "status": "assigned",
                    "note": f"Assigned to {owner} under {team_leader}",
                }
            )
            self._save(data)
            return task

    def add_evidence(self, task_id: str, evidence: Dict[str, Any], actor_id: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            task = data["tasks"][task_id]
            item = {**evidence, "ts": _utcnow(), "actor_id": actor_id}
            task["evidence"].append(item)
            task["updated_at"] = _utcnow()
            self._save(data)
            return task

    def set_qa(self, task_id: str, decision: str, by: str, notes: str = "") -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            task = data["tasks"][task_id]
            task["qa_decision"] = {
                "decision": decision,
                "by": by,
                "notes": notes,
                "ts": _utcnow(),
            }
            task["status"] = "qa" if decision == "PASS" else ("rejected" if decision == "FAIL" else "blocked")
            if decision == "PASS":
                task["status"] = "approved"
            task["updated_at"] = _utcnow()
            self._save(data)
            return task

    def approve(self, task_id: str, by: str, note: str = "") -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            task = data["tasks"][task_id]
            task["final_approval"] = {"by": by, "note": note, "ts": _utcnow()}
            task["status"] = "completed"
            task["completed_at"] = _utcnow()
            task["updated_at"] = _utcnow()
            self._save(data)
            return task

    def stats(self) -> Dict[str, Any]:
        tasks = self.list()
        counts: Dict[str, int] = {}
        for t in tasks:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        return {"total": len(tasks), "by_status": counts}
