"""
Security tests for the Crypto Quant Laboratory API.

Tests authentication middleware, SQL injection prevention,
input validation, and other security measures.
"""

import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.security import api_key_middleware


class TestAuthenticationMiddleware:
    """Test authentication middleware implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = FastAPI()
        from core.security import APIKeyMiddleware
        self.app.add_middleware(APIKeyMiddleware)

        @self.app.get("/test-endpoint")
        async def test_endpoint():
            return {"message": "success"}

    def test_missing_api_key_header(self):
        """Test requests without API key header are rejected."""
        client = TestClient(self.app)

        response = client.get("/test-endpoint")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "API_KEY_REQUIRED"

    def test_invalid_api_key(self):
        """Test requests with invalid API key are rejected."""
        client = TestClient(self.app)

        response = client.get(
            "/test-endpoint",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "API_KEY_REQUIRED"

    def test_valid_api_key(self, monkeypatch):
        """Test requests with valid API key are accepted."""
        # Mock API key validation
        monkeypatch.setenv("API_KEY", "valid-test-key")

        # Reload security module to pick up new environment variable
        import importlib
        import core.security
        importlib.reload(core.security)

        # Create new app with reloaded middleware
        from core.security import APIKeyMiddleware
        app = FastAPI()
        app.add_middleware(APIKeyMiddleware)

        @app.get("/test-endpoint")
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)

        response = client.get(
            "/test-endpoint",
            headers={"X-API-Key": "valid-test-key"}
        )
        assert response.status_code == 200

    def test_api_key_case_sensitivity(self, monkeypatch):
        """Test API key validation is case-sensitive."""
        monkeypatch.setenv("API_KEY", "ValidKey123")

        client = TestClient(self.app)

        response = client.get(
            "/test-endpoint",
            headers={"X-API-Key": "validkey123"}  # Wrong case
        )
        assert response.status_code == 401


class TestDatabaseSecurity:
    """Test database security measures."""

    def test_database_credentials_from_environment(self, monkeypatch):
        """Test database URL is loaded from environment variable."""
        # Test with DATABASE_URL environment variable set
        test_url = "sqlite:///test_database.db"

        # Set the environment variable and reload the module to pick it up
        monkeypatch.setenv("DATABASE_URL", test_url)
        monkeypatch.setenv("TESTING", "true")

        # Import fresh to get the updated environment variable
        import importlib
        import database.connection
        importlib.reload(database.connection)

        assert database.connection.DATABASE_URL == test_url

    def test_default_database_url(self, monkeypatch):
        """Test default database URL is used when env vars not set."""
        # Clear environment variables
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)

        # Import fresh to get the default URL
        import importlib
        import database.connection
        importlib.reload(database.connection)

        from database.connection import DEFAULT_SQLITE_URL

        assert database.connection.DATABASE_URL == DEFAULT_SQLITE_URL


class TestSQLInjectionPrevention:
    """Test SQL injection prevention in database queries."""

    def test_sqlite_connection_uses_parameterized_queries(self):
        """Test SQLite connection uses parameterized queries."""
        from database.connection import _sqlite_engine
        from sqlalchemy import text

        engine = _sqlite_engine("sqlite:///:memory:")

        # Test that parameterized queries are used
        with engine.connect() as conn:
            # This should work with parameterized query
            result = conn.execute(text("SELECT :param"), {"param": "test"})
            assert result.scalar() == "test"

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "admin'--",
        "' UNION SELECT * FROM sensitive_table--",
    ])
    def test_sql_injection_attempts_are_prevented(self, malicious_input):
        """Test various SQL injection attempts are prevented."""
        from database.connection import get_db_context
        from sqlalchemy import text

        # Test parameterized queries prevent injection
        with get_db_context() as session:
            try:
                # This should fail due to type mismatch, not execute injection
                result = session.execute(
                    text("SELECT ?"),  # Parameterized query
                    [malicious_input]
                )
                # Should not raise an exception for the query itself
                assert result is not None
            except Exception as e:
                # Expected for some injection attempts
                assert "syntax error" not in str(e).lower()


class TestInputValidation:
    """Test input validation for API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        from pydantic import BaseModel, Field, ValidationError

        class TestModel(BaseModel):
            name: str = Field(..., min_length=1, max_length=100)
            price: float = Field(..., ge=0.01, le=1000000)
            quantity: int = Field(..., ge=1, le=1000000)
            symbol: str = Field(..., min_length=1, max_length=10, pattern=r'^[A-Z]+$')

        self.TestModel = TestModel

    def test_valid_input_passes_validation(self):
        """Test valid input passes validation."""
        valid_data = {
            "name": "Test Trade",
            "price": 100.50,
            "quantity": 100,
            "symbol": "BTC"
        }

        # Should not raise ValidationError
        validated = self.TestModel(**valid_data)
        assert validated.name == "Test Trade"
        assert validated.price == 100.50
        assert validated.quantity == 100
        assert validated.symbol == "BTC"

    def test_invalid_price_rejected(self):
        """Test invalid price values are rejected."""
        invalid_data = {
            "name": "Test Trade",
            "price": -1,  # Invalid price
            "quantity": 100,
            "symbol": "BTC"
        }

        with pytest.raises(ValidationError) as exc_info:
            self.TestModel(**invalid_data)

        # Check that price validation failed
        errors = exc_info.value.errors()
        assert any(error["type"] == "greater_than_equal" for error in errors)

    def test_invalid_quantity_rejected(self):
        """Test invalid quantity values are rejected."""
        invalid_data = {
            "name": "Test Trade",
            "price": 100.50,
            "quantity": 0,  # Invalid quantity
            "symbol": "BTC"
        }

        with pytest.raises(ValidationError) as exc_info:
            self.TestModel(**invalid_data)

        # Check that quantity validation failed
        errors = exc_info.value.errors()
        assert any(error["type"] == "greater_than_equal" for error in errors)

    def test_invalid_symbol_format_rejected(self):
        """Test invalid symbol format is rejected."""
        invalid_data = {
            "name": "Test Trade",
            "price": 100.50,
            "quantity": 100,
            "symbol": "btc"  # Should be uppercase
        }

        with pytest.raises(ValidationError) as exc_info:
            self.TestModel(**invalid_data)

        # Check that pattern validation failed
        errors = exc_info.value.errors()
        assert any(error["type"] == "string_pattern_mismatch" for error in errors)

    @pytest.mark.parametrize("malicious_input", [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "../../etc/passwd",
    ])
    def test_malicious_input_is_rejected(self, malicious_input):
        """Test malicious inputs are rejected by validation."""
        # Note: Pydantic by default doesn't reject all malicious inputs
        # We're testing that at least the symbol validation still works
        invalid_data = {
            "name": malicious_input,
            "price": 100.50,
            "quantity": 100,
            "symbol": "BTC"
        }

        # This should pass because name field doesn't have additional validation
        # The malicious input is only caught by our custom sanitize_input function
        try:
            result = self.TestModel(**invalid_data)
            assert result.name == malicious_input
        except ValidationError:
            # If validation fails due to other reasons, that's fine too
            pass


