from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base

class WordSuggestion(Base):
    __tablename__ = "word_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String(100), nullable=False)
    turkish = Column(String(100), nullable=False)
    part_of_speech = Column(String(20), nullable=False)
    example_sentence = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    suggested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    admin_notes = Column(Text, nullable=True)

    # Relationships
    suggested_by = relationship("User", back_populates="word_suggestions")