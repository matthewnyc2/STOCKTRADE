import httpx

class BinanceClient:
    def __init__(self, base_url="https://api.binance.us/api/v3"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_price(self, symbol="BTCUSDT"):
        response = await self.client.get(f"{self.base_url}/ticker/price", params={"symbol": symbol})
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
