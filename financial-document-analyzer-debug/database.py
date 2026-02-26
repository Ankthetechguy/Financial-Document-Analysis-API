"""
Database initialization and session management
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DB_URL, SQLALCHEMY_ECHO

# Create engine
engine = create_engine(
    DB_URL,
    echo=SQLALCHEMY_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session in FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
