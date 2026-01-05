"""
Create a comprehensive OpenAPI specification for the Crypto Quant Laboratory API.

This script creates an OpenAPI spec based on the analyzed API structure,
which serves as the contract between frontend and backend.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Create the OpenAPI spec structure
spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Crypto Quant Laboratory",
        "description": "Quantitative analysis platform for cryptocurrency trading",
        "version": "0.1.0",
        "contact": {
            "name": "API Support"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {}
    },
    "paths": {},
    "tags": [
        {"name": "authentication", "description": "User authentication and token management"},
        {"name": "strategies", "description": "Trading strategy management"},
        {"name": "signals", "description": "Trading signals"},
        {"name": "portfolio", "description": "Portfolio management"},
        {"name": "whales", "description": "Whale tracking"},
        {"name": "ml", "description": "Machine learning models"},
        {"name": "settings", "description": "User settings"},
        {"name": "market_data", "description": "Market data endpoints"},
        {"name": "ai", "description": "AI reasoning endpoints"},
        {"name": "liquidations", "description": "Liquidation tracking"},
        {"name": "onboarding", "description": "User onboarding"}
    ]
}

# Helper function to create schema references
def ref(schema_name: str) -> Dict[str, str]:
    return {"$ref": f"#/components/schemas/{schema_name}"}

# Add basic schemas
spec["components"]["schemas"].update({
    # Strategy schemas
    "StrategyType": {
        "type": "string",
        "enum": ["composed", "genetic", "ml", "template"]
    },
    "Status": {
        "type": "string",
        "enum": ["active", "inactive", "draft"]
    },
    "Strategy": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "type": ref("StrategyType"),
            "parameters": {"type": "object"},
            "layers": {"type": "array", "items": {"type": "string"}},
            "status": ref("Status"),
            "created_at": {"type": "string", "format": "date-time"},
            "updated_at": {"type": "string", "format": "date-time"}
        },
        "required": ["id", "name", "type", "status"]
    },
    # Signal schemas
    "SignalType": {
        "type": "string",
        "enum": ["LONG", "SHORT", "CLOSE", "NEUTRAL"]
    },
    "Signal": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "strategy_id": {"type": "string"},
            "symbol": {"type": "string"},
            "signal_type": ref("SignalType"),
            "confidence": {"type": "number"},
            "price": {"type": "number"},
            "timestamp": {"type": "string", "format": "date-time"},
            "reasoning": {"type": "string"}
        },
        "required": ["id", "strategy_id", "symbol", "signal_type", "confidence", "price", "timestamp"]
    },
    # Portfolio schemas
    "Portfolio": {
        "type": "object",
        "properties": {
            "total_equity": {"type": "number"},
            "starting_balance": {"type": "number"},
            "total_pnl": {"type": "number"},
            "total_pnl_percent": {"type": "number"},
            "open_pnl": {"type": "number"},
            "positions": {"type": "array", "items": ref("Position")}
        }
    },
    "Position": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "symbol": {"type": "string"},
            "side": {"type": "string", "enum": ["LONG", "SHORT"]},
            "quantity": {"type": "number"},
            "entry_price": {"type": "number"},
            "current_price": {"type": "number"},
            "unrealized_pnl": {"type": "number"},
            "unrealized_pnl_percent": {"type": "number"}
        },
        "required": ["id", "symbol", "side", "quantity", "entry_price", "current_price"]
    },
    # Common error response
    "Error": {
        "type": "object",
        "properties": {
            "detail": {"type": "string"},
            "message": {"type": "string"},
            "code": {"type": "string"}
        }
    }
})

# Add example endpoints
spec["paths"].update({
    "/api/v1/strategies": {
        "get": {
            "tags": ["strategies"],
            "summary": "List all strategies",
            "operationId": "list_strategies",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": ref("Strategy")
                            }
                        }
                    }
                }
            }
        },
        "post": {
            "tags": ["strategies"],
            "summary": "Create a new strategy",
            "operationId": "create_strategy",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": ref("Strategy")
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Strategy created",
                    "content": {
                        "application/json": {
                            "schema": ref("Strategy")
                        }
                    }
                }
            }
        }
    },
    "/api/v1/strategies/{strategy_id}": {
        "get": {
            "tags": ["strategies"],
            "summary": "Get strategy by ID",
            "operationId": "get_strategy",
            "parameters": [
                {
                    "name": "strategy_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": ref("Strategy")
                        }
                    }
                },
                "404": {
                    "description": "Strategy not found",
                    "content": {
                        "application/json": {
                            "schema": ref("Error")
                        }
                    }
                }
            }
        }
    },
    "/api/v1/signals": {
        "get": {
            "tags": ["signals"],
            "summary": "List all signals",
            "operationId": "list_signals",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": ref("Signal")
                            }
                        }
                    }
                }
            }
        }
    },
    "/api/v1/portfolio": {
        "get": {
            "tags": ["portfolio"],
            "summary": "Get current portfolio",
            "operationId": "get_portfolio",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": ref("Portfolio")
                        }
                    }
                }
            }
        }
    }
})

# Save the spec
output_path = Path(__file__).parent.parent / "frontend" / "openapi.json"
with open(output_path, 'w') as f:
    json.dump(spec, f, indent=2)

print(f"[SUCCESS] OpenAPI spec created at: {output_path}")
print(f"[INFO] Total schemas: {len(spec['components']['schemas'])}")
print(f"[INFO] Total paths: {len(spec['paths'])}")
print("[INFO] This is a basic template. Update it with the full spec from the running backend.")
