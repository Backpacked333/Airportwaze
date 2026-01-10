# AirportWaze Setup Guide
## From MVP to Production with Real-Time Data Sources

This guide will help you set up the complete AirportWaze system with all the new features:
- PostgreSQL + TimescaleDB database
- TSA/CBP real-time wait times
- Flight data integration
- User telemetry collection
- Bayesian learning models
- Zone discovery algorithms

---

## Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.11+
- **PostgreSQL** 14+ with **TimescaleDB** extension
- **Redis** (optional, for caching)
- **Git**

---

## Part 1: Database Setup

### 1.1 Install PostgreSQL + TimescaleDB

**macOS (Homebrew):**
```bash
brew install postgresql@14
brew install timescaledb

# Start PostgreSQL
brew services start postgresql@14

# Enable TimescaleDB
sudo timescaledb-tune --quiet --yes
```

**Ubuntu/Debian:**
```bash
# Add PostgreSQL APT repository
sudo sh -c "echo 'deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main' > /etc/apt/sources.list.d/pgdg.list"
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

# Install PostgreSQL
sudo apt install postgresql-14 postgresql-contrib-14

# Add TimescaleDB repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update

# Install TimescaleDB
sudo apt install timescaledb-2-postgresql-14
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**Docker (Alternative):**
```bash
docker run -d --name airportwaze-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=airportwaze \
  -e POSTGRES_DB=airportwaze \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg14
```

### 1.2 Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create database and user
CREATE DATABASE airportwaze;
CREATE USER airportwaze WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE airportwaze TO airportwaze;

# Connect to new database
\c airportwaze

# Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS postgis;  # Optional, for geospatial queries

\q
```

### 1.3 Initialize Schema

```bash
cd airport-waze-backend

# Set database URL
export DATABASE_URL="postgresql://airportwaze:your_secure_password@localhost:5432/airportwaze"

# Install Python dependencies
poetry install  # or pip install -r requirements.txt

# Initialize database schema
python -c "from app.database import init_db; init_db()"

# Run initialization SQL
psql $DATABASE_URL < app/init_db.sql
```

### 1.4 Load Initial Airport Data

```bash
# Create a script to load existing airports into database
python scripts/load_airports.py
```

Create `/airport-waze-backend/scripts/load_airports.py`:

```python
from app.database import SessionLocal
from app.models import Airport, Checkpoint
from app.main import AIRPORTS_DATA

db = SessionLocal()

for code, data in AIRPORTS_DATA.items():
    # Create airport
    airport = Airport(
        code=code,
        name=data["name"],
        city=data["city"],
        lat=data["lat"],
        lng=data["lng"],
        terminals=data["terminals"]
    )
    db.add(airport)

    # Create checkpoints
    for cp_data in data["checkpoints"]:
        checkpoint = Checkpoint(
            id=cp_data["id"],
            airport_code=code,
            name=cp_data["name"],
            type=cp_data["type"],
            terminal=cp_data["terminal"],
            lat=cp_data["lat"],
            lng=cp_data["lng"],
            base_wait_minutes=cp_data["base_wait"],
            discovered=False
        )
        db.add(checkpoint)

db.commit()
db.close()
print("✅ Loaded airports and checkpoints into database")
```

---

## Part 2: Backend Configuration

### 2.1 Environment Variables

Create `/airport-waze-backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://airportwaze:your_secure_password@localhost:5432/airportwaze

# API Keys (optional but recommended)
FLIGHT_API_PROVIDER=aviation_edge  # or 'aerodatabox', 'flightaware', 'none'
FLIGHT_API_KEY=your_aviation_edge_api_key

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production  # or 'development'
LOG_LEVEL=INFO

# CORS (adjust for your frontend domain)
ALLOWED_ORIGINS=https://airport-waittimes-app-p9uty0v7.devinapps.com,http://localhost:5173
```

### 2.2 Update Dependencies

Add to `/airport-waze-backend/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
httpx = "^0.25.1"
numpy = "^1.26.2"
scipy = "^1.11.4"
python-dotenv = "^1.0.0"

# New dependencies
sqlalchemy = "^2.0.23"
psycopg2-binary = "^2.9.9"
alembic = "^1.13.0"
scikit-learn = "^1.3.2"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
black = "^23.11.0"
ruff = "^0.1.6"
```

Install:
```bash
poetry install
```

### 2.3 Update main.py to Use Database

Add to `/airport-waze-backend/app/main.py` (at the top):

