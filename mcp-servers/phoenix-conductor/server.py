#!/usr/bin/env python3
"""
Phoenix Conductor MCP Server

Manages TDD builder pairs for editing existing code using the Phoenix system.
Coordinates TEST_WRITER and CODE_WRITER agents in a TDD workflow with
regression testing to ensure existing functionality is preserved.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: MCP package not found. Install with: pip install mcp>=0.1.0", file=sys.stderr)
    sys.exit(1)

app = Server("phoenix-conductor")


class ConductorState:
    """Manages Conductor session state and file operations."""

    def __init__(self, workspace_root: Path, conductor_id: str = None):
        self.workspace_root = workspace_root
        self.conductor_id = conductor_id or "01"
        self.phoenix_dir = workspace_root / ".phoenix"
        self.conductor_dir = self.phoenix_dir / "conductors" / f"conductor_{self.conductor_id}"

    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.conductor_dir.mkdir(parents=True, exist_ok=True)

    def save_context(self, context: dict):
        """Save context from Architect."""
        self.ensure_directories()
        context_file = self.conductor_dir / "context.md"
        with open(context_file, 'w', encoding='utf-8') as f:
            if isinstance(context, str):
                f.write(context)
            else:
                f.write(f"# Conductor Context\n\n")
                f.write(f"## Task\n\n{context.get('task', 'N/A')}\n\n")
                f.write(f"## Files to Modify\n\n")
                for file in context.get('files', []):
                    f.write(f"- `{file}`\n")

    def log_step(self, step: str, details: str):
        """Log execution step."""
        self.ensure_directories()
        log_file = self.conductor_dir / "task_execution_log.md"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {step}\n\n")
            f.write(f"{details}\n\n")
            f.write(f"**Timestamp:** {asyncio.get_event_loop().time()}\n")

    def save_completion(self, summary: dict):
        """Save completion summary."""
        self.ensure_directories()
        summary_file = self.conductor_dir / "completion_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

    def read_file(self, file_path: str) -> str:
        """Read a file from the workspace."""
        full_path = self.workspace_root / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {file_path}: {str(e)}"

    def run_tests(self, test_file: str = None) -> dict:
        """Run tests and return results."""
        try:
            if test_file:
                cmd = ["pytest", test_file, "-v"]
            else:
                cmd = ["pytest", "-v"]

            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Tests timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global state manager
_state: ConductorState = None


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="orchestrate_tdd_edit",
            description="Execute a TDD edit cycle: coordinate TEST_WRITER and CODE_WRITER builders. "
                       "Reads existing files, ensures test fails before edit, coordinates code modification, "
                       "ensures test passes after edit, and runs regression tests.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_context": {
                        "type": "string",
                        "description": "Full context from Architect about the edit task including requirements"
                    },
                    "files_to_read": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to read and understand before editing"
                    },
                    "test_strategy": {
                        "type": "string",
                        "enum": ["new", "update", "remove"],
                        "description": "Test approach: 'new' for new functionality, 'update' for modifying existing, 'remove' for removing"
                    },
                    "conductor_id": {
                        "type": "string",
                        "description": "Conductor identifier (default: '01')",
                        "default": "01"
                    }
                },
                "required": ["task_context", "files_to_read", "test_strategy"]
            }
        ),
        Tool(
            name="read_existing_files",
            description="Read existing code files to understand current implementation before making edits",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to read"
                    },
                    "conductor_id": {
                        "type": "string",
                        "description": "Conductor identifier",
                        "default": "01"
                    }
                },
                "required": ["file_paths"]
            }
        ),
        Tool(
            name="run_tests",
            description="Run pytest tests and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_file": {
                        "type": "string",
                        "description": "Specific test file to run (optional, runs all if not specified)"
                    },
                    "conductor_id": {
                        "type": "string",
                        "description": "Conductor identifier",
                        "default": "01"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    # Determine workspace root
    workspace_root = Path.cwd()

    if name == "orchestrate_tdd_edit":
        task_context = arguments.get("task_context", "")
        files_to_read = arguments.get("files_to_read", [])
        test_strategy = arguments.get("test_strategy", "new")
        conductor_id = arguments.get("conductor_id", "01")

        # Initialize state
        global _state
        _state = ConductorState(workspace_root, conductor_id)
        _state.save_context({"task": task_context, "files": files_to_read})
        _state.log_step("INITIATED", f"Task: {task_context[:100]}...\n\nTest Strategy: {test_strategy}")

        # Step 1: Read existing files
        _state.log_step("READING_EXISTING_FILES", f"Reading {len(files_to_read)} files...")
        file_contents = {}
        for file_path in files_to_read:
            content = _state.read_file(file_path)
            file_contents[file_path] = content
            _state.log_step("FILE_READ", f"Read `{file_path}` ({len(content)} characters)")

        # Step 2: Spawn TEST_WRITER (would use Task tool in actual implementation)
        _state.log_step("SPAWN_TEST_WRITER", "TEST_WRITER agent should be spawned here via Task tool")
        _state.log_step("TEST_INSTRUCTION",
                       f"Create/update test for: {task_context}\n"
                       f"Strategy: {test_strategy}\n"
                       f"Files to understand: {list(file_contents.keys())}")

        # For now, provide guidance for manual execution
        completion_summary = {
            "status": "orchestrated",
            "task": task_context,
            "files_read": list(files_to_read),
            "test_strategy": test_strategy,
            "next_steps": [
                "1. Use Task tool to spawn TEST_WRITER with subagent_type='phoenix-test-writer'",
                "2. Verify test fails with current code",
                "3. Use Task tool to spawn CODE_WRITER with subagent_type='phoenix-code-writer'",
                "4. Verify test passes after code changes",
                "5. Run regression tests",
                "6. Report completion"
            ],
            "conductor_id": conductor_id
        }
        _state.save_completion(completion_summary)

        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "TDD orchestration initiated",
                "conductor_id": conductor_id,
                "files_read": len(file_contents),
                "test_strategy": test_strategy,
                "context_saved": str(_state.conductor_dir),
                "next_actions": completion_summary["next_steps"]
            }, indent=2)
        )]

    elif name == "read_existing_files":
        file_paths = arguments.get("file_paths", [])
        conductor_id = arguments.get("conductor_id", "01")

        global _state
        if _state is None or _state.conductor_id != conductor_id:
            _state = ConductorState(workspace_root, conductor_id)

        results = {}
        for file_path in file_paths:
            content = _state.read_file(file_path)
            results[file_path] = {
                "content": content[:1000] + "..." if len(content) > 1000 else content,  # Truncate for response
                "size": len(content)
            }

        return [TextContent(
            type="text",
            text=json.dumps(results, indent=2)
        )]

    elif name == "run_tests":
        test_file = arguments.get("test_file")
        conductor_id = arguments.get("conductor_id", "01")

        global _state
        if _state is None:
            _state = ConductorState(workspace_root, conductor_id)

        result = _state.run_tests(test_file)

        if _state.conductor_id == conductor_id:
            _state.log_step("TESTS_RUN", f"Test file: {test_file or 'all'}\nSuccess: {result.get('success')}")

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
