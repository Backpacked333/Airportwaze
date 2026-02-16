"""API routes for location intelligence and checkpoint discovery."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.middleware.rate_limit import limiter
from app.schemas.location_tracking import (
    LocationTraceCreate,
    LocationTraceResponse,
    DiscoveredCheckpointResponse,
    AirlineCheckpointSuggestion,
    CheckpointDiscoveryRequest,
    HeatmapRequest,
    HeatmapResponse
)
from app.services.location_intelligence_service import LocationIntelligenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/location", tags=["location-intelligence"])


@router.post("/trace", response_model=LocationTraceResponse)
@limiter.limit("100/minute")
async def submit_location_trace(
    trace: LocationTraceCreate,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Submit a location trace for analysis.

    This endpoint receives GPS location breadcrumbs from users as they move through
    the airport. The system automatically detects:
    - When users are standing still (potential check-in counter)
    - Movement patterns
    - Airline-specific locations

    **Privacy**: Location data is anonymized and used only for crowd-sourced analytics.
    """
    try:
        user_id = current_user.get("sub") if current_user else None
        location_trace = LocationIntelligenceService.create_location_trace(
            db=db,
            trace_data=trace,
            user_id=user_id
        )
        return LocationTraceResponse.from_orm(location_trace)
    except Exception as e:
        logger.error(f"Error creating location trace: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process location trace"
        )


@router.post("/discover-checkpoints", response_model=List[DiscoveredCheckpointResponse])
@limiter.limit("10/minute")
async def discover_checkpoints(
    request: CheckpointDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger checkpoint discovery using machine learning (DBSCAN clustering).

    This analyzes location traces to automatically discover:
    - Check-in counter locations
    - Security checkpoint queues
    - Gate waiting areas
    - Other points of interest

    **Algorithm**: Uses DBSCAN (Density-Based Spatial Clustering) to identify
    areas where users frequently stand still.
    """
    try:
        discovered = LocationIntelligenceService.discover_checkpoints_dbscan(
            db=db,
            airport_code=request.airport_code,
            airline=request.airline,
            min_samples=request.min_samples,
            max_radius_meters=request.max_radius_meters
        )
        return discovered
    except Exception as e:
        logger.error(f"Error discovering checkpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover checkpoints"
        )


@router.get("/airline-suggestions/{airport_code}", response_model=List[AirlineCheckpointSuggestion])
@limiter.limit("20/minute")
async def get_airline_checkpoint_suggestions(
    airport_code: str,
    min_confidence: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    Get AI-suggested airline check-in counter locations.

    This endpoint uses crowdsourced location data to suggest where each airline's
    check-in counters are located. For example:

    - If many users flying with Delta keep standing in area X, we suggest that's
      Delta's check-in counter
    - The system learns from user behavior patterns automatically
    - Higher confidence scores mean more reliable suggestions

    **Use Case**: Helps users find their airline's check-in counter even if it's
    not in our static database.
    """
    try:
        suggestions = LocationIntelligenceService.generate_airline_checkpoint_suggestions(
            db=db,
            airport_code=airport_code.upper(),
            min_confidence=min_confidence
        )
        return suggestions
    except Exception as e:
        logger.error(f"Error generating airline suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions"
        )


@router.post("/heatmap", response_model=HeatmapResponse)
@limiter.limit("30/minute")
async def get_location_heatmap(
    request: HeatmapRequest,
    db: Session = Depends(get_db)
):
    """
    Get location heatmap data for visualization.

    Returns a density map showing where users spend time in the airport.
    This can be visualized on a map to show:
    - High-traffic areas
    - Discovered checkpoints
    - Airline-specific zones

    **Visualization**: Use the returned points to render a heatmap layer on
    your map component (e.g., with Leaflet.heat or Google Maps Heatmap Layer).
    """
    try:
        heatmap_data = LocationIntelligenceService.generate_heatmap_data(
            db=db,
            airport_code=request.airport_code,
            airline=request.airline,
            terminal=request.terminal,
            hours_back=request.hours_back
        )
        return HeatmapResponse(**heatmap_data)
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate heatmap data"
        )


@router.get("/checkpoints/{airport_code}", response_model=List[DiscoveredCheckpointResponse])
@limiter.limit("50/minute")
async def get_discovered_checkpoints(
    airport_code: str,
    airline: Optional[str] = None,
    checkpoint_type: Optional[str] = None,
    min_confidence: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    Get all discovered checkpoints for an airport.

    Returns checkpoints that have been automatically discovered from user
    location data. You can filter by:
    - Airline (e.g., "Delta", "United")
    - Checkpoint type (e.g., "airline_checkin", "security_queue", "gate_waiting")
    - Minimum confidence score

    **Integration**: Use these discovered checkpoints alongside your static
    checkpoint data for the most accurate navigation.
    """
    from app.models.location_tracking import DiscoveredCheckpoint

    try:
        query = db.query(DiscoveredCheckpoint).filter(
            DiscoveredCheckpoint.airport_code == airport_code.upper(),
            DiscoveredCheckpoint.is_active == True,
            DiscoveredCheckpoint.confidence_score >= min_confidence
        )

        if airline:
            query = query.filter(DiscoveredCheckpoint.airline == airline)

        if checkpoint_type:
            query = query.filter(DiscoveredCheckpoint.checkpoint_type == checkpoint_type)

        checkpoints = query.order_by(DiscoveredCheckpoint.confidence_score.desc()).all()

        return [DiscoveredCheckpointResponse.from_orm(cp) for cp in checkpoints]
    except Exception as e:
        logger.error(f"Error getting discovered checkpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve checkpoints"
        )
