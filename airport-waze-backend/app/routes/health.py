"""Health check routes for API monitoring."""
import logging
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["health"])


@router.get("/healthz")
@limiter.limit("100/minute")
async def health_check(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Health check endpoint for API monitoring and load balancer probes.

    Checks:
    - API is running
    - Database connectivity
    - Current timestamp

    Returns:
        Health status with component checks

    Note:
        This endpoint should be excluded from authentication requirements
        and used by monitoring systems and load balancers.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AirportWaze API",
        "checks": {}
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "unhealthy"

    # Add version info if available
    try:
        from app.core.config import settings
        health_status["version"] = getattr(settings, "API_VERSION", "1.0.0")
    except Exception:
        pass

    return health_status
