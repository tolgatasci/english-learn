# app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list[str] = []

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordReset(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str