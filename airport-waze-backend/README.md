# AirportWaze Backend API

FastAPI-based backend service providing real-time airport wait time predictions and journey planning with probabilistic modeling using Monte Carlo simulations.

## Overview

The backend is built with **FastAPI** and uses **PostgreSQL** for persistence, **Redis** for caching, and **NumPy/SciPy** for statistical computations. It implements log-normal distributions for wait time predictions and runs Monte Carlo simulations to calculate flight-making probabilities.

## Features

- **RESTful API** with automatic OpenAPI documentation
- **Probabilistic Predictions** using log-normal distributions
- **Monte Carlo Simulations** (10,000+ iterations per request)
- **Real-time Caching** with Redis
- **JWT Authentication** with refresh tokens
- **Rate Limiting** to prevent abuse
- **Database Migrations** with Alembic
- **Structured Logging** with JSON output
- **Type Safety** with Pydantic v2
- **Comprehensive Testing** with pytest

## Tech Stack

- **Python**: 3.12+
- **Framework**: FastAPI 0.128+
- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Cache**: Redis 7
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib with bcrypt
- **Validation**: Pydantic v2
- **Scientific Computing**: NumPy, SciPy
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, ruff, mypy
- **Monitoring**: Sentry (optional)

## Project Structure

```
airport-waze-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── main_v2.py                 # Latest version with Monte Carlo
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic settings
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── cache.py               # Redis client
│   │   ├── security.py            # Auth utilities
│   │   └── logging.py             # Structured logging
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   └── wait_time_report.py   # Wait time report model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── airport.py             # Airport schemas
│   │   ├── checkpoint.py          # Checkpoint schemas
│   │   ├── flight.py              # Flight schemas
│   │   ├── journey.py             # Journey planning schemas
│   │   ├── wait_time.py           # Wait time schemas
│   │   └── user.py                # User schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── airports.py            # Airport endpoints
│   │   ├── journey.py             # Journey planning
│   │   ├── predictions.py         # Wait time predictions
│   │   ├── wait_times.py          # Crowdsourced reports
│   │   ├── auth.py                # Authentication
│   │   ├── tsa.py                 # TSA data integration
│   │   └── health.py              # Health checks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── airport_service.py     # Airport business logic
│   │   ├── journey_service.py     # Journey planning logic
│   │   ├── prediction_service.py  # Prediction algorithms
│   │   ├── wait_time_service.py   # Wait time aggregation
│   │   └── auth_service.py        # Auth logic
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── error_handler.py       # Global error handling
│   │   ├── logging.py             # Request/response logging
│   │   └── rate_limit.py          # Rate limiting
│   ├── data/
│   │   ├── __init__.py
│   │   └── airports.py            # Static airport data
│   └── utils/
│       ├── __init__.py
│       └── calculations.py        # Helper functions
├── alembic/
│   ├── versions/                  # Migration files
│   ├── env.py                     # Alembic environment
│   └── script.py.mako             # Migration template
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── test_airports.py
│   ├── test_journey.py
│   ├── test_predictions.py
│   └── test_auth.py
├── Dockerfile                     # Multi-stage Docker build
├── pyproject.toml                 # Poetry dependencies
├── poetry.lock                    # Locked dependencies
├── alembic.ini                    # Alembic configuration
├── pytest.ini                     # pytest configuration
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Poetry (recommended) or pip

### Installation

#### Option 1: Using Poetry (Recommended)

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Create virtual environment and install dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### Option 2: Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry
pip install poetry

# Install dependencies
poetry install
```

### Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

#### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/airportwaze

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (Generate secure random key!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Application
DEBUG=True
ENV=development
LOG_LEVEL=DEBUG
```

### Database Setup

#### Start PostgreSQL (Docker)

```bash
docker run --name airportwaze-postgres \
  -e POSTGRES_USER=airportwaze \
  -e POSTGRES_PASSWORD=changeme \
  -e POSTGRES_DB=airportwaze \
  -p 5432:5432 \
  -d postgres:16-alpine
```

#### Run Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Downgrade one version
alembic downgrade -1

# View migration history
alembic history
```

### Redis Setup

```bash
docker run --name airportwaze-redis \
  -p 6379:6379 \
  -d redis:7-alpine
```

## Running the Application

### Development Server

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the latest version
uvicorn app.main_v2:app --reload --host 0.0.0.0 --port 8000

# With auto-reload on code changes
uvicorn app.main:app --reload --log-level debug
```

### Production Server

```bash
# Using multiple workers
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --access-log \
  --log-config logging.json

# Or with Gunicorn + Uvicorn workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Docker

```bash
# Build image
docker build -t airportwaze-backend .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  airportwaze-backend
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing

### Run All Tests

```bash
# Using pytest
pytest

# With coverage
pytest --cov=app --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Specific Tests

```bash
# Single test file
pytest tests/test_predictions.py

# Single test function
pytest tests/test_predictions.py::test_monte_carlo_simulation

# Tests matching pattern
pytest -k "test_airport"

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Test Coverage Goals

- **Overall Coverage**: > 85%
- **Core Services**: > 90%
- **API Routes**: > 80%
- **Models**: 100%

## Code Quality

### Formatting

```bash
# Format code with black
black .

# Check formatting without changes
black --check .
```

### Linting

```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Type Checking

```bash
# Run mypy
mypy app/

# Strict mode
mypy --strict app/
```

### All Quality Checks

```bash
# Run all checks
black --check . && ruff check . && mypy app/ && pytest
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user profile fields"

# Create empty migration for manual changes
alembic revision -m "Add custom index"
```

### Applying Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade abc123

# Upgrade one version
alembic upgrade +1
```

### Rolling Back

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade abc123

# Downgrade to base (WARNING: drops all tables)
alembic downgrade base
```

### Migration History

```bash
# View history
alembic history

# Current version
alembic current

# Show SQL without executing
alembic upgrade head --sql
```

## API Endpoints

### Health & Status

```bash
GET /healthz
```

### Airports

```bash
# List all airports
GET /api/airports

# Get airport details
GET /api/airports/{airport_code}

# Get terminal gates
GET /api/airports/{airport_code}/terminals/{terminal}/gates
```

### Journey Planning

```bash
# Plan optimal journey
POST /api/journey/plan
{
  "airport_code": "JFK",
  "terminal": "Terminal 4",
  "gate": "A1",
  "has_tsa_precheck": true,
  "has_checked_bags": false,
  "mobility_factor": 1.0,
  "departure_time": "2024-01-15T14:30:00Z"
}
```

### Probabilistic Predictions

```bash
# Will I make my flight?
POST /api/will-i-make-it
{
  "flight": {
    "flight_number": "AA100",
    "airline": "American Airlines",
    "departure_time": "2024-01-15T14:30:00Z",
    "terminal": "Terminal 4",
    "gate": "A1",
    "airport_code": "JFK"
  },
  "has_tsa_precheck": true,
  "has_checked_bags": false,
  "mobility_factor": 1.0,
  "current_time": "2024-01-15T12:00:00Z"
}
```

### Wait Time Predictions

```bash
# Get predictions for next 24 hours
GET /api/predictions/{airport_code}?hours_ahead=24

# Get checkpoint distribution
GET /api/checkpoints/{checkpoint_id}/distribution
```

### Crowdsourced Reports

```bash
# Submit wait time report
POST /api/wait-times/report
{
  "airport_code": "JFK",
  "checkpoint_id": "jfk-t4-tsa-1",
  "reported_wait_minutes": 15
}

# Get recent reports
GET /api/wait-times/reports/{airport_code}?limit=20
```

## Configuration

### Core Settings

All settings are managed through `app/core/config.py` using Pydantic Settings:

```python
from app.core.config import settings

# Access settings
print(settings.DATABASE_URL)
print(settings.REDIS_URL)
print(settings.SIMULATION_RUNS)
```

### Environment Variables

See [.env.example](./.env.example) for complete list of configuration options.

## Monitoring & Logging

### Structured Logging

```python
from app.core.logging import logger

# Log with structured data
logger.info("journey_planned",
           airport_code="JFK",
           total_time=45,
           probability=0.87)
```

### Sentry Integration

```bash
# Enable Sentry in .env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

## Performance Optimization

### Caching Strategy

- **Airports**: 1 hour TTL
- **Predictions**: 10 minutes TTL
- **Wait Times**: 5 minutes TTL
- **User Sessions**: 30 minutes TTL

### Database Optimization

- Connection pooling (5 connections, 10 overflow)
- Query result caching for frequent reads
- Indexes on frequently queried fields
- Efficient joins using SQLAlchemy relationships

### Rate Limiting

- 60 requests/minute per IP
- 1000 requests/hour per IP
- Configurable via environment variables

## Deployment

See [../DEPLOYMENT.md](../DEPLOYMENT.md) for production deployment guide.

### Quick Docker Deploy

```bash
# Build
docker build -t airportwaze-backend .

# Run
docker run -d \
  --name airportwaze-backend \
  -p 8000:8000 \
  --env-file .env \
  airportwaze-backend

# View logs
docker logs -f airportwaze-backend
```

## Troubleshooting

### Common Issues

#### Database Connection Error

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Test connection
psql -h localhost -U airportwaze -d airportwaze
```

#### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping

# Should return: PONG
```

#### Migration Error

```bash
# Reset to clean state (WARNING: destroys data)
alembic downgrade base
alembic upgrade head

# Or manually drop and recreate database
dropdb airportwaze
createdb airportwaze
alembic upgrade head
```

#### Import Errors

```bash
# Reinstall dependencies
poetry install --no-cache

# Or clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

## Contributing

1. Follow PEP 8 style guide
2. Use type hints for all functions
3. Write docstrings for public APIs
4. Add tests for new features
5. Update API documentation
6. Run quality checks before committing

```bash
# Pre-commit checklist
black .
ruff check --fix .
mypy app/
pytest --cov=app
```

## License

MIT License - see [../LICENSE](../LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/airportwaze/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md)
