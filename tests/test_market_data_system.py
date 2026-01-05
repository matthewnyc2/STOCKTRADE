"""
Test script for the Market Data Storage System.

Run this to verify the implementation works correctly.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from models.market import (
            Coin, Exchange, MarketPair, StoredPriceData,
            MarketOverview, AssetType, ExchangeType
        )
        print("  models.market - OK")
    except Exception as e:
        print(f"  models.market - FAILED: {e}")
        return False

    try:
        from database.models.market import (
            CoinModel, ExchangeModel, MarketPairModel, StoredPriceDataModel
        )
        print("  database.models.market - OK")
    except Exception as e:
        print(f"  database.models.market - FAILED: {e}")
        return False

    try:
        from database.repositories.market import (
            CoinRepository, ExchangeRepository, MarketPairRepository,
            StoredPriceDataRepository
        )
        print("  database.repositories.market - OK")
    except Exception as e:
        print(f"  database.repositories.market - FAILED: {e}")
        return False

    try:
        from services.market_data_manager import MarketDataManager, get_market_data_manager
        print("  services.market_data_manager - OK")
    except Exception as e:
        print(f"  services.market_data_manager - FAILED: {e}")
        return False

    try:
        from api.markets import router
        print("  api.markets - OK")
    except Exception as e:
        print(f"  api.markets - FAILED: {e}")
        return False

    print("All imports successful!\n")
    return True


def test_pydantic_models():
    """Test Pydantic model validation."""
    print("Testing Pydantic models...")

    from models.market import Coin, Exchange, MarketPair, AssetType, ExchangeType
    from decimal import Decimal
    from datetime import datetime

    try:
        # Test Coin model
        coin = Coin(
            symbol="BTC",
            name="Bitcoin",
            type=AssetType.CRYPTO,
            is_active=True,
            market_cap=Decimal("1000000000000")
        )
        assert coin.symbol == "BTC"
        assert coin.type == AssetType.CRYPTO
        print("  Coin model - OK")
    except Exception as e:
        print(f"  Coin model - FAILED: {e}")
        return False

    try:
        # Test Exchange model
        exchange = Exchange(
            id="binance",
            name="Binance",
            type=ExchangeType.CEX,
            is_active=True,
            supports_websocket=True
        )
        assert exchange.id == "binance"
        assert exchange.type == ExchangeType.CEX
        print("  Exchange model - OK")
    except Exception as e:
        print(f"  Exchange model - FAILED: {e}")
        return False

    try:
        # Test MarketPair model
        pair = MarketPair(
            id="pair_binance_btc_usdt",
            exchange_id="binance",
            base_coin_id="BTC",
            quote_coin_id="USDT",
            symbol="BTC/USDT",
            is_active=True
        )
        assert pair.symbol == "BTC/USDT"
        print("  MarketPair model - OK")
    except Exception as e:
        print(f"  MarketPair model - FAILED: {e}")
        return False

    print("Pydantic model tests passed!\n")
    return True


def test_database_models():
    """Test SQLAlchemy ORM models."""
    print("Testing SQLAlchemy ORM models...")

    from database.models.market import CoinModel, ExchangeModel
    from decimal import Decimal
    from datetime import datetime

    try:
        # Test CoinModel instantiation
        coin = CoinModel(
            id="coin_test",
            symbol="TEST",
            name="Test Coin",
            type="crypto",
            is_active=True
        )
        assert coin.symbol == "TEST"
        print("  CoinModel - OK")
    except Exception as e:
        print(f"  CoinModel - FAILED: {e}")
        return False

    try:
        # Test ExchangeModel instantiation
        exchange = ExchangeModel(
            id="exchange_test",
            name="Test Exchange",
            type="cex",
            is_active=True
        )
        assert exchange.name == "Test Exchange"
        print("  ExchangeModel - OK")
    except Exception as e:
        print(f"  ExchangeModel - FAILED: {e}")
        return False

    print("SQLAlchemy ORM model tests passed!\n")
    return True


def test_repository_methods():
    """Test repository methods are available."""
    print("Testing repository methods...")

    from database.repositories.market import CoinRepository

    # Check that expected methods exist
    expected_methods = [
        'get_by_symbol',
        'get_active_coins',
        'get_coins_by_type',
        'get_coins_by_exchange',
        'search_coins',
        'upsert_coin',
        'bulk_upsert_coins',
        'get_top_by_market_cap',
        'get_top_by_volume',
        'get_top_gainers_24h',
        'get_top_losers_24h',
    ]

    for method in expected_methods:
        if not hasattr(CoinRepository, method):
            print(f"  CoinRepository.{method} - MISSING")
            return False

    print(f"  All {len(expected_methods)} CoinRepository methods present - OK")

    from database.repositories.market import ExchangeRepository

    exchange_methods = [
        'get_by_name',
        'get_active_exchanges',
        'get_by_type',
        'upsert_exchange',
    ]

    for method in exchange_methods:
        if not hasattr(ExchangeRepository, method):
            print(f"  ExchangeRepository.{method} - MISSING")
            return False

    print(f"  All {len(exchange_methods)} ExchangeRepository methods present - OK")
    print("Repository method tests passed!\n")
    return True


def test_service_methods():
    """Test service methods are available."""
    print("Testing service methods...")

    from services.market_data_manager import MarketDataManager

    expected_methods = [
        'sync_coins_from_exchange',
        'update_price_cache',
        'get_market_overview',
        'search_coins',
        'get_popular_coins',
        'get_available_pairs',
        'get_exchanges',
    ]

    for method in expected_methods:
        if not hasattr(MarketDataManager, method):
            print(f"  MarketDataManager.{method} - MISSING")
            return False

    print(f"  All {len(expected_methods)} MarketDataManager methods present - OK")
    print("Service method tests passed!\n")
    return True


def test_api_endpoints():
    """Test API router is configured."""
    print("Testing API endpoints...")

    from api.markets import router

    # Check that routes are registered
    routes = [route.path for route in router.routes]

    expected_routes = [
        "/markets",
        "/markets/coins",
        "/markets/coins/{symbol}",
        "/markets/coins/{symbol}/pairs",
        "/markets/coins/search/{query}",
        "/markets/coins/popular",
        "/markets/exchanges",
        "/markets/exchanges/{exchange_id}",
        "/markets/pairs",
        "/markets/pairs/{pair_id}",
        "/markets/sync",
        "/markets/cache/update",
        "/markets/cache/{symbol}",
    ]

    for route in expected_routes:
        if route not in routes:
            print(f"  Route {route} - MISSING")
            return False

    print(f"  All {len(expected_routes)} routes registered - OK")
    print("API endpoint tests passed!\n")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Market Data Storage System - Integration Test")
    print("=" * 60)
    print()

    tests = [
        test_imports,
        test_pydantic_models,
        test_database_models,
        test_repository_methods,
        test_service_methods,
        test_api_endpoints,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"Test {test.__name__} crashed: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\nAll tests passed! The Market Data Storage System is ready to use.")
        return 0
    else:
        print(f"\n{failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
