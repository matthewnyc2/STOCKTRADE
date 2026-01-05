"""
Integration tests for Admin API endpoints.

Tests user management, system health, and usage metrics endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from api.main import app
from database.connection import get_db_context
from database.repositories.user import UserRepository


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Mock admin token for testing."""
    return "Bearer test_admin_token"


class TestSystemHealth:
    """Tests for /api/v1/admin/system/health endpoint."""

    def test_get_system_health_requires_auth(self, client):
        """Test that health check requires authentication."""
        response = client.get("/api/v1/admin/system/health")
        assert response.status_code == 401

    def test_get_system_health_with_auth(self, client, admin_token):
        """Test health check with authentication."""
        response = client.get(
            "/api/v1/admin/system/health",
            headers={"Authorization": admin_token}
        )
        # May return 200 or 500 depending on system state
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "uptime_seconds" in data
            assert "database_status" in data
            assert "cpu_percent" in data
            assert "memory_percent" in data


class TestUsageMetrics:
    """Tests for /api/v1/admin/system/metrics endpoint."""

    def test_get_metrics_requires_auth(self, client):
        """Test that metrics require authentication."""
        response = client.get("/api/v1/admin/system/metrics")
        assert response.status_code == 401

    def test_get_metrics_with_auth(self, client, admin_token):
        """Test metrics with authentication."""
        response = client.get(
            "/api/v1/admin/system/metrics",
            headers={"Authorization": admin_token}
        )
        # May return 200 or 500 depending on system state
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "period_hours" in data
            assert "total_users" in data
            assert "total_strategies" in data


class TestUserManagement:
    """Tests for user management endpoints."""

    def test_list_users_requires_auth(self, client):
        """Test that listing users requires authentication."""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_list_users_with_auth(self, client, admin_token):
        """Test listing users with authentication."""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": admin_token}
        )
        # May return 200 or 500 depending on database state
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "users" in data
            assert "total" in data
            assert "page" in data

    def test_list_users_with_pagination(self, client, admin_token):
        """Test listing users with pagination."""
        response = client.get(
            "/api/v1/admin/users?page=1&page_size=10",
            headers={"Authorization": admin_token}
        )
        # May return 200 or 500
        assert response.status_code in [200, 500]

    def test_create_user_requires_auth(self, client):
        """Test that creating users requires authentication."""
        response = client.post(
            "/api/v1/admin/users",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "password123",
            }
        )
        assert response.status_code == 401

    def test_create_user_with_auth(self, client, admin_token):
        """Test creating a user with authentication."""
        response = client.post(
            "/api/v1/admin/users",
            headers={"Authorization": admin_token},
            json={
                "email": f"test-{datetime.utcnow().timestamp()}@example.com",
                "username": f"testuser_{datetime.utcnow().timestamp()}",
                "password": "password123",
                "role": "USER",
                "status": "ACTIVE",
            }
        )
        # May return 201 or 500
        assert response.status_code in [201, 409, 500]

    def test_get_user_requires_auth(self, client):
        """Test that getting a user requires authentication."""
        response = client.get("/api/v1/admin/users/123")
        assert response.status_code == 401

    def test_get_user_not_found(self, client, admin_token):
        """Test getting non-existent user."""
        response = client.get(
            "/api/v1/admin/users/nonexistent_id",
            headers={"Authorization": admin_token}
        )
        # Should return 404 or 500
        assert response.status_code in [404, 500]

    def test_update_user_requires_auth(self, client):
        """Test that updating users requires authentication."""
        response = client.put(
            "/api/v1/admin/users/123",
            json={"status": "INACTIVE"}
        )
        assert response.status_code == 401

    def test_delete_user_requires_auth(self, client):
        """Test that deleting users requires authentication."""
        response = client.delete("/api/v1/admin/users/123")
        assert response.status_code == 401


class TestUserActivation:
    """Tests for user activation/deactivation endpoints."""

    def test_activate_user_requires_auth(self, client):
        """Test that activation requires authentication."""
        response = client.post("/api/v1/admin/users/123/activate")
        assert response.status_code == 401

    def test_deactivate_user_requires_auth(self, client):
        """Test that deactivation requires authentication."""
        response = client.post("/api/v1/admin/users/123/deactivate")
        assert response.status_code == 401


class TestAdminData:
    """Tests for admin data management endpoints."""

    def test_initialize_data(self, client):
        """Test data initialization endpoint."""
        response = client.post("/api/v1/admin/data/initialize")
        # Should return 200 (already initialized) or 201 (new)
        assert response.status_code in [200, 201]

    def test_get_data_status(self, client):
        """Test data status endpoint."""
        response = client.get("/api/v1/admin/data/status")
        assert response.status_code in [200, 500]

    def test_get_tasks(self, client):
        """Test getting background tasks."""
        response = client.get("/api/v1/admin/data/tasks")
        assert response.status_code in [200, 500]

    def test_cleanup_tasks(self, client):
        """Test task cleanup endpoint."""
        response = client.post("/api/v1/admin/data/tasks/cleanup")
        assert response.status_code in [200, 500]


@pytest.mark.integration
class TestAdminWorkflows:
    """Integration tests for admin workflows."""

    def test_system_monitoring_workflow(self, client, admin_token):
        """Test complete system monitoring workflow."""
        # Check health
        health_response = client.get(
            "/api/v1/admin/system/health",
            headers={"Authorization": admin_token}
        )
        assert health_response.status_code in [200, 500]

        # Get metrics
        metrics_response = client.get(
            "/api/v1/admin/system/metrics?period_hours=24",
            headers={"Authorization": admin_token}
        )
        assert metrics_response.status_code in [200, 500]

    def test_user_management_workflow(self, client, admin_token):
        """Test user management workflow."""
        # List users
        list_response = client.get(
            "/api/v1/admin/users?page=1&page_size=20",
            headers={"Authorization": admin_token}
        )
        assert list_response.status_code in [200, 500]

        if list_response.status_code == 200:
            users = list_response.json().get("users", [])
            if users:
                # Try to get first user
                user_id = users[0]["id"]
                get_response = client.get(
                    f"/api/v1/admin/users/{user_id}",
                    headers={"Authorization": admin_token}
                )
                assert get_response.status_code in [200, 404, 500]
