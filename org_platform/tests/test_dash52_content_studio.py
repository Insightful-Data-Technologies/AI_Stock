"""Dash 52 Content Studio — no migration stub."""
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


def test_dash52_content_studio_fully_migrated(client):
    page = client.get("/content-studio")
    assert page.status_code == 200
    assert "Content Manager" in page.text
    for label in [
        "Writing",
        "Translate",
        "Articles",
        "Create Text",
        "Create MD Document",
        "Image Creation",
        "Canva Studio",
        "Keyboard Fix",
    ]:
        assert label in page.text
    assert "NOT YET MIGRATED" not in page.text.upper()
    assert "still available in the legacy dashboard" not in page.text
    assert "gpt52_dashboard_app.py" not in page.text
    assert "Menu" in page.text
    assert "Content Manager" in page.text
    # No emoji icons in the top nav (text-only dropdowns).
    assert "🏛️" not in page.text
    assert "✍️" not in page.text


def test_dash52_home_on_hub(client):
    page = client.get("/dash52")
    assert page.status_code == 200
    assert "AI Capital — Dash 52" in page.text
    assert "Content Manager" in page.text
    assert client.get("/dash-52").status_code == 200


def test_dash52_tools_apis(client):
    assert client.post(
        "/api/site-editor/keyboard-fix",
        json={"text": "akuo", "mode": "en_to_he"},
    ).json()["ok"] is True
    assert client.post(
        "/api/site-editor/images",
        json={"title": "Dash52", "subtitle": "CMS"},
    ).json()["ok"] is True
