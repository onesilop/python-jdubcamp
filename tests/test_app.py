import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_providers_default_false(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("FACEBOOK_CLIENT_ID", raising=False)
    monkeypatch.delenv("FACEBOOK_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("APPLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("APPLE_TEAM_ID", raising=False)
    monkeypatch.delenv("APPLE_KEY_ID", raising=False)
    monkeypatch.delenv("APPLE_PRIVATE_KEY", raising=False)

    response = client.get("/auth/providers")
    assert response.status_code == 200
    assert response.json() == {"google": False, "facebook": False, "apple": False}


def test_demo_login():
    response = client.post("/auth/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "demo login successful"
    assert data["user"]["email"] == os.getenv("DEMO_EMAIL", "demo@example.com")
    assert data["user"]["provider"] == "demo"
