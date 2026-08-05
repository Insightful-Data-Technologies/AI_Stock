"""Migrated Create Content tools in Site Editor."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("ORG_DATA_DIR", str(tmp_path / "org_data"))
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import importlib
    from org_platform.api import app as app_mod

    importlib.reload(app_mod)
    return TestClient(app_mod.app)


def test_page_has_migrated_content_tools(client):
    page = client.get("/site-editor")
    assert page.status_code == 200
    for label in [
        "Articles",
        "Create Text",
        "Create MD Document",
        "Image Creation",
        "Canva Studio",
        "Keyboard Fix",
    ]:
        assert label in page.text
    assert "Not yet migrated" not in page.text
    assert "still available in the legacy dashboard" not in page.text


def test_articles_and_create_text(client):
    art = client.post(
        "/api/site-editor/articles",
        json={"topic": "Yields", "notes": "Keep short", "tone": "institutional"},
    ).json()
    assert art["ok"] is True
    assert art["article"]
    assert art["document"]["id"].startswith("MD-")

    txt = client.post(
        "/api/site-editor/create-text",
        json={"prompt": "Write one sentence on equities.", "tone": "professional"},
    ).json()
    assert txt["ok"] is True
    assert txt["text"]


def test_image_canva_keyboard(client):
    img = client.post(
        "/api/site-editor/images",
        json={"title": "Brief", "subtitle": "AI Capital", "style": "institutional"},
    ).json()
    assert img["ok"] is True
    assert img["url"].endswith(".svg")
    listed = client.get("/api/site-editor/images").json()["images"]
    assert listed

    canva = client.post(
        "/api/site-editor/canva",
        json={"title": "Cover", "brief": "Dark navy institutional"},
    ).json()
    assert canva["ok"] is True
    assert "canva" in canva["canva_site_url"]

    kb = client.post(
        "/api/site-editor/keyboard-fix",
        json={"text": "akuo", "mode": "en_to_he"},
    ).json()
    assert kb["ok"] is True
    assert kb["fixed"]
