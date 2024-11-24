# tests/conftest.py
import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.database import Base, get_db  # get_db import edildi
from app.main import app
from app.models.user import User
from app.models.word import Word
from app.models.user_word import UserWord
from app.utils.security import create_access_token, get_password_hash

# Load environment variables
load_dotenv()

# Test database URL
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
TEST_DB_NAME = "english_learning_test"

# MySQL connection URL for creating test database
ROOT_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
TEST_DB_URL = f"{ROOT_URL}/{TEST_DB_NAME}"

# Test database engine
engine = create_engine(
    TEST_DB_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    """Test database session dependency"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database and tables"""
    # Connect to MySQL server
    root_engine = create_engine(ROOT_URL, isolation_level="AUTOCOMMIT")

    with root_engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        connection.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))
        connection.execute(text(f"USE {TEST_DB_NAME}"))

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

    with root_engine.connect() as connection:
        connection.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))


@pytest.fixture
def db() -> Generator:
    """Get database session for tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db) -> TestClient:
    """Create test client with database dependency override"""
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture
def test_user(db) -> Dict:
    """Create test user"""
    # Önce varsa eski test kullanıcısını temizle
    db.query(User).filter(User.username == "testuser").delete()
    db.commit()

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        full_name="Test User",
        daily_goal=10
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token({"sub": user.username})

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "token": access_token
    }


@pytest.fixture
def test_words(db) -> list:
    """Create test words"""
    # Önce varsa eski test kelimelerini temizle
    db.query(Word).delete()
    db.commit()

    words = [
        Word(
            english="hello",
            turkish="merhaba",
            difficulty_level=1,
            example_sentence="Hello, how are you?",
            part_of_speech="interjection"
        ),
        Word(
            english="world",
            turkish="dünya",
            difficulty_level=1,
            example_sentence="The world is beautiful.",
            part_of_speech="noun"
        ),
        Word(
            english="computer",
            turkish="bilgisayar",
            difficulty_level=2,
            example_sentence="I need a new computer.",
            part_of_speech="noun"
        )
    ]

    for word in words:
        db.add(word)
    db.commit()

    return [db.refresh(word) or word for word in words]


@pytest.fixture
def test_user_words(db, test_user, test_words) -> list:
    """Create test user-word relationships"""
    # Önce varsa eski ilişkileri temizle
    db.query(UserWord).filter(UserWord.user_id == test_user["id"]).delete()
    db.commit()

    user_words = []
    now = datetime.utcnow()

    for i, word in enumerate(test_words):
        user_word = UserWord(
            user_id=test_user["id"],
            word_id=word.id,
            retention_level=i,
            last_reviewed=now - timedelta(days=i),
            next_review=now + timedelta(days=i),
            times_reviewed=i,
            is_learned=(i == 2)
        )
        user_words.append(user_word)
        db.add(user_word)

    db.commit()
    return [db.refresh(user_word) or user_word for user_word in user_words]


@pytest.fixture(autouse=True)
def cleanup_db(db):
    """Clean up database after each test"""
    yield
    db.rollback()