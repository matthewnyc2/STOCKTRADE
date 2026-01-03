import httpx

class CoinGeckoAPI:
    """A client for interacting with the CoinGecko API."""
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, client=None):
        self.client = client or httpx.Client()

    def ping(self):
        """Checks if the CoinGecko API is reachable."""
        response = self.client.get(f"{self.BASE_URL}/ping")
        response.raise_for_status()
        return response.json()

    def get_price(self, ids, vs_currencies):
        """
        Fetches the current price of any active cryptocurrency in any other supported currency.

        Args:
            ids (str or list): The ID of the cryptocurrency (e.g., 'bitcoin').
            vs_currencies (str or list): The currency to compare against (e.g., 'usd').
        """
        params = {
            'ids': ids,
            'vs_currencies': vs_currencies
        }
        response = self.client.get(f"{self.BASE_URL}/simple/price", params=params)
        response.raise_for_status()
        return response.json()
