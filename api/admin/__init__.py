"""
Admin API package.

Contains admin-only endpoints for data management and system operations.
"""

from fastapi import APIRouter

from .data import router as data_router
from .routes import router as admin_routes_router

router = APIRouter(prefix="/admin", tags=["admin"])

# Include admin sub-routers
router.include_router(data_router)
router.include_router(admin_routes_router)
