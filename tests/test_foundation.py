"""
Foundation Tests - Fix First Priority
WHY: numpy missing breaks entire test suite, import chain broken
"""
import pytest


def test_all_dependencies_installed():
    """WHY: numpy missing breaks entire test suite"""
    import numpy
    import pandas
    import fastapi
    import sqlalchemy
    assert True


def test_basic_imports_work():
    """WHY: Import chain broken in services/__init__.py"""
    from api.main import app
    from services.genetic_optimizer import GeneticOptimizer
    assert app is not None
    assert GeneticOptimizer is not None


def test_database_connection():
    """WHY: Data persistence required for all features"""
    from core.database import get_db
    db = next(get_db())
    assert db is not None
