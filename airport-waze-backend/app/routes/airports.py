"""Airport routes for airport data and terminal operations."""
import logging
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.services.airport_service import AirportService
from app.schemas.airport import Airport
from app.core.database import get_db
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/airports", tags=["airports"])


@router.get("/", response_model=List[Dict])
@limiter.limit("100/minute")
async def get_all_airports(request: Request) -> List[Dict]:
    """
    Get list of all available airports.

    Returns:
        List of airports with basic information (code, name, city, location, terminals)
    """
    try:
        airports = AirportService.get_all_airports()
        return airports
    except Exception as e:
        logger.error(f"Error fetching airports: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve airports"
        )


@router.get("/{airport_code}", response_model=Airport)
@limiter.limit("200/minute")
async def get_airport(
    request: Request,
    airport_code: str
) -> Airport:
    """
    Get detailed airport information including checkpoints and current wait times.

    Args:
        airport_code: Three-letter airport code (e.g., "JFK", "LAX")

    Returns:
        Airport details with checkpoints and current wait times

    Raises:
        HTTPException: 404 if airport not found
    """
    airport = AirportService.get_airport(airport_code)

    if not airport:
        raise HTTPException(
            status_code=404,
            detail=f"Airport '{airport_code.upper()}' not found"
        )

    return airport


@router.get("/{airport_code}/terminals/{terminal}/gates")
@limiter.limit("200/minute")
async def get_terminal_gates(
    request: Request,
    airport_code: str,
    terminal: str
) -> Dict:
    """
    Get all gates for a specific terminal.

    Args:
        airport_code: Three-letter airport code (e.g., "JFK", "LAX")
        terminal: Terminal identifier (e.g., "A", "1", "International")

    Returns:
        Dictionary with terminal and list of gates with coordinates

    Raises:
        HTTPException: 404 if airport or terminal not found
    """
    gates_data = AirportService.get_terminal_gates(airport_code, terminal)

    if not gates_data:
        raise HTTPException(
            status_code=404,
            detail=f"Airport '{airport_code.upper()}' not found"
        )

    if not gates_data.get("gates"):
        raise HTTPException(
            status_code=404,
            detail=f"Terminal '{terminal}' not found at airport '{airport_code.upper()}'"
        )

    return gates_data
