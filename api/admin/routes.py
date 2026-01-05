"""
Admin API router.

Provides endpoints for user management, system health monitoring,
and administrative operations.
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from enum import Enum
import logging
import os
import sys

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])
security = HTTPBearer(auto_error=False)


# ============================================================================
# Enums
# ============================================================================


class UserRole(str, Enum):
    """User role enumeration."""

    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    """User status enumeration."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# ============================================================================
# Request/Response Models
# ============================================================================


class SystemHealthResponse(BaseModel):
    """System health check response."""

    status: str = Field(..., description="Overall system status: healthy, degraded, or unhealthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")

    # Service status
    database_status: str = Field(..., description="Database connection status")
    redis_status: str = Field(..., description="Redis cache status")
    websockets_active: int = Field(..., description="Number of active WebSocket connections")

    # Resource usage
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    memory_used_mb: float = Field(..., description="Memory used in MB")
    disk_percent: float = Field(..., description="Disk usage percentage")

    # API metrics
    total_requests: int = Field(..., description="Total API requests")
    requests_last_hour: int = Field(..., description="Requests in last hour")
    error_rate: float = Field(..., description="Error rate percentage")

    # Background tasks
    active_tasks: int = Field(..., description="Number of active background tasks")
    queued_tasks: int = Field(..., description="Number of queued tasks")


class UsageMetricsResponse(BaseModel):
    """Usage and performance metrics response."""

    period_hours: int = Field(..., description="Time period for metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # User metrics
    total_users: int = Field(..., description="Total registered users")
    active_users: int = Field(..., description="Active users in period")
    new_users: int = Field(..., description="New users in period")

    # Strategy metrics
    total_strategies: int = Field(..., description="Total strategies")
    active_strategies: int = Field(..., description="Active strategies")
    new_strategies: int = Field(..., description="New strategies in period")

    # Trading metrics
    total_backtests: int = Field(..., description="Total backtests run")
    backtests_period: int = Field(..., description="Backtests in period")
    total_trades: int = Field(..., description="Total paper trades")

    # Performance metrics
    avg_response_time_ms: float = Field(..., description="Average API response time")
    p95_response_time_ms: float = Field(..., description="95th percentile response time")
    error_rate_percent: float = Field(..., description="Error rate percentage")

    # Data metrics
    market_data_points: int = Field(..., description="Total market data points")
    signals_generated: int = Field(..., description="Total signals generated")


class UserListResponse(BaseModel):
    """User list response."""

    users: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserCreateRequest(BaseModel):
    """Request to create a new user."""

    email: str = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="User status")


class UserUpdateRequest(BaseModel):
    """Request to update a user."""

    email: Optional[str] = Field(None, description="User email")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    role: Optional[UserRole] = Field(None, description="User role")
    status: Optional[UserStatus] = Field(None, description="User status")