```python
from app.database import init_db
from app import telemetry
from app.data_sources import TSAWaitTimeAPI, CBPWaitTimeAPI, FlightDataAPI
from app.bayesian_learning import HierarchicalWaitTimeModel
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

    # Initialize data sources
    app.state.tsa_api = TSAWaitTimeAPI()
    app.state.cbp_api = CBPWaitTimeAPI()
    app.state.flight_api = FlightDataAPI()
    app.state.bayesian_model = HierarchicalWaitTimeModel()

    logger.info("✅ AirportWaze backend started successfully")

# Include telemetry router
app.include_router(telemetry.router)
```

### 2.4 Start Backend

```bash
cd airport-waze-backend

# Development
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production (with Gunicorn)
poetry run gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

---

## Part 3: Frontend Configuration

### 3.1 Environment Variables

Create `/airport-waze-frontend/.env.production`:

```bash
VITE_API_URL=https://app-awudjxxy.fly.dev  # or your backend URL
```

For local development (`.env.development`):

```bash
VITE_API_URL=http://localhost:8000
```

### 3.2 Update Dependencies

Add to `/airport-waze-frontend/package.json`:

```json
{
  "dependencies": {
    ...existing dependencies...,
    "@radix-ui/react-checkbox": "^1.0.4"
  }
}
```

Install:
```bash
cd airport-waze-frontend
npm install
```

### 3.3 Start Frontend

```bash
# Development
npm run dev

# Production build
npm run build
npm run preview
```

---

## Part 4: Background Workers (Optional but Recommended)

Set up periodic jobs for data updates and learning.

### 4.1 Create Worker Script

Create `/airport-waze-backend/workers/periodic_tasks.py`:

```python
"""
Background worker for periodic tasks:
- Fetch TSA/CBP/flight data every 5 minutes
- Run Bayesian learning update daily
- Run zone discovery weekly
"""

import asyncio
import logging
from datetime import datetime
from app.database import SessionLocal
from app.data_sources import TSAWaitTimeAPI, CBPWaitTimeAPI, FlightDataAPI
from app.bayesian_learning import run_learning_update
from app.zone_discovery import run_zone_discovery
from app.models import Checkpoint, WaitTimeObservation
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AIRPORTS = ["JFK", "LAX", "ORD", "ATL", "DFW", "SFO", "MIA", "DEN", "SEA"]

async def fetch_real_time_data():
    """Fetch TSA and CBP wait times every 5 minutes."""
    logger.info("Fetching real-time wait time data...")

    tsa_api = TSAWaitTimeAPI()
    cbp_api = CBPWaitTimeAPI()
    db = SessionLocal()

    try:
        for airport_code in AIRPORTS:
            # Fetch TSA data
            tsa_waits = await tsa_api.get_wait_times(airport_code)
            if tsa_waits:
                for checkpoint_id, wait_minutes in tsa_waits.items():
                    observation = WaitTimeObservation(
                        checkpoint_id=checkpoint_id,
                        observed_at=datetime.utcnow(),
                        wait_minutes=wait_minutes,
                        source="tsa_api",
                        confidence=0.8
                    )
                    db.add(observation)
                logger.info(f"TSA: {airport_code} - {len(tsa_waits)} checkpoints updated")

            # Fetch CBP data
            cbp_waits = await cbp_api.get_wait_times(airport_code)
            if cbp_waits:
                for checkpoint_id, wait_minutes in cbp_waits.items():
                    observation = WaitTimeObservation(
                        checkpoint_id=checkpoint_id,
                        observed_at=datetime.utcnow(),
                        wait_minutes=wait_minutes,
                        source="cbp_api",
                        confidence=0.8
                    )
                    db.add(observation)
                logger.info(f"CBP: {airport_code} - {len(cbp_waits)} checkpoints updated")

        db.commit()
        logger.info("✅ Real-time data fetch complete")

    except Exception as e:
        logger.error(f"Error fetching real-time data: {e}")
        db.rollback()

    finally:
        db.close()

async def run_daily_learning():
    """Run Bayesian learning update daily."""
    logger.info("Running daily Bayesian learning update...")
    try:
        result = run_learning_update(lookback_days=30)
        logger.info(f"✅ Learning update complete: {result}")
    except Exception as e:
        logger.error(f"Error in learning update: {e}")

async def run_weekly_zone_discovery():
    """Run zone discovery weekly for each airport."""
    logger.info("Running weekly zone discovery...")
    for airport_code in AIRPORTS:
        try:
            result = run_zone_discovery(airport_code, lookback_days=30)
            logger.info(f"Zone discovery for {airport_code}: {result}")
        except Exception as e:
            logger.error(f"Error in zone discovery for {airport_code}: {e}")
    logger.info("✅ Zone discovery complete")

