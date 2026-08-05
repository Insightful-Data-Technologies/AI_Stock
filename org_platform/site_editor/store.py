"""Site Editor CMS — local JSON workspace (tickets + markdown docs)."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DATA_ROOT = Path(os.getenv("ORG_DATA_DIR", "/tmp/org_platform_data_launch")) / "site_editor"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("tickets.json", "documents.json", "activity.json"):
        path = DATA_ROOT / name
        if not path.exists():
            path.write_text("[]", encoding="utf-8")


def _read(name: str) -> List[Dict[str, Any]]:
    _ensure()
    path = DATA_ROOT / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write(name: str, rows: List[Dict[str, Any]]) -> None:
    _ensure()
    (DATA_ROOT / name).write_text(json.dumps(rows, indent=2), encoding="utf-8")


def _log(action: str, detail: Dict[str, Any]) -> None:
    rows = _read("activity.json")
    rows.insert(0, {"id": str(uuid.uuid4())[:8], "at": _now(), "action": action, **detail})
    _write("activity.json", rows[:200])


def list_tickets() -> List[Dict[str, Any]]:
    return _read("tickets.json")


def create_ticket(title: str, body: str = "", priority: str = "P2") -> Dict[str, Any]:
    rows = list_tickets()
    item = {
        "id": f"T-{str(uuid.uuid4())[:8]}",
        "title": (title or "Untitled ticket").strip(),
        "body": (body or "").strip(),
        "priority": priority or "P2",
        "status": "open",
        "created_at": _now(),
    }
    rows.insert(0, item)
    _write("tickets.json", rows)
    _log("create_ticket", {"ticket_id": item["id"], "title": item["title"]})
    return item


def list_documents() -> List[Dict[str, Any]]:
    return _read("documents.json")


def create_md_document(title: str, content: str = "") -> Dict[str, Any]:
    rows = list_documents()
    safe_title = (title or "Untitled").strip()
    item = {
        "id": f"MD-{str(uuid.uuid4())[:8]}",
        "title": safe_title,
        "content": content or f"# {safe_title}\n\n",
        "created_at": _now(),
        "updated_at": _now(),
    }
    rows.insert(0, item)
    _write("documents.json", rows)
    _log("create_md", {"doc_id": item["id"], "title": item["title"]})
    return item


def update_md_document(doc_id: str, content: str, title: Optional[str] = None) -> Dict[str, Any]:
    rows = list_documents()
    for row in rows:
        if row.get("id") == doc_id:
            if title is not None:
                row["title"] = title.strip() or row["title"]
            row["content"] = content
            row["updated_at"] = _now()
            _write("documents.json", rows)
            _log("update_md", {"doc_id": doc_id})
            return row
    raise KeyError(doc_id)


def list_activity() -> List[Dict[str, Any]]:
    return _read("activity.json")


def log_activity(action: str, detail: Optional[Dict[str, Any]] = None) -> None:
    _log(action, detail or {})


def project_details() -> Dict[str, Any]:
    return {
        "company": "Insightful Data Technologies – 2.o AI",
        "product": "Site Editor CMS",
        "ceo": "Chanan Zevin",
        "modules": [
            "Company Core",
            "Create Content",
            "Run Pipeline",
            "Operations",
            "Documents",
            "Activity Reports",
        ],
        "tickets": len(list_tickets()),
        "documents": len(list_documents()),
        "data_dir": str(DATA_ROOT),
    }
