# app/utils/learning.py
from datetime import datetime, timedelta
import math
from typing import List, Dict
from ..models.user_word import UserWord


def calculate_retention_score(user_word: UserWord) -> float:
    """Calculate a retention score based on review history"""
    if not user_word.times_reviewed:
        return 0.0

    base_score = user_word.consecutive_correct * 0.2
    time_factor = 1.0

    if user_word.last_reviewed:
        days_since_review = (datetime.utcnow() - user_word.last_reviewed).days
        time_factor = math.exp(-0.1 * days_since_review)

    confidence_factor = user_word.confidence_level / 100.0

    return min(1.0, (base_score + confidence_factor) * time_factor)


def get_due_words(user_words: List[UserWord], limit: int = 10) -> List[UserWord]:
    """Get words that are due for review"""
    now = datetime.utcnow()
    return sorted(
        [uw for uw in user_words if uw.next_review <= now],
        key=lambda x: calculate_priority_score(x),
        reverse=True
    )[:limit]


def calculate_priority_score(user_word: UserWord) -> float:
    """Calculate priority score for word review ordering"""
    now = datetime.utcnow()
    days_overdue = (now - user_word.next_review).days if user_word.next_review else 0
    priority = (
            (days_overdue * 1.5) +  # Overdue factor
            ((5 - user_word.retention_level) * 0.8) +  # Lower retention = higher priority
            (user_word.mistakes_count * 0.3) +  # More mistakes = higher priority
            ((100 - user_word.confidence_level) * 0.01)  # Lower confidence = higher priority
    )
    return max(0, priority)


def analyze_learning_patterns(user_words: List[UserWord]) -> Dict:
    """Analyze user's learning patterns and performance"""
    total_words = len(user_words)
    if not total_words:
        return {
            "average_retention": 0,
            "learning_rate": 0,
            "problem_areas": [],
            "best_time_to_review": None
        }

    retention_scores = [calculate_retention_score(uw) for uw in user_words]
    review_times = [uw.last_reviewed for uw in user_words if uw.last_reviewed]

    return {
        "average_retention": sum(retention_scores) / total_words,
        "learning_rate": sum(1 for uw in user_words if uw.is_learned) / total_words,
        "problem_areas": identify_problem_areas(user_words),
        "best_time_to_review": calculate_best_review_time(review_times) if review_times else None
    }


def identify_problem_areas(user_words: List[UserWord]) -> List[Dict]:
    """Identify patterns in words that user struggles with"""
    problem_words = [uw for uw in user_words if uw.mistakes_count > 2]

    if not problem_words:
        return []

    # Group by word characteristics
    patterns = {}
    for uw in problem_words:
        pos = uw.word.part_of_speech
        if pos in patterns:
            patterns[pos]["count"] += 1
            patterns[pos]["total_mistakes"] += uw.mistakes_count
        else:
            patterns[pos] = {
                "type": "part_of_speech",
                "value": pos,
                "count": 1,
                "total_mistakes": uw.mistakes_count
            }

    return sorted(
        patterns.values(),
        key=lambda x: x["total_mistakes"],
        reverse=True
    )


def calculate_best_review_time(review_times: List[datetime]) -> Dict:
    """Calculate the most effective review times based on user history"""
    if not review_times:
        return None

    hour_counts = [0] * 24
    success_rates = [0.0] * 24

    for rt in review_times:
        hour_counts[rt.hour] += 1

    peak_hours = sorted(
        range(24),
        key=lambda h: hour_counts[h],
        reverse=True
    )[:3]

    return {
        "peak_hours": peak_hours,
        "recommended_time": peak_hours[0] if peak_hours else 9
    }