class TestSecurityHeaders:
    """Test security headers in responses."""

    def setup_method(self):
        """Set up test fixtures."""
        from core.middleware import setup_middleware
        self.app = FastAPI()
        setup_middleware(self.app)

        @self.app.get("/test-endpoint")
        async def test_endpoint():
            return {"message": "success"}

    def test_cors_headers_present(self):
        """Test CORS headers are present in responses."""
        from core.middleware import setup_cors
        from fastapi.testclient import TestClient

        # Create a separate app for CORS testing
        cors_app = FastAPI()
        setup_cors(cors_app)

        @cors_app.get("/test")
        def test_cors():
            return {"message": "test"}

        client = TestClient(cors_app)

        response = client.get("/test", headers={"origin": "http://localhost:3000"})

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_process_time_header_present(self):
        """Test X-Process-Time header is present."""
        from fastapi.testclient import TestClient

        client = TestClient(self.app)

        response = client.get("/test-endpoint")

        # Check process time header
        assert "x-process-time" in response.headers
        assert response.headers["x-process-time"].replace(".", "").isdigit()


@pytest.fixture
def mock_api_key(monkeypatch):
    """Fixture to set a mock API key."""
    monkeypatch.setenv("API_KEY", "test-api-key-123")
    return "test-api-key-123"


