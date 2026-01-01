"""
Middleware for Crypto Quant Laboratory.

Provides CORS, error handling, and request logging middleware.
"""

import logging
import os
import time
import traceback
from typing import Any, Callable

from fastapi import Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.security import create_rate_limit_middleware


logger = logging.getLogger(__name__)


class ErrorResponse(JSONResponse):
    """
    Standardized error response format.

    Ensures consistent error responses across the API.
    """

    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Create an error response.

        Args:
            detail: Human-readable error message
            status_code: HTTP status code
            error_code: Machine-readable error code
            context: Additional context about the error
        """
        content = {
            "success": False,
            "error": {
                "message": detail,
                "code": error_code or "INTERNAL_ERROR",
            },
        }

        if context:
            content["error"]["context"] = context

        super().__init__(content=content, status_code=status_code)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.

    Catches all exceptions and returns standardized error responses.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the error handler middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and handle any exceptions.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response or error response
        """
        try:
            response = await call_next(request)
            return response

        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error: {str(e)}")
            return ErrorResponse(
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="VALIDATION_ERROR",
            )

        except KeyError as e:
            # Missing required fields
            logger.warning(f"Missing field error: {str(e)}")
            return ErrorResponse(
                detail=f"Missing required field: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_FIELD",
            )

        except PermissionError as e:
            # Permission errors
            logger.warning(f"Permission error: {str(e)}")
            return ErrorResponse(
                detail=str(e),
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="PERMISSION_DENIED",
            )

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unhandled exception: {str(e)}")
            logger.debug(traceback.format_exc())

            # In production, don't expose internal details
            return ErrorResponse(
                detail="An internal error occurred",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="INTERNAL_ERROR",
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware.

    Logs all incoming requests with timing information.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the request logging middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and process.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response
        """
        start_time = time.time()

        # Extract request info
        method = request.method
        url = str(request.url)
        client_host = request.client.host if request.client else "unknown"

        # Log request
        logger.info(f"Request: {method} {url} from {client_host}")

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {method} {url} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )

            # Add timing header
            response.headers["X-Process-Time"] = str(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {method} {url} - "
                f"Error: {str(e)} - "
                f"Duration: {duration:.3f}s"
            )
            raise


def setup_cors(app) -> None:
    """
    Set up CORS middleware for the application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(
        CORSMiddleware,
        # Allow all origins in development
        # In production, specify exact origins
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )


def setup_middleware(app) -> None:
    """
    Set up all middleware for the application.

    Args:
        app: The FastAPI application
    """
    # CORS must be added first
    setup_cors(app)

    # Security headers (add second to last)
    from core.security import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting (add before security but after CORS)
    rate_limit_middleware = create_rate_limit_middleware(
        max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
        window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    )
    app.add_middleware(rate_limit_middleware)

    # Error handler (catches exceptions)
    app.add_middleware(ErrorHandlerMiddleware)

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)
