"""
CoinGecko Integration Tests
WHY: Need backup data source for reliability
"""
import pytest


def test_coingecko_client_exists():
    """WHY: Must have CoinGecko API client"""
    from services.data_sources.coingecko import CoinGeckoClient
    assert CoinGeckoClient is not None


def test_coingecko_get_current_price():
    """WHY: Backup data source for reliability"""
    from services.data_sources.coingecko import CoinGeckoClient
    client = CoinGeckoClient()
    price = client.get_current_price("bitcoin")
    assert price is not None
    assert price > 0
