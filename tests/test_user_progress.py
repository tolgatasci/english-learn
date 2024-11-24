# tests/test_user_progress.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User
from app.models.user_word import UserWord


def test_user_statistics(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Kullanıcı istatistikleri testi"""
    response = client.get(
        "/api/v1/users/me/statistics",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_words_learned" in data
    assert "words_in_progress" in data
    assert "completion_rate" in data
    assert "current_streak" in data
    assert "average_retention" in data


def test_update_daily_goal(client: TestClient, test_user: dict):
    """Test updating daily goal"""
    response = client.post(
        "/api/v1/users/me/daily-goal",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"goal": 15}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["daily_goal"] == 15


def test_delete_user(
        client: TestClient,
        test_user: dict,
        db: Session
):
    """Kullanıcı silme testi"""
    response = client.delete(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    # Status code kontrolü
    assert response.status_code == 204
    # Response body boş olmalı
    assert response.content == b''

    # Kullanıcının veritabanından silindiğini kontrol et
    user = db.query(User).filter(User.id == test_user["id"]).first()
    assert user is None

def test_reset_progress(
        client: TestClient,
        test_user: dict,
        test_user_words: list,
        db: Session
):
    """İlerleme sıfırlama testi"""
    response = client.post(
        "/api/v1/users/me/reset-progress",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200

    # Tüm kelimelerin sıfırlandığını kontrol et
    user_words = db.query(UserWord).filter(UserWord.user_id == test_user["id"]).all()
    for user_word in user_words:
        assert user_word.retention_level == 0
        assert user_word.confidence_level == 0
        assert not user_word.is_learned
        assert user_word.times_reviewed == 0
        assert user_word.mistakes_count == 0


def test_learning_patterns(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Öğrenme paternleri analizi testi"""
    response = client.get(
        "/api/v1/users/me/learning-patterns",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "average_retention" in data
    assert "learning_rate" in data
    assert "problem_areas" in data
    assert "best_time_to_review" in data


def test_update_user_profile(
        client: TestClient,
        test_user: dict,
        db: Session
):
    """Kullanıcı profili güncelleme testi"""
    update_data = {
        "full_name": "Updated Test User",
        "daily_goal": 20
    }

    response = client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["daily_goal"] == update_data["daily_goal"]

    # Veritabanında güncellendiğini kontrol et
    user = db.query(User).filter(User.id == test_user["id"]).first()
    assert user.full_name == update_data["full_name"]
    assert user.daily_goal == update_data["daily_goal"]