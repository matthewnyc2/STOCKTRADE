"""
AI API router.

Endpoints for AI-powered market analysis, signal reasoning, and risk assessment
with GLM-4.7 integration and preserved thinking.
"""

from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.websocket import get_websocket_manager
from services.ai_reasoning import get_ai_reasoning_engine


router = APIRouter(prefix="/ai", tags=["ai"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class MarketAnalysisRequest(BaseModel):
    """Schema for market analysis request."""

    symbol: str
    price_data: Dict[str, Any]
    indicators: Dict[str, Any]


class SignalReasoningRequest(BaseModel):
    """Schema for signal reasoning request."""

    signal: Dict[str, Any]
    price_data: Dict[str, Any]
    indicators: Dict[str, Any]


class RiskAssessmentRequest(BaseModel):
    """Schema for risk assessment request."""

    portfolio_state: Dict[str, Any]


class AIAnalysisResponse(BaseModel):
    """Schema for AI analysis response chunk."""

    session_id: str
    type: str
    reasoning_content: str
    content: str
    done: bool


class ReasoningSessionResponse(BaseModel):
    """Schema for reasoning session response."""

    id: str
    session_id: str
    reasoning_content: str
    created_at: str
    meta: Dict[str, Any]


# ============================================================================
# STREAMING ENDPOINTS
# ============================================================================


@router.post("/analyze", response_class=StreamingResponse)
async def analyze_market(request: MarketAnalysisRequest):
    """
    Request AI market analysis with streaming reasoning.

    Provides real-time streaming analysis with preserved thinking using
    GLM-4.7's chain-of-thought capabilities.

    Args:
        request: Market analysis request with symbol, price data, and indicators

    Returns:
        StreamingResponse: SSE stream of analysis chunks with reasoning_content
    """
    engine = get_ai_reasoning_engine()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generator for SSE events."""
        try:
            async for chunk in engine.analyze_market(
                symbol=request.symbol,
                price_data=request.price_data,
                indicators=request.indicators,
            ):
                # Format as SSE event
                data = {
                    "session_id": chunk.get("session_id", ""),
                    "type": chunk.get("type", "market_analysis"),
                    "reasoning_content": chunk.get("reasoning_content", ""),
                    "content": chunk.get("content", ""),
                    "done": chunk.get("done", False),
                }

                # Broadcast to WebSocket
                ws_manager = get_websocket_manager()
                await ws_manager.broadcast("ai-reasoning", data)

                # Send as SSE
                yield f"data: {chunk_to_json(data)}\n\n"

                if chunk.get("done"):
                    break

            # Send final done event
            yield f"data: {chunk_to_json({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in market analysis stream: {e}")
            error_data = {
                "error": str(e),
                "done": True,
            }
            yield f"data: {chunk_to_json(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/signal-reasoning", response_class=StreamingResponse)
async def get_signal_reasoning(request: SignalReasoningRequest):
    """
    Get AI reasoning for why a signal fired.

    Provides detailed explanation of signal generation with preserved thinking.

    Args:
        request: Signal reasoning request with signal data, price data, and indicators

    Returns:
        StreamingResponse: SSE stream of reasoning chunks
    """
    engine = get_ai_reasoning_engine()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generator for SSE events."""
        try:
            async for chunk in engine.generate_signal_reasoning(
                signal=request.signal,
                price_data=request.price_data,
                indicators=request.indicators,
            ):
                data = {
                    "session_id": chunk.get("session_id", ""),
                    "signal_id": chunk.get("signal_id", ""),
                    "type": chunk.get("type", "signal_reasoning"),
                    "reasoning_content": chunk.get("reasoning_content", ""),
                    "content": chunk.get("content", ""),
                    "done": chunk.get("done", False),
                }

                # Broadcast to WebSocket
                ws_manager = get_websocket_manager()
                await ws_manager.broadcast("ai-reasoning", data)

                yield f"data: {chunk_to_json(data)}\n\n"

                if chunk.get("done"):
                    break

            yield f"data: {chunk_to_json({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in signal reasoning stream: {e}")
            error_data = {
                "error": str(e),
                "done": True,
            }
            yield f"data: {chunk_to_json(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/risk-assessment", response_class=StreamingResponse)
