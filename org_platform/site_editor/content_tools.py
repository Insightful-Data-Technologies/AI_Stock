"""Create Content tools migrated into Site Editor CMS."""
from __future__ import annotations

import html
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from org_platform.content_studio.llm import content_studio_complete
from org_platform.site_editor import store as site_store

CANVA_SITE_URL = os.getenv(
    "CANVA_SITE_URL",
    "https://aizevinstocks.my.canva.site/stocks",
)
CANVA_CREATE_URL = os.getenv("CANVA_CREATE_URL", "https://www.canva.com/")

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
IMAGE_DIR = STATIC_DIR / "assets" / "site-editor" / "images"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", (text or "image").strip())[:48].strip("-")
    return s or "image"


def create_article(topic: str, notes: str = "", tone: str = "institutional") -> Dict[str, Any]:
    topic_s = (topic or "Market note").strip()
    notes_s = (notes or "").strip()
    seed = (
        f"# {topic_s}\n\n"
        f"Write an institutional financial article.\n\n"
        f"Notes:\n{notes_s or '- Lead with the market-moving fact.'}\n"
    )
    result = content_studio_complete(mode="rewrite", text=seed, tone=tone or "institutional")
    article_text = result.get("text") or seed
    doc = site_store.create_md_document(title=f"Article · {topic_s}", content=article_text)
    site_store.log_activity("create_article", {"doc_id": doc["id"], "topic": topic_s})
    return {
        "ok": True,
        "article": article_text,
        "document": doc,
        "provider": result.get("provider"),
    }


def create_text(prompt: str, tone: str = "professional") -> Dict[str, Any]:
    prompt_s = (prompt or "").strip()
    if not prompt_s:
        raise ValueError("Text prompt is empty")
    result = content_studio_complete(mode="rewrite", text=prompt_s, tone=tone or "professional")
    text_out = result.get("text") or prompt_s
    doc = site_store.create_md_document(title="Create Text", content=text_out)
    site_store.log_activity("create_text", {"doc_id": doc["id"]})
    return {"ok": True, "text": text_out, "document": doc, "provider": result.get("provider")}


def create_image(title: str, subtitle: str = "", style: str = "institutional") -> Dict[str, Any]:
    """Generate a branded SVG visual (works offline; no Azure image deployment required)."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    title_s = html.escape((title or "Insightful visual").strip()[:80])
    sub_s = html.escape((subtitle or "Insightful Data Technologies – 2.o AI").strip()[:120])
    style_l = (style or "institutional").lower()
    if style_l == "warm":
        c1, c2, accent = "#2a1c14", "#4a3224", "#c4a35a"
    elif style_l == "market":
        c1, c2, accent = "#0b1a14", "#123028", "#5fbf7a"
    else:
        c1, c2, accent = "#0b1220", "#1a2a44", "#3b82f6"

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)"/>
  <circle cx="1080" cy="140" r="180" fill="{accent}" fill-opacity="0.18"/>
  <circle cx="180" cy="580" r="220" fill="{accent}" fill-opacity="0.12"/>
  <text x="80" y="120" fill="#93a4bd" font-family="Arial, sans-serif" font-size="28">Site Editor · Image Creation</text>
  <text x="80" y="320" fill="#e8eef8" font-family="Arial, sans-serif" font-size="64" font-weight="700">{title_s}</text>
  <text x="80" y="390" fill="#c9d6e6" font-family="Arial, sans-serif" font-size="30">{sub_s}</text>
  <rect x="80" y="430" width="180" height="8" rx="4" fill="{accent}"/>
  <text x="80" y="660" fill="#8fa0b5" font-family="Arial, sans-serif" font-size="22">Insightful Data Technologies – 2.o AI</text>
</svg>
"""
    image_id = f"IMG-{uuid.uuid4().hex[:8]}"
    filename = f"{image_id}-{_slug(title)}.svg"
    path = IMAGE_DIR / filename
    path.write_text(svg, encoding="utf-8")
    url = f"/static/assets/site-editor/images/{filename}"
    site_store.log_activity("create_image", {"image_id": image_id, "url": url, "title": title_s})
    return {
        "ok": True,
        "image_id": image_id,
        "title": title,
        "subtitle": subtitle,
        "style": style_l,
        "url": url,
        "path": str(path),
        "created_at": _now(),
    }


def list_images() -> List[Dict[str, Any]]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(IMAGE_DIR.glob("*.svg"), key=lambda p: p.stat().st_mtime, reverse=True):
        rows.append(
            {
                "filename": path.name,
                "url": f"/static/assets/site-editor/images/{path.name}",
                "bytes": path.stat().st_size,
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            }
        )
    return rows[:40]


def canva_studio(brief: str = "", title: str = "") -> Dict[str, Any]:
    title_s = (title or "Canva brief").strip()
    brief_s = (brief or "Institutional market visual for Insightful Data Technologies.").strip()
    doc = site_store.create_md_document(
        title=f"Canva · {title_s}",
        content=(
            f"# Canva Studio brief\n\n"
            f"**Title:** {title_s}\n\n"
            f"## Creative brief\n{brief_s}\n\n"
            f"## Open\n"
            f"- Live site: {CANVA_SITE_URL}\n"
            f"- Create in Canva: {CANVA_CREATE_URL}\n"
        ),
    )
    site_store.log_activity("canva_studio", {"doc_id": doc["id"], "title": title_s})
    return {
        "ok": True,
        "title": title_s,
        "brief": brief_s,
        "document": doc,
        "canva_site_url": CANVA_SITE_URL,
        "canva_create_url": CANVA_CREATE_URL,
    }
