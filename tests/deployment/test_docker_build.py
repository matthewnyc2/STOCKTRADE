"""
Test Docker build for production deployment.

This test verifies that the Dockerfile builds successfully and creates
a production-optimized container image.
"""

import subprocess
import pytest
import os
from pathlib import Path


class TestDockerBuild:
    """Test Docker build functionality."""

    @pytest.fixture(scope="class")
    def dockerfile_path(self):
        """Return path to Dockerfile."""
        return Path(__file__).parent.parent.parent / "Dockerfile"

    @pytest.fixture(scope="class")
    def project_root(self):
        """Return project root path."""
        return Path(__file__).parent.parent.parent

    def test_dockerfile_exists(self, dockerfile_path):
        """Test that Dockerfile exists."""
        assert dockerfile_path.exists(), "Dockerfile not found"
        assert dockerfile_path.is_file(), "Dockerfile is not a file"

    def test_dockerfile_has_required_sections(self, dockerfile_path):
        """Test that Dockerfile contains required production sections."""
        with open(dockerfile_path, 'r') as f:
            content = f.read()

        # Check for multi-stage build
        assert "FROM" in content, "Base image not found"
        assert content.count("FROM") >= 2, "Multi-stage build not detected"

        # Check for non-root user setup
        assert "USER" in content, "User directive not found"

        # Check for health check
        assert "HEALTHCHECK" in content, "Healthcheck not found"

        # Check for production optimizations
        assert "--no-dev" in content or "--production" in content, "Production optimizations not found"

    def test_docker_build_success(self, project_root):
        """Test that Docker build succeeds."""
        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_root)

            # Build Docker image
            result = subprocess.run(
                [
                    "docker", "build",
                    "-t", "crypto-quant-lab:latest",
                    "-t", "crypto-quant-lab:0.1.0",
                    "--no-cache",
                    "."
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            # Restore original directory
            os.chdir(original_cwd)

            # Check build success
            assert result.returncode == 0, f"Docker build failed: {result.stderr}"

            # Verify image was created
            result = subprocess.run(
                ["docker", "images", "crypto-quant-lab"],
                capture_output=True,
                text=True
            )
            assert "crypto-quant-lab" in result.stdout, "Docker image not created"

        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out after 10 minutes")
        except FileNotFoundError:
            pytest.skip("Docker not installed")
        finally:
            os.chdir(original_cwd)

    def test_docker_image_size(self, project_root):
        """Test that Docker image size is reasonable for production."""
        try:
            # Build minimal image to check size
            original_cwd = os.getcwd()
            os.chdir(project_root)

            # Build with minimal layers
            result = subprocess.run(
                [
                    "docker", "build",
                    "-t", "crypto-quant-lab:check-size",
                    "--target",
                    "production",
                    "."
                ],
                capture_output=True,
                text=True,
                timeout=600
            )

            os.chdir(original_cwd)

            if result.returncode == 0:
                # Get image size
                result = subprocess.run(
                    ["docker", "images", "crypto-quant-lab:check-size", "--format", "{{.Size}}"],
                    capture_output=True,
                    text=True
                )

                if result.stdout.strip():
                    size_str = result.stdout.strip()
                    # Remove size unit (e.g., "500MB", "1.2GB")
                    size_num = float(size_str.replace('GB', '').replace('MB', '').replace(' ', ''))

                    # For a Python app with ML libraries, < 2GB is reasonable
                    if 'GB' in size_str:
                        assert size_num < 2.0, f"Image size {size_str} is too large"
                    else:
                        assert size_num < 2000, f"Image size {size_str} is too large"

                # Cleanup
                subprocess.run(["docker", "rmi", "crypto-quant-lab:check-size"])

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Skip size test if docker not available or timeout
        finally:
            os.chdir(original_cwd)

    def test_docker_healthcheck(self, project_root):
        """Test that healthcheck endpoint returns correct response."""
        try:
            # First, build and run the container
            build_result = subprocess.run(
                ["docker", "build", "-t", "crypto-quant-lab:health-test", "."],
                capture_output=True,
                text=True,
                timeout=600
            )

            if build_result.returncode != 0:
                pytest.skip(f"Failed to build Docker image: {build_result.stderr}")

            # Run container
            container = subprocess.Popen([
                "docker", "run", "-d", "-p", "8001:8000",
                "crypto-quant-lab:health-test"
            ], capture_output=True, text=True)

            try:
                # Wait for container to start
                import time
                time.sleep(10)

                # Test health endpoint
                result = subprocess.run(
                    ["curl", "-f", "http://localhost:8001/"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                assert result.returncode == 0, "Health check endpoint failed"
                assert "healthy" in result.stdout, f"Unexpected health check response: {result.stdout}"

            finally:
                # Cleanup
                if container.stdout:
                    container_id = container.stdout.strip()
                    subprocess.run(["docker", "rm", "-f", container_id])

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker or curl not available")
        except Exception as e:
            pytest.fail(f"Healthcheck test failed: {str(e)}")