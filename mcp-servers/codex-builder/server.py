#!/usr/bin/env python3
"""
Codex Cloud MCP Server for PROMETHEUS Builders
Provides code generation via OpenAI Codex API
"""

import asyncio
import json
import os
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx

app = Server("codex-builder")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Codex builder tools"""
    return [
        Tool(
            name="codex_implement_test",
            description="Implement code to pass a single test using OpenAI Codex. Optimized for minimal, focused code generation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "test_code": {
                        "type": "string",
                        "description": "The test code that must pass"
                    },
                    "test_context": {
                        "type": "string",
                        "description": "Context explaining WHY this test matters"
                    },
                    "allowed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files the builder may modify"
                    },
                    "expected_behavior": {
                        "type": "string",
                        "description": "Description of expected behavior"
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (python, javascript, typescript, etc.)",
                        "default": "python"
                    },
                    "max_tokens": {
                        "type": "number",
                        "description": "Maximum tokens for response",
                        "default": 4096
                    }
                },
                "required": ["test_code", "test_context", "allowed_files", "expected_behavior"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute Codex tool"""

    if name == "codex_implement_test":
        test_code = arguments["test_code"]
        test_context = arguments["test_context"]
        allowed_files = arguments["allowed_files"]
        expected_behavior = arguments["expected_behavior"]
        language = arguments.get("language", "python")
        max_tokens = arguments.get("max_tokens", 4096)

        # Build prompt for Codex
        prompt = f"""You are a Builder in the PROMETHEUS system. Write MINIMAL code to pass this test.

Context (WHY): {test_context}

Allowed Files: {', '.join(allowed_files)}

Expected Behavior: {expected_behavior}

Test to Pass:
```{language}
{test_code}
```

Instructions:
- Write ONLY the code needed to pass this test
- No extra features
- No future-proofing
- Simple, clear, minimal

Provide your response in this JSON format:
{{
  "status": "complete" | "blocked",
  "files_changed": ["path/to/file.ext"],
  "code_changes": {{
    "path/to/file.ext": "code content here"
  }},
  "explanation": "Brief explanation of changes",
  "question": null | "question if blocked"
}}
"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",  # Use gpt-4 or specific Codex model if available
                    "messages": [
                        {"role": "system", "content": "You are a code generator that produces minimal code to pass tests."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.3,  # Lower temperature for more focused code
                    "response_format": {"type": "json_object"}
                }
            )

            if response.status_code != 200:
                return [TextContent(
                    type="text",
                    text=f"Error: OpenAI API returned {response.status_code}: {response.text}"
                )]

            result = response.json()
            builder_response = result["choices"][0]["message"]["content"]

            return [TextContent(
                type="text",
                text=builder_response
            )]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
