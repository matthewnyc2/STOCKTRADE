"""
Main FastAPI application for Crypto Quant Laboratory.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from api.backtests import router as backtests_router
from api.genetic import router as genetic_router
from api.liquidations import router as liquidations_router
from api.market_data import router as market_data_router
from api.ml import router as ml_router
from api.portfolio import router as portfolio_router
from api.settings import router as settings_router
from api.shadow import router as shadow_router
from api.signals import router as signals_router
from api.strategies import router as strategies_router
from api.whales import router as whales_router
from api.ai import router as ai_router
from core.middleware import setup_middleware
from core.websocket import get_websocket_manager
from database.connection import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for FastAPI.

    Handles startup and shutdown events.
    """
    # Startup
    init_db()
    yield
    # Shutdown
    from database.connection import close_db
    close_db()


app = FastAPI(
    title="Crypto Quant Laboratory",
    description="Quantitative analysis platform for cryptocurrency trading",
    version="0.1.0",
    lifespan=lifespan,
)

# Set up middleware (CORS, error handling, request logging)
setup_middleware(app)

# Include all API routers
app.include_router(strategies_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(backtests_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(whales_router, prefix="/api")
app.include_router(ml_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(market_data_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(genetic_router, prefix="/api")
app.include_router(shadow_router, prefix="/api")
app.include_router(liquidations_router, prefix="/api")


@app.get("/")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: A dictionary with the service status and name.
    """
    return {"status": "healthy", "service": "crypto-quant-lab"}


@app.get("/ws")
async def websocket_info():
    """
    WebSocket endpoint information.

    Returns information about available WebSocket channels.
    """
    ws_manager = get_websocket_manager()
    return {
        "websocket": "available",
        "channels": [
            {"name": "signals", "description": "Live signal updates"},
            {"name": "portfolio", "description": "Portfolio updates"},
            {"name": "whales", "description": "Whale activity alerts"},
            {"name": "ai-reasoning", "description": "AI reasoning stream"},
            {"name": "price-ticker", "description": "Real-time price updates"},
            {"name": "genetic-progress", "description": "Genetic algorithm optimization progress"},
            {"name": "arbitrage", "description": "Dark arbitrage opportunity alerts"},
            {"name": "liquidations", "description": "Real-time liquidation feed and cascade alerts"},
        ],
        "connection_info": ws_manager.get_connection_info(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint.

    Connects clients and allows them to subscribe to channels.

    Query parameters:
        channels: Comma-separated list of channels to subscribe to
                 (signals, portfolio, whales, ai-reasoning, price-ticker)
    """
    ws_manager = get_websocket_manager()

    # Get channels from query params
    channels_str = websocket.query_params.get("channels", "signals")
    channels = [c.strip() for c in channels_str.split(",") if c.strip()]

    # Validate channels
    valid_channels = {"signals", "portfolio", "whales", "ai-reasoning", "price-ticker", "genetic-progress", "arbitrage", "liquidations"}
    channels = [c for c in channels if c in valid_channels]

    if not channels:
        channels = ["signals"]  # Default channel

    # Connect and subscribe
    await ws_manager.connect(websocket, channels)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle subscription changes
            if data.get("action") == "subscribe":
                channel = data.get("channel")
                if channel and channel in valid_channels:
                    await ws_manager.subscribe(websocket, channel)

            elif data.get("action") == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    await ws_manager.unsubscribe(websocket, channel)

            elif data.get("action") == "ping":
                # Respond to ping with pong
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """
    Test WebSocket endpoint that responds to ping with pong.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