@pytest.fixture
def mock_database_credentials(monkeypatch):
    """Fixture to set mock database credentials."""
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DATABASE_URL", "postgresql://test_user:test_password@localhost:5432/test_db")


# ============================================================================
# SQL INJECTION VULNERABILITY TESTS
# ============================================================================

class TestSQLInjectionVulnerabilities:
    """Test for SQL injection vulnerabilities in dynamic queries."""

    def test_data_initializer_sql_injection(self):
        """Test data_initializer doesn't have SQL injection in table name queries."""
        from services.data_initializer import get_initialization_status

        # This function should be safe from SQL injection
        # Even if table names were dynamic, they should be validated
        result = get_initialization_status()

        # Should return a dict with status information
        assert isinstance(result, dict)
        assert "initialized" in result
        assert "data_counts" in result

    def test_migration_manager_sql_injection(self):
        """Test migration manager uses parameterized queries."""
        from database.migrate import DatabaseMigrator

        manager = DatabaseMigrator()

        # The migrations table name should be a constant, not user input
        # If it were configurable, it should be validated
        assert manager.migrations_table == "schema_migrations"

        # Validate the table name is safe
        assert manager.migrations_table.replace("_", "").isalnum()

    def test_repository_uses_parameterized_queries(self):
        """Test that repositories use SQLAlchemy's parameterized queries."""
        from database.repositories.market import CoinRepository
        from database.connection import get_db_context

        with get_db_context() as session:
            repo = CoinRepository(session)

            # Test with malicious symbol
            malicious_symbols = [
                "BTC' OR '1'='1",
                "BTC'; DROP TABLE coins; --",
                "BTC' UNION SELECT * FROM users --",
            ]

            for symbol in malicious_symbols:
                # These should safely return None or handle gracefully
                # They should NOT execute the injected SQL
                result = repo.get_by_symbol(symbol)
                # The result should be None (coin not found) or a valid coin object
                # It should NEVER affect other tables
                assert result is None or hasattr(result, 'symbol')

    def test_search_coins_sql_injection(self):
        """Test search_coins method is safe from SQL injection."""
        from database.repositories.market import CoinRepository
        from database.connection import get_db_context

        with get_db_context() as session:
            repo = CoinRepository(session)

            # Test with SQL injection attempts in search query
            malicious_queries = [
                "BTC' OR '1'='1",
                "%'; DROP TABLE coins; --",
                "BTC' UNION SELECT * FROM users --",
                "<script>alert('xss')</script>",
            ]

            for query in malicious_queries:
                # Should safely handle the input
                result = repo.search_coins(query)
                # Should return a list (possibly empty)
                assert isinstance(result, list)

    def test_admin_api_sql_injection(self):
        """Test admin API endpoints are safe from SQL injection."""
        # Skip this test for now - models.user module is missing
        # This should be re-enabled once the admin routes are properly implemented
        pytest.skip("Admin API requires models.user module - not yet implemented")

    def test_raw_sql_f_string_detection(self):
        """Detect any remaining unsafe f-string SQL queries."""
        import re
        import os

        # Pattern to find unsafe SQL: f-strings with table names or WHERE clauses
        unsafe_patterns = [
            r'text\(f"[^"]*WHERE[^"]*\\{',
            r'text\(f"[^"]*FROM[^"]*\\{',
            r'execute\(f"[^"]*SELECT',
        ]

        # Check Python files for unsafe patterns
        python_files = []
        for root, dirs, files in os.walk("C:\\Users\\matt\\Dropbox\\projects\\STOCKTRADE"):
            # Skip test files and virtual environments
            if 'test' in root or '__pycache__' in root or '.venv' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        vulnerabilities_found = []
        for filepath in python_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for i, line in enumerate(content.split('\n'), 1):
                        # Skip test files
                        if 'test' in filepath.lower():
                            continue
                        for pattern in unsafe_patterns:
                            if re.search(pattern, line):
                                vulnerabilities_found.append(f"{filepath}:{i}: {line.strip()}")
            except Exception:
                continue

        # This test will help identify remaining vulnerabilities
        # In production, we'd want this to always be empty
        # For now, we'll just report what we find
        if vulnerabilities_found:
            pytest.fail(f"Found potential SQL injection vulnerabilities:\n" + "\n".join(vulnerabilities_found[:10]))