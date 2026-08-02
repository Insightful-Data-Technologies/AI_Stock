#!/usr/bin/env python3
"""Copy a local reference video into the Meeting 41 B avatar slot."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "org_platform" / "static" / "assets" / "avatar" / "agent-girl.mp4"
DEFAULTS = [
    Path(r"C:\Users\azureuser\Desktop\2026-08-03_01-01-17.mp4"),
    Path("/mnt/c/Users/azureuser/Desktop/2026-08-03_01-01-17.mp4"),
    Path.home() / "Desktop" / "2026-08-03_01-01-17.mp4",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Path to the girl reference .mp4")
    args = parser.parse_args()
    source = Path(args.source) if args.source else next((p for p in DEFAULTS if p.exists()), None)
    if source is None or not source.exists():
        print("Source video not found. Pass the path to 2026-08-03_01-01-17.mp4", file=sys.stderr)
        return 1
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEST)
    print(f"Installed avatar video → {DEST} ({DEST.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
