from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func, text, case

from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime, timedelta, timezone

from ...database import get_db
from ...models.user import User
from ...models.user_word import UserWord
from ...models.word import Word
from ..endpoints.auth import get_current_user
from ...utils.learning import (
    analyze_learning_patterns,
    calculate_retention_score,
    identify_problem_areas
)

router = APIRouter()


@router.get("/daily-progress")
async def get_daily_progress(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's daily learning progress"""
    today = datetime.utcnow().date()

    today_reviews = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        func.date(UserWord.last_reviewed) == today
    ).all()

    words_due = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.next_review <= datetime.utcnow()
    ).count()

    return {
        "daily_goal": current_user.daily_goal,
        "words_reviewed_today": len(today_reviews),
        "progress_percentage": min(100, (len(today_reviews) / max(1, current_user.daily_goal) * 100)),
        "streak_days": current_user.streak_days,
        "total_words_learned": len([w for w in today_reviews if w.is_learned]),
        "words_due": words_due
    }


@router.get("/streak-info")
async def get_streak_info(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's learning streak information"""
    today = datetime.utcnow().date()

    today_activity = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        func.date(UserWord.last_reviewed) == today
    ).count()

    yesterday = today - timedelta(days=1)
    yesterday_activity = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        func.date(UserWord.last_reviewed) == yesterday
    ).count()

    current_streak = current_user.streak_days

    if today_activity > 0:
        if yesterday_activity == 0 and current_streak > 0:
            current_streak = 1
        elif yesterday_activity > 0:
            current_streak += 1
    elif yesterday_activity == 0 and current_streak > 0:
        current_streak = 0

    if current_streak != current_user.streak_days:
        current_user.streak_days = current_streak
        db.commit()

    return {
        "current_streak": current_streak,
        "today_activity": today_activity > 0,
        "daily_goal_met": today_activity >= current_user.daily_goal
    }


def get_weekly_stats_query(user_id: int, week_ago: datetime) -> dict:
    """Helper function to get weekly stats using raw SQL"""
    try:
        query = text("""
            SELECT 
                DATE(last_reviewed) as review_date,
                COUNT(*) as words_reviewed,
                SUM(CASE WHEN retention_level > 0 THEN 1 ELSE 0 END) as correct_answers
            FROM user_words
            WHERE user_id = :user_id 
            AND last_reviewed >= :week_ago
            GROUP BY DATE(last_reviewed)
            ORDER BY DATE(last_reviewed)
        """)

        return {
            "query": query,
            "params": {
                "user_id": user_id,
                "week_ago": week_ago
            }
        }
    except Exception as e:
        print(f"Query creation error: {str(e)}")
        raise
@router.get("/weekly-stats")
async def get_weekly_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's weekly learning statistics"""
    try:
        # Get date range
        today = datetime.now(timezone.utc).date()
        week_ago = today - timedelta(days=7)

        # Initialize stats dictionary with zeros for all days
        daily_stats = {
            (week_ago + timedelta(days=i)).isoformat(): {
                "words_reviewed": 0,
                "correct_answers": 0,
                "accuracy": 0
            } for i in range(8)
        }

        # Get query and parameters
        query_data = get_weekly_stats_query(current_user.id, week_ago)

        # Execute query
        result = db.execute(
            query_data["query"],
            query_data["params"]
        )

        total_reviewed = 0
        total_correct = 0

        # Process results
        for row in result:
            date_str = row.review_date.isoformat()
            words_reviewed = row.words_reviewed
            correct_answers = row.correct_answers or 0

            if date_str in daily_stats:
                daily_stats[date_str].update({
                    "words_reviewed": words_reviewed,
                    "correct_answers": correct_answers,
                    "accuracy": round((correct_answers / words_reviewed * 100), 2) if words_reviewed > 0 else 0
                })

            total_reviewed += words_reviewed
            total_correct += correct_answers

        return {
            "daily_stats": daily_stats,
            "total_words_reviewed": total_reviewed,
            "average_accuracy": round((total_correct / total_reviewed * 100), 2) if total_reviewed > 0 else 0,
            "current_streak": current_user.streak_days
        }

    except Exception as e:
        print(f"Error in weekly_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/weekly-stats-alt")
async def get_weekly_stats_alt(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user's weekly learning statistics using SQLAlchemy expressions"""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    # Query using SQLAlchemy expressions
    result = db.query(
        func.date(UserWord.last_reviewed).label('review_date'),
        func.count().label('words_reviewed'),
        func.sum(case(
            (UserWord.retention_level > 0, 1),
            else_=0
        )).label('correct_answers')
    ).filter(
        UserWord.user_id == current_user.id,
        UserWord.last_reviewed >= week_ago
    ).group_by(
        func.date(UserWord.last_reviewed)
    ).all()

    daily_stats = {
        (week_ago + timedelta(days=i)).isoformat(): {
            "words_reviewed": 0,
            "correct_answers": 0,
            "accuracy": 0
        } for i in range(8)
    }

    total_reviewed = 0
    total_correct = 0

    for row in result:
        date_str = row.review_date.isoformat()
        words_reviewed = row.words_reviewed
        correct_answers = row.correct_answers or 0

        daily_stats[date_str] = {
            "words_reviewed": words_reviewed,
            "correct_answers": correct_answers,
            "accuracy": (correct_answers / words_reviewed * 100) if words_reviewed > 0 else 0
        }

        total_reviewed += words_reviewed
        total_correct += correct_answers

    return {
        "daily_stats": daily_stats,
        "total_words_reviewed": total_reviewed,
        "average_accuracy": (total_correct / total_reviewed * 100) if total_reviewed > 0 else 0,
        "current_streak": current_user.streak_days
    }

@router.get("/performance-analysis")
async def get_performance_analysis(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get detailed analysis of learning performance"""
    user_words = db.query(UserWord).filter(
        UserWord.user_id == current_user.id
    ).all()

    if not user_words:
        return {
            "total_words": 0,
            "performance_metrics": None,
            "problem_areas": []
        }

    total_words = len(user_words)
    mastered_words = len([w for w in user_words if w.is_learned])

    if total_words > 0:
        average_retention = sum(w.retention_level for w in user_words) / total_words
    else:
        average_retention = 0

    return {
        "total_words": total_words,
        "performance_metrics": {
            "mastery_rate": (mastered_words / total_words * 100) if total_words > 0 else 0,
            "average_retention": average_retention,
            "total_reviews": sum(w.times_reviewed for w in user_words)
        },
        "problem_areas": [
                             w.word.part_of_speech for w in user_words
                             if w.mistakes_count > 2
                         ][:3]
    }