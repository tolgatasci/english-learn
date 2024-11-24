# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime

from ...database import get_db
from ...models.user import User
from ...models.user_word import UserWord
from ...schemas.user import UserUpdate, UserResponse, UserStatistics
from ..endpoints.auth import get_current_user
from ...utils.learning import analyze_learning_patterns
from fastapi import Body
from pydantic import BaseModel
class DailyGoalUpdate(BaseModel):
    goal: int
router = APIRouter()


@router.get("/me/statistics", response_model=UserStatistics)
async def get_user_statistics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get current user's learning statistics"""
    user_words = db.query(UserWord).filter(UserWord.user_id == current_user.id).all()

    total_words = len(user_words)
    learned_words = len([w for w in user_words if w.is_learned])
    words_in_progress = total_words - learned_words

    if total_words > 0:
        completion_rate = (learned_words / total_words) * 100
        average_retention = sum(w.retention_level for w in user_words) / total_words
    else:
        completion_rate = 0
        average_retention = 0

    return {
        "total_words_learned": learned_words,
        "words_in_progress": words_in_progress,
        "completion_rate": completion_rate,
        "current_streak": current_user.streak_days,
        "average_retention": average_retention
    }


@router.delete("/me")
async def delete_user(
        response: Response,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> None:
    """Delete current user's account"""
    db.delete(current_user)
    db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@router.put("/me", response_model=UserResponse)
async def update_user(
        user_update: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Update current user's information"""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    current_user.last_activity = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/me/daily-goal")
async def update_daily_goal(
        update: DailyGoalUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Update user's daily learning goal"""
    if update.goal < 1 or update.goal > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Daily goal must be between 1 and 100"
        )

    current_user.daily_goal = update.goal
    db.commit()

    return {
        "status": "success",
        "daily_goal": update.goal,
        "message": "Daily goal updated successfully"
    }


@router.post("/me/reset-progress")
async def reset_learning_progress(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Reset user's learning progress"""
    user_words = db.query(UserWord).filter(UserWord.user_id == current_user.id).all()
    for user_word in user_words:
        user_word.retention_level = 0
        user_word.confidence_level = 0
        user_word.is_learned = False
        user_word.times_reviewed = 0
        user_word.mistakes_count = 0
        user_word.next_review = datetime.utcnow()

    db.commit()
    return {"message": "Learning progress reset successfully"}


@router.get("/me/learning-patterns")
async def get_learning_patterns(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's learning patterns and analytics"""
    user_words = db.query(UserWord).filter(UserWord.user_id == current_user.id).all()
    return analyze_learning_patterns(user_words)