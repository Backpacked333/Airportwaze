"""Journey planning routes for airport navigation."""
import logging
from fastapi import APIRouter, HTTPException, Request

from app.services.journey_service import JourneyService
from app.schemas.journey import JourneyRequest, JourneyPlan
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/journey", tags=["journey"])


@router.post("/plan", response_model=JourneyPlan)
@limiter.limit("100/minute")
async def plan_journey(
    request: Request,
    journey_request: JourneyRequest
) -> JourneyPlan:
    """
    Plan a journey through the airport from current location to gate.

    Creates a step-by-step journey plan including:
    - Bag check (if needed)
    - Security screening (TSA or TSA PreCheck)
    - Walk to gate
    - Estimated times and distances for each step
    - Recommended arrival time at airport

    Args:
        journey_request: Journey planning parameters including:
            - airport_code: Three-letter airport code
            - terminal: Terminal identifier
            - gate: Gate number
            - has_tsa_precheck: Whether user has TSA PreCheck
            - has_global_entry: Whether user has Global Entry
            - has_checked_bags: Whether user has checked bags
            - mobility_factor: Walking speed multiplier (1.0 = normal)
            - departure_time: Flight departure time (ISO format)
            - user_lat/user_lng: Current location (optional)

    Returns:
        Journey plan with steps, total time, distance, and recommended arrival time

    Raises:
        HTTPException: 404 if airport not found, 400 for invalid input
    """
    try:
        journey_plan = JourneyService.plan_journey(journey_request)

        if not journey_plan:
            raise HTTPException(
                status_code=404,
                detail=f"Airport '{journey_request.airport_code.upper()}' not found"
            )

        return journey_plan

    except ValueError as e:
        logger.warning(f"Invalid journey request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error planning journey: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to plan journey"
        )