async def assess_portfolio_risk(request: RiskAssessmentRequest):
    """
    Get AI risk assessment for portfolio.

    Provides comprehensive risk analysis with preserved thinking.

    Args:
        request: Risk assessment request with portfolio state

    Returns:
        StreamingResponse: SSE stream of risk assessment chunks
    """
    engine = get_ai_reasoning_engine()

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generator for SSE events."""
        try:
            async for chunk in engine.assess_risk(
                portfolio_state=request.portfolio_state,
            ):
                data = {
                    "session_id": chunk.get("session_id", ""),
                    "type": chunk.get("type", "risk_assessment"),
                    "reasoning_content": chunk.get("reasoning_content", ""),
                    "content": chunk.get("content", ""),
                    "done": chunk.get("done", False),
                }

                # Broadcast to WebSocket
                ws_manager = get_websocket_manager()
                await ws_manager.broadcast("ai-reasoning", data)

                yield f"data: {chunk_to_json(data)}\n\n"

                if chunk.get("done"):
                    break

            yield f"data: {chunk_to_json({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Error in risk assessment stream: {e}")
            error_data = {
                "error": str(e),
                "done": True,
            }
            yield f"data: {chunk_to_json(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# NON-STREAMING ENDPOINTS
# ============================================================================


@router.get("/reasoning/history", response_model=List[ReasoningSessionResponse])
async def get_reasoning_history(
    symbol: Optional[str] = Query(None, description="Filter by trading symbol"),
    hours: int = Query(24, description="Lookback period in hours", ge=1, le=168),
    limit: int = Query(50, description="Maximum number of sessions", ge=1, le=100),
) -> List[ReasoningSessionResponse]:
    """
    Retrieve historical reasoning sessions.

    Args:
        symbol: Optional filter by trading symbol
        hours: Lookback period in hours (default: 24, max: 168)
        limit: Maximum number of sessions to return (default: 50, max: 100)

    Returns:
        List[ReasoningSessionResponse]: List of reasoning sessions
    """
    engine = get_ai_reasoning_engine()
    sessions = await engine.get_reasoning_history(symbol=symbol, hours=hours, limit=limit)

    return [
        ReasoningSessionResponse(
            id=session["id"],
            session_id=session["session_id"],
            reasoning_content=session["reasoning_content"],
            created_at=session["created_at"],
            meta=session["meta"],
        )
        for session in sessions
    ]


@router.get("/reasoning/{session_id}", response_model=ReasoningSessionResponse)
async def get_reasoning_session(session_id: str) -> ReasoningSessionResponse:
    """
    Get a specific reasoning session by session ID.

    Args:
        session_id: The reasoning session ID

    Returns:
        ReasoningSessionResponse: The reasoning session

    Raises:
        HTTPException: If session not found
    """
    from database.connection import get_db_session
    from database.repositories import AIReasoningSessionRepository

    with get_db_session() as session:
        repo = AIReasoningSessionRepository(session)
        reasoning_model = repo.get_by_session_id(session_id)

        if reasoning_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reasoning session {session_id} not found",
            )

        return ReasoningSessionResponse(
            id=reasoning_model.id,
            session_id=reasoning_model.session_id,
            reasoning_content=reasoning_model.reasoning_content,
            created_at=reasoning_model.created_at.isoformat(),
            meta=reasoning_model.meta,
        )


@router.delete("/reasoning/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reasoning_session(session_id: str) -> None:
    """
    Delete a reasoning session.

    Args:
        session_id: The reasoning session ID

    Raises:
        HTTPException: If session not found
    """
    from database.connection import get_db_session
    from database.repositories import AIReasoningSessionRepository

    with get_db_session() as session:
        repo = AIReasoningSessionRepository(session)
        reasoning_model = repo.get_by_session_id(session_id)

        if reasoning_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reasoning session {session_id} not found",
            )

        repo.delete(reasoning_model.id)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


import json
import logging

logger = logging.getLogger(__name__)


def chunk_to_json(data: Dict[str, Any]) -> str:
    """Convert chunk data to JSON string."""
    return json.dumps(data)
