# app/models/word.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String(100), unique=True, nullable=False, index=True)
    turkish = Column(String(100), nullable=False)
    phonetic = Column(String(100), nullable=True)  # IPA pronunciation
    difficulty_level = Column(Integer, default=1)  # 1: Easy, 2: Medium, 3: Hard
    part_of_speech = Column(String(20), nullable=True)  # noun, verb, adjective, etc.
    example_sentence = Column(Text, nullable=True)
    example_sentence_translation = Column(Text, nullable=True)
    audio_url = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
    tags = Column(String(255), nullable=True)  # Comma separated tags
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user_words = relationship("UserWord", back_populates="word", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Word {self.english} ({self.turkish})>"

    @property
    def usage_count(self):
        return len(self.user_words)