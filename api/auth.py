"""
Authentication API router.

Endpoints for user authentication and token management.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
import jwt as PyJWT
import bcrypt

from core.error_handlers import (
    UnauthorizedException,
    BadRequestException,
    ConflictException,
)
from database.connection import get_db_session
from database.repositories import UserRepository


router = APIRouter(prefix="/auth", tags=["authentication"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security scheme for token validation
security = HTTPBearer(auto_error=False)


# ============================================================================
# SCHEMAS
# ============================================================================


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Schema for registration request."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(
        ..., min_length=8, max_length=100, description="Password (min 8 characters)"
    )
    full_name: str | None = Field(None, max_length=100, description="Full name")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token")


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: dict[str, Any] = Field(..., description="User information")


class UserResponse(BaseModel):
    """Schema for user information."""

    id: str
    email: str
    username: str
    is_superuser: bool = False
    full_name: str | None
    created_at: str
    updated_at: str


# ============================================================================
# TOKEN UTILITIES
# ============================================================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = PyJWT.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = PyJWT.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = PyJWT.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWT.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired")
    except PyJWT.InvalidTokenError:
        raise UnauthorizedException("Invalid token")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ============================================================================
# DEPENDENCIES
# ============================================================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        User information

    Raises:
        HTTPException: If not authenticated
    """
    if not credentials:
        raise UnauthorizedException("Not authenticated")

    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    with get_db_session() as session:
        repo = UserRepository(session)
        user = repo.get(user_id)

        if user is None:
            raise UnauthorizedException("User not found")

        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """
    Get the current user if authenticated, otherwise return None.

    Args:
        credentials: HTTP bearer credentials

    Returns:
        User information or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except Exception:
        return None


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest) -> LoginResponse:
    """
    Authenticate a user and return JWT tokens.

    Args:
        login_data: Login credentials

    Returns:
        LoginResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    with get_db_session() as session:
        repo = UserRepository(session)

        # Find user by email
        user = repo.get_by_email(login_data.email)

        if not user:
            raise UnauthorizedException("Invalid email or password")

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(register_data: RegisterRequest) -> LoginResponse:
    """
    Register a new user.

    Args:
        register_data: Registration information

    Returns:
        LoginResponse: Access token, refresh token, and user info

    Raises:
        HTTPException: If registration fails
    """
    from uuid import uuid4

    with get_db_session() as session:
        repo = UserRepository(session)

        # Check if email already exists
        existing = repo.get_by_email(register_data.email)
        if existing:
            raise ConflictException("Email already registered")

        # Check if username already exists
        existing = repo.get_by_username(register_data.username)
        if existing:
            raise ConflictException("Username already taken")

        # Hash password
        hashed_password = hash_password(register_data.password)

        # Create user
        user = repo.create(
            id=f"user_{uuid4().hex[:12]}",
            email=register_data.email,
            username=register_data.username,
            hashed_password=hashed_password,
            full_name=register_data.full_name,
        )

        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(refresh_data: RefreshTokenRequest) -> LoginResponse:
    """
    Refresh an access token using a refresh token.

    Args:
        refresh_data: Refresh token

    Returns:
        LoginResponse: New access token and user info

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)

    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    # Get user
    with get_db_session() as session:
        repo = UserRepository(session)
        user = repo.get(user_id)

        if user is None:
            raise UnauthorizedException("User not found")

        # Create new tokens
        access_token = create_access_token(data={"sub": user.id})
        new_refresh_token = create_refresh_token(data={"sub": user.id})

        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        )


@router.get("/demo", response_model=LoginResponse)
async def demo_login() -> LoginResponse:
    """
    Create a demo/guest session without credentials.
    Useful for development and testing.
    """
    from uuid import uuid4
    from datetime import timedelta

    demo_user_id = f"demo_{uuid4().hex[:12]}"

    # Create long-lived tokens for demo
    access_token = create_access_token(
        data={"sub": demo_user_id},
        expires_delta=timedelta(days=7),  # 7 days for demo
    )
    refresh_token = create_refresh_token(data={"sub": demo_user_id})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=7 * 24 * 60 * 60,  # 7 days in seconds
        user={
            "id": demo_user_id,
            "email": "demo@cryptoquant.lab",
            "username": "DemoTrader",
            "full_name": "Demo User",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get the current authenticated user's information.

    Args:
        current_user: Current user from dependency

    Returns:
        User information
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout a user.

    Note: In a JWT-based system, logout is typically handled client-side
    by deleting the token. This endpoint can be used for server-side
    tracking or invalidating refresh tokens in a real system.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}