# ============================================================================
# Dependencies
# ============================================================================


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> None:
    """
    Require admin authentication.

    Validates JWT token and checks user has admin role.
    Raises HTTPException if not admin.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode token and get user
        from api.auth import decode_token

        payload = decode_token(credentials.credentials)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Get user from database
        with get_db_context() as session:
            result = session.execute(
                text("SELECT is_superuser FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).first()

            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            is_superuser = result[0]
            if not is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin privileges required",
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


# ============================================================================
# System Health Endpoints
# ============================================================================


@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(admin: None = Depends(require_admin)) -> SystemHealthResponse:
    """
    Get system health status.

    Returns comprehensive health information including service status,
    resource usage, and API metrics.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        # Get server uptime (platform independent)
        if sys.platform == "win32":
            uptime = 0  # psutil.boot_time() may not work on Windows
        else:
            try:
                import psutil

                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = (datetime.utcnow() - boot_time).total_seconds()
            except Exception:
                uptime = 0

        # Get resource usage (platform independent)
        cpu_percent = 0
        memory_percent = 0
        memory_used_mb = 0
        disk_percent = 0

        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)

            # Try getting disk usage (may fail on some systems)
            if sys.platform == "win32":
                disk = psutil.disk_usage("C:\\")
            else:
                disk = psutil.disk_usage("/")
            disk_percent = disk.percent
        except Exception:
            pass

        # Check database connection
        database_status = "healthy"
        try:
            with get_db_context() as session:
                session.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            database_status = "unhealthy"

        # Check Redis (optional)
        redis_status = "not_configured"
        try:
            import redis

            redis_client = redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
            )
            redis_client.ping()
            redis_status = "healthy"
        except Exception:
            pass

        # Get WebSocket connections
        try:
            from core.websocket import get_websocket_manager

            ws_manager = get_websocket_manager()
            websockets_active = len(ws_manager._subscriptions)
        except Exception:
            websockets_active = 0

        # Get background tasks
        try:
            from services.background_tasks import get_task_queue

            queue = get_task_queue()
            active_tasks = len([t for t in queue.get_all_tasks() if t.get("status") == "running"])
            queued_tasks = len([t for t in queue.get_all_tasks() if t.get("status") == "pending"])
        except Exception:
            active_tasks = 0
            queued_tasks = 0

        # Calculate overall status
        overall_status = "healthy"
        if database_status == "unhealthy":
            overall_status = "unhealthy"
        elif cpu_percent > 80 or memory_percent > 80:
            overall_status = "degraded"

        return SystemHealthResponse(
            status=overall_status,
            uptime_seconds=uptime,
            version="0.1.0",
            environment=os.getenv("ENVIRONMENT", "development"),
            database_status=database_status,
            redis_status=redis_status,
            websockets_active=websockets_active,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            disk_percent=disk_percent,
            total_requests=0,  # Would come from metrics store
            requests_last_hour=0,  # Would come from metrics store
            error_rate=0.0,  # Would come from metrics store
            active_tasks=active_tasks,
            queued_tasks=queued_tasks,
        )

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}",
        )


