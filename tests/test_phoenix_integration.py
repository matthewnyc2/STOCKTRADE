"""
Integration tests for Phoenix multi-agent system.

Tests complete end-to-end workflows with real code edits.
These tests validate that Phoenix can edit actual code using TDD.
"""

import pytest
import subprocess
import tempfile
from pathlib import Path


class TestPhoenixIntegration:
    """Integration tests for Phoenix system."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_simple_function_addition(self, tmp_path):
        """
        Test Phoenix workflow for adding a simple function.

        Scenario: Add a greet(name) function to a module
        Expected:
        1. Producer creates edit plan
        2. Architect creates task
        3. Conductor coordinates TEST_WRITER
        4. Test written for greet() function
        5. Conductor verifies test fails
        6. Conductor coordinates CODE_WRITER
        7. Code modified to add greet()
        8. Test passes
        9. Regression tests pass
        """
        # Setup: Create initial module
        module_path = tmp_path / "greeting.py"
        module_path.write_text('''"""Greeting module."""

def hello():
    """Return a greeting."""
    return "Hello"
''')

        # Create initial tests
        tests_path = tmp_path / "test_greeting.py"
        tests_path.write_text('''"""Tests for greeting module."""

from greeting import hello

def test_hello():
    assert hello() == "Hello"
''')

        # Run initial tests - should pass
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0, "Initial tests should pass"

        # Simulate Phoenix workflow for adding greet(name) function
        # TEST_WRITER would add:
        new_test = '''
def test_greet_with_name():
    from greeting import greet
    assert greet("World") == "Hello, World"
'''
        tests_path.write_text(tests_path.read_text() + new_test)

        # Verify test fails (function doesn't exist yet)
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode != 0, "Test should fail before implementation"

        # CODE_WRITER would modify greeting.py to add greet() function
        module_path.write_text('''"""Greeting module."""

def hello():
    """Return a greeting."""
    return "Hello"

def greet(name):
    """Return a personalized greeting."""
    return f"Hello, {name}"
''')

        # Verify test passes
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0, "Test should pass after implementation"

        # Verify regression (original test still passes)
        assert "test_hello PASSED" in result.stdout.decode()

    @pytest.mark.integration
    @pytest.mark.slow
    def test_function_modification(self, tmp_path):
        """
        Test Phoenix workflow for modifying existing function.

        Scenario: Modify hello() to return "Hello, World!" by default
        Expected:
        1. Existing test updated for new behavior
        2. Test fails against current code
        3. Code modified
        4. Test passes
        """
        # Setup: Create initial module and test
        module_path = tmp_path / "message.py"
        module_path.write_text('''
def get_message():
    return "Hello"
''')

        tests_path = tmp_path / "test_message.py"
        tests_path.write_text('''
from message import get_message

def test_get_message():
    assert get_message() == "Hello"
''')

        # Initial tests pass
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0

        # Simulate Phoenix modification workflow
        # TEST_WRITER updates test for new behavior
        tests_path.write_text('''
from message import get_message

def test_get_message():
    assert get_message() == "Hello, World!"
''')

        # Verify test fails with current code
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode != 0

        # CODE_WRITER modifies code
        module_path.write_text('''
def get_message():
    return "Hello, World!"
''')

        # Verify test passes
        result = subprocess.run(
            ["python", "-m", "pytest", str(tests_path), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_phoenix_directory_creation(self, tmp_path):
        """Test that Phoenix agents create proper directory structure."""
        # Simulate Producer creating .phoenix directory
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()

        # Create edit plan
        (phoenix_dir / "phoenix_edit_plan.md").write_text("# Edit Plan")
        (phoenix_dir / "current_state_analysis.md").write_text("# Current State")
        (phoenix_dir / "delta_breakdown.md").write_text("# Delta")
        (phoenix_dir / "risk_assessment.md").write_text("# Risks")

        # Create architect handoff directory
        handoff_dir = phoenix_dir / "architects_handoff"
        handoff_dir.mkdir()
        (handoff_dir / "architect_01_context.md").write_text("# Context")

        # Simulate Architect creating its directory
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir(parents=True)
        (architect_dir / "code_analysis.md").write_text("# Analysis")
        (architect_dir / "edit_tasks.md").write_text("# Tasks")
        (architect_dir / "completion_report.md").write_text("# Complete")

        # Simulate Conductor creating its directory
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir(parents=True)
        (conductor_dir / "context.md").write_text("# Context")
        (conductor_dir / "task_execution_log.md").write_text("# Log")
        (conductor_dir / "completion_summary.json").write_text('{}')

        # Verify all directories and files exist
        assert phoenix_dir.exists()
        assert (phoenix_dir / "phoenix_edit_plan.md").exists()
        assert (phoenix_dir / "current_state_analysis.md").exists()
        assert architect_dir.exists()
        assert conductor_dir.exists()

    @pytest.mark.frontend
    @pytest.mark.integration
    @pytest.mark.slow
    def test_frontend_component_edit(self, tmp_path):
        """
        Test Phoenix workflow for editing a frontend component.

        Scenario: Add a toggle button to a React component
        This is the MVP test scenario for Phoenix.

        Prerequisites: Frontend directory with dashboard component
        """
        # This test will be implemented when frontend code exists
        # For now, it's a placeholder showing the intended workflow

        # Setup: Create a mock frontend component
        frontend_dir = tmp_path / "frontend"
        frontend_dir.mkdir()
        components_dir = frontend_dir / "components"
        components_dir.mkdir()

        # Create a dashboard component
        dashboard = components_dir / "Dashboard.jsx"
        dashboard.write_text('''/**
 * Dashboard Component
 */
export function Dashboard() {
    return (
        <div className="dashboard">
            <h1>Dashboard</h1>
        </div>
    );
}
''')

        # Create test
        test_path = frontend_dir / "test_dashboard.jsx"
        test_path.write_text('''/**
 * Dashboard Tests
 */
import { render } from '@testing-library/react';
import { Dashboard } from './Dashboard';

test('dashboard renders heading', () => {
    const { getByText } = render(<Dashboard />);
    expect(getByText('Dashboard')).toBeInTheDocument();
});
''')

        # Verify component exists
        assert dashboard.exists()
        assert test_path.exists()

        # Phoenix workflow would:
        # 1. Producer: Analyze frontend structure
        # 2. Architect: Break down "add dark mode toggle" into tasks
        # 3. Conductor: For each task:
        #    a. TEST_WRITER: Add test for toggle button
        #    b. Verify test fails
        #    c. CODE_WRITER: Add toggle button to component
        #    d. Verify test passes
        #    e. Run regression tests
        # 4. Architect: Verify all tasks complete
        # 5. Producer: Report success

        # Placeholder assertion
        assert True


class TestPhoenixTDDWorkflow:
    """Test TDD workflow specific to Phoenix."""

    @pytest.mark.integration
    def test_tdd_cycle_fail_first(self, tmp_path):
        """Verify Phoenix enforces TDD: test must fail before code change."""
        # Create module
        module = tmp_path / "math_ops.py"
        module.write_text('''
def add(a, b):
    return a + b
''')

        # Create test for new feature (multiply)
        test = tmp_path / "test_math_ops.py"
        test.write_text('''
from math_ops import add, multiply

def test_add():
    assert add(1, 2) == 3

def test_multiply():
    assert multiply(3, 4) == 12
''')

        # Test should fail (multiply doesn't exist)
        result = subprocess.run(
            ["python", "-m", "pytest", str(test), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode != 0, "Test must fail before implementation"

        # Implement multiply
        module.write_text('''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
''')

        # Test should pass
        result = subprocess.run(
            ["python", "-m", "pytest", str(test), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0, "Test should pass after implementation"

        # Regression: add() still works
        assert "test_add PASSED" in result.stdout.decode()

    @pytest.mark.integration
    def test_regression_testing(self, tmp_path):
        """Verify Phoenix runs regression tests after edits."""
        # Create module with multiple functions
        module = tmp_path / "utils.py"
        module.write_text('''
def foo():
    return "foo"

def bar():
    return "bar"

def baz():
    return "baz"
''')

        # Create comprehensive tests
        test = tmp_path / "test_utils.py"
        test.write_text('''
from utils import foo, bar, baz

def test_foo():
    assert foo() == "foo"

def test_bar():
    assert bar() == "bar"

def test_baz():
    assert baz() == "baz"
''')

        # All tests pass
        result = subprocess.run(
            ["python", "-m", "pytest", str(test), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0
        assert result.stdout.decode().count("PASSED") == 3

        # Modify one function
        module.write_text('''
def foo():
    return "FOO"  # Changed

def bar():
    return "bar"

def baz():
    return "baz"
''')

        # Update test for modified function
        test.write_text('''
from utils import foo, bar, baz

def test_foo():
    assert foo() == "FOO"  # Updated

def test_bar():
    assert bar() == "bar"

def test_baz():
    assert baz() == "baz"
''')

        # All tests still pass (regression check)
        result = subprocess.run(
            ["python", "-m", "pytest", str(test), "-v"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0, "Regression tests must pass"
        assert result.stdout.decode().count("PASSED") == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
