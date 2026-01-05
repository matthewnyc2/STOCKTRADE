"""
Background Task Service.

Provides a simple task queue for async operations with status tracking
and progress reporting. Used for long-running sync operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Any, Callable
from uuid import uuid4
import json

from sqlalchemy import text
from core.database import engine

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundTask:
    """
    Represents a background task with status tracking.
    """

    def __init__(
        self, task_id: str, name: str, func: Callable, args: tuple = (), kwargs: dict = None
    ):
        """
        Initialize a background task.

        Args:
            task_id: Unique task identifier
            name: Human-readable task name
            func: Async function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
        """
        self.task_id = task_id
        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.message = ""
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at and self.started_at
                else None
            ),
        }


class TaskQueue:
    """
    Simple in-memory task queue with database persistence.

    Manages background tasks with status tracking and progress reporting.
    """

    def __init__(self):
        """Initialize the task queue."""
        self.tasks: Dict[str, BackgroundTask] = {}
        self._init_db()

    def _init_db(self):
        """Initialize the background_tasks table."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS background_tasks (
                        task_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        progress INTEGER DEFAULT 0,
                        message TEXT,
                        result TEXT,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)
                )
                conn.commit()

                # Load existing tasks
                results = conn.execute(text("SELECT * FROM background_tasks")).fetchall()

                for row in results:
                    task = BackgroundTask(
                        task_id=row[0],
                        name=row[1],
                        func=None,  # Function not persisted
                    )
                    task.status = TaskStatus(row[2])
                    task.progress = row[3]
                    task.message = row[4]
                    task.result = json.loads(row[5]) if row[5] else None
                    task.error = row[6]
                    task.created_at = datetime.fromisoformat(row[7]) if row[7] else None
                    task.started_at = datetime.fromisoformat(row[8]) if row[8] else None
                    task.completed_at = datetime.fromisoformat(row[9]) if row[9] else None

                    # Only load non-running tasks (they would have been interrupted)
                    if task.status != TaskStatus.RUNNING:
                        self.tasks[task.task_id] = task

        except Exception as e:
            logger.error(f"Error initializing task queue: {e}")

    def _persist_task(self, task: BackgroundTask):
        """Persist task state to database."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT OR REPLACE INTO background_tasks
                        (task_id, name, status, progress, message, result, error, created_at, started_at, completed_at)
                        VALUES (:task_id, :name, :status, :progress, :message, :result, :error, :created_at, :started_at, :completed_at)
                    """),
                    {
                        "task_id": task.task_id,
                        "name": task.name,
                        "status": task.status.value,
                        "progress": task.progress,
                        "message": task.message,
                        "result": json.dumps(task.result) if task.result else None,
                        "error": task.error,
                        "created_at": task.created_at,
                        "started_at": task.started_at,
                        "completed_at": task.completed_at,
                    },
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error persisting task: {e}")

    def create_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        auto_run: bool = False,
    ) -> str:
        """
        Create a new background task.

        Args:
            name: Human-readable task name
            func: Async function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            auto_run: Whether to automatically start the task

        Returns:
            Task ID
        """
        task_id = str(uuid4())

        task = BackgroundTask(task_id=task_id, name=name, func=func, args=args, kwargs=kwargs)

        self.tasks[task_id] = task
        self._persist_task(task)

        logger.info(f"Created background task: {task_id} - {name}")

        if auto_run:
            asyncio.create_task(self._run_task(task_id))

        return task_id

    async def _run_task(self, task_id: str):
        """
        Execute a background task.

        Args:
            task_id: Task identifier
        """
        task = self.tasks.get(task_id)

        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        if task.func is None:
            logger.error(f"Task has no function (loaded from persistence): {task_id}")
            return

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.message = "Task started"
        self._persist_task(task)

        try:
            logger.info(f"Running background task: {task_id} - {task.name}")

            # Execute the function
            result = await task.func(*task.args, **task.kwargs)

            task.result = result
            task.status = TaskStatus.SUCCESS
            task.message = "Task completed successfully"
            task.progress = 100

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.message = "Task was cancelled"
            logger.info(f"Task cancelled: {task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.message = f"Task failed: {e}"
            logger.error(f"Task failed: {task_id} - {e}")

        finally:
            task.completed_at = datetime.utcnow()
            self._persist_task(task)

            logger.info(
                f"Task completed: {task_id} - {task.name} - "
                f"status={task.status.value}, "
                f"duration={((task.completed_at - task.started_at).total_seconds() if task.started_at and task.completed_at else 0):.2f}s"
            )

    def run_task(self, task_id: str) -> bool:
        """
        Start executing a task.

        Args:
            task_id: Task identifier

        Returns:
            True if task started, False otherwise
        """
        task = self.tasks.get(task_id)

        if not task:
            logger.error(f"Task not found: {task_id}")
            return False

        if task.status == TaskStatus.RUNNING:
            logger.warning(f"Task already running: {task_id}")
            return False

        asyncio.create_task(self._run_task(task_id))
        return True

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status.

        Args:
            task_id: Task identifier

        Returns:
            Task information or None if not found
        """
        task = self.tasks.get(task_id)

        if not task:
            return None

        return task.to_dict()

    def get_all_tasks(self, status: Optional[TaskStatus] = None) -> list:
        """
        Get all tasks.

        Args:
            status: Optional filter by status

        Returns:
            List of task information
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        return [t.to_dict() for t in tasks]

    def update_progress(self, task_id: str, progress: int, message: str = ""):
        """
        Update task progress.

        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        task = self.tasks.get(task_id)

        if not task:
            logger.warning(f"Task not found for progress update: {task_id}")
            return

        task.progress = max(0, min(100, progress))
        if message:
            task.message = message

        self._persist_task(task)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False otherwise
        """
        task = self.tasks.get(task_id)

        if not task:
            return False

        if task.status == TaskStatus.RUNNING:
            # Can't cancel running tasks in this simple implementation
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        self._persist_task(task)

        return True

    def cleanup_old_tasks(self, max_age_hours: int = 24, keep_recent: int = 100):
        """
        Clean up old completed tasks.

        Args:
            max_age_hours: Maximum age in hours for tasks to keep
            keep_recent: Always keep this many recent tasks
        """
        try:
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=max_age_hours)

            # Get completed/failed tasks sorted by completion time
            completed_tasks = [
                t
                for t in self.tasks.values()
                if t.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED)
                and t.completed_at
            ]

            # Sort by completion time (newest first)
            completed_tasks.sort(key=lambda t: t.completed_at, reverse=True)

            # Keep recent tasks
            to_keep = set()
            for task in completed_tasks[:keep_recent]:
                to_keep.add(task.task_id)

            # Remove old tasks
            for task in completed_tasks:
                if task.task_id not in to_keep and task.completed_at < cutoff:
                    del self.tasks[task.task_id]

                    # Remove from database
                    with engine.connect() as conn:
                        conn.execute(
                            text("DELETE FROM background_tasks WHERE task_id = :task_id"),
                            {"task_id": task.task_id},
                        )
                        conn.commit()

            logger.info(f"Cleaned up old tasks, kept {len(to_keep)} recent tasks")

        except Exception as e:
            logger.error(f"Error cleaning up old tasks: {e}")


