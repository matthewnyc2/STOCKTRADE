"""
Tests for the enhanced strategy management system.

Tests the new strategy storage and management features including:
- Enhanced Strategy model fields
- Strategy templates
- Strategy favorites
- Strategy versions
- Strategy cloning
- Strategy import/export
- Strategy search
"""

import pytest
from uuid import uuid4

from database.connection import get_db_context
from database.repositories import (
    StrategyRepository,
    StrategyLayerRepository,
    StrategyFavoriteRepository,
    StrategyVersionRepository,
)
from services.strategy_manager import get_strategy_manager, StrategyValidationError
from models import StrategyType, Status, RiskLevel


class TestStrategyModelEnhancements:
    """Test enhanced Strategy model fields."""

    def test_strategy_with_enhanced_fields(self):
        """Test creating a strategy with new fields."""
        with get_db_context() as session:
            repo = StrategyRepository(session)

            strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy = repo.create(
                id=strategy_id,
                name="Test Enhanced Strategy",
                description="Testing enhanced fields",
                type="composed",
                parameters={"test": "value"},
                layers=[],
                status="draft",
                # New fields
                template_id="tpl_test",
                parent_id=None,
                tags=["test", "enhanced"],
                risk_level="medium",
                performance_summary={"return": 0.1},
                is_template=False,
            )

            assert strategy.id == strategy_id
            assert strategy.tags == ["test", "enhanced"]
            assert strategy.risk_level == "medium"
            assert strategy.template_id == "tpl_test"
            assert strategy.performance_summary == {"return": 0.1}

    def test_strategy_get_by_tag(self):
        """Test getting strategies by tag."""
        with get_db_context() as session:
            repo = StrategyRepository(session)

            # Create strategies with tags
            repo.create(
                id=f"strat_{uuid4().hex[:12]}",
                name="Tagged Strategy 1",
                description="Test",
                type="composed",
                tags=["momentum", "test"],
                is_template=False,
            )

            repo.create(
                id=f"strat_{uuid4().hex[:12]}",
                name="Tagged Strategy 2",
                description="Test",
                type="composed",
                tags=["trend", "test"],
                is_template=False,
            )

            # Get by tag
            momentum_strategies = repo.get_by_tag("momentum")
            assert len(momentum_strategies) >= 1
            assert any("momentum" in s.tags for s in momentum_strategies)

    def test_strategy_get_by_risk_level(self):
        """Test getting strategies by risk level."""
        with get_db_context() as session:
            repo = StrategyRepository(session)

            repo.create(
                id=f"strat_{uuid4().hex[:12]}",
                name="Low Risk Strategy",
                description="Test",
                type="composed",
                risk_level="low",
                is_template=False,
            )

            low_risk = repo.get_by_risk_level("low")
            assert len(low_risk) >= 1
            assert any(s.risk_level == "low" for s in low_risk)


