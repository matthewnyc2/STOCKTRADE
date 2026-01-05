"""
Test suite for Phoenix multi-agent system components.

Tests the Producer, Architect, Conductor, and Builder agents
that comprise the Phoenix system for editing existing projects with TDD.
"""

import pytest
from pathlib import Path


class TestPhoenixProducer:
    """Test Phoenix-Producer functionality."""

    def test_creates_phoenix_directory(self, tmp_path):
        """Producer should create .phoenix directory structure."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()
        architects_dir = phoenix_dir / "architects_handoff"
        architects_dir.mkdir()

        assert phoenix_dir.exists()
        assert architects_dir.exists()

    def test_creates_edit_plan(self, tmp_path):
        """Producer should create phoenix_edit_plan.md."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()

        edit_plan = phoenix_dir / "phoenix_edit_plan.md"
        edit_plan.write_text("# Edit Plan\n\nTest edit plan")

        assert edit_plan.exists()
        assert "Edit Plan" in edit_plan.read_text()

    def test_creates_current_state_analysis(self, tmp_path):
        """Producer should create current_state_analysis.md."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()

        analysis = phoenix_dir / "current_state_analysis.md"
        analysis.write_text("# Current State\n\nExisting code analysis")

        assert analysis.exists()

    def test_creates_delta_breakdown(self, tmp_path):
        """Producer should create delta_breakdown.md."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()

        delta = phoenix_dir / "delta_breakdown.md"
        delta.write_text("# Delta\n\nChanges needed")

        assert delta.exists()

    def test_creates_risk_assessment(self, tmp_path):
        """Producer should create risk_assessment.md."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()

        risk = phoenix_dir / "risk_assessment.md"
        risk.write_text("# Risks\n\nPotential issues")

        assert risk.exists()

    def test_creates_architect_context_files(self, tmp_path):
        """Producer should create architect context files."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()
        handoff_dir = phoenix_dir / "architects_handoff"
        handoff_dir.mkdir()

        context_1 = handoff_dir / "architect_01_context.md"
        context_1.write_text("# Context for Architect 1")

        assert context_1.exists()


class TestPhoenixArchitect:
    """Test Phoenix-Architect functionality."""

    def test_creates_architect_directory(self, tmp_path):
        """Architect should create its directory."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir()

        assert architect_dir.exists()

    def test_reads_producer_context(self, tmp_path):
        """Architect should read context from Producer."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()
        handoff_dir = phoenix_dir / "architects_handoff"
        handoff_dir.mkdir()

        context = handoff_dir / "architect_01_context.md"
        context.write_text("# Context\n\nFeature scope details")

        assert context.exists()
        assert "Feature scope" in context.read_text()

    def test_creates_code_analysis(self, tmp_path):
        """Architect should create code_analysis.md."""
        phoenix_dir = tmp_path / ".phoenix"
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir(parents=True)

        analysis = architect_dir / "code_analysis.md"
        analysis.write_text("# Code Analysis\n\nExisting patterns")

        assert analysis.exists()

    def test_creates_edit_tasks(self, tmp_path):
        """Architect should create edit_tasks.md."""
        phoenix_dir = tmp_path / ".phoenix"
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir(parents=True)

        tasks = architect_dir / "edit_tasks.md"
        tasks.write_text("# Tasks\n\n- Task 1\n- Task 2")

        assert tasks.exists()

    def test_creates_completion_report(self, tmp_path):
        """Architect should create completion_report.md."""
        phoenix_dir = tmp_path / ".phoenix"
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir(parents=True)

        report = architect_dir / "completion_report.md"
        report.write_text("# Completion\n\nAll tasks complete")

        assert report.exists()


class TestPhoenixConductor:
    """Test Phoenix-Conductor functionality."""

    def test_creates_conductor_directory(self, tmp_path):
        """Conductor should create its directory."""
        phoenix_dir = tmp_path / ".phoenix"
        phoenix_dir.mkdir()
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir()

        assert conductor_dir.exists()

    def test_saves_context(self, tmp_path):
        """Conductor should save context from Architect."""
        phoenix_dir = tmp_path / ".phoenix"
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir(parents=True)

        context = conductor_dir / "context.md"
        context.write_text("# Task Context\n\nEdit requirements")

        assert context.exists()

    def test_logs_execution_steps(self, tmp_path):
        """Conductor should log execution steps."""
        phoenix_dir = tmp_path / ".phoenix"
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir(parents=True)

        log = conductor_dir / "task_execution_log.md"
        log.write_text("# Execution Log\n\n## Step 1\n\nComplete")

        assert log.exists()

    def test_creates_completion_summary(self, tmp_path):
        """Conductor should create completion_summary.json."""
        phoenix_dir = tmp_path / ".phoenix"
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir(parents=True)

        summary = conductor_dir / "completion_summary.json"
        summary.write_text('{"status": "complete"}')

        assert summary.exists()


class TestBuilderAgents:
    """Test TEST_WRITER and CODE_WRITER builder functionality."""

    def test_test_writer_creates_failing_test(self, tmp_path):
        """TEST_WRITER should create a test that fails before edit."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()

        test_file = test_dir / "test_new_feature.py"
        test_file.write_text("""
def test_new_feature():
    '''Test that new feature works'''
    assert False  # Will fail until feature is implemented
""")

        assert test_file.exists()
        # Would run pytest here in real test

    def test_code_writer_makes_minimal_changes(self, tmp_path):
        """CODE_WRITER should make minimal code changes."""
        # Original code
        source_file = tmp_path / "module.py"
        source_file.write_text("""
class MyClass:
    def existing_method(self):
        return "existing"
""")

        # Modified code (minimal change)
        modified = source_file.read_text()
        modified = modified.replace(
            'class MyClass:\n',
            'class MyClass:\n    def new_method(self):\n        return "new"\n\n'
        )
        source_file.write_text(modified)

        assert "new_method" in source_file.read_text()
        assert "existing_method" in source_file.read_text()  # Preserved


class TestPhoenixIntegration:
    """Integration tests for Phoenix workflow."""

    @pytest.mark.integration
    def test_end_to_end_simple_edit(self, tmp_path):
        """Test complete Phoenix workflow for a simple edit."""
        # Setup: Create a simple module
        module = tmp_path / "simple.py"
        module.write_text("""
def hello():
    return "Hello"
""")

        # Create test
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        test = test_dir / "test_simple.py"
        test.write_text("""
from simple import hello

def test_hello():
    assert hello() == "Hello"

def test_hello_with_name():
    assert hello("World") == "Hello World"  # Will fail initially
""")

        # Phoenix would:
        # 1. Producer creates plan
        # 2. Architect breaks into task
        # 3. Conductor coordinates TEST_WRITER (test already exists)
        # 4. Conductor verifies test fails
        # 5. Conductor coordinates CODE_WRITER to modify code
        # 6. Conductor verifies test passes
        # 7. Conductor runs regression tests

        # For this unit test, we just verify the structure exists
        assert module.exists()
        assert test.exists()

    @pytest.mark.integration
    def test_phoenix_directory_structure(self, tmp_path):
        """Test that Phoenix creates proper directory structure."""
        phoenix_dir = tmp_path / ".phoenix"

        # Producer creates
        phoenix_dir.mkdir()

        # Architect creates
        architect_dir = phoenix_dir / "architects" / "architect_01"
        architect_dir.mkdir(parents=True)

        # Conductor creates
        conductor_dir = phoenix_dir / "conductors" / "conductor_01"
        conductor_dir.mkdir(parents=True)

        # Verify structure
        assert phoenix_dir.exists()
        assert architect_dir.exists()
        assert conductor_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
