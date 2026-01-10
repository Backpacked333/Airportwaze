"""
Database configuration and session management.
Supports both PostgreSQL (production) and SQLite (local development).
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os
import logging

logger = logging.getLogger(__name__)

# Database URL from environment variable
# For PostgreSQL: postgresql://user:password@host:port/database
# For SQLite: sqlite:///./airportwaze.db
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./airportwaze.db"  # Default to SQLite for local development
)

# Determine database type
is_sqlite = DATABASE_URL.startswith("sqlite")

# Create engine with appropriate settings
if is_sqlite:
    logger.info("Using SQLite database for local development")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite with FastAPI
        echo=False  # Set to True for SQL debugging
    )
else:
    logger.info("Using PostgreSQL database")
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=False  # Set to True for SQL debugging
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency function for FastAPI to get database session.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database schema.
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)
