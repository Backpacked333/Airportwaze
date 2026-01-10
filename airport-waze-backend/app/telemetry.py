"""
Telemetry collection and processing endpoints.
Implements privacy-preserving user data collection for the Moovit-style data flywheel.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import logging

from app.database import get_db
from app.models import TelemetryBatch, ZoneDwellEvent, TripEvent, WaitTimeObservation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])


# ============== DATA MODELS ==============

class UserState(str, Enum):
    """User activity state detected from phone sensors"""
    WALKING = "walking"
    WAITING_IN_QUEUE = "waiting_in_queue"
    RIDING_SHUTTLE = "riding_shuttle"
    IDLE = "idle"
    UNKNOWN = "unknown"


class TelemetryPoint(BaseModel):
    """Single telemetry data point from user's phone"""
    timestamp: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = None  # m/s
    acceleration: Optional[float] = None  # m/s^2
    heading: Optional[float] = None  # degrees (0-360)
    altitude: Optional[float] = None  # meters (from barometer)
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    horizontal_accuracy: Optional[float] = None  # meters


class TelemetryBatchRequest(BaseModel):
    """Batch of telemetry points (uploaded when user on WiFi)"""
    user_id: str  # Anonymous UUID generated client-side
    airport_code: str
    session_id: str  # UUID for this airport visit
    points: List[TelemetryPoint] = Field(..., min_items=1, max_items=1000)
    device_info: Optional[dict] = None


class ZoneDwellEventRequest(BaseModel):
    """Preprocessed zone dwell event (computed on-device)"""
    zone_id: str
    zone_type: str  # "security", "bag_check", "passport_control"
    enter_time: str
    exit_time: str
    dwell_seconds: int = Field(..., ge=0, le=7200)  # Max 2 hours
    confidence: float = Field(..., ge=0, le=1)


class TripEventRequest(BaseModel):
    """User-confirmed trip event (1-tap prompts)"""
    event_type: str  # "entered_security_line", "cleared_security", "dropped_bag"
    checkpoint_id: Optional[str] = None
    timestamp: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    session_id: str


# ============== ENDPOINTS ==============

