"""Load key=value pairs from a .env file into os.environ (no secret logging)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List


def load_dotenv(paths: Iterable[str | Path] | None = None) -> List[str]:
    """Load first existing .env path; do not override already-set env vars."""
    candidates = list(paths or [])
    if not candidates:
        root = Path(__file__).resolve().parents[2]
        candidates = [root / ".env", Path.cwd() / ".env"]
    loaded: List[str] = []
    for raw in candidates:
        path = Path(raw)
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, val = s.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if not key:
                continue
            if key not in os.environ or os.environ.get(key, "") == "":
                os.environ[key] = val
        loaded.append(str(path))
        break
    return loaded
