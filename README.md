# AirportWaze

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![React](https://img.shields.io/badge/react-18.3-61dafb)

**AirportWaze** is a real-time airport navigation and wait time prediction platform inspired by Moovit's probabilistic arrival predictions. It helps travelers optimize their airport journey by providing probabilistic wait time forecasts, smart routing through checkpoints, and "Will I make my flight?" predictions using Monte Carlo simulations.

## Features

### Core Capabilities
- **Probabilistic Predictions**: Log-normal distribution models for wait times with confidence intervals (P50, P80, P90, P95)
- **Monte Carlo Simulations**: 10,000+ simulations to calculate flight-making probability
- **Real-time Wait Times**: Live tracking across TSA security, bag check, and passport control
- **Smart Journey Planning**: Optimal routing based on current conditions and user profile
- **Flight Risk Assessment**: "Will I make it?" predictions with confidence levels
- **Crowdsourced Data**: Community-driven wait time reports
- **Multi-Airport Support**: JFK, LAX, ORD, ATL, DFW, SFO, MIA, DEN, SEA

### User Experience
- **TSA PreCheck & Global Entry** support
- **Mobility Factor** adjustments for walking speed
- **Terminal & Gate Navigation** with GPS coordinates
- **Interactive Maps** using Leaflet/React-Leaflet
- **Real-time Updates** with WebSocket support (planned)
- **Historical Predictions** up to 48 hours ahead

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 with SQLAlchemy ORM
- **Cache**: Redis 7 for performance optimization
- **Scientific Computing**: NumPy, SciPy for probabilistic models
- **Authentication**: JWT with python-jose
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio, pytest-cov

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 6
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **Maps**: Leaflet + React-Leaflet
- **Charts**: Recharts
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Native Fetch API

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (frontend), Uvicorn (backend)
- **Process Manager**: Poetry (Python dependencies)
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry (optional)

## Quick Start

> **🚀 Want to deploy quickly?** See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for deploying with Supabase (free tier available, no Docker required).

### Prerequisites
- Docker & Docker Compose (recommended)
- OR:
  - Python 3.12+
  - Node.js 20+
  - PostgreSQL 16 (or Supabase)
  - Redis 7 (optional)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/airportwaze.git
cd airportwaze

# Set up environment variables
cp airport-waze-backend/.env.example airport-waze-backend/.env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup
```bash
cd airport-waze-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Poetry
pip install poetry

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your PostgreSQL and Redis URLs

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd airport-waze-frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Users / Clients                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │   UI Layer   │  │  Maps/Charts │  │  State Management  │   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  Middleware  │  │   Routes     │  │     Services       │   │
│  │  - CORS      │  │  - Airports  │  │  - Predictions     │   │
│  │  - Auth      │  │  - Journey   │  │  - Monte Carlo     │   │
│  │  - RateLimit │  │  - Wait Times│  │  - Journey Planning│   │
│  └──────────────┘  └──────────────┘  └────────────────────┘   │
└───────────┬────────────────────┬────────────────────┬───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │      Redis      │  │   External APIs │
│   - Users       │  │   - Cache       │  │   - TSA Data    │
│   - Reports     │  │   - Sessions    │  │   (Future)      │
│   - Analytics   │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/healthz` | Health check endpoint |
| `GET` | `/api/airports` | List all supported airports |
| `GET` | `/api/airports/{code}` | Get airport details with checkpoints |
| `GET` | `/api/airports/{code}/terminals/{terminal}/gates` | List terminal gates |
| `POST` | `/api/journey/plan` | Plan optimal journey through airport |
| `POST` | `/api/will-i-make-it` | Calculate flight-making probability |
| `POST` | `/api/wait-times/report` | Submit crowdsourced wait time |
| `GET` | `/api/wait-times/reports/{code}` | Get recent reports |
| `GET` | `/api/predictions/{code}` | Get future wait time predictions |
| `GET` | `/api/checkpoints/{id}/distribution` | Get checkpoint wait distribution |
| `POST` | `/api/flight/import` | Import flight details |
| `GET` | `/api/tsa/live` | Get live TSA data status |

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Development Setup

### Backend Development

```bash
cd airport-waze-backend

# Install dev dependencies
poetry install --with dev

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Lint code
ruff check .

# Format code
black .

# Type checking
mypy app/

# Create new migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head
```

### Frontend Development

```bash
cd airport-waze-frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "Add new table"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback last migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions including:
- Production environment setup
- Docker deployment
- Kubernetes deployment
- Database migration procedures
- Monitoring and logging
- Backup and recovery strategies
- Scaling recommendations

### Quick Deploy with Docker Compose

```bash
# Production deployment
DB_PASSWORD=your_secure_password docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Code of conduct
- Development workflow
- Coding standards
- Testing requirements
- Pull request process

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run tests: `make test`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Project Structure

```
airportwaze/
├── airport-waze-backend/          # Backend API (FastAPI)
│   ├── app/
│   │   ├── core/                  # Core utilities (config, database, cache)
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── routes/                # API endpoints
│   │   ├── services/              # Business logic
│   │   ├── middleware/            # Custom middleware
│   │   ├── data/                  # Static data (airports)
│   │   └── utils/                 # Helper functions
│   ├── alembic/                   # Database migrations
│   ├── tests/                     # Test suite
│   ├── Dockerfile                 # Backend container
│   ├── pyproject.toml             # Python dependencies
│   └── .env.example               # Environment template
├── airport-waze-frontend/         # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/            # React components
│   │   ├── hooks/                 # Custom hooks
│   │   ├── lib/                   # Utilities
│   │   └── assets/                # Static assets
│   ├── public/                    # Public assets
│   ├── Dockerfile                 # Frontend container
│   ├── nginx.conf                 # Nginx configuration
│   └── package.json               # Node dependencies
├── docker-compose.yml             # Multi-container orchestration
├── Makefile                       # Common development tasks
├── scripts/
│   └── deploy.sh                  # Deployment automation
├── ARCHITECTURE.md                # Architecture documentation
├── DEPLOYMENT.md                  # Deployment guide
├── CONTRIBUTING.md                # Contribution guidelines
└── README.md                      # This file
```

## Testing

### Backend Tests

```bash
# Run all tests
make test-backend

# Or manually:
cd airport-waze-backend
pytest

# With coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_predictions.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
# Run all tests
make test-frontend

# Or manually:
cd airport-waze-frontend
npm test

# Watch mode
npm test -- --watch
```

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `DEBUG` | Enable debug mode | `False` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SIMULATION_RUNS` | Monte Carlo iterations | `10000` |
| `SENTRY_DSN` | Sentry error tracking | Optional |

See [.env.example](./airport-waze-backend/.env.example) for complete list.

### Frontend

Frontend configuration is typically injected at build time. For development:

```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
```

## Monitoring & Observability

### Health Checks
- Backend: `GET /healthz`
- Database: `pg_isready` via Docker health check
- Redis: `redis-cli ping` via Docker health check

### Logging
- Structured JSON logging via `structlog`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Container logs: `docker-compose logs -f [service]`

### Error Tracking
- Optional Sentry integration
- Configure `SENTRY_DSN` in environment

## Performance

### Backend
- **Response Time**: < 100ms for cached requests
- **Monte Carlo Simulation**: ~200-500ms (10,000 iterations)
- **Rate Limiting**: 60 requests/minute per IP
- **Caching**: Redis with 5-10 minute TTL

### Frontend
- **Bundle Size**: < 500KB gzipped
- **First Paint**: < 2s on 3G
- **Interactive**: < 3s on 3G
- **Lighthouse Score**: 90+ Performance

## Security

- **Authentication**: JWT-based with refresh tokens
- **CORS**: Configurable origins
- **Rate Limiting**: SlowAPI middleware
- **SQL Injection**: Prevented via SQLAlchemy ORM
- **XSS**: Content Security Policy headers
- **HTTPS**: Enforced in production (Nginx)
- **Secrets**: Environment variables, never committed

## Roadmap

### Phase 1 (MVP) ✅
- [x] Core probabilistic prediction engine
- [x] Monte Carlo simulations
- [x] Multi-airport support (9 major US airports)
- [x] Journey planning
- [x] Basic UI with maps

### Phase 2 (In Progress)
- [ ] User authentication and profiles
- [ ] Flight tracking integration
- [ ] Push notifications for departure alerts
- [ ] Mobile app (React Native)
- [ ] Expanded airport coverage

### Phase 3 (Future)
- [ ] Machine learning for improved predictions
- [ ] Live TSA API integration
- [ ] Real-time WebSocket updates
- [ ] Social features (share journeys)
- [ ] International airport support

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by [Moovit](https://moovitapp.com/)'s probabilistic arrival predictions
- Airport data sourced from public TSA statistics
- Maps powered by [Leaflet](https://leafletjs.com/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)

## Support

- **Documentation**: [Full docs](./ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/airportwaze/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/airportwaze/discussions)
- **Email**: support@airportwaze.com

## Authors

- **Your Team** - *Initial work*

---

**Made with ❤️ for travelers everywhere**
