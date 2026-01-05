"""
Admin Data API endpoints.

Provides endpoints for data initialization, synchronization,
and management of reference data from exchanges.
"""

import logging
from typing import List, Optional
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from services.data_initializer import (
    initialize_reference_data,
    get_initialization_status,
    is_initialized
)
from services.exchange_sync import ExchangeSync
from services.background_tasks import get_task_queue, run_background_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/data", tags=["admin-data"])


# ============================================================================
# Request/Response Models
# ============================================================================

class InitializeRequest(BaseModel):
    """Request model for data initialization."""
    force: bool = False
    components: Optional[List[str]] = None  # ['exchanges', 'coins', 'trading_pairs', 'templates']


class InitializeResponse(BaseModel):
    """Response model for data initialization."""
    success: bool
    message: str
    timestamp: str
    results: Optional[dict] = None


class SyncRequest(BaseModel):
    """Request model for data synchronization."""
    exchanges: Optional[List[str]] = None  # None = sync all enabled exchanges
    force: bool = False


class SyncResponse(BaseModel):
    """Response model for data synchronization."""
    task_id: str
    message: str
    exchanges: List[str]


class DataStatusResponse(BaseModel):
    """Response model for data status."""
    initialized: bool
    initialized_at: Optional[str] = None
    data_counts: dict
    sync_status: Optional[list] = None
    quality_metrics: Optional[dict] = None


class TaskResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    name: str
    status: str
    progress: int
    message: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


class TasksListResponse(BaseModel):
    """Response model for tasks list."""
    tasks: List[dict]
    count: int


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/initialize", response_model=InitializeResponse)
async def initialize_data(request: InitializeRequest):
    """
    Initialize all reference data.

    Sets up default exchanges, coins, trading pairs, and strategy templates.
    Skips already initialized data unless force=True.

    Args:
        request: Initialization request with force and components options

    Returns:
        Initialization results
    """
    try:
        # Check if already initialized
        if is_initialized() and not request.force:
            return InitializeResponse(
                success=True,
                message="Data already initialized. Use force=True to re-initialize.",
                timestamp=get_initialization_status().get("initialized_at"),
            )

        logger.info("Initializing reference data...")

        # Run initialization
        results = initialize_reference_data()

        if results.get("success"):
            return InitializeResponse(
                success=True,
                message="Data initialized successfully",
                timestamp=results["timestamp"],
                results=results,
            )
        else:
            return InitializeResponse(
                success=False,
                message=f"Initialization failed: {results.get('error', 'Unknown error')}",
                timestamp=results["timestamp"],
                results=results,
            )

    except Exception as e:
        logger.error(f"Error initializing data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize data: {str(e)}"
        )


@router.post("/sync", response_model=SyncResponse)
async def sync_data(request: SyncRequest):
    """
    Trigger data synchronization from exchanges.

    Starts a background task to sync trading pairs and coin listings
    from configured exchanges.

    Args:
        request: Sync request with exchanges list and force option

    Returns:
        Task ID for tracking sync progress
    """
    try:
        # Create sync service
        sync_service = ExchangeSync()

        # Determine which exchanges to sync
        if request.exchanges:
            exchanges = request.exchanges
        else:
            # Get enabled exchanges from database
            from database.connection import get_db_context
            from sqlalchemy import text

            with get_db_context() as session:
                result = session.execute(
                    text("SELECT id FROM exchanges WHERE enabled = 1")
                )
                exchanges = [row[0] for row in result.fetchall()]

        if not exchanges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No exchanges configured for sync"
            )

        logger.info(f"Starting sync for exchanges: {exchanges}")

        # Create background task
        async def sync_task():
            return await sync_service.sync_all_exchanges(exchanges=exchanges)

        task_id = run_background_task(
            name=f"Sync exchanges: {', '.join(exchanges)}",
            func=sync_task,
            auto_run=True
        )

        return SyncResponse(
            task_id=task_id,
            message=f"Sync started for {len(exchanges)} exchange(s)",
            exchanges=exchanges,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start sync: {str(e)}"
        )