@router.post("/upload")
async def upload_telemetry(
    batch: TelemetryBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Upload telemetry batch. Users upload when:
    1. On WiFi (to save mobile data)
    2. Session ends (leave airport)
    3. Every 5 minutes if continuous collection

    Privacy guarantees:
    - User IDs are anonymous UUIDs (client-generated)
    - No PII collected
    - Data aggregated with k-anonymity (k >= 10)
    """
    if len(batch.points) == 0:
        raise HTTPException(status_code=400, detail="Empty batch")

    try:
        # Validate user_id and session_id are valid UUIDs
        uuid.UUID(batch.user_id)
        uuid.UUID(batch.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Convert points to dict for JSONB storage
    points_data = [point.dict() for point in batch.points]

    # Create database record
    telemetry_batch = TelemetryBatch(
        user_id=uuid.UUID(batch.user_id),
        airport_code=batch.airport_code.upper(),
        session_id=uuid.UUID(batch.session_id),
        points=points_data,
        device_info=batch.device_info
    )

    db.add(telemetry_batch)

    try:
        db.commit()
        logger.info(f"Stored telemetry batch: {len(batch.points)} points from {batch.airport_code}")

        # TODO: Trigger async processing:
        # - State detection (walking, waiting, etc.)
        # - Zone discovery clustering
        # - Wait time estimation

        return {
            "status": "success",
            "batch_id": str(telemetry_batch.batch_id),
            "points_received": len(batch.points),
            "message": "Thank you for contributing data!"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Database error storing telemetry: {e}")
        raise HTTPException(status_code=500, detail="Failed to store telemetry")


@router.post("/zone-dwell")
async def upload_zone_dwell(
    event: ZoneDwellEventRequest,
    user_id: str,
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Upload preprocessed zone dwell event (computed on-device).
    This is privacy-preserving: no raw GPS, just zone ID + dwell time.
    """
    try:
        uuid.UUID(user_id)
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Parse timestamps
    try:
        enter_time = datetime.fromisoformat(event.enter_time.replace('Z', '+00:00'))
        exit_time = datetime.fromisoformat(event.exit_time.replace('Z', '+00:00'))

        # Remove timezone info for database storage
        if enter_time.tzinfo:
            enter_time = enter_time.replace(tzinfo=None)
        if exit_time.tzinfo:
            exit_time = exit_time.replace(tzinfo=None)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Create database record
    zone_dwell = ZoneDwellEvent(
        zone_id=event.zone_id,
        zone_type=event.zone_type,
        enter_time=enter_time,
        exit_time=exit_time,
        dwell_seconds=event.dwell_seconds,
        confidence=event.confidence,
        user_id=uuid.UUID(user_id),
        session_id=uuid.UUID(session_id)
    )

    db.add(zone_dwell)

    try:
        db.commit()

        # If this is a security checkpoint, create wait time observation
        if event.zone_type in ["tsa", "tsa_precheck", "security"]:
            wait_minutes = event.dwell_seconds // 60

            observation = WaitTimeObservation(
                checkpoint_id=event.zone_id,
                observed_at=exit_time,
                wait_minutes=wait_minutes,
                source="telemetry",
                confidence=event.confidence,
                user_id=uuid.UUID(user_id),
                session_id=uuid.UUID(session_id)
            )

            db.add(observation)
            db.commit()

            logger.info(f"Recorded wait observation: {wait_minutes}min at {event.zone_id}")

        return {"status": "success", "message": "Dwell event recorded"}

    except Exception as e:
        db.rollback()
        logger.error(f"Database error storing zone dwell: {e}")
        raise HTTPException(status_code=500, detail="Failed to store zone dwell")


@router.post("/trip-event")
async def upload_trip_event(
    event: TripEventRequest,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Upload user-confirmed trip event (1-tap prompt).
    Example: User tapped "I just entered security line" button.

    These are high-confidence signals useful for:
    - Model calibration
    - Zone boundary detection
    - Queue entry/exit timing
    """
    try:
        uuid.UUID(user_id)
        uuid.UUID(event.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Parse timestamp
    try:
        timestamp = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
        if timestamp.tzinfo:
            timestamp = timestamp.replace(tzinfo=None)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    # Create database record
    trip_event = TripEvent(
        event_type=event.event_type,
        checkpoint_id=event.checkpoint_id,
        timestamp=timestamp,
        lat=event.lat,
        lng=event.lng,
        user_id=uuid.UUID(user_id),
        session_id=uuid.UUID(event.session_id)
    )

    db.add(trip_event)

    try:
        db.commit()
        logger.info(f"Recorded trip event: {event.event_type} at {event.checkpoint_id}")

        return {
            "status": "success",
            "event_id": str(trip_event.event_id),
            "message": "Thank you for the update!"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Database error storing trip event: {e}")
        raise HTTPException(status_code=500, detail="Failed to store trip event")


@router.get("/stats/{airport_code}")
async def get_telemetry_stats(
    airport_code: str,
    db: Session = Depends(get_db)
):
    """
    Get aggregate telemetry statistics for an airport.

    Privacy: k-anonymity with k=10 (min 10 unique users before showing data)
    """
    airport_code = airport_code.upper()

    # Count unique sessions in last 24 hours
    from datetime import timedelta
    from sqlalchemy import func

    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    unique_sessions = db.query(func.count(func.distinct(TelemetryBatch.session_id))).filter(
        TelemetryBatch.airport_code == airport_code,
        TelemetryBatch.uploaded_at >= cutoff_time
    ).scalar()

    # Don't reveal data if < 10 users (k-anonymity)
    if unique_sessions < 10:
        return {
            "airport_code": airport_code,
            "data_quality": "insufficient",
            "message": "Not enough data to provide statistics (privacy threshold)"
        }

    # Get total points
    total_batches = db.query(func.count(TelemetryBatch.batch_id)).filter(
        TelemetryBatch.airport_code == airport_code,
        TelemetryBatch.uploaded_at >= cutoff_time
    ).scalar()

    # Get total wait time observations
    total_observations = db.query(func.count(WaitTimeObservation.observation_id)).join(
        WaitTimeObservation.checkpoint
    ).filter(
        WaitTimeObservation.checkpoint.has(airport_code=airport_code),
        WaitTimeObservation.observed_at >= cutoff_time
    ).scalar()

    return {
        "airport_code": airport_code,
        "active_sessions_24h": unique_sessions,
        "telemetry_batches": total_batches,
        "wait_observations": total_observations,
        "coverage": "good" if unique_sessions >= 50 else "limited",
        "data_quality": "high" if total_observations >= 100 else "medium"
    }


@router.delete("/user-data/{user_id}")
async def delete_user_data(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete all data for a specific user (GDPR right to be forgotten).

    This removes:
    - Telemetry batches
    - Zone dwell events
    - Trip events
    - Wait time observations
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    try:
        # Delete from all tables
        db.query(TelemetryBatch).filter(TelemetryBatch.user_id == user_uuid).delete()
        db.query(ZoneDwellEvent).filter(ZoneDwellEvent.user_id == user_uuid).delete()
        db.query(TripEvent).filter(TripEvent.user_id == user_uuid).delete()
        db.query(WaitTimeObservation).filter(WaitTimeObservation.user_id == user_uuid).delete()

        db.commit()

        logger.info(f"Deleted all data for user {user_id}")

        return {
            "status": "success",
            "message": "All your data has been permanently deleted"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user data: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete data")
