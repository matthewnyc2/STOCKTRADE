"""
Security module for Crypto Quant Laboratory.

Provides authentication, API key validation, and security utilities.
"""

import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Security configuration
API_KEY_HEADER = "X-API-Key"
API_KEY_LENGTH = 32
API_KEY_EXPIRY_DAYS = 365

# Initialize API key header
api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)


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


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        str: A secure API key
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(API_KEY_LENGTH)

    # Encode to base64 URL-safe
    api_key = secrets.token_urlsafe(API_KEY_LENGTH)

    return api_key


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        api_key: The API key to hash

    Returns:
        str: The hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against a stored hash.

    Args:
        api_key: The API key to verify
        hashed_key: The stored hash to compare against

    Returns:
        bool: True if verification succeeds, False otherwise
    """
    return hmac.compare_digest(
        hashlib.sha256(api_key.encode()).hexdigest(),
        hashed_key
    )


class APIKeyManager:
    """Manages API keys and validation."""

    def __init__(self):
        """Initialize the API key manager."""
        self._api_keys: Dict[str, Dict[str, Any]] = {}
        # Load API keys from environment
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from environment variables."""
        # Get API key from environment
        env_key = os.getenv("API_KEY")
        if env_key:
            # Store the API key
            self._api_keys[env_key] = {
                "created_at": datetime.now(timezone.utc),
                "last_used": datetime.now(timezone.utc),
                "active": True,
                "user_id": "default",
                "description": "Default API key from environment"
            }

    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key.

        Args:
            api_key: The API key to validate

        Returns:
            Optional[Dict[str, Any]]: User data if valid, None otherwise
        """
        if not api_key:
            return None

        # Check if API key exists
        if api_key not in self._api_keys:
            return None

        # Check if API key is active
        user_data = self._api_keys[api_key]
        if not user_data.get("active", False):
            return None

        # Update last used timestamp
        user_data["last_used"] = datetime.now(timezone.utc)

        return user_data

    def add_api_key(self, api_key: str, user_id: str, description: str = "") -> None:
        """
        Add a new API key.

        Args:
            api_key: The API key to add
            user_id: The user ID associated with the key
            description: Description of the API key
        """
        self._api_keys[api_key] = {
            "created_at": datetime.now(timezone.utc),
            "last_used": datetime.now(timezone.utc),
            "active": True,
            "user_id": user_id,
            "description": description
        }

    def deactivate_api_key(self, api_key: str) -> bool:
        """
        Deactivate an API key.

        Args:
            api_key: The API key to deactivate

        Returns:
            bool: True if deactivated successfully, False if not found
        """
        if api_key in self._api_keys:
            self._api_keys[api_key]["active"] = False
            return True
        return False

    def list_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        List all API keys (excluding the actual key values).

        Returns:
            Dict[str, Dict[str, Any]]: API key metadata
        """
        result = {}
        for key, data in self._api_keys.items():
            # Don't include the actual API key
            result_key = f"***{key[-4:]}" if len(key) > 4 else "***"
            result[result_key] = {
                "created_at": data["created_at"].isoformat(),
                "last_used": data["last_used"].isoformat(),
                "active": data["active"],
                "user_id": data["user_id"],
                "description": data.get("description", "")
            }
        return result


# Global API key manager instance
_api_key_manager = APIKeyManager()


async def get_api_key(api_key: Optional[str] = Depends(api_key_header)) -> Dict[str, Any]:
    """
    Get API key from request header and validate it.

    Args:
        api_key: The API key from the header

    Returns:
        Dict[str, Any]: User data associated with the API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate the API key
    user_data = _api_key_manager.validate_api_key(api_key)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Validates the X-API-Key header on all requests.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and validate the API key.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response: The response from the next handler or error response
        """
        # Skip authentication for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)

        # Extract API key from header
        api_key = request.headers.get(API_KEY_HEADER)

        # Validate API key
        user_data = _api_key_manager.validate_api_key(api_key)
        if not user_data:
            # Return standard error response
            return ErrorResponse(
                detail="Authentication required. Please provide a valid API key.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="API_KEY_REQUIRED"
            )

        # Add user data to request state
        request.state.user_data = user_data

        # Process the request
        response = await call_next(request)

        return response


def api_key_middleware(app):
    """
    Add API key middleware to the application.

    Args:
        app: The FastAPI application
    """
    app.add_middleware(APIKeyMiddleware)


# Rate limiting helper
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Size of the window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Check if a request is allowed based on rate limiting.

        Args:
            identifier: The identifier to track (e.g., IP address)

        Returns:
            bool: True if allowed, False if rate limited
        """
        now = datetime.now(timezone.utc)

        # Get existing requests for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if (now - req_time).total_seconds() < self.window_seconds
        ]

        # Check if request is allowed
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Add this request
        self.requests[identifier].append(now)
        return True


# Global rate limiter instance
_rate_limiter = RateLimiter()


def create_rate_limit_middleware(max_requests: int = 100, window_seconds: int = 60):
    """
    Create a rate limiting middleware.

    Args:
        max_requests: Maximum requests allowed in the window
        window_seconds: Size of the window in seconds

    Returns:
        BaseHTTPMiddleware: The rate limiting middleware
    """
    class RateLimitMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app)

        async def dispatch(self, request: Request, call_next):
            # Get client IP for rate limiting
            client_ip = request.client.host if request.client else "unknown"

            # Check rate limit
            if not _rate_limiter.is_allowed(client_ip):
                return ErrorResponse(
                    detail="Rate limit exceeded. Please try again later.",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    error_code="RATE_LIMITED"
                )

            return await call_next(request)

    return RateLimitMiddleware


# Content Security Policy headers
def add_security_headers(response: Response) -> Response:
    """
    Add security headers to the response.

    Args:
        response: The response object

    Returns:
        Response: The response with security headers
    """
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )

    # Other security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=()"

    return response


def create_security_headers_middleware():
    """
    Create a middleware to add security headers.

    Returns:
        BaseHTTPMiddleware: The security headers middleware
    """
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: ASGIApp):
            super().__init__(app)

        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            return add_security_headers(response)

    return SecurityHeadersMiddleware


# Export the middleware class directly
SecurityHeadersMiddleware = create_security_headers_middleware()


# Input sanitization
def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize input text to prevent XSS and injection attacks.

    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length

    Returns:
        str: The sanitized text
    """
    if not text:
        return ""

    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove null bytes
    text = text.replace('\x00', '')

    # Basic XSS prevention
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '`']
    for char in dangerous_chars:
        text = text.replace(char, '')

    return text


# SQL injection prevention
def validate_sql_identifier(identifier: str) -> bool:
    """
    Validate an SQL identifier to prevent injection.

    Args:
        identifier: The identifier to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Only allow alphanumeric, underscores, and dots
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.')
    return all(c in allowed_chars for c in identifier)


def validate_sql_value(value: str) -> bool:
    """
    Validate a SQL value to prevent injection.

    Args:
        value: The value to validate

    Returns:
        bool: True if valid, False otherwise
    """
    # Check for common SQL injection patterns
    dangerous_patterns = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "UNION", "EXEC", "EXECUTE", "SP_", "XP_", "TRUNCATE", "DECLARE",
        ";", "--", "/*", "*/", "1=1", "1=0"
    ]

    value_upper = value.upper()
    return not any(pattern in value_upper for pattern in dangerous_patterns)