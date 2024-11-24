# app/schemas/user.py
from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    daily_goal: Optional[int] = 10

    @validator('daily_goal')
    def validate_daily_goal(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('Daily goal must be between 1 and 100')
        return v


class UserCreate(UserBase):
    password: constr(min_length=8)
    password_confirm: str

    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    daily_goal: Optional[int] = None
    email: Optional[EmailStr] = None

    class Config:
        extra = "forbid"


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_activity: Optional[datetime]
    streak_days: int

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    streak_days: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserStatistics(BaseModel):
    total_words_learned: int
    words_in_progress: int
    completion_rate: float
    current_streak: int
    average_retention: float