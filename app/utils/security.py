# app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import settings

# Özel bcrypt konfigürasyonu
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Hash round sayısı
    bcrypt__salt_size=16,  # Salt boyutu
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        # Debug bilgileri
        print(f"Password verification attempt:")
        print(f"Plain password length: {len(plain_password)}")
        print(f"Hash length: {len(hashed_password)}")

        # Şifre doğrulama
        is_valid = pwd_context.verify(plain_password, hashed_password)
        print(f"Verification result: {is_valid}")

        return is_valid
    except Exception as e:
        print(f"Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    try:
        # Debug bilgileri
        print(f"Generating hash for password length: {len(password)}")

        # Hash oluştur
        hashed = pwd_context.hash(password)
        print(f"Generated hash length: {len(hashed)}")

        return hashed
    except Exception as e:
        print(f"Password hashing error: {str(e)}")
        raise


def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None