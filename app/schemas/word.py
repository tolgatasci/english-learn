# app/schemas/word.py
from enum import Enum

from pydantic import BaseModel, constr, validator
from typing import Optional, List
from datetime import datetime
class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PRONOUN = "pronoun"
    INTERJECTION = "interjection"
    ARTICLE = "article"  # Yeni eklendi
    DETERMINER = "determiner"  # Yeni eklendi
    OTHER = "other"  # Fallback için
class WordBase(BaseModel):
    english: constr(min_length=1, max_length=100)
    turkish: constr(min_length=1, max_length=100)
    phonetic: Optional[str] = None
    difficulty_level: Optional[int] = 1
    part_of_speech: PartOfSpeech
    example_sentence: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    tags: Optional[str] = None

    @validator('difficulty_level')
    def validate_difficulty(cls, v):
        if v is not None and v not in [1, 2, 3]:
            raise ValueError('Difficulty level must be 1, 2, or 3')
        return v

    @validator('part_of_speech')
    def validate_pos(cls, v):
        valid_pos = ['noun', 'verb', 'adjective', 'adverb', 'preposition', 'conjunction', 'pronoun', 'interjection']
        if v is not None and v.lower() not in valid_pos:
            raise ValueError(f'Invalid part of speech. Must be one of: {", ".join(valid_pos)}')
        return v.lower() if v else None

class WordCreate(WordBase):
    pass

class WordUpdate(BaseModel):
    turkish: Optional[str] = None
    phonetic: Optional[str] = None
    difficulty_level: Optional[int] = None
    example_sentence: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    tags: Optional[str] = None

class WordInDB(WordBase):
    id: int
    created_at: datetime
    updated_at: datetime
    audio_url: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True
class PartOfSpeechEnum(str, Enum):
    noun = 'noun'
    verb = 'verb'
    adjective = 'adjective'
    adverb = 'adverb'
    preposition = 'preposition'
    conjunction = 'conjunction'
    pronoun = 'pronoun'
    interjection = 'interjection'
    determiner = 'determiner'
class WordSchema(BaseModel):
    id: int
    english: str
    turkish: str
    phonetic: Optional[str]
    difficulty_level: int
    part_of_speech: Optional[str]
    example_sentence: Optional[str]
    example_sentence_translation: Optional[str]
    audio_url: Optional[str]
    image_url: Optional[str]
    tags: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True
class WordResponse(BaseModel):
    id: int
    english: str
    turkish: str
    phonetic: Optional[str] = None
    difficulty_level: int
    part_of_speech: Optional[PartOfSpeechEnum] = None
    example_sentence: Optional[str] = None
    example_sentence_translation: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[str] = None

    class Config:
        from_attributes = True

class WordWithProgress(WordResponse):
    retention_level: int
    confidence_level: int
    next_review: datetime
    is_learned: bool
    mistakes_count: int

class WordLearningStatus(BaseModel):
    word_id: int
    retention_level: int
    confidence_level: int
    review_count: int
    last_reviewed: Optional[datetime]
    next_review: datetime
    is_due: bool

class WordReviewSubmission(BaseModel):
    word_id: int
    quality: int  # 0-5 rating of recall quality
    response_time: float  # milliseconds
    was_correct: bool

    @validator('quality')
    def validate_quality(cls, v):
        if not 0 <= v <= 5:
            raise ValueError('Quality must be between 0 and 5')
        return v

    @validator('response_time')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('Response time cannot be negative')
        return v

class WordSuggestionCreate(BaseModel):
    english: str
    turkish: str
    part_of_speech: str
    example_sentence: str

class WordSuggestionResponse(WordSuggestionCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True