"""
Tests for repository pattern and CRUD operations.
"""

import os
import pytest
import tempfile

from datetime import datetime
from decimal import Decimal


@pytest.fixture
def repo_db_url():
    """Provide a test database URL for repository tests."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"
    yield url
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def initialized_db(repo_db_url):
    """Initialize database with schema for repository tests."""
    import importlib
    import database.connection as conn_module
    importlib.reload(conn_module)

    original_url = conn_module.DATABASE_URL
    conn_module.DATABASE_URL = repo_db_url

    try:
        from database.migrations import run_migrations

        run_migrations()

        yield

    finally:
        conn_module.DATABASE_URL = original_url


class TestBaseRepository:
    """Tests for BaseRepository CRUD operations."""

    def test_create(self, initialized_db):
        """Test creating a record."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        strategy = repo.create(
            id="test_strat_1",
            name="Test Strategy",
            type="composed",
            status="draft",
        )

        assert strategy.id == "test_strat_1"
        assert strategy.name == "Test Strategy"
        assert strategy.type == "composed"

        session.close()

    def test_get(self, initialized_db):
        """Test getting a record by ID."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        # Create
        created = repo.create(
            id="test_strat_2",
            name="Get Test",
            type="template",
        )

        # Get
        retrieved = repo.get("test_strat_2")
        assert retrieved is not None
        assert retrieved.id == "test_strat_2"
        assert retrieved.name == "Get Test"

        session.close()

    def test_get_not_found(self, initialized_db):
        """Test getting non-existent record returns None."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        result = repo.get("nonexistent")
        assert result is None

        session.close()

    def test_update(self, initialized_db):
        """Test updating a record."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        # Create
        created = repo.create(
            id="test_strat_3",
            name="Before Update",
            type="ml",
        )

        # Update
        updated = repo.update("test_strat_3", name="After Update")
        assert updated is not None
        assert updated.name == "After Update"

        session.close()

    def test_delete(self, initialized_db):
        """Test deleting a record."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        # Create
        created = repo.create(
            id="test_strat_4",
            name="To Delete",
            type="genetic",
        )

        # Delete
        deleted = repo.delete("test_strat_4")
        assert deleted is True

        # Verify gone
        result = repo.get("test_strat_4")
        assert result is None

        session.close()

    def test_get_many(self, initialized_db):
        """Test getting multiple records."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        # Create multiple
        for i in range(5):
            repo.create(
                id=f"test_strat_many_{i}",
                name=f"Strategy {i}",
                type="composed",
            )

        # Get all
        all_strategies = repo.get_all()
        assert len(all_strategies) >= 5

        # Get with limit
        some_strategies = repo.get_many(limit=3)
        assert len(some_strategies) == 3

        session.close()

    def test_count(self, initialized_db):
        """Test counting records."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        # Create with specific type
        for i in range(3):
            repo.create(
                id=f"test_strat_count_{i}",
                name=f"Count {i}",
                type="ml",
            )

        count = repo.count(type="ml")
        assert count >= 3

        session.close()

    def test_exists(self, initialized_db):
        """Test checking if records exist."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        repo.create(
            id="test_strat_exists",
            name="Exists Test",
            type="template",
        )

        assert repo.exists(id="test_strat_exists") is True
        assert repo.exists(id="does_not_exist") is False

        session.close()


class TestStrategyRepository:
    """Tests for StrategyRepository specific methods."""

    def test_get_by_name(self, initialized_db):
        """Test getting strategy by name."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        repo.create(
            id="test_by_name",
            name="Unique Name Here",
            type="composed",
        )

        result = repo.get_by_name("Unique Name Here")
        assert result is not None
        assert result.id == "test_by_name"

        session.close()

    def test_get_by_type(self, initialized_db):
        """Test getting strategies by type."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        for i in range(3):
            repo.create(
                id=f"test_type_ml_{i}",
                name=f"ML Strategy {i}",
                type="ml",
            )

        results = repo.get_by_type("ml")
        assert len(results) >= 3

        session.close()

    def test_get_active_strategies(self, initialized_db):
        """Test getting active strategies."""
        from database.connection import get_db_session
        from database.repositories import StrategyRepository

        session = get_db_session()
        repo = StrategyRepository(session)

        repo.create(
            id="test_active_1",
            name="Active Strategy",
            type="composed",
            status="active",
        )
        repo.create(
            id="test_active_2",
            name="Another Active",
            type="ml",
            status="active",
        )
        repo.create(
            id="test_inactive",
            name="Inactive Strategy",
            type="genetic",
            status="inactive",
        )

        active = repo.get_active_strategies()
        assert len(active) >= 2

        session.close()


class TestSignalRepository:
    """Tests for SignalRepository."""

    def test_create_signal(self, initialized_db):
        """Test creating a signal."""
        from database.connection import get_db_session
        from database.repositories import SignalRepository

        session = get_db_session()
        repo = SignalRepository(session)

        signal = repo.create(
            id="test_sig_1",
            strategy_id="test_strat",
            symbol="BTC/USDT",
            signal_type="long",
            confidence=0.85,
            price=50000.0,
        )

        assert signal.id == "test_sig_1"
        assert signal.symbol == "BTC/USDT"
        assert signal.signal_type == "long"

        session.close()

    def test_get_by_symbol(self, initialized_db):
        """Test getting signals by symbol."""
        from database.connection import get_db_session
        from database.repositories import SignalRepository

        session = get_db_session()
        repo = SignalRepository(session)

        repo.create(
            id="test_sig_btc_1",
            strategy_id="strat_1",
            symbol="BTC/USDT",
            signal_type="long",
            confidence=0.9,
            price=50000.0,
        )

        results = repo.get_by_symbol("BTC/USDT")
        assert len(results) >= 1
        assert results[0].symbol == "BTC/USDT"

        session.close()


class TestPortfolioRepository:
    """Tests for PortfolioRepository."""

    def test_get_current_creates_default(self, initialized_db):
        """Test getting current portfolio creates default if missing."""
        from database.connection import get_db_session
        from database.repositories import PortfolioRepository

        session = get_db_session()
        repo = PortfolioRepository(session)

        portfolio = repo.get_current()
        assert portfolio is not None
        assert portfolio.id == "current"

        session.close()


class TestWhaleRepository:
    """Tests for WhaleRepository."""

    def test_create_whale(self, initialized_db):
        """Test creating a whale."""
        from database.connection import get_db_session
        from database.repositories import WhaleRepository

        session = get_db_session()
        repo = WhaleRepository(session)

        whale = repo.create(
            address="0x1234567890abcdef",
            tier="mega",
            holdings_usd=1000000.0,
            holdings_24h_change=0.05,
            pattern_type="accumulator",
        )

        assert whale.address == "0x1234567890abcdef"
        assert whale.tier == "mega"

        session.close()
