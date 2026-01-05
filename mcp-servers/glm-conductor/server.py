#!/usr/bin/env python3
"""
GLM 4.7 Max MCP Server for PROMETHEUS Conductors
Provides conductor orchestration via Z.ai API
"""

import asyncio
import json
import os
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx

app = Server("glm-conductor")

ZAI_API_KEY = os.getenv("ZAI_API_KEY")
if not ZAI_API_KEY:
    raise ValueError("ZAI_API_KEY environment variable required")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available GLM conductor tools"""
    return [
        Tool(
            name="glm_conduct_task",
            description="Execute a task using GLM 4.7 Max conductor. Best for long-running orchestration of test specification and builder monitoring.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_specification": {
                        "type": "string",
                        "description": "Full task specification with context, acceptance criteria, and scope"
                    },
                    "context": {
                        "type": "string",
                        "description": "Project context (WHY this matters)"
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "System prompt for conductor role"
                    },
                    "max_tokens": {
                        "type": "number",
                        "description": "Maximum tokens for response",
                        "default": 8192
                    }
                },
                "required": ["task_specification", "context", "system_prompt"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Execute GLM tool"""

    if name == "glm_conduct_task":
        task_spec = arguments["task_specification"]
        context = arguments["context"]
        system_prompt = arguments["system_prompt"]
        max_tokens = arguments.get("max_tokens", 8192)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.z.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {ZAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4.7-max",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context:\n{context}\n\nTask:\n{task_spec}"}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                return [TextContent(
                    type="text",
                    text=f"Error: GLM API returned {response.status_code}: {response.text}"
                )]

            result = response.json()
            conductor_response = result["choices"][0]["message"]["content"]

            return [TextContent(
                type="text",
                text=conductor_response
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
