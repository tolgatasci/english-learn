# app/api/endpoints/words.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime, timedelta

from ...database import get_db
from ...models.word import Word
from ...models.user_word import UserWord
from ...models.user import User
from ...models.word_suggestion import WordSuggestion
from ...schemas.word import (
    WordCreate,
    WordResponse,
    WordWithProgress,
    WordReviewSubmission,
    WordLearningStatus, WordSuggestionCreate, WordSuggestionResponse, WordSchema, PartOfSpeechEnum
)
from ..endpoints.auth import get_current_user
from ...utils.learning import (
    get_due_words,
    calculate_retention_score,
    calculate_priority_score
)
class BulkAddRequest(BaseModel):
    word_ids: List[int]
router = APIRouter()


from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from ...models.word import Word
from ...models.user_word import UserWord
from ...schemas.word import WordResponse, WordWithProgress
from ..endpoints.auth import get_current_user
from ...database import get_db

router = APIRouter()

@router.get("/next-words", response_model=List[WordWithProgress])
async def get_next_review_words(
        limit: int = Query(default=10, ge=1, le=50),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get next words for review based on spaced repetition"""
    user_words = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.next_review <= datetime.utcnow()
    ).order_by(UserWord.next_review).limit(limit).all()

    # Fetch the word details for each UserWord
    word_data = []
    for uw in user_words:
        word = db.query(Word).get(uw.word_id)
        part_of_speech = word.part_of_speech
        if part_of_speech in PartOfSpeechEnum.__members__:
            part_of_speech_enum = PartOfSpeechEnum(part_of_speech)
        else:
            part_of_speech_enum = None

        word_response = WordResponse(
            id=word.id,
            english=word.english,
            turkish=word.turkish,
            phonetic=word.phonetic,
            difficulty_level=word.difficulty_level,
            part_of_speech=part_of_speech_enum,
            example_sentence=word.example_sentence,
            example_sentence_translation=word.example_sentence_translation,
            audio_url=word.audio_url,
            image_url=word.image_url,
            tags=word.tags
        )
        word_data.append({
            **word_response.dict(),
            "retention_level": uw.retention_level,
            "confidence_level": uw.confidence_level,
            "next_review": uw.next_review,
            "is_learned": uw.is_learned,
            "mistakes_count": uw.mistakes_count
        })

    return word_data

@router.get("/next-learning-words", response_model=List[WordSchema])
async def get_next_learning_words(
        limit: int = Query(default=10, ge=1, le=50),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get next words for learning"""
    # Get words user is already learning
    learning_word_ids = db.query(UserWord.word_id).filter(
        UserWord.user_id == current_user.id
    ).all()
    learning_word_ids = [w[0] for w in learning_word_ids]

    # Get new words user hasn't started learning yet
    new_words = db.query(Word).filter(
        ~Word.id.in_(learning_word_ids) if learning_word_ids else True
    ).order_by(
        Word.difficulty_level
    ).limit(limit).all()

    if not new_words:
        return []

    # Artık burada UserWord oluşturmuyoruz, sadece kelimeleri dönüyoruz
    return [WordSchema.from_orm(word) for word in new_words]

@router.post("/suggest", response_model=WordSuggestionResponse)
async def suggest_word(
        suggestion: WordSuggestionCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Submit a word suggestion for admin review"""

    # Check if word already exists
    existing_word = db.query(Word).filter(
        func.lower(Word.english) == func.lower(suggestion.english)
    ).first()

    if existing_word:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This word already exists in our database"
        )

    # Check if same suggestion is pending
    existing_suggestion = db.query(WordSuggestion).filter(
        func.lower(WordSuggestion.english) == func.lower(suggestion.english),
        WordSuggestion.status == "pending"
    ).first()

    if existing_suggestion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This word is already suggested and pending review"
        )

    # Validate part_of_speech
    valid_pos = ['noun', 'verb', 'adjective', 'adverb', 'preposition',
                 'conjunction', 'pronoun', 'interjection']
    if suggestion.part_of_speech.lower() not in valid_pos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid part of speech. Must be one of: {', '.join(valid_pos)}"
        )

    # Create word suggestion
    word_suggestion = WordSuggestion(
        english=suggestion.english,
        turkish=suggestion.turkish,
        part_of_speech=suggestion.part_of_speech.lower(),
        example_sentence=suggestion.example_sentence,
        suggested_by_user_id=current_user.id,
        status="pending"
    )

    try:
        db.add(word_suggestion)
        db.commit()
        db.refresh(word_suggestion)

        return word_suggestion
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating word suggestion: {str(e)}"
        )
@router.post("/review")
async def submit_word_review(
        review: WordReviewSubmission,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Submit a word review and update learning progress"""
    user_word = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.word_id == review.word_id
    ).first()

    if not user_word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found in user's learning list"
        )

    # Update retention level based on review quality
    if review.was_correct:
        user_word.retention_level += 1
        if review.quality >= 4:  # High quality review
            user_word.retention_level += 1
    else:
        user_word.retention_level = max(0, user_word.retention_level - 1)

    # Update other metrics
    user_word.last_reviewed = datetime.utcnow()
    user_word.times_reviewed += 1
    user_word.last_response_time = review.response_time

    # Calculate next review time based on retention level
    interval_days = 2 ** user_word.retention_level  # Exponential spacing
    user_word.next_review = datetime.utcnow() + timedelta(days=interval_days)

    db.commit()
    db.refresh(user_word)

    return {
        "word_id": user_word.word_id,
        "retention_level": user_word.retention_level,
        "next_review": user_word.next_review,
        "times_reviewed": user_word.times_reviewed
    }


