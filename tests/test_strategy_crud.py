"""
Tests for Strategy CRUD operations and validation.

Tests create, read, update, delete operations with proper validation,
status management, and business rules.
"""

import pytest
from datetime import datetime

from fastapi.testclient import TestClient

from api.main import app
from database.connection import get_db_session
from database.repositories import StrategyRepository, StrategyLayerRepository
from models import StrategyType, Status


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    with get_db_session() as session:
        yield session


class TestStrategyCreate:
    """Tests for strategy creation with validation."""

    def test_create_strategy_success(self, test_client, db_session):
        """Test successful strategy creation."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "My Test Strategy",
                "description": "A test strategy for validation",
                "type": "composed",
                "parameters": {"param1": "value1"},
                "layers": [],
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Strategy"
        assert data["status"] == "draft"
        assert "id" in data
        db_session.rollback()

    def test_create_strategy_name_too_short(self, test_client):
        """Test strategy name must be at least 3 characters."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "AB",  # Too short
                "type": "composed",
            }
        )
        assert response.status_code == 422

    def test_create_strategy_name_too_long(self, test_client):
        """Test strategy name must be at most 100 characters."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "A" * 101,  # Too long
                "type": "composed",
            }
        )
        assert response.status_code == 422

    def test_create_strategy_empty_name(self, test_client):
        """Test strategy name cannot be empty or whitespace."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "   ",  # Whitespace only
                "type": "composed",
            }
        )
        assert response.status_code == 422

    def test_create_strategy_duplicate_name(self, test_client, db_session):
        """Test cannot create strategy with duplicate name."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create first strategy
        repo.create(
            id=f"strat_{uuid4().hex[:8]}",
            name="Duplicate Name",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        # Try to create duplicate
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "Duplicate Name",
                "type": "composed",
            }
        )
        assert response.status_code == 409
        db_session.rollback()

    def test_create_strategy_default_status(self, test_client, db_session):
        """Test new strategies default to DRAFT status."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "New Strategy",
                "type": "composed",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        db_session.rollback()


