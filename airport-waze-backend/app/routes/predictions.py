"""Prediction routes for probabilistic flight predictions and wait time forecasting."""
import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Request, Query

from app.services.prediction_service import PredictionService
from app.services.wait_time_service import WaitTimeService
from app.schemas.flight import WillIMakeItRequest, WillIMakeItResponse, Flight
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["predictions"])


@router.post("/will-i-make-it", response_model=WillIMakeItResponse)
@limiter.limit("50/minute")
async def will_i_make_it(
    request: Request,
    prediction_request: WillIMakeItRequest
) -> WillIMakeItResponse:
    """
    Calculate the probability of making your flight using Monte Carlo simulation.

    This endpoint uses probabilistic modeling to simulate thousands of possible
    journey scenarios and provides:
    - Probability of making the flight
    - Recommended leave-by times for different confidence levels (80%, 90%, 95%)
    - Time distribution percentiles (P50, P80, P90, P95)
    - Detailed breakdown of each journey segment

    Args:
        prediction_request: Request containing:
            - flight: Flight details (departure time, terminal, gate, airport)
            - has_tsa_precheck: Whether user has TSA PreCheck
            - has_global_entry: Whether user has Global Entry
            - has_checked_bags: Whether user has checked bags
            - mobility_factor: Walking speed multiplier (1.0 = normal)
            - current_time: Current time (defaults to now)
            - user_lat/user_lng: Current location (optional)

    Returns:
        Probability analysis with confidence bands and leave-by times

    Raises:
        HTTPException: 404 if airport not found, 400 for invalid input
    """
    try:
        result = PredictionService.will_i_make_it(prediction_request)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Airport '{prediction_request.flight.airport_code.upper()}' not found"
            )

        return result

    except ValueError as e:
        logger.warning(f"Invalid prediction request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error calculating prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate probability"
        )


@router.get("/predictions/{airport_code}")
@limiter.limit("100/minute")
async def get_predictions(
    request: Request,
    airport_code: str,
    hours_ahead: int = Query(default=24, ge=1, le=48, description="Hours to predict (1-48)")
) -> Dict:
    """
    Get wait time predictions for the next 24-48 hours.

    Provides forecasted wait times at 2-hour intervals based on:
    - Historical patterns
    - Time of day
    - Day of week
    - Seasonal factors

    Args:
        airport_code: Three-letter airport code (e.g., "JFK", "LAX")
        hours_ahead: Number of hours to predict (default 24, max 48)

    Returns:
        Dictionary with airport code and list of predictions for each time interval

    Raises:
        HTTPException: 404 if airport not found
    """
    predictions = PredictionService.get_predictions(airport_code, hours_ahead)

    if not predictions:
        raise HTTPException(
            status_code=404,
            detail=f"Airport '{airport_code.upper()}' not found"
        )

    return predictions


@router.post("/flight/import")
@limiter.limit("50/minute")
async def import_flight(
    request: Request,
    flight: Flight
) -> Dict:
    """
    Validate and import flight information.

    This endpoint validates flight data format and returns normalized information.
    Useful for validating user input before submitting to other endpoints.

    Args:
        flight: Flight information to validate

    Returns:
        Validated and normalized flight information

    Raises:
        HTTPException: 400 for invalid flight data format
    """
    try:
        # Basic validation
        if not flight.airport_code or len(flight.airport_code) != 3:
            raise ValueError("Invalid airport code - must be 3 letters")

        if not flight.terminal:
            raise ValueError("Terminal is required")

        if not flight.gate:
            raise ValueError("Gate is required")

        if not flight.departure_time:
            raise ValueError("Departure time is required")

        return {
            "status": "valid",
            "flight": {
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "departure_time": flight.departure_time,
                "terminal": flight.terminal,
                "gate": flight.gate,
                "airport_code": flight.airport_code.upper()
            }
        }

    except ValueError as e:
        logger.warning(f"Invalid flight data: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error validating flight: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to validate flight information"
        )


@router.get("/checkpoints/{checkpoint_id}/distribution")
@limiter.limit("100/minute")
async def get_checkpoint_distribution(
    request: Request,
    checkpoint_id: str
) -> Dict:
    """
    Get wait time distribution for a specific checkpoint.

    Returns probabilistic wait time information including:
    - Percentiles (P50, P80, P90, P95)
    - Distribution parameters (mu, sigma)
    - Sample size and confidence level

    Args:
        checkpoint_id: Checkpoint identifier (e.g., "jfk-t4-tsa-main")

    Returns:
        Checkpoint information with wait time distribution

    Raises:
        HTTPException: 404 if checkpoint not found
    """
    distribution = WaitTimeService.get_checkpoint_distribution(checkpoint_id)

    if not distribution:
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint '{checkpoint_id}' not found"
        )

    return distribution
