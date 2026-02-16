"""Logging middleware for request/response logging."""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Log request and response details."""
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }
        )

        return response
