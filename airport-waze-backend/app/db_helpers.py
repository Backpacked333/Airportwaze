"""
Database helper functions for converting SQLAlchemy models to API responses.
This keeps main.py clean and separates concerns.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import numpy as np

from app.models import Airport as DBairport, Checkpoint as DBCheckpoint, CheckpointDistribution
from app.database import is_sqlite


def get_checkpoint_current_wait(db: Session, checkpoint: DBCheckpoint, context: Optional[Dict] = None) -> int:
    """
    Get current wait time estimate for a checkpoint.
    Uses learned distribution if available, otherwise uses base wait time.

    Args:
        db: Database session
        checkpoint: Checkpoint model
        context: Optional context (time of day, day of week) for adjustments

    Returns:
        Estimated wait time in minutes (P50 - median)
    """
    # Try to get learned distribution
    distribution = db.query(CheckpointDistribution).filter(
        CheckpointDistribution.checkpoint_id == checkpoint.id
    ).first()

    if distribution and distribution.sample_size > 0:
        # Use learned distribution
        mu = distribution.mu
        sigma = distribution.sigma

        # Apply context adjustments if provided
        if context:
            mu, sigma = apply_context_adjustment(mu, sigma, context)

        # Calculate P50 (median)
        p50 = int(np.exp(mu))
        return max(1, p50)
    else:
        # Fall back to base wait time with time-of-day adjustment
        base_wait = checkpoint.base_wait_minutes

        if context and 'hour' in context:
            hour = context['hour']
            if 6 <= hour <= 9 or 16 <= hour <= 20:
                # Peak hours: increase by 40%
                base_wait = int(base_wait * 1.4)
            elif 22 <= hour or hour <= 5:
                # Late night: decrease by 40%
                base_wait = int(base_wait * 0.6)

        return base_wait


def apply_context_adjustment(mu: float, sigma: float, context: Dict) -> tuple:
    """Apply context-specific adjustments to distribution parameters."""
    adjusted_mu = mu
    adjusted_sigma = sigma

    # Time of day adjustment
    if 'hour' in context:
        hour = context['hour']
        if 6 <= hour <= 9 or 16 <= hour <= 20:
            # Peak hours: increase mean by 40%
            adjusted_mu += np.log(1.4)
        elif 22 <= hour or hour <= 5:
            # Late night: decrease mean by 40%
            adjusted_mu -= np.log(1.4)

    # Day of week adjustment
    if 'day_of_week' in context:
        day = context['day_of_week']
        if day in [4, 5, 6]:  # Friday, Saturday, Sunday
            # Weekend: increase mean by 20%
            adjusted_mu += np.log(1.2)

    # Increase variance for peak times (less predictable)
    if context.get('is_peak', False):
        adjusted_sigma *= 1.2

    return adjusted_mu, adjusted_sigma


def checkpoint_to_api_model(db: Session, checkpoint: DBCheckpoint) -> Dict:
    """
    Convert SQLAlchemy Checkpoint to API response dict.

    Args:
        db: Database session
        checkpoint: SQLAlchemy Checkpoint model

    Returns:
        Dict matching the Checkpoint Pydantic model
    """
    now = datetime.utcnow()
    context = {
        'hour': now.hour,
        'day_of_week': now.weekday(),
        'is_peak': (6 <= now.hour <= 9) or (16 <= now.hour <= 20)
    }

    current_wait = get_checkpoint_current_wait(db, checkpoint, context)

    # Determine status based on wait time
    if current_wait < 10:
        status = "low"
    elif current_wait < 20:
        status = "moderate"
    elif current_wait < 35:
        status = "high"
    else:
        status = "very_high"

    return {
        "id": checkpoint.id,
        "name": checkpoint.name,
        "type": checkpoint.type,
        "terminal": checkpoint.terminal,
        "lat": checkpoint.lat,
        "lng": checkpoint.lng,
        "current_wait_minutes": current_wait,
        "historical_avg_minutes": checkpoint.base_wait_minutes,
        "status": status,
        "last_updated": now.isoformat()
    }


def airport_to_api_model(db: Session, airport: DBairport, include_checkpoints: bool = True) -> Dict:
    """
    Convert SQLAlchemy Airport to API response dict.

    Args:
        db: Database session
        airport: SQLAlchemy Airport model
        include_checkpoints: Whether to include checkpoint data

    Returns:
        Dict matching the Airport Pydantic model
    """
    # Parse terminals from JSON (SQLite stores as JSON string)
    if is_sqlite:
        terminals = json.loads(airport.terminals) if isinstance(airport.terminals, str) else airport.terminals
    else:
        terminals = airport.terminals

    result = {
        "code": airport.code,
        "name": airport.name,
        "city": airport.city,
        "lat": airport.lat,
        "lng": airport.lng,
        "terminals": terminals or []
    }

    if include_checkpoints:
        checkpoints = db.query(DBCheckpoint).filter(
            DBCheckpoint.airport_code == airport.code
        ).all()

        result["checkpoints"] = [
            checkpoint_to_api_model(db, cp) for cp in checkpoints
        ]

    return result


def get_wait_time_distribution(db: Session, checkpoint_id: str, context: Optional[Dict] = None) -> Dict:
    """
    Get wait time distribution for a checkpoint.

    Args:
        db: Database session
        checkpoint_id: Checkpoint ID
        context: Optional context for adjustments

    Returns:
        Distribution dict with percentiles (P50, P80, P90, P95)
    """
    distribution = db.query(CheckpointDistribution).filter(
        CheckpointDistribution.checkpoint_id == checkpoint_id
    ).first()

    if not distribution:
        # No learned distribution, use checkpoint base wait
        checkpoint = db.query(DBCheckpoint).filter(DBCheckpoint.id == checkpoint_id).first()
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        # Create default distribution from base wait
        base_wait = checkpoint.base_wait_minutes
        mu = np.log(base_wait) if base_wait > 0 else np.log(10)

        if checkpoint.type == "tsa_precheck":
            sigma = 0.25
        elif checkpoint.type == "tsa":
            sigma = 0.4
        elif checkpoint.type == "bag_check":
            sigma = 0.5
        else:
            sigma = 0.45

        confidence = "low"
        sample_size = 0
    else:
        mu = distribution.mu
        sigma = distribution.sigma
        confidence = distribution.confidence
        sample_size = distribution.sample_size

    # Apply context adjustments
    if context:
        mu, sigma = apply_context_adjustment(mu, sigma, context)

    # Calculate percentiles
    from scipy import stats as scipy_stats

    p50 = int(np.exp(mu))
    p80 = int(np.exp(mu + sigma * scipy_stats.norm.ppf(0.80)))
    p90 = int(np.exp(mu + sigma * scipy_stats.norm.ppf(0.90)))
    p95 = int(np.exp(mu + sigma * scipy_stats.norm.ppf(0.95)))

    return {
        "p50": max(1, p50),
        "p80": max(1, p80),
        "p90": max(1, p90),
        "p95": max(1, p95),
        "mu": round(mu, 4),
        "sigma": round(sigma, 4),
        "sample_size": sample_size,
        "confidence": confidence
    }
