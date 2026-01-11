"""Wait time routes for crowdsourced wait time reporting."""
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Query, status
from sqlalchemy.orm import Session

from app.services.wait_time_service import WaitTimeService
from app.schemas.wait_time import WaitTimeReport
from app.core.database import get_db
from app.core.security import get_current_user
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wait-times", tags=["wait-times"])


@router.post("/report", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def submit_wait_time_report(
    request: Request,
    report: WaitTimeReport,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user)
) -> Dict:
    """
    Submit a crowdsourced wait time report.

    Allows users to report actual wait times at checkpoints to help improve
    predictions for other travelers. Reports can be submitted anonymously or
    by authenticated users.

    Args:
        report: Wait time report containing:
            - airport_code: Three-letter airport code
            - checkpoint_id: Checkpoint identifier
            - reported_wait_minutes: Actual wait time in minutes
            - reporter_id: Anonymous reporter ID (optional)
            - user_lat/user_lng: User location for verification (optional)
        db: Database session
        current_user: Current authenticated user (optional)

    Returns:
        Created report confirmation with ID and timestamp

    Raises:
        HTTPException: 400 for invalid input, 500 for server errors
    """
    try:
        # Validate wait time is reasonable
        if report.reported_wait_minutes < 0:
            raise ValueError("Wait time cannot be negative")

        if report.reported_wait_minutes > 300:  # 5 hours max
            raise ValueError("Wait time seems unreasonably high (max 300 minutes)")

        # Get user ID if authenticated
        user_id = current_user.get("sub") if current_user else None

        # Create report
        db_report = WaitTimeService.create_report(db, report, user_id)

        logger.info(f"Wait time report created: {db_report.id} for {report.airport_code}-{report.checkpoint_id}")

        return {
            "id": db_report.id,
            "status": "success",
            "message": "Wait time report submitted successfully",
            "timestamp": db_report.created_at.isoformat()
        }

    except ValueError as e:
        logger.warning(f"Invalid wait time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating wait time report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit wait time report"
        )


@router.get("/reports/{airport_code}")
@limiter.limit("100/minute")
async def get_recent_reports(
    request: Request,
    airport_code: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of reports to return"),
    hours_back: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve (max 168)")
) -> Dict:
    """
    Get recent crowdsourced wait time reports for an airport.

    Retrieves the most recent user-submitted wait time reports, which can be
    used to assess current conditions and validate predicted wait times.

    Args:
        airport_code: Three-letter airport code (e.g., "JFK", "LAX")
        db: Database session
        limit: Maximum number of reports to return (default 20, max 100)
        hours_back: Hours of history to retrieve (default 24, max 168)

    Returns:
        Dictionary with airport code and list of recent reports

    Raises:
        HTTPException: 400 for invalid parameters
    """
    try:
        reports = WaitTimeService.get_recent_reports(
            db,
            airport_code,
            limit=limit,
            hours_back=hours_back
        )

        return {
            "airport_code": airport_code.upper(),
            "count": len(reports),
            "hours_back": hours_back,
            "reports": reports
        }

    except Exception as e:
        logger.error(f"Error fetching wait time reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve wait time reports"
        )
