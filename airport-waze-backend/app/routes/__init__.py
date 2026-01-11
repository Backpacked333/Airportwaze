"""
Routes module for AirportWaze API.

This module imports and exports all API routers for easy inclusion in the main FastAPI application.
"""

from app.routes.airports import router as airports_router
from app.routes.auth import router as auth_router
from app.routes.journey import router as journey_router
from app.routes.predictions import router as predictions_router
from app.routes.wait_times import router as wait_times_router
from app.routes.health import router as health_router
from app.routes.tsa import router as tsa_router
from app.routes.location_intelligence import router as location_intelligence_router

__all__ = [
    "airports_router",
    "auth_router",
    "journey_router",
    "predictions_router",
    "wait_times_router",
    "health_router",
    "tsa_router",
    "location_intelligence_router",
]
