"""
Database configuration and session management.
Uses PostgreSQL with TimescaleDB extension for time-series data.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Database URL from environment variable
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://airportwaze:password@localhost:5432/airportwaze"
)

# Create engine with connection pooling
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
