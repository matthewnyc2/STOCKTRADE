"""
Export OpenAPI specification from FastAPI to JSON file.

This script exports the OpenAPI spec without importing the full application,
avoiding database initialization issues.
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def export_openapi():
    """Export OpenAPI spec to JSON file."""

    # Import only what we need
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Create a minimal FastAPI app for spec generation
    app = FastAPI(
        title="Crypto Quant Laboratory",
        description="Quantitative analysis platform for cryptocurrency trading",
        version="0.1.0",
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Now import and include all routers
    try:
        from api.auth import router as auth_router
        from api.strategies import router as strategies_router
        from api.signals import router as signals_router
        from api.portfolio import router as portfolio_router
        from api.whales import router as whales_router
        from api.ml import router as ml_router
        from api.settings import router as settings_router
        from api.market_data import router as market_data_router
        from api.markets import router as markets_router
        from api.ai import router as ai_router
        from api.genetic import router as genetic_router
        from api.shadow import router as shadow_router
        from api.liquidations import router as liquidations_router
        from api.traders import router as traders_router
        from api.onboarding import router as onboarding_router
        from api.templates import router as templates_router
        from api.backtests import router as backtests_router

        # Include all routers
        app.include_router(auth_router, prefix="/api")
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

    except Exception as e:
        print(f"Warning: Some routers failed to load: {e}")
        print("Continuing with available routers...")

    # Get OpenAPI spec
    openapi_spec = app.openapi()

    # Save to file
    output_path = Path(__file__).parent.parent / "frontend" / "openapi.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(openapi_spec, f, indent=2)

    print(f"[SUCCESS] OpenAPI spec exported to: {output_path}")
    print(f"[INFO] Total endpoints: {len(openapi_spec.get('paths', {}))}")
    print(f"[INFO] Total schemas: {len(openapi_spec.get('components', {}).get('schemas', {}))}")

    # Print endpoint summary
    paths = openapi_spec.get('paths', {})
    print("\n[SUMMARY] Endpoint Summary:")
    for path, methods in sorted(paths.items()):
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                operation_id = details.get('operationId', 'N/A')
                tags = details.get('tags', [])
                print(f"   {method.upper():6} {path:50} [{', '.join(tags)}]")

    return openapi_spec


if __name__ == "__main__":
    export_openapi()
