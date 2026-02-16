"""
Pytest configuration and shared fixtures for AirportWaze tests.
"""
import pytest
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///./test.db")
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["TSA_API_KEY"] = "test-tsa-api-key"
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/1")

from app.core.database import Base, get_db
from app.models import User, WaitTimeReport


# Test database setup
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before running tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def override_get_db(db: Session):
    """Override the get_db dependency with test database."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass
    return _override_get_db


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user in the database."""
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = User(
        email="testuser@example.com",
        hashed_password=pwd_context.hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        has_tsa_precheck=True,
        has_global_entry=False,
        default_mobility_factor="1.0"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def test_wait_time_reports(db: Session) -> list[WaitTimeReport]:
    """Create sample wait time reports in the database."""
    from datetime import datetime, timedelta

    reports = []
    base_time = datetime.utcnow()

    for i in range(10):
        report = WaitTimeReport(
            airport_code="JFK",
            checkpoint_id="jfk_t4_security_main",
            reported_wait_minutes=10 + (i * 2),
            reporter_id=f"test-reporter-{i}",
            user_lat=40.6413,
            user_lng=-73.7781,
            created_at=base_time - timedelta(minutes=i * 5)
        )
        reports.append(report)
        db.add(report)

    db.commit()

    return reports


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Generate authentication headers for testing protected endpoints."""
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(autouse=True)
def reset_redis_cache():
    """Clear Redis cache before each test (if Redis is available)."""
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        r = redis.from_url(redis_url)
        r.flushdb()
    except Exception:
        # Redis not available in test environment, skip
        pass

    yield


@pytest.fixture
def mock_tsa_api_response():
    """Mock TSA API response for testing."""
    return {
        "airports": [
            {
                "code": "JFK",
                "name": "John F. Kennedy International Airport",
                "checkpoints": [
                    {
                        "checkpoint_id": "jfk_t4_security_main",
                        "terminal": "4",
                        "wait_time_minutes": 15,
                        "last_updated": "2026-01-11T12:00:00Z"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_external_flight_api():
    """Mock external flight API responses."""
    return {
        "flight_number": "AA100",
        "departure_time": "2026-01-11T14:30:00Z",
        "terminal": "8",
        "gate": "B20",
        "status": "On Time"
    }


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring database/services"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication and authorization tests"
    )
    config.addinivalue_line(
        "markers", "database: Database-related tests"
    )
    config.addinivalue_line(
        "markers", "cache: Redis cache tests"
    )
    config.addinivalue_line(
        "markers", "external: Tests requiring external API calls"
    )
