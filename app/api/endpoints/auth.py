# app/api/endpoints/auth.py


from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from typing import Any

from ...database import get_db
from ...models.user import User
from ...schemas.auth import Token, LoginRequest, PasswordReset
from ...schemas.user import UserCreate, UserResponse
from ...utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token
)
from ...config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if not payload:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


@router.post("/register", response_model=UserResponse)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
) -> Any:
    """Register a new user"""
    # Check existing user
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check existing email
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        daily_goal=user_data.daily_goal
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any


@router.get("/debug-password")
async def debug_password(
        email: str = Query(..., description="Email address to check"),
        password: str = Query(..., description="Password to verify"),
        db: Session = Depends(get_db)
) -> Any:
    """Debug password hashing (sadece geliştirme ortamında kullanın!)"""
    try:
        # Kullanıcıyı bul
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {
                "status": "error",
                "message": "User not found",
                "email": email,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Şifre doğrulamasını kontrol et
        is_valid = verify_password(password, user.password_hash)

        return {
            "status": "info",
            "email": email,
            "username": user.username,
            "password_input": password,
            "stored_hash": user.password_hash,
            "is_valid": is_valid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


@router.post("/login", response_model=Token)
async def login(
        request: Request,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
) -> Any:
    """Login user"""
    try:
        # Debug için gelen verileri yazdır
        print(f"Login attempt - Username: {form_data.username}, Password length: {len(form_data.password)}")

        # Kullanıcıyı bul (email veya username ile)
        user = db.query(User).filter(
            (User.username == form_data.username) |
            (User.email == form_data.username)
        ).first()

        if not user:
            print(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Password verification debug
        print(f"Verifying password for user: {user.username}")
        print(f"Stored hash: {user.password_hash}")
        is_valid = verify_password(form_data.password, user.password_hash)
        print(f"Password verification result: {is_valid}")

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": user.username}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise

# Test endpoint for creating a new password hash
@router.get("/hash-password")
async def hash_password(
    password: str,
    db: Session = Depends(get_db)
) -> Any:
    """Test password hashing"""
    try:
        hashed = get_password_hash(password)
        return {
            "password": password,
            "hash": hashed
        }
    except Exception as e:
        return {"error": str(e)}
@router.post("/reset-password")
async def reset_password(
        password_data: PasswordReset,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Any:
    """Reset user password"""
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )

    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user information"""
    return current_user