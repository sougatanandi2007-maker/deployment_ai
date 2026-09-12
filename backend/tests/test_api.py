import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "providers" in data
    assert "vercel" in data["providers"]
    assert "render" in data["providers"]

def test_providers_status_endpoint():
    resp = client.get("/api/config/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "github" in data
    assert "vercel" in data

def test_deploy_validation():
    # Attempting to deploy without confirmation should return 400
    resp = client.post("/api/deploy", json={
        "repo_url": "https://github.com/example/repo",
        "platform": "vercel",
        "user_confirmed": False
    })
    assert resp.status_code == 400

    # Attempting to deploy with unsafe command should return 400
    resp_unsafe = client.post("/api/deploy", json={
        "repo_url": "https://github.com/example/repo",
        "platform": "vercel",
        "user_confirmed": True,
        "build_command": "npm run build; rm -rf /"
    })
    assert resp_unsafe.status_code == 400
    assert "unsafe" in resp_unsafe.json()["detail"].lower()