# Global task queue instance
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """
    Get the global task queue instance.

    Returns:
        TaskQueue instance
    """
    global _task_queue

    if _task_queue is None:
        _task_queue = TaskQueue()

    return _task_queue


async def run_background_task(
    name: str, func: Callable, args: tuple = (), kwargs: dict = None, auto_run: bool = True
) -> str:
    """
    Convenience function to create and run a background task.

    Args:
        name: Human-readable task name
        func: Async function to execute
        args: Positional arguments for function
        kwargs: Keyword arguments for function
        auto_run: Whether to automatically start task

    Returns:
        Task ID
    """
    queue = get_task_queue()

    task_id = queue.create_task(name=name, func=func, args=args, kwargs=kwargs, auto_run=auto_run)

    return task_id


async def schedule_gap_detection_task(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    auto_backfill: bool = True,
    check_interval_hours: int = 1,
) -> str:
    """
    Schedule periodic gap detection and backfill task.

    This function creates a background task that will run periodically
    to detect gaps in historical data and automatically trigger backfill.

    Args:
        symbols: List of symbols to check (default: major pairs)
        timeframes: List of timeframes to check (default: ["1h", "1d"])
        auto_backfill: Whether to automatically backfill gaps
        check_interval_hours: How often to run gap detection

    Returns:
        Task ID
    """
    from services.historical_data_manager import get_gap_detector

    async def gap_detection_loop():
        """Periodic gap detection loop."""
        queue = get_task_queue()

        # Default symbols to check
        default_symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "UNIUSDT"]
        default_timeframes = timeframes or ["1h", "1d"]

        gap_detector = get_gap_detector()

        while True:
            try:
                logger.info("Starting periodic gap detection...")

                # Detect gaps for all symbols and timeframes
                all_gaps = gap_detector.detect_gaps_batch(
                    symbols=default_symbols,
                    timeframes=default_timeframes,
                    start=datetime.utcnow() - timedelta(hours=check_interval_hours * 2),
                    end=datetime.utcnow(),
                )

                total_gaps = sum(len(gaps) for gaps in all_gaps.values())

                logger.info(f"Gap detection complete: {total_gaps} gaps found")

                # Optionally trigger backfill
                if auto_backfill and total_gaps > 0:
                    from services.historical_data_manager import get_backfill_manager

                    backfill_manager = get_backfill_manager()

                    # Create backfill task
                    backfill_task_id = queue.create_task(
                        name=f"Backfill Gaps ({len(default_symbols)} symbols)",
                        func=backfill_manager.backfill_batch,
                        args=(default_symbols,),
                        kwargs={"timeframe": "1h"},
                        auto_run=False,
                    )

                    # Run backfill immediately
                    queue.run_task(backfill_task_id)

                    logger.info(f"Triggered backfill task: {backfill_task_id}")

                # Wait for next check
                await asyncio.sleep(check_interval_hours * 3600)

            except asyncio.CancelledError:
                logger.info("Gap detection task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in gap detection loop: {e}")
                # Wait and retry
                await asyncio.sleep(check_interval_hours * 3600)

    # Start the loop in background
    task_id = queue.create_task(
        name="Periodic Gap Detection",
        func=gap_detection_loop,
        auto_run=False,  # Don't auto-run, let caller decide
    )

    queue.run_task(task_id)

    return task_id
