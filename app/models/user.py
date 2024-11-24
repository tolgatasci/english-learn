# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    daily_goal = Column(Integer, default=10)
    streak_days = Column(Integer, default=0)
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Relationships
    user_words = relationship("UserWord", back_populates="user", cascade="all, delete-orphan")
    word_suggestions = relationship("WordSuggestion", back_populates="suggested_by")

    def __repr__(self):
        return f"<User {self.username}>"

    @property
    def is_authenticated(self):
        return True if self.is_active else False