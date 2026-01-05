# Phoenix Conductor MCP Server

Part of the Phoenix multi-agent system for editing existing projects with TDD.

## Purpose

The Phoenix Conductor is the task execution manager that orchestrates TDD builder pairs (TEST_WRITER and CODE_WRITER) to implement code edits while preserving existing functionality through regression testing.

## Tools

### `orchestrate_tdd_edit`
Main tool for executing TDD edit cycles:
- Reads existing files to understand current implementation
- Coordinates TEST_WRITER to create/update tests
- Verifies tests fail before code changes
- Coordinates CODE_WRITER to modify code
- Verifies tests pass after changes
- Runs regression tests to ensure nothing broke

### `read_existing_files`
Read existing code files to understand current implementation before making edits.

### `run_tests`
Run pytest tests and return results.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

The server is designed to be run as an MCP server:

```bash
python server.py
```

Or registered in Claude Code's MCP server configuration.

## Architecture

```
Architect → spawns Conductor with task context
    ↓
Conductor reads existing files
    ↓
Conductor spawns TEST_WRITER (via Task tool)
    ↓
Conductor verifies test fails
    ↓
Conductor spawns CODE_WRITER (via Task tool)
    ↓
Conductor verifies test passes
    ↓
Conductor runs regression tests
    ↓
Conductor reports completion to Architect
```

## State Management

Session state is maintained in `.phoenix/conductors/conductor_N/`:
- `context.md` - Task context from Architect
- `task_execution_log.md` - Step-by-step execution log
- `completion_summary.json` - Results and verification

## Integration

This MCP server is used by the Phoenix Architect command (`/phoenix-architect`) to coordinate TDD workflows.

## See Also

- `PHOENIX_SYSTEM_ARCHITECTURE.md` - Overall system design
- `PHOENIX_AGENT_PROMPTS.md` - Agent prompt specifications
- `.phoenix/` - Runtime directory structure
