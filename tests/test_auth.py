# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_register_user(client: TestClient, db: Session):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword123",
            "password_confirm": "newpassword123",
            "full_name": "New User",
            "daily_goal": 10
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "password" not in data


def test_register_duplicate_username(client: TestClient, test_user: dict):
    """Var olan kullanıcı adı ile kayıt testi"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user["username"],
            "email": "another@example.com",
            "password": "password",
            "password_confirm": "password"
        }
    )

    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_login(client: TestClient, test_user: dict):
    """Test user login"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["username"],
            "password": "testpassword"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == test_user["username"]


def test_login_wrong_password(client: TestClient, test_user: dict):
    """Yanlış şifre ile giriş testi"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["username"],
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_get_current_user(client: TestClient, test_user: dict):
    """Mevcut kullanıcı bilgilerini alma testi"""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]


def test_reset_password(client: TestClient, test_user: dict):
    """Şifre sıfırlama testi"""
    response = client.post(
        "/api/v1/auth/reset-password",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "old_password": "testpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }
    )

    assert response.status_code == 200
    assert "Password updated successfully" in response.json()["message"]

    # Yeni şifre ile giriş yapabildiğimizi kontrol et
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["username"],
            "password": "newpassword123"
        }
    )

    assert login_response.status_code == 200


def test_unauthorized_access(client: TestClient):
    """Yetkisiz erişim testi"""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401