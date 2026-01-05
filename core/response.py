"""
Standardized API Response Wrapper Middleware.

This module provides middleware for wrapping all API responses in a consistent format
that matches the frontend API contract.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar, Optional
from functools import wraps

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

T = TypeVar("T")


class ApiResponse(Generic[T]):
    """Standardized API response wrapper."""

    @staticmethod
    def success(
        data: T,
        meta: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Create a success response.

        Args:
            data: The response data
            meta: Optional metadata (pagination, timestamps, etc)

        Returns:
            Formatted success response
        """
        response: dict[str, Any] = {
            "success": True,
            "data": data,
        }

        if meta:
            response["meta"] = {
                **meta,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        else:
            response["meta"] = {"timestamp": datetime.utcnow().isoformat() + "Z"}

        return response

    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Any] = None,
        status_code: int = 400
    ) -> JSONResponse:
        """
        Create an error response.

        Args:
            code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
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


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """
    Middleware to wrap all JSON responses in the standard format.

    This middleware automatically wraps successful responses in the
    ApiResponse.success() format.
    """

    def __init__(self, app: ASGIApp, exclude_paths: set[str] | None = None):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            exclude_paths: Paths to exclude from wrapping (e.g., /docs, /health)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/ws",
            "/ws/test",
        }

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and wrap the response.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Wrapped or original response
        """
        # Skip wrapping for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)

        # Process the request
        response = await call_next(request)

        # Only wrap JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Skip if response is already wrapped (has success field)
        try:
            body = await self._decode_response(response)
            if isinstance(body, dict) and "success" in body:
                return response
        except Exception:
            # If we can't decode, return as-is
            return response

        # Wrap the response
        try:
            data = await self._decode_response(response)
            wrapped = ApiResponse.success(data)

            return JSONResponse(
                content=wrapped,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except Exception:
            # If wrapping fails, return original
            return response

    async def _decode_response(self, response: Response) -> Any:
        """Decode response body."""
        # For streaming responses, we can't wrap
        if hasattr(response, "body_iterator"):
            raise ValueError("Cannot decode streaming response")

        # Read the body
        import json
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        return json.loads(body)


def paginated_response(
    items: list[T],
    page: int = 1,
    limit: int = 20,
    total: int | None = None
) -> dict[str, Any]:
    """
    Create a paginated response.

    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        limit: Items per page
        total: Total number of items (calculated if not provided)

    Returns:
        Paginated response dict
    """
    if total is None:
        total = len(items)

    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return ApiResponse.success(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }
    )


# Decorator for wrapping function returns
def wrap_response(func):
    """
    Decorator to wrap a function's return value in ApiResponse format.

    Usage:
        @wrap_response
        async def my_endpoint():
            return {"data": "value"}  # Automatically wrapped
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)

        # If already a dict with success, return as-is
        if isinstance(result, dict) and "success" in result:
            return result

        # If a Response object, return as-is
        from fastapi import Response
        if isinstance(result, Response):
            return result

        # Wrap the result
        return ApiResponse.success(result)

    return wrapper
