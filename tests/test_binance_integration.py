"""
Binance Integration Tests
WHY: Need real-time market data from Binance
"""
import pytest


def test_binance_client_exists():
    """WHY: Must have Binance API client"""
    from services.data_sources.binance import BinanceClient
    assert BinanceClient is not None


def test_binance_get_current_price():
    """WHY: Real-time prices needed for trading"""
    from services.data_sources.binance import BinanceClient
    client = BinanceClient()
    price = client.get_current_price("BTCUSDT")
    assert price is not None
    assert price > 0