class TestStrategyRead:
    """Tests for strategy retrieval."""

    def test_get_strategy_by_id(self, test_client, db_session):
        """Test getting a strategy by ID."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Test Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.get(f"/api/strategies/{strategy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy_id
        assert data["name"] == "Test Strategy"
        db_session.rollback()

    def test_get_strategy_not_found(self, test_client):
        """Test getting non-existent strategy returns 404."""
        response = test_client.get("/api/strategies/nonexistent_id")
        assert response.status_code == 404

    def test_list_strategies(self, test_client, db_session):
        """Test listing all strategies."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create a few strategies
        for i in range(3):
            repo.create(
                id=f"strat_{uuid4().hex[:8]}",
                name=f"Strategy {i}",
                type="composed",
                parameters={},
                layers=[],
                status="draft",
            )
        db_session.commit()

        response = test_client.get("/api/strategies/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        db_session.rollback()

    def test_list_strategies_by_status(self, test_client, db_session):
        """Test filtering strategies by status."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create strategies with different statuses
        repo.create(
            id=f"strat_{uuid4().hex[:8]}",
            name="Active Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="active",
        )
        repo.create(
            id=f"strat_{uuid4().hex[:8]}",
            name="Draft Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.get("/api/strategies/?status_filter=active")
        assert response.status_code == 200
        data = response.json()
        assert all(s.get("status") == "active" for s in data)
        db_session.rollback()


class TestStrategyUpdate:
    """Tests for strategy updates."""

    def test_update_strategy_name(self, test_client, db_session):
        """Test updating strategy name."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Original Name",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.put(
            f"/api/strategies/{strategy_id}",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        db_session.rollback()

    def test_update_strategy_parameters(self, test_client, db_session):
        """Test updating strategy parameters."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Test Strategy",
            type="composed",
            parameters={"old": "value"},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.put(
            f"/api/strategies/{strategy_id}",
            json={"parameters": {"new": "params"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parameters"] == {"new": "params"}
        db_session.rollback()

    def test_update_strategy_not_found(self, test_client):
        """Test updating non-existent strategy returns 404."""
        response = test_client.put(
            "/api/strategies/nonexistent_id",
            json={"name": "New Name"}
        )
        assert response.status_code == 404

    def test_update_strategy_name_validation(self, test_client, db_session):
        """Test updating strategy name still validates length."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Valid Name",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.put(
            f"/api/strategies/{strategy_id}",
            json={"name": "AB"}  # Too short
        )
        assert response.status_code == 422
        db_session.rollback()


class TestStrategyDelete:
    """Tests for strategy deletion."""

    def test_delete_strategy_success(self, test_client, db_session):
        """Test successful strategy deletion."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        strategy = repo.create(
            id=strategy_id,
            name="Delete Me",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.delete(f"/api/strategies/{strategy_id}")
        assert response.status_code == 204

        # Verify it's deleted
        assert repo.get(strategy_id) is None
        db_session.rollback()

    def test_delete_active_strategy_forbidden(self, test_client, db_session):
        """Test cannot delete an active strategy."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Active Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="active",
        )
        db_session.commit()

        response = test_client.delete(f"/api/strategies/{strategy_id}")
        assert response.status_code == 400
        data = response.json()
        assert "Cannot delete active strategy" in data.get("detail", "")
        db_session.rollback()

    def test_delete_strategy_not_found(self, test_client):
        """Test deleting non-existent strategy returns 404."""
        response = test_client.delete("/api/strategies/nonexistent_id")
        assert response.status_code == 404

    def test_delete_strategy_with_layers(self, test_client, db_session):
        """Test deleting strategy also deletes its layers."""
        repo = StrategyRepository(db_session)
        layer_repo = StrategyLayerRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        layer_id = f"layer_{uuid4().hex[:8]}"

        repo.create(
            id=strategy_id,
            name="Strategy with Layers",
            type="composed",
            parameters={},
            layers=[layer_id],
            status="draft",
        )
        layer_repo.create(
            id=layer_id,
            strategy_id=strategy_id,
            layer_order=0,
            weight=1.0,
            config={},
        )
        db_session.commit()

        response = test_client.delete(f"/api/strategies/{strategy_id}")
        assert response.status_code == 204

        # Verify layer is also deleted
        assert layer_repo.get(layer_id) is None
        db_session.rollback()


class TestStrategyActivation:
    """Tests for strategy activation and deactivation."""

    def test_activate_strategy(self, test_client, db_session):
        """Test activating a draft strategy."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Draft Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.post(f"/api/strategies/{strategy_id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        db_session.rollback()

    def test_deactivate_strategy(self, test_client, db_session):
        """Test deactivating an active strategy."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Active Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="active",
        )
        db_session.commit()

        response = test_client.post(f"/api/strategies/{strategy_id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "inactive"
        db_session.rollback()

    def test_activate_not_found_strategy(self, test_client):
        """Test activating non-existent strategy returns 404."""
        response = test_client.post("/api/strategies/nonexistent_id/activate")
        assert response.status_code == 404

    def test_deactivate_not_found_strategy(self, test_client):
        """Test deactivating non-existent strategy returns 404."""
        response = test_client.post("/api/strategies/nonexistent_id/deactivate")
        assert response.status_code == 404

    def test_status_transition_draft_to_active(self, test_client, db_session):
        """Test status transition from DRAFT to ACTIVE."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Draft Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        # Draft -> Active is allowed
        response = test_client.post(f"/api/strategies/{strategy_id}/activate")
        assert response.status_code == 200
        db_session.rollback()

    def test_status_transition_active_to_inactive(self, test_client, db_session):
        """Test status transition from ACTIVE to INACTIVE."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Active Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="active",
        )
        db_session.commit()

        # Active -> Inactive is allowed
        response = test_client.post(f"/api/strategies/{strategy_id}/deactivate")
        assert response.status_code == 200
        db_session.rollback()

    def test_get_active_strategies(self, test_client, db_session):
        """Test getting only active strategies."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create mixed strategies
        active_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=active_id,
            name="Active Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="active",
        )
        repo.create(
            id=f"strat_{uuid4().hex[:8]}",
            name="Draft Strategy",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.get("/api/strategies/?status_filter=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(s.get("status") == "active" for s in data)
        db_session.rollback()


class TestStrategyRepository:
    """Tests for StrategyRepository methods."""

    def test_get_by_status(self, db_session):
        """Test get_by_status repository method."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create strategies with different statuses
        for i in range(2):
            repo.create(
                id=f"strat_{uuid4().hex[:8]}",
                name=f"Active {i}",
                type="composed",
                parameters={},
                layers=[],
                status="active",
            )
        for i in range(3):
            repo.create(
                id=f"strat_{uuid4().hex[:8]}",
                name=f"Draft {i}",
                type="composed",
                parameters={},
                layers=[],
                status="draft",
            )
        db_session.commit()

        active_strategies = repo.get_by_status("active")
        assert len(active_strategies) >= 2
        assert all(s.status == "active" for s in active_strategies)
        db_session.rollback()

    def test_get_user_strategies(self, db_session):
        """Test get_user_strategies returns all strategies (placeholder)."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        # Create a few strategies
        for i in range(3):
            repo.create(
                id=f"strat_{uuid4().hex[:8]}",
                name=f"User Strategy {i}",
                type="composed",
                parameters={},
                layers=[],
                status="draft",
            )
        db_session.commit()

        # For now, get_user_strategies returns all (no auth yet)
        user_strategies = repo.get_all(limit=100)
        assert len(user_strategies) >= 3
        db_session.rollback()


class TestStrategyLayers:
    """Tests for strategy layer management."""

    def test_add_layer_to_strategy(self, test_client, db_session):
        """Test adding a layer to a strategy."""
        repo = StrategyRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        repo.create(
            id=strategy_id,
            name="Strategy for Layer",
            type="composed",
            parameters={},
            layers=[],
            status="draft",
        )
        db_session.commit()

        response = test_client.post(
            f"/api/strategies/{strategy_id}/layers",
            json={
                "layer_order": 0,
                "weight": 1.0,
                "config": {"type": "sma"},
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["strategy_id"] == strategy_id
        assert data["layer_order"] == 0
        db_session.rollback()

    def test_remove_layer_from_strategy(self, test_client, db_session):
        """Test removing a layer from a strategy."""
        repo = StrategyRepository(db_session)
        layer_repo = StrategyLayerRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        layer_id = f"layer_{uuid4().hex[:8]}"

        repo.create(
            id=strategy_id,
            name="Strategy with Layer",
            type="composed",
            parameters={},
            layers=[layer_id],
            status="draft",
        )
        layer_repo.create(
            id=layer_id,
            strategy_id=strategy_id,
            layer_order=0,
            weight=1.0,
            config={},
        )
        db_session.commit()

        response = test_client.delete(f"/api/strategies/{strategy_id}/layers/{layer_id}")
        assert response.status_code == 204

        # Verify layer removed from strategy
        strategy = repo.get(strategy_id)
        assert layer_id not in strategy.layers
        db_session.rollback()

    def test_get_strategy_layers(self, test_client, db_session):
        """Test getting all layers for a strategy."""
        repo = StrategyRepository(db_session)
        layer_repo = StrategyLayerRepository(db_session)
        from uuid import uuid4

        strategy_id = f"strat_{uuid4().hex[:8]}"
        layer1_id = f"layer_{uuid4().hex[:8]}"
        layer2_id = f"layer_{uuid4().hex[:8]}"

        repo.create(
            id=strategy_id,
            name="Multi Layer Strategy",
            type="composed",
            parameters={},
            layers=[layer1_id, layer2_id],
            status="draft",
        )
        layer_repo.create(
            id=layer1_id,
            strategy_id=strategy_id,
            layer_order=0,
            weight=0.5,
            config={"type": "sma"},
        )
        layer_repo.create(
            id=layer2_id,
            strategy_id=strategy_id,
            layer_order=1,
            weight=0.5,
            config={"type": "rsi"},
        )
        db_session.commit()

        response = test_client.get(f"/api/strategies/{strategy_id}/layers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        db_session.rollback()


class TestParameterValidation:
    """Tests for parameter schema validation."""

    def test_parameters_can_be_any_dict(self, test_client, db_session):
        """Test parameters accept any valid dictionary."""
        response = test_client.post(
            "/api/strategies/",
            json={
                "name": "Custom Params Strategy",
                "type": "composed",
                "parameters": {
                    "rsi_period": 14,
                    "sma_fast": 10,
                    "sma_slow": 30,
                    "custom_field": "custom_value",
                    "nested": {"key": "value"},
                },
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["parameters"]["rsi_period"] == 14
        db_session.rollback()
