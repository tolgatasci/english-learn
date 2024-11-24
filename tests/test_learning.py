# tests/test_learning.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.user import User
from app.models.user_word import UserWord


def test_daily_progress(client: TestClient, test_user: dict, test_user_words: list, db: Session):
    """Test daily progress endpoint"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Set daily goal first
    client.post(
        "/api/v1/users/me/daily-goal",
        headers=headers,
        json={"goal": 5}
    )

    response = client.get(
        "/api/v1/learning/daily-progress",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "daily_goal" in data
    assert "words_reviewed_today" in data
    assert "progress_percentage" in data
    assert "streak_days" in data


def test_weekly_stats(
        client: TestClient,
        test_user: dict,
        test_user_words: list,
        db: Session
):
    """Haftalık istatistikler testi"""
    # Son bir hafta için review verileri ekleyelim
    today = datetime.utcnow()
    for i, user_word in enumerate(test_user_words):
        review_date = today - timedelta(days=i % 7)
        user_word.last_reviewed = review_date
        user_word.retention_level = 3 if i % 2 == 0 else 1
        user_word.last_response_time = 1500  # milliseconds
    db.commit()

    response = client.get(
        "/api/v1/learning/weekly-stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "daily_stats" in data
    assert len(data["daily_stats"]) == 8  # 7 gün + bugün
    assert "total_words_reviewed" in data
    assert "average_accuracy" in data
    assert data["total_words_reviewed"] > 0


def test_learning_schedule(
        client: TestClient,
        test_user: dict,
        test_user_words: list
):
    """Öğrenme programı testi"""
    response = client.get(
        "/api/v1/learning/learning-schedule",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        params={"days": 7}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7  # 7 günlük program
    for date, schedule in data.items():
        assert "total_words" in schedule
        assert "new_words" in schedule
        assert "review_words" in schedule


def test_performance_analysis(
        client: TestClient,
        test_user: dict,
        test_user_words: list,
        db: Session
):
    """Performans analizi testi"""
    # Test verisini zenginleştirelim
    for i, user_word in enumerate(test_user_words):
        user_word.retention_level = i % 5
        user_word.confidence_level = (i + 1) * 20
        user_word.mistakes_count = i % 3
        user_word.is_learned = i > len(test_user_words) / 2
    db.commit()

    response = client.get(
        "/api/v1/learning/performance-analysis",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "total_words" in data
    assert "performance_metrics" in data
    assert "problem_areas" in data
    assert "recommendations" in data

    metrics = data["performance_metrics"]
    assert "average_retention" in metrics
    assert "mastery_rate" in metrics
    assert "average_mistakes" in metrics


def test_empty_learning_progress(
        client: TestClient,
        test_user: dict,
        db: Session
):
    """Hiç kelime öğrenilmemiş durumda test"""
    # Tüm user_words kayıtlarını silelim
    db.query(UserWord).filter(UserWord.user_id == test_user["id"]).delete()
    db.commit()

    response = client.get(
        "/api/v1/learning/performance-analysis",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_words"] == 0
    assert data["performance_metrics"] is None
    assert len(data["problem_areas"]) == 0


def test_streak_calculation(client: TestClient, test_user: dict, test_user_words: list, db: Session):
    """Test streak calculation"""
    if not test_user_words:
        pytest.skip("No test words available")

    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Review a word to start streak
    word = test_user_words[0]
    client.post(
        "/api/v1/words/review",
        headers=headers,
        json={
            "word_id": word.word_id,
            "quality": 5,
            "response_time": 1500.0,
            "was_correct": True
        }
    )

    response = client.get("/api/v1/learning/streak-info", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "current_streak" in data
    assert "today_activity" in data


def test_retention_level_progress(client: TestClient, test_user: dict, test_words: list, db: Session):
    """Test learning retention progress"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Add word to learning list
    word = test_words[0]
    client.post(
        f"/api/v1/words/add-to-learning?word_id={word.id}",
        headers=headers
    )

    # Submit reviews with increasing quality
    for quality in [3, 4, 5]:
        response = client.post(
            "/api/v1/words/review",
            headers=headers,
            json={
                "word_id": word.id,
                "quality": quality,
                "response_time": 1500.0,
                "was_correct": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "retention_level" in data
        assert data["retention_level"] > 0

    # Verify final retention level
    progress_response = client.get(
        f"/api/v1/words/progress/{word.id}",
        headers=headers
    )
    assert progress_response.status_code == 200
    progress_data = progress_response.json()
    assert progress_data["retention_level"] > 0


def test_learning_patterns(
        client: TestClient,
        test_user: dict,
        test_user_words: list,
        db: Session
):
    """Öğrenme paternleri analizi testi"""
    # Farklı zorluk seviyelerinde kelimeler ekleyelim
    difficulties = ['noun', 'verb', 'adjective']
    for i, user_word in enumerate(test_user_words):
        word = user_word.word
        word.part_of_speech = difficulties[i % 3]
        user_word.mistakes_count = (i % 3) + 1
    db.commit()

    response = client.get(
        "/api/v1/learning/performance-analysis",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    assert response.status_code == 200
    data = response.json()
    problem_areas = data["problem_areas"]
    assert len(problem_areas) > 0
    assert "type" in problem_areas[0]
    assert "value" in problem_areas[0]
    assert "total_mistakes" in problem_areas[0]