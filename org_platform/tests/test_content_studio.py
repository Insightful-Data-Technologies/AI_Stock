"""Content Studio rewrite / translate tests."""
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


def test_content_studio_page(client):
    page = client.get("/content-studio")
    assert page.status_code == 200
    assert "Content Studio" in page.text
    assert "Rewrite" in page.text
    assert "Translate" in page.text
    assert "Target tone" in page.text or "Target Tone" in page.text


def test_content_studio_meta(client):
    meta = client.get("/api/content-studio/meta").json()
    assert meta["ok"] is True
    assert "professional" in meta["tones"]
    assert "rewrite" in meta["modes"]


def test_rewrite_works_without_cloud(client):
    res = client.post(
        "/api/content-studio/run",
        json={
            "mode": "rewrite",
            "tone": "professional",
            "text": "Markets moved higher today on rate hopes.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["text"]
    assert "DeploymentNotFound" not in data["text"]
    assert data["provider"] == "local-fallback"


def test_translate_works_without_cloud(client):
    res = client.post(
        "/api/content-studio/run",
        json={
            "mode": "translate",
            "target_lang": "he",
            "text": "Capital allocation remains the priority.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "Capital allocation" in data["text"]


def test_empty_draft_rejected(client):
    res = client.post("/api/content-studio/run", json={"mode": "rewrite", "text": "  "})
    assert res.status_code == 400
