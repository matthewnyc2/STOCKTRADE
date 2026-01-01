"""
Pytest configuration and fixtures for async testing.
"""

import pytest


@pytest.fixture
def anyio_backend():
    """Configure pytest-asyncio to use asyncio backend."""
    return "asyncio"