async def main():
    """Main worker loop."""
    import schedule
    import time

    # Schedule tasks
    schedule.every(5).minutes.do(lambda: asyncio.create_task(fetch_real_time_data()))
    schedule.every().day.at("03:00").do(lambda: asyncio.create_task(run_daily_learning()))
    schedule.every().sunday.at("04:00").do(lambda: asyncio.create_task(run_weekly_zone_discovery()))

    logger.info("🚀 Worker started. Scheduled tasks:")
    logger.info("  - Real-time data fetch: every 5 minutes")
    logger.info("  - Bayesian learning: daily at 3:00 AM")
    logger.info("  - Zone discovery: weekly on Sunday at 4:00 AM")

    # Run initial fetch
    await fetch_real_time_data()

    while True:
        schedule.run_pending()
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
```

Install scheduler:
```bash
poetry add schedule
```

Run worker:
```bash
python workers/periodic_tasks.py
```

### 4.2 Set Up as Systemd Service (Linux)

Create `/etc/systemd/system/airportwaze-worker.service`:

```ini
[Unit]
Description=AirportWaze Background Worker
After=network.target postgresql.service

[Service]
Type=simple
User=airportwaze
WorkingDirectory=/path/to/airport-waze-backend
Environment="DATABASE_URL=postgresql://airportwaze:password@localhost:5432/airportwaze"
ExecStart=/path/to/poetry run python workers/periodic_tasks.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable airportwaze-worker
sudo systemctl start airportwaze-worker
sudo systemctl status airportwaze-worker
```

---

## Part 5: Deployment

### 5.1 Deploy Backend to Fly.io

Your backend is already on Fly.io. Update it:

```bash
cd airport-waze-backend

# Update fly.toml to include database secret
fly secrets set DATABASE_URL="your_production_database_url"
fly secrets set FLIGHT_API_KEY="your_api_key"

# Deploy
fly deploy
```

### 5.2 PostgreSQL on Fly.io

Create managed PostgreSQL on Fly:

```bash
fly postgres create --name airportwaze-db \
  --region sjc \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 10

# Attach to app
fly postgres attach airportwaze-db --app app-awudjxxy
```

---

## Part 6: Testing

### 6.1 Test Database Connection

```bash
python -c "from app.database import engine; print('✅ Database connected' if engine.connect() else '❌ Connection failed')"
```

### 6.2 Test TSA API

```bash
python -c "
import asyncio
from app.data_sources import TSAWaitTimeAPI

async def test():
    api = TSAWaitTimeAPI()
    waits = await api.get_wait_times('JFK')
    print(f'TSA wait times: {waits}')

asyncio.run(test())
"
```

### 6.3 Test Telemetry Upload

```bash
curl -X POST http://localhost:8000/api/telemetry/upload \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "airport_code": "JFK",
    "session_id": "660e8400-e29b-41d4-a716-446655440000",
    "points": [{
      "timestamp": "2026-01-10T12:00:00Z",
      "lat": 40.6413,
      "lng": -73.7781,
      "speed": 0.5,
      "acceleration": null,
      "heading": null,
      "altitude": null,
      "battery_level": 85.0,
      "horizontal_accuracy": 10.0
    }]
  }'
```

---

## Part 7: Monitoring

### 7.1 Database Monitoring

```bash
# Check hypertable stats
psql $DATABASE_URL -c "SELECT * FROM timescaledb_information.hypertables;"

# Check telemetry data
psql $DATABASE_URL -c "SELECT airport_code, COUNT(*) as batches FROM telemetry_batches GROUP BY airport_code;"

# Check observations
psql $DATABASE_URL -c "SELECT source, COUNT(*) as observations FROM wait_time_observations GROUP BY source;"
```

### 7.2 Application Logs

```bash
# Backend logs (if using systemd)
sudo journalctl -u airportwaze-backend -f

# Worker logs
sudo journalctl -u airportwaze-worker -f

# Fly.io logs
fly logs --app app-awudjxxy
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### TSA/CBP API Not Working

- TSA API can be unreliable. The system falls back to model predictions.
- Check if your IP is blocked (rate limiting).

### Telemetry Not Uploading

- Check browser console for errors
- Verify CORS settings in backend
- Test API endpoint with curl

---

## Next Steps

1. **Add More Airports**: Expand `AIRPORTS_DATA` in `main.py`
2. **Improve Zone Discovery**: Fine-tune DBSCAN parameters
3. **Add Flight Data**: Sign up for Aviation Edge or FlightAware API
4. **Mobile App**: Consider building native iOS/Android apps for better background location tracking
5. **Real-Time WebSocket**: Add WebSocket support for live updates

---

## Resources

- [TimescaleDB Docs](https://docs.timescale.com/)
- [TSA API](https://www.tsa.gov/data/apcp.xml)
- [CBP Wait Times](https://bwt.cbp.gov/)
- [Aviation Edge API](https://aviation-edge.com/)
- [DBSCAN Clustering](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html)

---

**Questions?** Open an issue on GitHub or contact the maintainers.