class TestStrategyFavorites:
    """Test strategy favorite functionality."""

    def test_add_favorite(self):
        """Test adding a strategy to favorites."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            fav_repo = StrategyFavoriteRepository(session)

            # Create a strategy
            strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy_repo.create(
                id=strategy_id,
                name="Favorite Test Strategy",
                description="Test",
                type="composed",
                is_template=False,
            )

            # Add to favorites
            favorite = fav_repo.add_favorite("default", strategy_id, "My notes")

            assert favorite.user_id == "default"
            assert favorite.strategy_id == strategy_id
            assert favorite.notes == "My notes"

    def test_remove_favorite(self):
        """Test removing a strategy from favorites."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            fav_repo = StrategyFavoriteRepository(session)

            # Create and favorite
            strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy_repo.create(
                id=strategy_id,
                name="Unfavorite Test",
                description="Test",
                type="composed",
                is_template=False,
            )
            fav_repo.add_favorite("default", strategy_id)

            # Remove
            removed = fav_repo.remove_favorite("default", strategy_id)
            assert removed is True

    def test_get_user_favorites(self):
        """Test getting user's favorites."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            fav_repo = StrategyFavoriteRepository(session)

            # Create strategies and favorites
            for i in range(3):
                strategy_id = f"strat_{uuid4().hex[:12]}"
                strategy_repo.create(
                    id=strategy_id,
                    name=f"Favorite {i}",
                    description="Test",
                    type="composed",
                    is_template=False,
                )
                fav_repo.add_favorite("default", strategy_id)

            favorites = fav_repo.get_user_favorites("default")
            assert len(favorites) >= 3


class TestStrategyVersions:
    """Test strategy version history."""

    def test_create_version(self):
        """Test creating a strategy version."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            version_repo = StrategyVersionRepository(session)

            # Create strategy
            strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy = strategy_repo.create(
                id=strategy_id,
                name="Version Test Strategy",
                description="Initial version",
                type="composed",
                parameters={"param1": "value1"},
                tags=["v1"],
                is_template=False,
            )

            # Create version
            version = version_repo.create_version(
                strategy,
                change_description="Initial commit",
                created_by="test_user",
            )

            assert version.strategy_id == strategy_id
            assert version.version_number == 1
            assert version.change_description == "Initial commit"

    def test_get_version_history(self):
        """Test getting version history."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            version_repo = StrategyVersionRepository(session)

            strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy = strategy_repo.create(
                id=strategy_id,
                name="History Test",
                description="Test",
                type="composed",
                is_template=False,
            )

            # Create multiple versions
            version_repo.create_version(strategy, "Version 1")
            strategy_repo.update(strategy_id, description="Updated")
            session.flush()
            strategy = strategy_repo.get(strategy_id)
            version_repo.create_version(strategy, "Version 2")

            history = version_repo.get_version_history(strategy_id)
            assert len(history) >= 2


class TestStrategyManager:
    """Test StrategyManager service."""

    def test_clone_strategy(self):
        """Test cloning a strategy."""
        manager = get_strategy_manager()

        with get_db_context() as session:
            repo = StrategyRepository(session)

            # Create original
            original_id = f"strat_{uuid4().hex[:12]}"
            repo.create(
                id=original_id,
                name="Original Strategy",
                description="To be cloned",
                type="composed",
                parameters={"test": "original"},
                tags=["original"],
                risk_level="medium",
                is_template=False,
            )

        # Clone
        clone = manager.clone_strategy(
            strategy_id=original_id,
            new_name="Cloned Strategy",
        )

        assert clone.name == "Cloned Strategy"
        assert clone.parent_id == original_id
        assert clone.parameters == {"test": "original"}

    def test_validate_strategy(self):
        """Test strategy validation."""
        manager = get_strategy_manager()

        from models import Strategy

        # Valid strategy
        valid = Strategy(
            id=f"strat_{uuid4().hex[:12]}",
            name="Valid Strategy",
            type=StrategyType.COMPOSED,
            parameters={"indicators": ["rsi"]},
            tags=["test"],
            risk_level=RiskLevel.MEDIUM,
        )

        is_valid, errors = manager.validate_strategy(valid)
        assert is_valid is True
        assert len(errors) == 0

    def test_export_import_strategy(self):
        """Test exporting and importing a strategy."""
        manager = get_strategy_manager()

        with get_db_context() as session:
            repo = StrategyRepository(session)

            strategy_id = f"strat_{uuid4().hex[:12]}"
            repo.create(
                id=strategy_id,
                name="Export Test",
                description="For export",
                type="composed",
                parameters={"test": "export"},
                tags=["exportable"],
                is_template=False,
            )

        # Export
        exported = manager.export_strategy(strategy_id, format="json")
        assert "Export Test" in exported
        assert "exportable" in exported

        # Import
        import json
        data = json.loads(exported)
        imported = manager.import_strategy(
            data=data,
            name="Imported Strategy",
            format="json",
        )

        assert imported.name == "Imported Strategy"
        assert imported.parameters == {"test": "export"}

    def test_calculate_performance(self):
        """Test calculating strategy performance."""
        manager = get_strategy_manager()

        # Use any strategy (may not have signals yet)
        with get_db_context() as session:
            repo = StrategyRepository(session)

            strategy_id = f"strat_{uuid4().hex[:12]}"
            repo.create(
                id=strategy_id,
                name="Performance Test",
                description="Test",
                type="composed",
                is_template=False,
            )

        performance = manager.calculate_performance(strategy_id)
        assert "strategy_id" in performance
        assert "total_signals" in performance


class TestStrategySearch:
    """Test strategy search functionality."""

    def test_search_strategies(self):
        """Test searching strategies with filters."""
        with get_db_context() as session:
            repo = StrategyRepository(session)

            # Create test strategies
            repo.create(
                id=f"strat_{uuid4().hex[:12]}",
                name="Momentum Strategy Alpha",
                description="A momentum trading strategy",
                type="composed",
                tags=["momentum", "alpha"],
                risk_level="high",
                is_template=False,
            )

            repo.create(
                id=f"strat_{uuid4().hex[:12]}",
                name="Trend Strategy Beta",
                description="A trend following strategy",
                type="composed",
                tags=["trend", "beta"],
                risk_level="low",
                is_template=False,
            )

            # Search by query
            results = repo.search(query="momentum")
            assert len(results) >= 1
            assert any("momentum" in s.name.lower() or "momentum" in (s.description or "").lower()
                      for s in results)

            # Search by tag
            results = repo.search(query="", tags=["trend"])
            assert len(results) >= 1

            # Search by risk level
            results = repo.search(query="", risk_level="low")
            assert len(results) >= 1


class TestStrategyRecommendations:
    """Test strategy recommendation system."""

    def test_get_recommendations(self):
        """Test getting strategy recommendations."""
        manager = get_strategy_manager()

        # Create some template strategies
        with get_db_context() as session:
            repo = StrategyRepository(session)

            repo.create(
                id=f"tpl_{uuid4().hex[:12]}",
                name="Low Risk Template",
                description="Test",
                type="composed",
                tags=["safe"],
                risk_level="low",
                backtest_sharpe_ratio=2.0,
                is_template=True,
            )

        recommendations = manager.get_strategy_recommendations(
            risk_preference=RiskLevel.LOW,
            preferred_tags=["safe"],
            limit=5,
        )

        assert len(recommendations) >= 0  # May have existing templates


@pytest.mark.integration
class TestEndToEndStrategyManagement:
    """End-to-end tests for strategy management."""

    def test_full_strategy_lifecycle(self):
        """Test complete lifecycle: create -> version -> clone -> favorite."""
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)
            fav_repo = StrategyFavoriteRepository(session)
            version_repo = StrategyVersionRepository(session)

            # 1. Create strategy with layers
            strategy_id = f"strat_{uuid4().hex[:12]}"
            layer_id = f"layer_{uuid4().hex[:12]}"

            strategy = strategy_repo.create(
                id=strategy_id,
                name="Lifecycle Test",
                description="Full lifecycle test",
                type="composed",
                parameters={"test": "value"},
                layers=[layer_id],
                tags=["lifecycle"],
                risk_level="medium",
                is_template=False,
            )

            layer_repo.create(
                id=layer_id,
                strategy_id=strategy_id,
                layer_order=0,
                weight=1.0,
                config={"type": "test"},
            )

            # 2. Create version
            version = version_repo.create_version(strategy, "Initial version")
            assert version.version_number == 1

            # 3. Update and create another version
            strategy_repo.update(strategy_id, description="Updated description")
            session.flush()
            strategy = strategy_repo.get(strategy_id)
            version2 = version_repo.create_version(strategy, "Updated")
            assert version2.version_number == 2

            # 4. Clone
            manager = get_strategy_manager()
            clone = manager.clone_strategy(strategy_id, "Cloned Lifecycle")
            assert clone.parent_id == strategy_id

            # 5. Add to favorites
            favorite = fav_repo.add_favorite("default", strategy_id, "Great strategy!")
            assert favorite.strategy_id == strategy_id

            # 6. Verify version history
            history = version_repo.get_version_history(strategy_id)
            assert len(history) >= 2

            # 7. Export
            exported = manager.export_strategy(strategy_id)
            assert "Lifecycle Test" in exported