@router.get("/system/metrics", response_model=UsageMetricsResponse)
async def get_usage_metrics(
    period_hours: int = Query(default=24, ge=1, le=168, description="Time period in hours"),
    admin: None = Depends(require_admin),
) -> UsageMetricsResponse:
    """
    Get system usage and performance metrics.

    Returns aggregated metrics for specified time period.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Calculate time period
            since = datetime.utcnow() - timedelta(hours=period_hours)

            # User metrics (using raw SQL)
            total_users = 0
            active_users = 0
            new_users = 0

            try:
                total_users_result = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
                total_users = total_users_result or 0

                active_users_result = session.execute(
                    text("SELECT COUNT(*) FROM users WHERE created_at >= :since"), {"since": since}
                ).scalar()
                active_users = active_users_result or 0

                new_users = active_users  # For now, same as active
            except Exception:
                pass

            # Strategy metrics
            total_strategies = 0
            active_strategies = 0
            new_strategies = 0

            try:
                from database.models.strategy import StrategyModel

                total_strategies = session.query(StrategyModel).count() or 0
                active_strategies = (
                    session.query(StrategyModel).filter(StrategyModel.status == "ACTIVE").count()
                    or 0
                )
                new_strategies = (
                    session.query(StrategyModel).filter(StrategyModel.created_at >= since).count()
                    or 0
                )
            except Exception:
                pass

            # Backtest metrics
            total_backtests = 0
            backtests_period = 0

            try:
                from database.models.backtest import BacktestResultModel

                total_backtests = session.query(BacktestResultModel).count() or 0
                backtests_period = (
                    session.query(BacktestResultModel)
                    .filter(BacktestResultModel.start_date >= since)
                    .count()
                    or 0
                )
            except Exception:
                pass

            # Trade metrics (using 0 for now)
            total_trades = 0

            # Market data metrics
            market_data_points = 0

            try:
                from database.models.price import PriceModel

                market_data_points = session.query(PriceModel).count() or 0
            except Exception:
                pass

            # Signal metrics
            signals_generated = 0

            try:
                from database.models.signal import SignalModel

                signals_generated = session.query(SignalModel).count() or 0
            except Exception:
                pass

            return UsageMetricsResponse(
                period_hours=period_hours,
                total_users=total_users,
                active_users=active_users,
                new_users=new_users,
                total_strategies=total_strategies,
                active_strategies=active_strategies,
                new_strategies=new_strategies,
                total_backtests=total_backtests,
                backtests_period=backtests_period,
                total_trades=total_trades,
                avg_response_time_ms=0.0,  # Would come from metrics store
                p95_response_time_ms=0.0,  # Would come from metrics store
                error_rate_percent=0.0,  # Would come from metrics store
                market_data_points=market_data_points,
                signals_generated=signals_generated,
            )

    except Exception as e:
        logger.error(f"Error getting usage metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage metrics: {str(e)}",
        )


# ============================================================================
# User Management Endpoints
# ============================================================================


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Page size"),
    status_filter: Optional[UserStatus] = Query(default=None, description="Filter by status"),
    role_filter: Optional[UserRole] = Query(default=None, description="Filter by role"),
    search: Optional[str] = Query(default=None, description="Search in email/username"),
    admin: None = Depends(require_admin),
) -> UserListResponse:
    """
    List all users with pagination and filtering.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Build query
            query = "SELECT id, email, username, is_active, is_superuser, created_at, updated_at FROM users"
            params = {}

            # Add filters (not implemented for now since UserModel doesn't have role/status)
            conditions = []
            # if status_filter:
            #     conditions.append("status = :status")
            #     params["status"] = status_filter.value
            # if role_filter:
            #     conditions.append("role = :role")
            #     params["role"] = role_filter.value
            if search:
                conditions.append("(email LIKE :search OR username LIKE :search)")
                params["search"] = f"%{search}%"

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM users WHERE {(' AND '.join(conditions)) if conditions else '1=1'}"
            total = session.execute(text(count_query), params).scalar() or 0

            # Add pagination
            offset = (page - 1) * page_size
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = page_size
            params["offset"] = offset

            # Execute query
            result = session.execute(text(query), params)

            users_data = [
                {
                    "id": row[0],
                    "email": row[1],
                    "username": row[2],
                    "role": "ADMIN" if row[4] else "USER",
                    "status": "ACTIVE" if row[3] else "INACTIVE",
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None,
                    "last_login": None,
                }
                for row in result
            ]

            total_pages = (total + page_size - 1) // page_size

            return UserListResponse(
                users=users_data,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}",
        )


