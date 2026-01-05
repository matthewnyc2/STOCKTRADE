"""
Standardized Error Handlers.

This module provides custom exception handlers that return errors
in the format specified by the API contract.
"""

from datetime import datetime
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class ApiException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        details: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class NotFoundException(ApiException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND
        )


class BadRequestException(ApiException):
    """Bad request exception."""

    def __init__(self, message: str = "Bad request", details: Any = None):
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UnauthorizedException(ApiException):
    """Unauthorized exception."""

    def __init__(self, message: str = "Unauthorized", details: Any = None):
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(ApiException):
    """Forbidden exception."""

    def __init__(self, message: str = "Forbidden", details: Any = None):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictException(ApiException):
    """Conflict exception."""

    def __init__(self, message: str = "Conflict", details: Any = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            details=details,
            status_code=status.HTTP_409_CONFLICT
        )


class ValidationException(ApiException):
    """Validation exception."""

    def __init__(self, message: str = "Validation failed", details: Any = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class RateLimitException(ApiException):
    """Rate limit exceeded exception."""

    def __init__(self, message: str = "Rate limit exceeded", details: Any = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class InternalServerException(ApiException):
    """Internal server error exception."""

    def __init__(self, message: str = "Internal server error", details: Any = None):
        super().__init__(
            message=message,
            code="INTERNAL_SERVER_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DatabaseException(ApiException):
    """Database error exception."""

    def __init__(self, message: str = "Database error", details: Any = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# ERROR RESPONSE FORMATTER
# ============================================================================

def error_response(
    code: str,
    message: str,
    details: Any = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        code: Error code (e.g., "NOT_FOUND", "VALIDATION_ERROR")
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code

    Returns:
        JSONResponse with formatted error
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }
    )


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    """Handle custom API exceptions."""
    return error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError | ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    # Log the error for debugging
    import logging
    logging.getLogger(__name__).exception(f"Unhandled exception: {exc}")

    # Don't expose internal errors in production
    import os
    is_debug = os.getenv("DEBUG", "false").lower() == "true"

    return error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details=str(exc) if is_debug else None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# SETUP FUNCTION
# ============================================================================

def setup_error_handlers(app: FastAPI) -> None:
    """
    Register all custom exception handlers with the FastAPI app.

    Args:
        app: The FastAPI application instance
    """
    # Custom API exceptions
    app.add_exception_handler(ApiException, api_exception_handler)

    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Generic catch-all
    app.add_exception_handler(Exception, generic_exception_handler)
