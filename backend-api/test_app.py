"""
Diwaanka Ajaanibka - Unit Tests
"""
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success():
    response = client.post("/token", data={
        "username": "Ridwan",
        "password": "AKIID12345"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fail():
    response = client.post("/token", data={
        "username": "wrong",
        "password": "wrong"
    })
    assert response.status_code == 401


def test_unauthorized_scan():
    response = client.post("/scan-face/")
    assert response.status_code == 401


def test_authorized_scan():
    login = client.post("/token", data={
        "username": "Ridwan",
        "password": "AKIID12345"
    })
    token = login.json()["access_token"]
    response = client.get("/stats/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