@router.get("/users/{user_id}")
async def get_user(user_id: str, admin: None = Depends(require_admin)) -> dict[str, Any]:
    """
    Get a specific user by ID.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            result = session.execute(
                text(
                    "SELECT id, email, username, is_active, is_superuser, created_at, updated_at FROM users WHERE id = :user_id"
                ),
                {"user_id": user_id},
            ).first()

            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
                )

            return {
                "id": result[0],
                "email": result[1],
                "username": result[2],
                "role": "ADMIN" if result[4] else "USER",
                "status": "ACTIVE" if result[3] else "INACTIVE",
                "created_at": result[5].isoformat() if result[5] else None,
                "updated_at": result[6].isoformat() if result[6] else None,
                "last_login": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest, admin: None = Depends(require_admin)
) -> dict[str, Any]:
    """
    Create a new user.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Check if email already exists
            existing = session.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": user_data.email}
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email '{user_data.email}' already exists",
                )

            # Hash password
            import bcrypt

            password_hash = bcrypt.hashpw(
                user_data.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Generate user ID
            import uuid

            user_id = f"user_{uuid.uuid4().hex[:12]}"

            # Create user
            session.execute(
                text("""INSERT INTO users (id, email, username, hashed_password, is_active, is_superuser, created_at, updated_at)
                     VALUES (:id, :email, :username, :hashed_password, :is_active, :is_superuser, :created_at, :updated_at)"""),
                {
                    "id": user_id,
                    "email": user_data.email,
                    "username": user_data.username,
                    "hashed_password": password_hash,
                    "is_active": user_data.status == UserStatus.ACTIVE,
                    "is_superuser": user_data.role == UserRole.ADMIN,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            session.commit()

            return {
                "id": user_id,
                "email": user_data.email,
                "username": user_data.username,
                "role": user_data.role.value,
                "status": user_data.status.value,
                "created_at": datetime.utcnow().isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.put("/users/{user_id}")
async def update_user(
    user_id: str, user_data: UserUpdateRequest, admin: None = Depends(require_admin)
) -> dict[str, Any]:
    """
    Update a user.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Check if user exists
            existing = session.execute(
                text("SELECT id, is_superuser FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).first()

            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
                )

            is_superuser = existing[1]

            # Build update dict
            update_fields = []
            params = {"user_id": user_id, "updated_at": datetime.utcnow()}

            if user_data.email is not None:
                # Check if email is taken by another user
                email_check = session.execute(
                    text("SELECT id FROM users WHERE email = :email AND id != :user_id"),
                    {"email": user_data.email, "user_id": user_id},
                ).first()

                if email_check:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Email '{user_data.email}' already in use",
                    )

                update_fields.append("email = :email")
                params["email"] = user_data.email

            if user_data.username is not None:
                update_fields.append("username = :username")
                params["username"] = user_data.username

            if user_data.role is not None and is_superuser:
                # Only update is_superuser if already an admin
                update_fields.append("is_superuser = :is_superuser")
                params["is_superuser"] = user_data.role == UserRole.ADMIN

            if user_data.status is not None:
                update_fields.append("is_active = :is_active")
                params["is_active"] = user_data.status == UserStatus.ACTIVE

            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = :updated_at WHERE id = :user_id"
                session.execute(text(query), params)
                session.commit()

            # Get updated user
            result = session.execute(
                text(
                    "SELECT id, email, username, is_active, is_superuser, updated_at FROM users WHERE id = :user_id"
                ),
                {"user_id": user_id},
            ).first()

            return {
                "id": result[0],
                "email": result[1],
                "username": result[2],
                "role": "ADMIN" if result[4] else "USER",
                "status": "ACTIVE" if result[3] else "INACTIVE",
                "updated_at": result[6].isoformat() if result[6] else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, admin: None = Depends(require_admin)) -> None:
    """
    Delete a user.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Check if user exists
            existing = session.execute(
                text("SELECT is_superuser FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).first()

            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
                )

            # Prevent deletion of admin users (optional safety check)
            if existing[0]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete admin users"
                )

            # Delete user
            session.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            session.commit()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )


@router.post("/users/{user_id}/activate")
async def activate_user(user_id: str, admin: None = Depends(require_admin)) -> dict[str, Any]:
    """
    Activate a user account.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Check if user exists
            existing = session.execute(
                text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).first()

            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
                )

            # Activate user
            session.execute(
                text(
                    "UPDATE users SET is_active = 1, updated_at = :updated_at WHERE id = :user_id"
                ),
                {"user_id": user_id, "updated_at": datetime.utcnow()},
            )
            session.commit()

            return {"id": user_id, "status": "ACTIVE", "message": "User activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}",
        )


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, admin: None = Depends(require_admin)) -> dict[str, Any]:
    """
    Deactivate a user account.

    Authentication:
        Requires Bearer token in Authorization header
    """
    try:
        with get_db_context() as session:
            # Check if user exists
            existing = session.execute(
                text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}
            ).first()

            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found"
                )

            # Deactivate user
            session.execute(
                text(
                    "UPDATE users SET is_active = 0, updated_at = :updated_at WHERE id = :user_id"
                ),
                {"user_id": user_id, "updated_at": datetime.utcnow()},
            )
            session.commit()

            return {"id": user_id, "status": "INACTIVE", "message": "User deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        )
