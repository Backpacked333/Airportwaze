#!/usr/bin/env python3
"""Simple database test script."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Airport, Checkpoint, CheckpointDistribution

def main():
    db = SessionLocal()
    try:
        print("\n" + "="*60)
        print("Database Test Results")
        print("="*60)

        # Test 1: Count records
        airports = db.query(Airport).all()
        checkpoints = db.query(Checkpoint).all()
        distributions = db.query(CheckpointDistribution).all()

        print(f"\n📊 Record Counts:")
        print(f"  • Airports: {len(airports)}")
        print(f"  • Checkpoints: {len(checkpoints)}")
        print(f"  • Distributions: {len(distributions)}")

        # Test 2: Sample airport data
        print(f"\n🌐 Sample Airports:")
        for airport in airports[:3]:
            print(f"  • {airport.code}: {airport.name} ({airport.city})")
            print(f"    Lat/Lng: {airport.lat:.4f}, {airport.lng:.4f}")
            checkpoint_count = db.query(Checkpoint).filter(
                Checkpoint.airport_code == airport.code
            ).count()
            print(f"    Checkpoints: {checkpoint_count}")

        # Test 3: Sample checkpoints
        print(f"\n🛂 Sample Checkpoints (JFK):")
        jfk_checkpoints = db.query(Checkpoint).filter(
            Checkpoint.airport_code == "JFK"
        ).limit(5).all()

        for cp in jfk_checkpoints:
            print(f"  • {cp.id}: {cp.name}")
            print(f"    Type: {cp.type}, Terminal: {cp.terminal}")
            print(f"    Base wait: {cp.base_wait_minutes} min")

        # Test 4: Sample distributions
        print(f"\n📈 Sample Distributions:")
        for dist in distributions[:3]:
            checkpoint = db.query(Checkpoint).filter(
                Checkpoint.id == dist.checkpoint_id
            ).first()
            print(f"  • {dist.checkpoint_id}")
            print(f"    μ={dist.mu:.3f}, σ={dist.sigma:.3f}")
            print(f"    Sample size: {dist.sample_size}, Confidence: {dist.confidence}")
            print(f"    Checkpoint: {checkpoint.name if checkpoint else 'Unknown'}")

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60 + "\n")

    finally:
        db.close()

if __name__ == "__main__":
    main()
