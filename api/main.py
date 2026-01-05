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
from api.markets import router as markets_router
from api.ml import router as ml_router
from api.portfolio import router as portfolio_router
from api.settings import router as settings_router
from api.shadow import router as shadow_router
from api.signals import router as signals_router
from api.strategies import router as strategies_router
from api.templates import router as templates_router
from api.whales import router as whales_router
from api.ai import router as ai_router
from api.traders import router as traders_router
from api.onboarding import router as onboarding_router
from api.auth import router as auth_router
from api.admin import router as admin_router
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

    # Check if data is initialized
    import os
    auto_init = os.getenv("AUTO_INITIALIZE_DATA", "false").lower() == "true"

    if auto_init:
        from services.data_initializer import is_initialized, initialize_reference_data
        if not is_initialized():
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Auto-initializing reference data on first run...")
            try:
                initialize_reference_data()
                logger.info("Reference data initialized successfully")
            except Exception as e:
                logger.error(f"Failed to auto-initialize data: {e}")

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
# Auth endpoints remain at /api/auth (no versioning)
app.include_router(auth_router, prefix="/api")
# All other endpoints use /api/v1 prefix
app.include_router(strategies_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(backtests_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(whales_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(market_data_router, prefix="/api/v1")
app.include_router(markets_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(genetic_router, prefix="/api/v1")
app.include_router(shadow_router, prefix="/api/v1")
app.include_router(liquidations_router, prefix="/api/v1")
app.include_router(traders_router, prefix="/api/v1")
app.include_router(onboarding_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
async def dashboard():
    """Dashboard endpoint."""
    return {"status": "healthy", "service": "crypto-quant-lab"}


@app.get("/api/dashboard/components")
async def dashboard_components():
    """Dashboard components endpoint."""
    return {
        "charts": ["price_chart", "volume_chart"],
        "tables": ["positions", "orders"],
        "controls": ["buy_sell", "settings"]
    }


@app.get("/ws")
async def websocket_info():
    """
    WebSocket endpoint information.

    Returns information about available WebSocket channels and dedicated endpoints.
    """
    ws_manager = get_websocket_manager()
    return {
        "websocket": "available",
        "endpoints": [
            {"path": "/ws/signals", "channel": "signals", "description": "Live signal updates"},
            {"path": "/ws/portfolio", "channel": "portfolio", "description": "Portfolio updates"},
            {"path": "/ws/whales", "channel": "whales", "description": "Whale activity alerts"},
            {"path": "/ws/prices", "channel": "price-ticker", "description": "Real-time price updates"},
            {"path": "/ws/shadow", "channel": "arbitrage", "description": "Shadow Protocol events"},
            {"path": "/ws/ai-reasoning", "channel": "ai-reasoning", "description": "AI reasoning stream"},
            {"path": "/ws/genetic", "channel": "genetic-progress", "description": "Genetic algorithm optimization progress"},
            {"path": "/ws/liquidations", "channel": "liquidations", "description": "Real-time liquidation feed"},
            {"path": "/ws", "channel": "multi-channel", "description": "Multi-channel endpoint with query param subscription"},
        ],
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


@app.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard WebSocket endpoint."""
    await websocket.accept()
    await websocket.send_json({
        "market_data": {"price": 50000, "volume": 1000},
        "timestamp": "2026-01-01T02:22:29.831-08:00"
    })


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


# ============================================================================
# DEDICATED WEBSOCKET ENDPOINTS
# ============================================================================

@app.websocket("/ws/signals")
async def signals_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for signals channel.

    Clients connecting to this endpoint are automatically subscribed
    to the signals channel and will receive live signal updates.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["signals"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/portfolio")
async def portfolio_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for portfolio updates.

    Clients connecting to this endpoint are automatically subscribed
    to the portfolio channel and will receive portfolio updates.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["portfolio"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/whales")
async def whales_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for whale activity.

    Clients connecting to this endpoint are automatically subscribed
    to the whales channel and will receive whale activity alerts.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["whales"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/prices")
async def prices_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for price ticker.

    Clients connecting to this endpoint are automatically subscribed
    to the price-ticker channel and will receive real-time price updates.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["price-ticker"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/shadow")
async def shadow_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for Shadow Protocol events.

    Clients connecting to this endpoint are automatically subscribed
    to the arbitrage channel and will receive Shadow Protocol events.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["arbitrage"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/ai-reasoning")
async def ai_reasoning_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for AI reasoning stream.

    Clients connecting to this endpoint are automatically subscribed
    to the ai-reasoning channel and will receive AI reasoning updates.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["ai-reasoning"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/genetic")
async def genetic_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for genetic algorithm progress.

    Clients connecting to this endpoint are automatically subscribed
    to the genetic-progress channel and will receive optimization updates.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["genetic-progress"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.websocket("/ws/liquidations")
async def liquidations_websocket(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for liquidation feed.

    Clients connecting to this endpoint are automatically subscribed
    to the liquidations channel and will receive real-time liquidation alerts.
    """
    await websocket.accept()
    ws_manager = get_websocket_manager()
    await ws_manager.connect(websocket, ["liquidations"])

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_json()

            # Handle ping/pong for connection health
            if data.get("action") == "ping":
                await ws_manager.send_personal({"action": "pong"}, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
        raise


@app.get("/ws/test")
async def websocket_test_page():
    """
    Returns a simple HTML test page for WebSocket testing.
    """
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
        <style>
            body { font-family: monospace; padding: 20px; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; }
            .message { margin: 5px 0; padding: 5px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <div>
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
            <button onclick="sendPing()">Send Ping</button>
        </div>
        <div id="messages"></div>
        <script>
            let ws = null;

            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws?channels=signals,portfolio,whales`;

                ws = new WebSocket(wsUrl);

                ws.onopen = function() {
                    addMessage('Connected to WebSocket');
                };

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(`Received: ${JSON.stringify(data, null, 2)}`);
                };

                ws.onclose = function() {
                    addMessage('Disconnected from WebSocket');
                };

                ws.onerror = function(error) {
                    addMessage(`Error: ${error}`);
                };
            }

            function disconnect() {
                if (ws) {
                    ws.close();
                }
            }

            function sendPing() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({action: 'ping'}));
                    addMessage('Sent: ping');
                }
            }

            function addMessage(text) {
                const div = document.createElement('div');
                div.className = 'message';
                div.textContent = text;
                document.getElementById('messages').appendChild(div);
            }
        </script>
    </body>
    </html>
    """)
