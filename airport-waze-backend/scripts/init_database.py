#!/usr/bin/env python3
"""
Database initialization script for AirportWaze.
This script:
1. Creates all database tables
2. Loads airport data from main.py into the database
3. Initializes baseline distributions for checkpoints
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine, SessionLocal, Base, is_sqlite
from app.models import Airport, Checkpoint, CheckpointDistribution
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import airport data from main.py
# We'll read it as a module to get AIRPORTS_DATA
import importlib.util
spec = importlib.util.spec_from_file_location("main", Path(__file__).parent.parent / "app" / "main.py")
main_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_module)

AIRPORTS_DATA = main_module.AIRPORTS_DATA


def init_schema():
    """Create all database tables."""
    logger.info("Creating database schema...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create schema: {e}")
        return False


def load_airports_data():
    """Load airport and checkpoint data from AIRPORTS_DATA."""
    logger.info("Loading airport data...")

    db = SessionLocal()
    try:
        airports_loaded = 0
        checkpoints_loaded = 0

        for code, data in AIRPORTS_DATA.items():
            # Check if airport already exists
            existing_airport = db.query(Airport).filter(Airport.code == code).first()

            if existing_airport:
                logger.info(f"Airport {code} already exists, skipping...")
                continue

            # Create airport
            airport = Airport(
                code=code,
                name=data["name"],
                city=data["city"],
                lat=data["lat"],
                lng=data["lng"],
                terminals=json.dumps(data["terminals"]) if is_sqlite else data["terminals"]
            )
            db.add(airport)
            airports_loaded += 1
            logger.info(f"Added airport: {code} - {data['name']}")

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
                    discovered=False,
                    confidence=None
                )
                db.add(checkpoint)
                checkpoints_loaded += 1

        db.commit()
        logger.info(f"✅ Loaded {airports_loaded} airports and {checkpoints_loaded} checkpoints")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to load airport data: {e}")
        return False
    finally:
        db.close()


def initialize_distributions():
    """Initialize baseline distributions for all checkpoints."""
    logger.info("Initializing checkpoint distributions...")

    db = SessionLocal()
    try:
        checkpoints = db.query(Checkpoint).all()
        distributions_created = 0

        for checkpoint in checkpoints:
            # Check if distribution already exists
            existing_dist = db.query(CheckpointDistribution).filter(
                CheckpointDistribution.checkpoint_id == checkpoint.id
            ).first()

            if existing_dist:
                continue

            # Calculate initial distribution based on checkpoint type
            # Using log-normal: log(wait_time) ~ Normal(mu, sigma)
            base_wait = checkpoint.base_wait_minutes
            import numpy as np

            # Initial parameters (will be refined by Bayesian learning)
            if checkpoint.type == "tsa_precheck":
                mu = np.log(base_wait) if base_wait > 0 else np.log(5)
                sigma = 0.25  # Low variance for PreCheck
            elif checkpoint.type == "tsa":
                mu = np.log(base_wait) if base_wait > 0 else np.log(20)
                sigma = 0.4  # Moderate variance
            elif checkpoint.type == "bag_check":
                mu = np.log(base_wait) if base_wait > 0 else np.log(10)
                sigma = 0.5  # Higher variance
            elif checkpoint.type == "passport_control":
                mu = np.log(base_wait) if base_wait > 0 else np.log(15)
                sigma = 0.45  # Moderate-high variance
            else:
                mu = np.log(15)
                sigma = 0.4

            # Create distribution
            distribution = CheckpointDistribution(
                checkpoint_id=checkpoint.id,
                mu=mu,
                sigma=sigma,
                sample_size=0,
                confidence="low",  # Initial confidence is low
                last_updated=datetime.utcnow()
            )
            db.add(distribution)
            distributions_created += 1

        db.commit()
        logger.info(f"✅ Initialized {distributions_created} checkpoint distributions")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to initialize distributions: {e}")
        return False
    finally:
        db.close()


def test_database():
    """Test database connection and data."""
    logger.info("Testing database...")

    db = SessionLocal()
    try:
        # Count airports
        airport_count = db.query(Airport).count()
        logger.info(f"  Airports in database: {airport_count}")

        # Count checkpoints
        checkpoint_count = db.query(Checkpoint).count()
        logger.info(f"  Checkpoints in database: {checkpoint_count}")

        # Count distributions
        dist_count = db.query(CheckpointDistribution).count()
        logger.info(f"  Distributions in database: {dist_count}")

        # Sample a few airports
        airports = db.query(Airport).limit(3).all()
        for airport in airports:
            logger.info(f"  Sample: {airport.code} - {airport.name} ({airport.city})")
            checkpoint_count = db.query(Checkpoint).filter(
                Checkpoint.airport_code == airport.code
            ).count()
            logger.info(f"    Checkpoints: {checkpoint_count}")

        logger.info("✅ Database test passed")
        return True

    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Main initialization function."""
    logger.info("="*60)
    logger.info("AirportWaze Database Initialization")
    logger.info("="*60)
    logger.info(f"Database: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    logger.info("")

    # Step 1: Initialize schema
    if not init_schema():
        logger.error("Schema initialization failed. Exiting.")
        sys.exit(1)

    logger.info("")

    # Step 2: Load airport data
    if not load_airports_data():
        logger.error("Airport data loading failed. Exiting.")
        sys.exit(1)

    logger.info("")

    # Step 3: Initialize distributions
    if not initialize_distributions():
        logger.error("Distribution initialization failed. Exiting.")
        sys.exit(1)

    logger.info("")

    # Step 4: Test database
    if not test_database():
        logger.error("Database test failed. Exiting.")
        sys.exit(1)

    logger.info("")
    logger.info("="*60)
    logger.info("✅ Database initialization complete!")
    logger.info("="*60)
    logger.info("")
    logger.info("You can now:")
    logger.info("  1. Start the backend: poetry run uvicorn app.main:app --reload")
    logger.info("  2. Check database file: ls -lh airportwaze.db")
    logger.info("  3. Query database: sqlite3 airportwaze.db")
    logger.info("")


if __name__ == "__main__":
    main()
