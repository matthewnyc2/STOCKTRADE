#!/usr/bin/env python3
"""
GLM 4.7 + GPT Researcher Integration
Token-efficient research using GPT Researcher's web synthesis + GLM 4.7 analysis via z.ai

## Required Environment Variables

1. TAVILY_API_KEY - For GPT Researcher's web search
   - Get your key at: https://tavily.com/
   - Windows (CMD): set TAVILY_API_KEY=tvly-your-key-here
   - Windows (PowerShell): $env:TAVILY_API_KEY="tvly-your-key-here"
   - Linux/Mac: export TAVILY_API_KEY="tvly-your-key-here"
   - For permanent setup, add to your shell profile (.bashrc, .zshrc) or system environment variables

2. GLM_API_KEY - For GLM 4.7 via z.ai (BigModel)
   - Get your key at: https://open.bigmodel.cn/
   - Set same way as TAVILY_API_KEY above
"""
import asyncio
import json
import os
import sys
from openai import AsyncOpenAI
from gpt_researcher import GPTResearcher


def check_api_keys():
    """Validate that required API keys are set."""
    missing = []

    tavily_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_key:
        missing.append("TAVILY_API_KEY")

    glm_key = os.environ.get("GLM_API_KEY")
    if not glm_key:
        missing.append("GLM_API_KEY")

    if missing:
        print("=" * 70)
        print("❌ Missing Required API Keys")
        print("=" * 70)
        print("\nThe following environment variables are not set:")
        for key in missing:
            print(f"  • {key}")
        print("\n📖 Setup Instructions:")
        print("\n1. TAVILY_API_KEY (for web search):")
        print("   - Get key: https://tavily.com/")
        print("   - Windows CMD: set TAVILY_API_KEY=tvly-your-key-here")
        print("   - PowerShell: $env:TAVILY_API_KEY='tvly-your-key-here'")
        print("   - Linux/Mac: export TAVILY_API_KEY='tvly-your-key-here'")
        print("\n2. GLM_API_KEY (for AI analysis):")
        print("   - Get key: https://open.bigmodel.cn/")
        print("   - Set same way as TAVILY_API_KEY above")
        print("\n💡 For permanent setup, add to your shell profile (.bashrc, .zshrc)")
        print("   or set as system environment variables.")
        print("=" * 70)
        sys.exit(1)

    return glm_key


# Validate API keys on import
GLM_API_KEY = check_api_keys()

# Initialize GLM client (z.ai uses OpenAI-compatible API)
client = AsyncOpenAI(
    api_key=GLM_API_KEY,
    base_url="https://open.bigmodel.cn/api/paas/v4/"  # z.ai/GLM endpoint
)


async def perform_research(query: str, report_type: str = "research_report") -> str:
    """
    Execute GPT Researcher and return synthesized report.

    Args:
        query: The research question/topic
        report_type: Type of report (research_report, subtopic_report, etc.)

    Returns:
        Synthesized research report text
    """
    print(f"\n🔎 Starting research on: {query}...")

    try:
        researcher = GPTResearcher(query=query, report_type=report_type)
        await researcher.conduct_research()
        report = await researcher.write_report()

        print(f"✅ Research complete. Report length: {len(report)} characters.")
        return report

    except Exception as e:
        error_msg = f"❌ Research failed: {str(e)}"
        print(error_msg)
        return error_msg


# Tool schema for GLM's function calling
TOOLS = [
    {
        "name": "deep_research",
        "description": "Conducts deep, autonomous web research on a specific topic and generates a comprehensive report. Use this when the user asks for detailed information that requires browsing multiple sources, current events, or factual verification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The specific research topic or question to investigate."
                }
            },
            "required": ["query"]
        }
    }
]


async def run_research_session(user_query: str):
    """
    Main research session: GLM 4.7 determines if research is needed,
    executes it, and provides analysis.
    """
    print(f"💬 User: {user_query}\n")

    messages = [{"role": "user", "content": user_query}]

    # First call - let GLM decide if research is needed
    response = await client.chat.completions.create(
        model="glm-4-plus",  # or "glm-4.7" depending on z.ai model naming
        messages=messages,
        tools=TOOLS,
        temperature=0.7
    )

    # Check if GLM wants to use the research tool
    message = response.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_inputs = json.loads(tool_call.function.arguments)  # Parse JSON args

        print(f"🤖 GLM invoking tool: {tool_name}")

        # Execute research
        if tool_name == "deep_research":
            research_result = await perform_research(tool_inputs["query"])

            # Feed result back to GLM for analysis
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": message.tool_calls
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": research_result
            })

            # Get GLM's analysis
            final_response = await client.chat.completions.create(
                model="glm-4-plus",
                messages=messages,
                tools=TOOLS,
                temperature=0.7
            )

            print("\n" + "="*60)
            print("🤖 GLM Analysis:\n")
            print(final_response.choices[0].message.content)
            print("="*60)

    else:
        # No research needed, direct response
        print(message.content)


def main():
    """CLI entry point"""
    if len(sys.argv) > 1:
        # Query passed as command line argument
        query = " ".join(sys.argv[1:])
    else:
        # Interactive prompt
        query = input("Enter your research question: ")

    asyncio.run(run_research_session(query))


if __name__ == "__main__":
    main()
