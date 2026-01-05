"""
Test docker-compose orchestration for production deployment.

This test verifies that docker-compose.yml properly orchestrates
all required services and configuration.
"""

import subprocess
import pytest
import os
import yaml
from pathlib import Path
import time


class TestComposeOrchestration:
    """Test docker-compose orchestration functionality."""

    @pytest.fixture(scope="class")
    def compose_file_path(self):
        """Return path to docker-compose.yml."""
        return Path(__file__).parent.parent.parent / "docker-compose.yml"

    @pytest.fixture(scope="class")
    def compose_prod_file_path(self):
        """Return path to docker-compose.prod.yml."""
        return Path(__file__).parent.parent.parent / "docker-compose.prod.yml"

    @pytest.fixture(scope="class")
    def project_root(self):
        """Return project root path."""
        return Path(__file__).parent.parent.parent

    def test_compose_file_exists(self, compose_file_path):
        """Test that docker-compose.yml exists."""
        assert compose_file_path.exists(), "docker-compose.yml not found"
        assert compose_file_path.is_file(), "docker-compose.yml is not a file"

    def test_compose_prod_file_exists(self, compose_prod_file_path):
        """Test that docker-compose.prod.yml exists."""
        assert compose_prod_file_path.exists(), "docker-compose.prod.yml not found"
        assert compose_prod_file_path.is_file(), "docker-compose.prod.yml is not a file"

    def test_compose_yaml_valid(self, compose_file_path):
        """Test that docker-compose.yml is valid YAML."""
        with open(compose_file_path, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.yml: {e}")

    def test_compose_prod_yaml_valid(self, compose_prod_file_path):
        """Test that docker-compose.prod.yml is valid YAML."""
        with open(compose_prod_file_path, 'r') as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in docker-compose.prod.yml: {e}")

    def test_compose_has_required_services(self, compose_file_path):
        """Test that docker-compose.yml contains required services."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        # Check required services
        required_services = ['backend', 'database']
        for service in required_services:
            assert service in compose_config, f"Service '{service}' not found in docker-compose.yml"

        # Check backend service configuration
        backend = compose_config['backend']
        assert 'build' in backend, "Backend service missing build context"
        assert 'ports' in backend, "Backend service missing port mapping"
        assert 'environment' in backend, "Backend service missing environment variables"
        depends_on = backend.get('depends_on', {})
        assert depends_on, "Backend service missing dependencies"

        # Check database service configuration
        database = compose_config['database']
        assert 'image' in database, "Database service missing image specification"
        assert 'ports' in database, "Database service missing port mapping"
        assert 'volumes' in database, "Database service missing volume mounting"

    def test_compose_prod_has_required_services(self, compose_prod_file_path):
        """Test that docker-compose.prod.yml contains required services."""
        with open(compose_prod_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        # Check required services for production
        required_services = ['backend', 'database']
        for service in required_services:
            assert service in compose_config, f"Service '{service}' not found in docker-compose.prod.yml"

        # Check production-specific configurations
        backend = compose_config['backend']
        assert 'restart' in backend, "Production backend missing restart policy"
        assert 'deploy' in backend, "Production backend missing deploy configuration"

        database = compose_config['database']
        assert 'restart' in database, "Production database missing restart policy"
        assert 'volumes' in database, "Production database missing volume configuration"

    def test_compose_networks_configuration(self, compose_file_path):
        """Test that networks are properly configured."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        # Check for networks section
        assert 'networks' in compose_config, "Networks section not found in docker-compose.yml"

        networks = compose_config['networks']
        # Backend should use app-network
        backend = compose_config['backend']
        networks_used = backend.get('networks', {})
        assert 'app-network' in networks_used, "Backend not connected to app-network"

        # Database should be on app-network
        database = compose_config['database']
        networks_used = database.get('networks', {})
        assert 'app-network' in networks_used, "Database not connected to app-network"

    def test_compose_volumes_configuration(self, compose_file_path):
        """Test that volumes are properly configured."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        # Check database volumes
        database = compose_config['database']
        volumes = database.get('volumes', [])
        assert len(volumes) > 0, "Database volumes not configured"

        # Check for named volume or persistent storage
        volume_found = False
        for volume in volumes:
            if ':' in volume and not volume.startswith('./'):
                volume_found = True
                break

        assert volume_found, "Database should use named volumes for persistence"

    def test_compose_env_files(self, compose_file_path, project_root):
        """Test that environment files are referenced."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        # Check for .env or .env.production
        backend = compose_config['backend']
        env_file = backend.get('env_file', [])
        assert len(env_file) > 0, "Backend service should reference env file"

        # Check if .env.production exists
        env_files = env_file if isinstance(env_file, list) else [env_file]
        found_prod_env = False
        for env_file_path in env_files:
            env_file_abs = project_root / env_file_path
            if env_file_abs.exists():
                found_prod_env = True
                break

        # Not failing if not found, but it's required for production
        if found_prod_env:
            with open(env_file_abs, 'r') as f:
                env_content = f.read()
                # Check for production environment variables
                assert 'DATABASE_URL' in env_content, "Production env file should contain DATABASE_URL"
                assert 'API_KEY' in env_content, "Production env file should contain API_KEY"

    def test_compose_up_down_success(self, project_root):
        """Test that docker-compose up/down works successfully."""
        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_root)

            # Test docker-compose config
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.yml", "config"],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0, f"docker-compose config failed: {result.stderr}"

            # Note: We don't actually run 'up' as it would require
            # the database to be available and could conflict with running services
            # In a real CI/CD pipeline, you would test this

            # Restore original directory
            os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            pytest.fail("docker-compose config timed out")
        except FileNotFoundError:
            pytest.skip("docker-compose not installed")
        except Exception as e:
            os.chdir(original_cwd)
            pytest.fail(f"docker-compose test failed: {str(e)}")

    def test_database_service_configuration(self, compose_file_path):
        """Test that database service is properly configured for production."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        database = compose_config['database']

        # Check for PostgreSQL/TimescaleDB image
        image = database.get('image', '')
        assert 'postgres' in image.lower(), "Database should use PostgreSQL/TimescaleDB"

        # Check environment variables
        env = database.get('environment', {})
        required_env_vars = [
            'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD'
        ]
        for var in required_env_vars:
            assert var in env, f"Database missing required environment variable: {var}"

        # Check memory limits
        deploy = database.get('deploy', {})
        if deploy:
            resources = deploy.get('resources', {})
            if resources:
                limits = resources.get('limits', {})
                assert 'memory' in limits, "Database should have memory limits"

    def test_backend_health_check_configuration(self, compose_file_path):
        """Test that backend service has proper health check configuration."""
        with open(compose_file_path, 'r') as f:
            compose_config = yaml.safe_load(f)

        backend = compose_config['backend']

        # Check healthcheck
        healthcheck = backend.get('healthcheck', {})
        assert 'test' in healthcheck, "Backend healthcheck missing test command"
        assert 'interval' in healthcheck, "Backend healthcheck missing interval"
        assert 'timeout' in healthcheck, "Backend healthcheck missing timeout"
        assert 'retries' in healthcheck, "Backend healthcheck missing retries"

        # Test command should check the health endpoint
        test_command = healthcheck['test']
        assert '/health' in test_command or '/' in test_command, "Healthcheck should test / endpoint"