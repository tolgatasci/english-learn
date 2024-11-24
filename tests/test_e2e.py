# tests/test_e2e.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.word import Word
from app.models.user import User
from app.models.user_word import UserWord
from tests.conftest import TestingSessionLocal


class TestUserJourney:
    """Kullanıcının tüm öğrenme yolculuğunu test eden sınıf"""

    def test_complete_user_journey(self, client: TestClient, db: Session):
        # 0. Prepare test data - Add sample words
        sample_words = [
            Word(
                english="hello",
                turkish="merhaba",
                difficulty_level=1,
                example_sentence="Hello, how are you?",
                part_of_speech="interjection"
            ),
            Word(
                english="world",
                turkish="dünya",
                difficulty_level=1,
                example_sentence="The world is beautiful.",
                part_of_speech="noun"
            ),
            Word(
                english="computer",
                turkish="bilgisayar",
                difficulty_level=2,
                example_sentence="I need a new computer.",
                part_of_speech="noun"
            )
        ]

        for word in sample_words:
            db.add(word)
        db.commit()

        # 1. Register
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "journey_user",
                "email": "journey@test.com",
                "password": "journey123",
                "password_confirm": "journey123",
                "full_name": "Journey User",
                "daily_goal": 5
            }
        )
        assert register_response.status_code == 200
        user_data = register_response.json()
        assert user_data["username"] == "journey_user"

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "journey_user",
                "password": "journey123"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Set daily goal
        goal_response = client.post(
            "/api/v1/users/me/daily-goal",
            headers=headers,
            json={"goal": 5}
        )
        assert goal_response.status_code == 200

        # 4. Get words to learn
        words_response = client.get(
            "/api/v1/words/next-words?limit=5",
            headers=headers
        )
        assert words_response.status_code == 200
        words = words_response.json()
        assert len(words) > 0, "No words available for learning"

        # 5. Learn first word
        word = words[0]
        review_response = client.post(
            "/api/v1/words/review",
            headers=headers,
            json={
                "word_id": word["id"],
                "quality": 5,
                "response_time": 1000.0,
                "was_correct": True
            }
        )
        assert review_response.status_code == 200
        review_data = review_response.json()
        assert review_data["retention_level"] > 0

        # 6. Check daily progress
        progress_response = client.get(
            "/api/v1/learning/daily-progress",
            headers=headers
        )
        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["words_reviewed_today"] > 0

        # 7. Clean up test data
        db.query(UserWord).delete()
        db.query(User).delete()
        db.query(Word).delete()
        db.commit()

    def teardown_method(self, method):
        """Clean up after each test method"""
        db = TestingSessionLocal()
        try:
            db.query(UserWord).delete()
            db.query(User).delete()
            db.query(Word).delete()
            db.commit()
        finally:
            db.close()

def test_spaced_repetition_flow(
        client: TestClient,
        test_user: dict,
        test_words: list
):
    """Test spaced repetition system"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Add word to learning
    word = test_words[0]
    add_response = client.post(
        f"/api/v1/words/add-to-learning?word_id={word.id}",
        headers=headers
    )
    assert add_response.status_code == 200

    # Review the word multiple times
    for quality in [3, 4, 5]:
        review_response = client.post(
            "/api/v1/words/review",
            headers=headers,
            json={
                "word_id": word.id,
                "quality": quality,
                "response_time": 1500.0,
                "was_correct": True
            }
        )
        assert review_response.status_code == 200


def test_learning_analytics(client: TestClient, test_user: dict, test_user_words: list, db: Session):
    """Test learning analytics with realistic data"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Add some learning activity
    for word in test_user_words[:3]:  # Use only first 3 words
        client.post(
            "/api/v1/words/review",
            headers=headers,
            json={
                "word_id": word.word_id,
                "quality": 4,
                "response_time": 1500.0,
                "was_correct": True
            }
        )

    analytics_response = client.get("/api/v1/learning/performance-analysis", headers=headers)
    assert analytics_response.status_code == 200
    data = analytics_response.json()
    assert data["total_words"] >= 3


def test_error_handling(client: TestClient, test_user: dict):
    """Test error handling"""
    # Test invalid goal
    response = client.post(
        "/api/v1/users/me/daily-goal",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"goal": -1}
    )
    assert response.status_code == 400

    # Test invalid word review
    response = client.post(
        "/api/v1/words/review",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={
            "word_id": 99999,  # Non-existent word
            "quality": 5,
            "response_time": 1500.0,
            "was_correct": True
        }
    )
    assert response.status_code == 404

    # Test invalid authentication
    response = client.get(
        "/api/v1/learning/daily-progress",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401