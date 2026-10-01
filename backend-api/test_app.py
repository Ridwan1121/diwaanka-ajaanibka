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

def test_admin_demo_login():
    response = client.post("/token", data={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"

def test_login_fail():
    response = client.post("/token", data={
        "username": "wrong",
        "password": "wrong"
    })
    assert response.status_code == 401

def test_unauthorized_scan():
    response = client.post("/scan-face/")
    assert response.status_code == 401

def test_detect_faces_requires_authentication():
    response = client.post("/detect-faces/")
    assert response.status_code == 401

def test_scan_rejects_invalid_image():
    login = client.post("/token", data={
        "username": "Ridwan",
        "password": "AKIID12345"
    })
    response = client.post(
        "/scan-face/",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 400

def test_detect_faces_rejects_invalid_image():
    login = client.post("/token", data={
        "username": "Ridwan",
        "password": "AKIID12345"
    })
    response = client.post(
        "/detect-faces/",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        files={"file": ("invalid.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 400
