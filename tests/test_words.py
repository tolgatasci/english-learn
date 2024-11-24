# tests/test_words.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.user import User
from app.models.word import Word
from app.models.user_word import UserWord
from app.database import get_db

def test_get_next_words(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Sıradaki kelimeleri alma testi"""
    response = client.get(
        "/api/v1/words/next-words",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "english" in data[0]
    assert "turkish" in data[0]
    assert "retention_level" in data[0]


def test_submit_word_review(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Test submitting a word review"""
    word = test_user_words[0]
    response = client.post(
        "/api/v1/words/review",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "word_id": word.word_id,
            "quality": 5,
            "response_time": 1500.0,
            "was_correct": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["word_id"] == word.word_id
    assert data["retention_level"] >= word.retention_level

def test_search_words(
        client: TestClient,
        test_user: dict,
        test_words: list
):
    """Kelime arama testi"""
    response = client.get(
        "/api/v1/words/search?query=hello",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["english"] == "hello"
    assert "learning_status" in data[0]


def test_add_to_learning(
        client: TestClient,
        test_user: dict,
        test_words: list,
        db: Session
):
    """Test adding a word to learning list"""
    word = test_words[0]

    # Clear existing user_words
    db.query(UserWord).filter(
        UserWord.user_id == test_user["id"],
        UserWord.word_id == word.id
    ).delete()
    db.commit()

    response = client.post(
        f"/api/v1/words/add-to-learning?word_id={word.id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "next_review" in data
    assert "message" in data


def test_get_difficult_words(client: TestClient, test_user: dict, test_user_words: list, db: Session):
    """Test getting difficult words"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Add some mistakes to words
    for uw in test_user_words[:2]:
        uw.mistakes_count = 3
        db.add(uw)
    db.commit()

    response = client.get(
        "/api/v1/words/difficult-words",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "mistakes" in data[0]
        assert "word" in data[0]


def test_retention_level_progress(client: TestClient, test_user: dict, test_words: list, db: Session):
    """Test retention level progress"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Add word to learning list
    word = test_words[0]
    add_response = client.post(
        f"/api/v1/words/add-to-learning?word_id={word.id}",
        headers=headers
    )
    assert add_response.status_code == 200

    # Submit multiple good reviews
    for _ in range(3):
        review_response = client.post(
            "/api/v1/words/review",
            headers=headers,
            json={
                "word_id": word.id,
                "quality": 5,
                "response_time": 1000.0,
                "was_correct": True
            }
        )
        assert review_response.status_code == 200
        data = review_response.json()
        assert "retention_level" in data
        assert data["retention_level"] > 0

    # Check final progress
    progress_response = client.get(
        f"/api/v1/words/progress/{word.id}",
        headers=headers
    )
    assert progress_response.status_code == 200
    progress_data = progress_response.json()
    assert progress_data["retention_level"] > 0

def test_get_learned_words(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Öğrenilen kelimeleri alma testi"""
    response = client.get(
        "/api/v1/words/learned-words",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Fixture'da bir kelime öğrenilmiş durumda
    assert data[0]["is_learned"] == True


def test_bulk_add_words(client: TestClient, test_user: dict, test_words: list):
    """Test bulk adding words"""
    word_ids = [word.id for word in test_words]
    response = client.post(
        "/api/v1/words/bulk-add",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"word_ids": word_ids}
    )

    assert response.status_code == 200
    data = response.json()
    assert "added_count" in data
    assert "skipped_count" in data