@router.get("/progress/{word_id}")
async def get_word_progress(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get learning progress for a specific word"""
    user_word = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.word_id == word_id
    ).first()

    if not user_word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found in user's learning list"
        )

    return {
        "word_id": user_word.word_id,
        "retention_level": user_word.retention_level,
        "times_reviewed": user_word.times_reviewed,
        "last_reviewed": user_word.last_reviewed,
        "next_review": user_word.next_review,
        "mastered": user_word.retention_level >= 5
    }

@router.get("/search")
async def search_words(
        query: str = Query(..., min_length=1),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Search for words in the database"""
    words = db.query(Word).filter(
        Word.english.ilike(f"%{query}%") |
        Word.turkish.ilike(f"%{query}%")
    ).all()

    # Get learning progress for found words
    result = []
    for word in words:
        user_word = db.query(UserWord).filter(
            UserWord.user_id == current_user.id,
            UserWord.word_id == word.id
        ).first()

        word_data = {
            "id": word.id,
            "english": word.english,
            "turkish": word.turkish,
            "difficulty_level": word.difficulty_level,
            "example_sentence": word.example_sentence,
            "part_of_speech": word.part_of_speech,
            "learning_status": None
        }

        if user_word:
            word_data["learning_status"] = {
                "retention_level": user_word.retention_level,
                "confidence_level": user_word.confidence_level,
                "is_learned": user_word.is_learned,
                "next_review": user_word.next_review
            }

        result.append(word_data)

    return result


@router.post("/add-to-learning")
async def add_word_to_learning(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Add a word to user's learning list"""
    # Check if word exists
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )

    # Check if word is already in learning list
    existing = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.word_id == word_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Word is already in learning list"
        )

    # Add word to learning list
    user_word = UserWord(
        user_id=current_user.id,
        word_id=word_id,
        next_review=datetime.utcnow()
    )

    db.add(user_word)
    db.commit()
    db.refresh(user_word)

    return {
        "message": "Word added to learning list",
        "next_review": user_word.next_review
    }


@router.delete("/remove-from-learning/{word_id}")
async def remove_word_from_learning(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Remove a word from user's learning list"""
    user_word = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.word_id == word_id
    ).first()

    if not user_word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found in learning list"
        )

    db.delete(user_word)
    db.commit()

    return {"message": "Word removed from learning list"}


@router.get("/difficult-words")
async def get_difficult_words(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's difficult words"""
    difficult_words = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.mistakes_count > 0
    ).order_by(
        UserWord.mistakes_count.desc()
    ).limit(10).all()

    return [
        {
            "word_id": uw.word_id,
            "mistakes": uw.mistakes_count,
            "retention_level": uw.retention_level,
            "last_reviewed": uw.last_reviewed,
            "word": {
                "english": uw.word.english,
                "turkish": uw.word.turkish,
                "difficulty_level": uw.word.difficulty_level
            }
        }
        for uw in difficult_words
    ]


@router.get("/learned-words", response_model=List[WordWithProgress])
async def get_learned_words(
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Get user's learned words"""
    learned_words = db.query(UserWord).filter(
        UserWord.user_id == current_user.id,
        UserWord.is_learned == True
    ).order_by(
        UserWord.last_reviewed.desc()
    ).offset(offset).limit(limit).all()

    return [
        {
            **WordResponse.model_validate(uw.word).dict(),
            "retention_level": uw.retention_level,
            "confidence_level": uw.confidence_level,
            "next_review": uw.next_review,
            "is_learned": uw.is_learned,
            "mistakes_count": uw.mistakes_count
        }
        for uw in learned_words
    ]


@router.post("/bulk-add")
async def add_multiple_words(
        data: BulkAddRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Add multiple words to user's learning list"""
    existing_words = db.query(UserWord.word_id).filter(
        UserWord.user_id == current_user.id,
        UserWord.word_id.in_(data.word_ids)
    ).all()
    existing_word_ids = [w[0] for w in existing_words]

    new_words = []
    for word_id in data.word_ids:
        if word_id not in existing_word_ids:
            word = db.query(Word).get(word_id)
            if word:
                user_word = UserWord(
                    user_id=current_user.id,
                    word_id=word_id,
                    next_review=datetime.utcnow()
                )
                new_words.append(user_word)

    if new_words:
        db.add_all(new_words)
        db.commit()

    return {
        "status": "success",
        "added_count": len(new_words),
        "skipped_count": len(data.word_ids) - len(new_words),
        "message": f"Added {len(new_words)} new words to learning list"
    }

