# AirportWaze Architecture

Comprehensive technical architecture documentation for AirportWaze, including system design, component interactions, data models, and design decisions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Technology Stack](#technology-stack)
- [Component Architecture](#component-architecture)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Probabilistic Prediction Model](#probabilistic-prediction-model)
- [Caching Strategy](#caching-strategy)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)
- [Design Decisions](#design-decisions)

## System Overview

AirportWaze is a real-time airport navigation platform that uses probabilistic modeling to predict wait times and journey durations. The system is built on a modern microservices-inspired architecture with clear separation between frontend, backend, and data layers.

### Key Features

- **Probabilistic Wait Time Predictions**: Log-normal distributions with P50, P80, P90, P95 percentiles
- **Monte Carlo Simulations**: 10,000+ iterations for flight probability calculations
- **Real-time Data**: Crowdsourced wait time reports
- **Multi-Airport Support**: 9 major US airports (JFK, LAX, ORD, ATL, DFW, SFO, MIA, DEN, SEA)
- **Journey Planning**: Optimal routing through airport checkpoints
- **RESTful API**: Comprehensive API with OpenAPI documentation

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Web App    │  │  Mobile App  │  │   Third-party API        │  │
│  │  (React)     │  │  (Future)    │  │   Clients                │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
└─────────┼──────────────────┼───────────────────┼────────────────────┘
          │                  │                   │
          │              HTTPS/REST API          │
          └──────────────────┼───────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────┐
│                     Application Layer                               │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────┐      │
│  │              Nginx Reverse Proxy                          │      │
│  │    - SSL Termination                                      │      │
│  │    - Load Balancing                                       │      │
│  │    - Rate Limiting                                        │      │
│  └─────────┬────────────────────────────────┬────────────────┘      │
│            │                                │                        │
│  ┌─────────▼──────────┐         ┌──────────▼──────────┐            │
│  │  Frontend (Nginx)  │         │  Backend API        │            │
│  │  - React SPA       │         │  (FastAPI)          │            │
│  │  - Static Assets   │         │  - Business Logic   │            │
│  │  - Client Routing  │         │  - API Endpoints    │            │
│  └────────────────────┘         └──────────┬──────────┘            │
└──────────────────────────────────────────────┼────────────────────────┘
                                              │
┌──────────────────────────────────────────────┼────────────────────────┐
│                      Service Layer           │                        │
│  ┌─────────────────┬─────────────────┬──────▼────────┬────────────┐ │
│  │  Prediction     │  Journey        │  Airport      │  Auth      │ │
│  │  Service        │  Service        │  Service      │  Service   │ │
│  │                 │                 │               │            │ │
│  │  - Monte Carlo  │  - Path Finding │  - Data Mgmt  │  - JWT     │ │
│  │  - Distributions│  - Optimization │  - Checkpoints│  - Tokens  │ │
│  └────────┬────────┴─────────┬───────┴──────┬────────┴────────────┘ │
└───────────┼──────────────────┼───────────────┼──────────────────────┘
            │                  │               │
┌───────────┼──────────────────┼───────────────┼──────────────────────┐
│     Data Layer               │               │                       │
│  ┌──────────▼────────┐  ┌───▼──────────┐  ┌▼──────────────┐       │
│  │  PostgreSQL DB    │  │  Redis Cache  │  │ Static Data   │       │
│  │                   │  │               │  │               │       │
│  │  - Users          │  │  - Sessions   │  │  - Airports   │       │
│  │  - Reports        │  │  - Predictions│  │  - Gates      │       │
│  │  - History        │  │  - API Cache  │  │  - Terminals  │       │
│  └───────────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────────┘

                              External Services
┌─────────────────────────────────────────────────────────────────────┐
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐    │
│  │  TSA API       │  │  Sentry         │  │  Future:         │    │
│  │  (Planned)     │  │  (Monitoring)   │  │  - Flight APIs   │    │
│  │                │  │                 │  │  - Weather APIs  │    │
│  └────────────────┘  └─────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend
```
React 18.3           → UI Framework
TypeScript 5.6       → Type Safety
Vite 6.0             → Build Tool
Tailwind CSS 3.4     → Styling
shadcn/ui            → UI Components (Radix UI)
Leaflet 1.9          → Interactive Maps
Recharts 2.12        → Data Visualization
React Hook Form 7.70 → Form Management
Zod 4.3              → Schema Validation
```

### Backend
```
Python 3.12          → Programming Language
FastAPI 0.128        → Web Framework
SQLAlchemy 2.0       → ORM
Alembic 1.13         → Database Migrations
Pydantic 2.12        → Data Validation
NumPy 2.4            → Numerical Computing
SciPy 1.16           → Statistical Functions
python-jose 3.3      → JWT Authentication
Redis 5.0 (client)   → Caching Client
httpx 0.28           → HTTP Client
structlog 24.1       → Structured Logging
```

### Infrastructure
```
PostgreSQL 16        → Primary Database
Redis 7              → Cache & Session Store
Nginx 1.25           → Reverse Proxy & Static Files
Docker 20.10+        → Containerization
Docker Compose v2    → Multi-container Orchestration
```

## Component Architecture

### Backend Components

#### 1. API Layer (`app/routes/`)

```python
routes/
├── airports.py      # Airport CRUD operations
├── journey.py       # Journey planning endpoints
├── predictions.py   # Wait time predictions
├── wait_times.py    # Crowdsourced reports
├── auth.py          # Authentication endpoints
├── tsa.py           # TSA data integration
└── health.py        # Health checks
```

**Responsibilities:**
- HTTP request/response handling
- Input validation (Pydantic schemas)
- Response formatting
- Error handling

#### 2. Service Layer (`app/services/`)

```python
services/
├── prediction_service.py    # Monte Carlo simulations
├── journey_service.py       # Journey optimization
├── airport_service.py       # Airport data management
├── wait_time_service.py     # Wait time aggregation
└── auth_service.py          # Authentication logic
```

**Responsibilities:**
- Business logic implementation
- Service orchestration
- Data transformation
- External API integration

#### 3. Data Layer (`app/models/`, `app/schemas/`)

```python
models/                     # SQLAlchemy ORM Models
├── user.py                 # User account model
└── wait_time_report.py     # Crowdsourced report model

schemas/                    # Pydantic Schemas
├── airport.py              # Airport data structures
├── checkpoint.py           # Checkpoint schemas
├── flight.py               # Flight information
├── journey.py              # Journey planning schemas
├── wait_time.py            # Wait time structures
└── user.py                 # User schemas
```

#### 4. Core Infrastructure (`app/core/`)

```python
core/
├── config.py       # Application configuration
├── database.py     # Database connection & session
├── cache.py        # Redis client & operations
├── security.py     # JWT & password hashing
└── logging.py      # Structured logging setup
```

#### 5. Middleware (`app/middleware/`)

```python
middleware/
├── error_handler.py    # Global exception handling
├── logging.py          # Request/response logging
└── rate_limit.py       # Rate limiting
```

### Frontend Components

```
src/
├── components/
│   ├── ui/                 # shadcn/ui base components
│   ├── AirportMap.tsx      # Leaflet map component
│   ├── CheckpointCard.tsx  # Checkpoint status display
│   ├── FlightForm.tsx      # Flight input form
│   ├── JourneyPlanner.tsx  # Journey planning UI
│   ├── ProbabilityDisplay.tsx  # Probability visualization
│   └── WaitTimeChart.tsx   # Wait time charts
├── hooks/
│   ├── useAirports.ts      # Airport data fetching
│   ├── useJourney.ts       # Journey planning hook
│   ├── usePrediction.ts    # Probability predictions
│   └── useWaitTimes.ts     # Wait time data
├── lib/
│   ├── api.ts              # API client wrapper
│   ├── utils.ts            # Utility functions
│   └── types.ts            # TypeScript type definitions
└── App.tsx                 # Main application
```

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

### Wait Time Reports Table

```sql
CREATE TABLE wait_time_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airport_code VARCHAR(10) NOT NULL,
    checkpoint_id VARCHAR(50) NOT NULL,
    reported_wait_minutes INTEGER NOT NULL,
    user_id UUID REFERENCES users(id),
    user_lat DOUBLE PRECISION,
    user_lng DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_wait_minutes CHECK (reported_wait_minutes >= 0 AND reported_wait_minutes <= 300)
);

CREATE INDEX idx_reports_airport ON wait_time_reports(airport_code);
CREATE INDEX idx_reports_checkpoint ON wait_time_reports(checkpoint_id);
CREATE INDEX idx_reports_created ON wait_time_reports(created_at DESC);
```

### Future Tables (Planned)

```sql
-- User Preferences
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    has_tsa_precheck BOOLEAN DEFAULT FALSE,
    has_global_entry BOOLEAN DEFAULT FALSE,
    mobility_factor DECIMAL(3,2) DEFAULT 1.0,
    preferred_airports TEXT[],
    notification_enabled BOOLEAN DEFAULT TRUE
);

-- Journey History
CREATE TABLE journey_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    airport_code VARCHAR(10) NOT NULL,
    flight_number VARCHAR(20),
    departure_time TIMESTAMP NOT NULL,
    actual_journey_time INTEGER,
    predicted_time INTEGER,
    made_flight BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics (aggregated data)
CREATE TABLE checkpoint_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    checkpoint_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    avg_wait_minutes INTEGER,
    p50_wait_minutes INTEGER,
    p80_wait_minutes INTEGER,
    p90_wait_minutes INTEGER,
    p95_wait_minutes INTEGER,
    sample_count INTEGER,

    UNIQUE(checkpoint_id, date, hour)
);
```

## API Design

### RESTful Principles

- **Resource-oriented URLs**: `/api/airports/{code}`
- **HTTP methods**: GET, POST, PUT, DELETE
- **JSON payloads**: Standard request/response format
- **HTTP status codes**: Proper use of 2xx, 4xx, 5xx
- **Pagination**: `?limit=20&offset=0`
- **Filtering**: `?airport_code=JFK&hours_ahead=24`

### API Versioning

Current: `/api/*` (v1 implicit)
Future: `/api/v2/*` for breaking changes

### Response Format

```json
{
  "status": "success",
  "data": {
    // Response payload
  },
  "meta": {
    "timestamp": "2024-01-15T12:00:00Z",
    "request_id": "uuid"
  }
}
```

### Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "AIRPORT_NOT_FOUND",
    "message": "Airport code 'XYZ' not found",
    "details": {}
  },
  "meta": {
    "timestamp": "2024-01-15T12:00:00Z",
    "request_id": "uuid"
  }
}
```

### Endpoint Structure

```
/healthz                                    # Health check
/api/airports                               # List airports
/api/airports/{code}                        # Get airport
/api/airports/{code}/terminals/{terminal}/gates  # Get gates
/api/journey/plan                           # Plan journey (POST)
/api/will-i-make-it                         # Calculate probability (POST)
/api/predictions/{code}                     # Get predictions
/api/checkpoints/{id}/distribution          # Get wait distribution
/api/wait-times/report                      # Submit report (POST)
/api/wait-times/reports/{code}              # Get reports
/api/tsa/live                               # TSA data status
/api/auth/login                             # Login (POST)
/api/auth/register                          # Register (POST)
/api/auth/refresh                           # Refresh token (POST)
```

## Probabilistic Prediction Model

### Overview

AirportWaze uses **log-normal distributions** to model wait times, inspired by Moovit's probabilistic transit predictions. This provides realistic confidence intervals rather than single-point estimates.

### Log-Normal Distribution

**Why log-normal?**
- Wait times are always positive
- Distribution is right-skewed (long tail)
- Realistic for queueing systems
- Natural variance representation

**Parameters:**
- `μ (mu)`: Mean of log-transformed wait times
- `σ (sigma)`: Standard deviation of log-transformed wait times

### Percentile Calculation

```python
def get_wait_time_distribution(base_wait: int, checkpoint_type: str) -> WaitTimeDistribution:
    """Generate log-normal distribution for checkpoint wait time."""
    multiplier = get_time_multiplier()  # Time-of-day adjustment
    median_wait = max(2, base_wait * multiplier)

    # Variance depends on checkpoint type
    sigma_map = {
        "bag_check": 0.5,       # High variance
        "tsa": 0.4,             # Moderate variance
        "tsa_precheck": 0.25,   # Low variance (predictable)
        "passport_control": 0.45
    }
    sigma = sigma_map.get(checkpoint_type, 0.4)

    # For log-normal: median = e^μ
    mu = np.log(median_wait)

    # Calculate percentiles
    p50 = int(np.exp(mu))  # Median
    p80 = int(np.exp(mu + sigma * stats.norm.ppf(0.80)))
    p90 = int(np.exp(mu + sigma * stats.norm.ppf(0.90)))
    p95 = int(np.exp(mu + sigma * stats.norm.ppf(0.95)))

    return WaitTimeDistribution(p50, p80, p90, p95, mu, sigma, ...)
```

### Monte Carlo Simulation

**Purpose:** Calculate probability of making flight given journey time distribution

**Algorithm:**
1. Run 10,000 simulations
2. For each simulation:
   - Sample wait time from each checkpoint's log-normal distribution
   - Sample walking time with variance
   - Sum total journey time
3. Calculate proportion of simulations where total time ≤ time available

```python
def run_monte_carlo_simulation(segments, num_simulations=10000):
    """Run Monte Carlo simulation for journey time."""
    total_times = np.zeros(num_simulations)

    for i in range(num_simulations):
        total = 0
        for segment in segments:
            # Sample from distributions
            if segment.wait_distribution:
                wait = sample_wait_time(segment.wait_distribution)
            else:
                wait = 0

            walk = sample_walking_time(segment.walk_minutes, segment.mobility_factor)
            total += wait + walk

        total_times[i] = total

    return total_times

def calculate_probability(total_times, time_available):
    """Calculate probability of making it."""
    return float(np.mean(total_times <= time_available))
```

### Time-of-Day Adjustments

```python
def get_time_multiplier() -> float:
    """Adjust base wait times based on time of day and week."""
    now = datetime.utcnow()
    hour = now.hour
    day = now.weekday()  # 0=Monday, 6=Sunday

    # Peak hours: 6-9 AM, 4-8 PM
    if 6 <= hour <= 9 or 16 <= hour <= 20:
        multiplier = 1.4
    # Overnight: 10 PM - 5 AM
    elif 22 <= hour or hour <= 5:
        multiplier = 0.6
    else:
        multiplier = 1.0

    # Weekend adjustment (Fri-Sun)
    if day in [4, 5, 6]:
        multiplier *= 1.2

    return multiplier
```

## Caching Strategy

### Cache Layers

```
┌─────────────────────────────────────┐
│     Application Cache (Redis)       │
│  - API responses (5-10 min)         │
│  - User sessions (30 min)           │
│  - Predictions (10 min)              │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│     Database Query Cache             │
│  - SQLAlchemy query cache            │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│     PostgreSQL                       │
│  - Persistent storage                │
└─────────────────────────────────────┘
```

### Cache Keys

```python
# Airport data (1 hour TTL)
f"airport:{airport_code}"

# Wait time predictions (10 min TTL)
f"predictions:{airport_code}:{hours_ahead}"

# Checkpoint distribution (5 min TTL)
f"checkpoint:dist:{checkpoint_id}"

# User session (30 min TTL)
f"session:{user_id}"

# Rate limiting (1 min window)
f"ratelimit:{ip_address}:{window}"
```

### Cache Implementation

```python
# app/core/cache.py
import redis
from typing import Optional, Any
import json

class CacheClient:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL."""
        self.client.setex(key, ttl, json.dumps(value))

    def delete(self, key: str):
        """Delete key from cache."""
        self.client.delete(key)
```

### Cache Invalidation

- **Time-based**: TTL expiration
- **Event-based**: Invalidate on data update
- **Manual**: Admin cache flush

## Security Architecture

### Authentication Flow

```
1. User Login
   ↓
2. Validate Credentials (bcrypt)
   ↓
3. Generate JWT Access Token (30 min) + Refresh Token (7 days)
   ↓
4. Return tokens to client
   ↓
5. Client stores tokens (localStorage/cookie)
   ↓
6. Subsequent requests include access token in header
   ↓
7. Backend validates JWT signature
   ↓
8. If expired, client uses refresh token to get new access token
```

### JWT Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "email": "user@example.com",
    "exp": 1705334400,
    "iat": 1705332600,
    "type": "access"
  },
  "signature": "..."
}
```

### Security Measures

1. **Password Security**
   - bcrypt hashing (cost factor 12)
   - Minimum 8 characters
   - Complexity requirements

2. **API Security**
   - Rate limiting (60/min per IP)
   - CORS configuration
   - Input validation (Pydantic)
   - SQL injection prevention (ORM)

3. **Transport Security**
   - HTTPS/TLS 1.3
   - HSTS headers
   - Secure cookies (httponly, secure, samesite)

4. **Data Security**
   - Database encryption at rest
   - Secrets management (environment variables)
   - No sensitive data in logs

## Scalability & Performance

### Horizontal Scaling

```
           Load Balancer
                 │
    ┌────────────┼────────────┐
    │            │            │
Backend 1    Backend 2    Backend 3
    │            │            │
    └────────────┼────────────┘
                 │
          PostgreSQL + Redis
```

### Performance Optimizations

1. **Database**
   - Connection pooling (5 base, 10 overflow)
   - Indexes on frequently queried columns
   - Query optimization with EXPLAIN ANALYZE
   - Read replicas for heavy read workloads

2. **Caching**
   - Redis for hot data
   - CDN for static assets
   - Browser caching headers

3. **API**
   - Async/await (FastAPI)
   - Response compression (gzip)
   - Pagination for large result sets
   - Field selection (`?fields=id,name`)

4. **Frontend**
   - Code splitting
   - Lazy loading
   - Image optimization
   - Bundle size < 500KB

### Monitoring

- **Application Metrics**: Response time, error rate, throughput
- **System Metrics**: CPU, memory, disk, network
- **Business Metrics**: Active users, API calls, predictions made

## Design Decisions

### Why FastAPI?

✅ **Pros:**
- Automatic OpenAPI documentation
- Fast performance (async/await)
- Type hints with Pydantic
- Easy to learn and use
- Great ecosystem

### Why PostgreSQL?

✅ **Pros:**
- Mature and reliable
- ACID compliance
- Rich feature set (JSON, full-text search)
- Strong community support
- Excellent ORMs (SQLAlchemy)

### Why Redis?

✅ **Pros:**
- In-memory speed
- Simple key-value operations
- Built-in TTL support
- Pub/sub capabilities
- Widely used and battle-tested

### Why React + TypeScript?

✅ **Pros:**
- Large ecosystem
- Strong typing with TypeScript
- Component reusability
- Great developer experience
- Industry standard

### Why Log-Normal Distribution?

✅ **Pros:**
- Realistic for wait times (positive, right-skewed)
- Well-understood statistical properties
- Easy to calculate percentiles
- Used by Moovit (proven approach)

### Monorepo vs Multi-Repo

**Decision**: Monorepo (frontend + backend together)

✅ **Pros:**
- Easier to manage dependencies
- Shared documentation
- Atomic commits across stack
- Simplified deployment

### Microservices vs Monolith

**Decision**: Modular monolith (single backend, clear boundaries)

✅ **Pros:**
- Simpler to develop and deploy
- Lower operational complexity
- Easier debugging
- Can split later if needed

---

**Last Updated**: January 2026
**Version**: 2.0.0
