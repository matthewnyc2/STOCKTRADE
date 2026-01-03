import pytest
from services.data_sources.binance import BinanceClient

@pytest.mark.asyncio
async def test_get_btc_usdt_price():
    client = BinanceClient()
    try:
        data = await client.get_price("BTCUSDT")
        assert isinstance(data, dict)
        assert "symbol" in data
        assert "price" in data
        assert data["symbol"] == "BTCUSDT"
    finally:
        await client.close()