@router.post("/refresh/{exchange_id}", response_model=SyncResponse)
async def refresh_exchange(exchange_id: str):
    """
    Refresh data from a specific exchange.

    Args:
        exchange_id: Exchange identifier (binance, coingecko, etc.)

    Returns:
        Task ID for tracking sync progress
    """
    try:
        # Validate exchange exists
        from database.connection import get_db_context
        from sqlalchemy import text

        with get_db_context() as session:
            result = session.execute(
                text("SELECT id FROM exchanges WHERE id = :exchange_id"),
                {"exchange_id": exchange_id}
            )
            if not result.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exchange not found: {exchange_id}"
                )

        logger.info(f"Refreshing exchange: {exchange_id}")

        # Create sync service
        sync_service = ExchangeSync()

        # Create background task
        async def sync_task():
            return await sync_service.sync_exchange(exchange_id)

        task_id = run_background_task(
            name=f"Refresh exchange: {exchange_id}",
            func=sync_task,
            auto_run=True
        )

        return SyncResponse(
            task_id=task_id,
            message=f"Refresh started for exchange: {exchange_id}",
            exchanges=[exchange_id],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh exchange: {str(e)}"
        )


@router.get("/status", response_model=DataStatusResponse)
async def get_data_status():
    """
    Get current data status and sync information.

    Returns initialization status, data counts, sync status,
    and data quality metrics.

    Returns:
        Data status information
    """
    try:
        # Get initialization status
        init_status = get_initialization_status()

        # Get sync status
        sync_service = ExchangeSync()
        sync_status = sync_service.get_sync_status()

        # Get quality metrics
        quality_metrics = sync_service.get_data_quality_metrics()

        return DataStatusResponse(
            initialized=init_status.get("initialized", False),
            initialized_at=init_status.get("initialized_at"),
            data_counts=init_status.get("data_counts", {}),
            sync_status=sync_status if isinstance(sync_status, list) else [sync_status],
            quality_metrics=quality_metrics,
        )

    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data status: {str(e)}"
        )


@router.get("/sync/{exchange_id}")
async def get_exchange_sync_status(exchange_id: str):
    """
    Get sync status for a specific exchange.

    Args:
        exchange_id: Exchange identifier

    Returns:
        Sync status for the exchange
    """
    try:
        sync_service = ExchangeSync()
        status = sync_service.get_sync_status(exchange_id)

        if not status or "error" in status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sync status found for exchange: {exchange_id}"
            )

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    Get status of a background task.

    Args:
        task_id: Task identifier

    Returns:
        Task status information
    """
    try:
        queue = get_task_queue()
        task = queue.get_task(task_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task not found: {task_id}"
            )

        return TaskResponse(**task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/tasks", response_model=TasksListResponse)
async def get_all_tasks(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=100, description="Max tasks to return")
):
    """
    Get all background tasks.

    Args:
        status: Optional filter by status (pending, running, success, failed, cancelled)
        limit: Maximum number of tasks to return

    Returns:
        List of tasks
    """
    try:
        queue = get_task_queue()

        # Filter by status if provided
        from services.background_tasks import TaskStatus
        task_status = TaskStatus(status) if status else None

        tasks = queue.get_all_tasks(status=task_status)

        # Sort by created_at (newest first) and limit
        tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        tasks = tasks[:limit]

        return TasksListResponse(
            tasks=tasks,
            count=len(tasks),
        )

    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tasks: {str(e)}"
        )


@router.post("/tasks/cleanup")
async def cleanup_old_tasks(
    max_age_hours: int = Query(default=24, ge=1, le=168, description="Maximum age in hours"),
    keep_recent: int = Query(default=100, ge=10, le=1000, description="Number of recent tasks to keep")
):
    """
    Clean up old completed tasks.

    Args:
        max_age_hours: Maximum age in hours for tasks to keep
        keep_recent: Always keep this many recent tasks

    Returns:
        Cleanup result
    """
    try:
        queue = get_task_queue()
        queue.cleanup_old_tasks(max_age_hours=max_age_hours, keep_recent=keep_recent)

        return {
            "success": True,
            "message": f"Cleaned up tasks older than {max_age_hours}h (keeping {keep_recent} recent)"
        }

    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup tasks: {str(e)}"
        )


@router.get("/metrics/quality")
async def get_quality_metrics():
    """
    Get data quality metrics.

    Returns detailed metrics about the synchronized data including
    counts, coverage, and per-exchange breakdowns.

    Returns:
        Data quality metrics
    """
    try:
        sync_service = ExchangeSync()
        metrics = sync_service.get_data_quality_metrics()

        return metrics

    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality metrics: {str(e)}"
        )
