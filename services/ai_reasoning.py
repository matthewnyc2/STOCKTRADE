"""
AI Reasoning Service for GLM-4.7 Integration.

Provides market analysis, signal reasoning, and risk assessment with
preserved thinking using GLM-4.7's chain-of-thought capabilities.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

import httpx

from database.connection import get_db_session
from database.repositories import AIReasoningSessionRepository


logger = logging.getLogger(__name__)


class AIReasoningEngine:
    """
    AI Reasoning Engine with GLM-4.7 integration.

    Provides streaming analysis with preserved thinking for:
    - Market analysis
    - Signal reasoning
    - Risk assessment
    """

    # GLM-4.7 API Configuration
    API_BASE = "https://open.bigmodel.cn/api/paas/v4"
    CHAT_ENDPOINT = f"{API_BASE}/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Reasoning Engine.

        Args:
            api_key: GLM API key (defaults to GLM_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        if not self.api_key:
            logger.warning("GLM_API_KEY not set - AI reasoning will be mocked")

        self.client = httpx.AsyncClient(
            base_url=self.API_BASE,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _make_request(
        self,
        messages: List[Dict[str, Any]],
        model: str = "glm-4.7",
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Make a streaming request to GLM-4.7 API.

        Args:
            messages: Chat messages for the model
            model: Model identifier (default: glm-4.7)
            stream: Whether to stream the response

        Yields:
            Chunks of the API response
        """
        if not self.api_key:
            # Mock response for development
            yield {
                "reasoning_content": "AI reasoning is not configured. Please set GLM_API_KEY environment variable.",
                "content": "AI service unavailable.",
                "done": True,
            }
            return

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "thinking": {
                "type": "enabled",
                "clear_thinking": False,  # Preserve thinking across turns
            },
        }

        try:
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"GLM API error: {response.status_code} - {error_text}")
                    yield {
                        "reasoning_content": f"API Error: {response.status_code}",
                        "content": "Failed to get AI response.",
                        "done": True,
                    }
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            yield {"done": True}
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                choice = choices[0]
                                delta = choice.get("delta", {})

                                # Extract reasoning content (GLM-4.7 thinking)
                                reasoning = delta.get("reasoning_content", "")
                                content = delta.get("content", "")

                                yield {
                                    "reasoning_content": reasoning,
                                    "content": content,
                                    "done": choice.get("finish_reason") == "stop",
                                }
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data_str}")
                            continue

        except httpx.RequestError as e:
            logger.error(f"GLM API request error: {e}")
            yield {
                "reasoning_content": f"Network Error: {str(e)}",
                "content": "Failed to connect to AI service.",
                "done": True,
            }

    def _save_reasoning_session(
        self,
        session_id: str,
        reasoning_content: str,
        metadata: Dict[str, Any],
    ) -> None:
        """
        Save reasoning session to database.

        Args:
            session_id: Unique session identifier
            reasoning_content: The thinking/reasoning content
            metadata: Additional metadata about the session
        """
        try:
            with get_db_session() as session:
                repo = AIReasoningSessionRepository(session)

                # Check if session exists
                existing = repo.get_by_session_id(session_id)

                if existing:
                    # Update existing session
                    existing.reasoning_content = (
                        existing.reasoning_content + "\n\n" + reasoning_content
                    )
                    existing.meta = {**existing.meta, **metadata}
                else:
                    # Create new session
                    from uuid import uuid4

                    repo.create(
                        id=f"ai_{uuid4().hex[:12]}",
                        session_id=session_id,
                        reasoning_content=reasoning_content,
                        meta=metadata,
                    )

        except Exception as e:
            logger.error(f"Failed to save reasoning session: {e}")

    async def analyze_market(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        indicators: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Analyze market data and return reasoning chain.

        Args:
            symbol: Trading symbol (e.g., "BTC/USDT")
            price_data: Price data including OHLCV
            indicators: Technical indicators

        Yields:
            Streaming analysis chunks with reasoning_content
        """
        session_id = f"market_analysis_{symbol}_{datetime.utcnow().isoformat()}"

        # Build context from market data
        current_price = price_data.get("closes", [{}])[-1] if price_data.get("closes") else 0
        price_change = (
            (price_data["closes"][-1] - price_data["closes"][-2]) / price_data["closes"][-2] * 100
            if len(price_data.get("closes", [])) > 1
            else 0
        )

        rsi_value = indicators.get("rsi_14", [{}])[-1]
        macd_value = indicators.get("macd_line", [{}])[-1]

        system_prompt = """You are an expert cryptocurrency market analyst for the Crypto Quant Laboratory.

Your task is to analyze market data and provide:
1. Technical analysis summary
2. Key support/resistance levels
3. Trend direction and strength
4. Potential trading opportunities
5. Risk factors to consider

Always show your reasoning process step-by-step before providing the final analysis."""

        user_prompt = f"""Analyze the following market data for {symbol}:

Current Price: ${current_price:.2f}
24h Change: {price_change:+.2f}%

Technical Indicators:
- RSI(14): {rsi_value:.2f}
- MACD: {macd_value:.4f}

Provide a detailed analysis with your reasoning process."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        full_reasoning = ""

        async for chunk in self._make_request(messages):
            if chunk.get("reasoning_content"):
                full_reasoning += chunk["reasoning_content"]

            chunk["session_id"] = session_id
            chunk["type"] = "market_analysis"

            yield chunk

        # Save reasoning session
        if full_reasoning:
            self._save_reasoning_session(
                session_id=session_id,
                reasoning_content=full_reasoning,
                metadata={
                    "symbol": symbol,
                    "analysis_type": "market_analysis",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def generate_signal_reasoning(
        self,
        signal: Dict[str, Any],
        price_data: Dict[str, Any],
        indicators: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Explain why a signal fired with detailed reasoning.

        Args:
            signal: Signal data including type, confidence, etc.
            price_data: Price data including OHLCV
            indicators: Technical indicators

        Yields:
            Streaming reasoning chunks with reasoning_content
        """
        signal_id = signal.get("id", "unknown")
        session_id = f"signal_reasoning_{signal_id}_{datetime.utcnow().isoformat()}"

        signal_type = signal.get("signal_type", "NEUTRAL")
        confidence = signal.get("confidence", 0.0)
        symbol = signal.get("symbol", "UNKNOWN")

        system_prompt = """You are an expert trading signal analyst for the Crypto Quant Laboratory.

Your task is to explain why a trading signal was generated by:
1. Analyzing the technical conditions that led to the signal
2. Identifying the key indicators that contributed
3. Explaining the confidence level
4. Highlighting risk factors and validation points
5. Suggesting confirmation strategies

Always show your reasoning process step-by-step."""

        user_prompt = f"""Explain the following {signal_type} signal for {symbol}:

Signal Details:
- Type: {signal_type}
- Confidence: {confidence:.2%}
- Price: ${signal.get('price', 0):.2f}

Provide a detailed explanation of why this signal was generated."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        full_reasoning = ""

        async for chunk in self._make_request(messages):
            if chunk.get("reasoning_content"):
                full_reasoning += chunk["reasoning_content"]

            chunk["session_id"] = session_id
            chunk["signal_id"] = signal_id
            chunk["type"] = "signal_reasoning"

            yield chunk

        # Save reasoning session
        if full_reasoning:
            self._save_reasoning_session(
                session_id=session_id,
                reasoning_content=full_reasoning,
                metadata={
                    "signal_id": signal_id,
                    "signal_type": signal_type,
                    "symbol": symbol,
                    "analysis_type": "signal_reasoning",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def assess_risk(
        self,
        portfolio_state: Dict[str, Any],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Assess portfolio risk with detailed reasoning.

        Args:
            portfolio_state: Current portfolio state including positions, equity, etc.

        Yields:
            Streaming risk assessment chunks with reasoning_content
        """
        session_id = f"risk_assessment_{datetime.utcnow().isoformat()}"

        total_equity = portfolio_state.get("total_equity", 0)
        open_pnl = portfolio_state.get("open_pnl", 0)
        positions = portfolio_state.get("positions", [])

        system_prompt = """You are an expert risk analyst for the Crypto Quant Laboratory.

Your task is to assess portfolio risk by:
1. Analyzing current position exposure
2. Identifying concentration risks
3. Evaluating drawdown potential
4. Suggesting risk mitigation strategies
5. Highlighting warning signs

Always show your reasoning process step-by-step."""

        user_prompt = f"""Assess the risk for the following portfolio:

Total Equity: ${total_equity:.2f}
Open P&L: ${open_pnl:+.2f}
Number of Positions: {len(positions)}

Positions:
{json.dumps(positions, indent=2)}

Provide a detailed risk assessment with your reasoning process."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        full_reasoning = ""

        async for chunk in self._make_request(messages):
            if chunk.get("reasoning_content"):
                full_reasoning += chunk["reasoning_content"]

            chunk["session_id"] = session_id
            chunk["type"] = "risk_assessment"

            yield chunk

        # Save reasoning session
        if full_reasoning:
            self._save_reasoning_session(
                session_id=session_id,
                reasoning_content=full_reasoning,
                metadata={
                    "total_equity": total_equity,
                    "open_pnl": open_pnl,
                    "num_positions": len(positions),
                    "analysis_type": "risk_assessment",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    async def get_reasoning_history(
        self,
        symbol: Optional[str] = None,
        hours: int = 24,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical reasoning sessions.

        Args:
            symbol: Filter by trading symbol
            hours: Lookback period in hours
            limit: Maximum number of sessions to return

        Returns:
            List of reasoning sessions
        """
        try:
            with get_db_session() as session:
                repo = AIReasoningSessionRepository(session)

                if symbol:
                    # Search by symbol in metadata
                    sessions = repo.search_reasoning(symbol, limit)
                else:
                    sessions = repo.get_recent(hours, limit)

                return [
                    {
                        "id": s.id,
                        "session_id": s.session_id,
                        "reasoning_content": s.reasoning_content,
                        "created_at": s.created_at.isoformat(),
                        "meta": s.meta,
                    }
                    for s in sessions
                ]

        except Exception as e:
            logger.error(f"Failed to retrieve reasoning history: {e}")
            return []


# Global AI Reasoning Engine instance
_engine: Optional[AIReasoningEngine] = None


def get_ai_reasoning_engine() -> AIReasoningEngine:
    """
    Get the global AI Reasoning Engine instance.

    Returns:
        AI Reasoning Engine singleton
    """
    global _engine
    if _engine is None:
        api_key = os.getenv("GLM_API_KEY")
        _engine = AIReasoningEngine(api_key=api_key)
    return _engine
