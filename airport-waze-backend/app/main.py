"""
AirportWaze API - Production-Ready Application
Modern, modular FastAPI application with authentication, caching, rate limiting, and monitoring.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

# Core configuration and setup
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging

# Middleware
from app.middleware import (
    LoggingMiddleware,
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler,
    setup_rate_limiting,
)

# Routes
from app.routes import (
    airports_router,
    auth_router,
    journey_router,
    predictions_router,
    wait_times_router,
    health_router,
    tsa_router,
    location_intelligence_router,
)

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Real-time airport wait times, journey planning, and probabilistic flight predictions",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware with production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Rate limiting
setup_rate_limiting(app)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routers
app.include_router(health_router)  # No prefix for health check
app.include_router(airports_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(journey_router, prefix=settings.API_V1_PREFIX)
app.include_router(predictions_router, prefix=settings.API_V1_PREFIX)
app.include_router(wait_times_router, prefix=settings.API_V1_PREFIX)
app.include_router(tsa_router, prefix=settings.API_V1_PREFIX)
app.include_router(location_intelligence_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if settings.ENV == "production":
            raise

    # Setup Sentry for error tracking (if configured)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.SENTRY_ENVIRONMENT,
                traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            )
            logger.info("Sentry error tracking initialized")
        except Exception as e:
            logger.warning(f"Sentry initialization failed: {e}")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down application")
    logger.info("Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/healthz",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
