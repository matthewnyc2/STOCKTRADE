"""
Polymarket API Client.

Provides access to Polymarket's CLOB, Gamma, and Data APIs
for fetching markets, trades, positions, and order book data.

Rate limits (Cloudflare throttled, sliding 10s windows):
  - CLOB general: 9,000 req/10s
  - Gamma general: 4,000 req/10s
  - Data general: 1,000 req/10s
  - Data /trades: 200 req/10s
  - Data /positions: 150 req/10s
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

CLOB_BASE = "https://clob.polymarket.com"
GAMMA_BASE = "https://gamma-api.polymarket.com"
DATA_BASE = "https://data-api.polymarket.com"

# Default request timeout
_TIMEOUT = 15.0


class PolymarketClient:
    """Async HTTP client for Polymarket public APIs."""

    def __init__(self, timeout: float = _TIMEOUT) -> None:
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Generic request with retry
    # ------------------------------------------------------------------

    async def _get(self, url: str, params: Optional[dict] = None) -> Any:
        client = await self._get_client()
        backoff = 1.0
        for attempt in range(4):
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 429:
                    wait = min(backoff, 16.0)
                    logger.warning("Rate limited (429), retrying in %.1fs", wait)
                    await asyncio.sleep(wait)
                    backoff *= 2
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError:
                raise
            except httpx.HTTPError as exc:
                if attempt == 3:
                    raise
                logger.warning("HTTP error %s, retry %d/3", exc, attempt + 1)
                await asyncio.sleep(backoff)
                backoff *= 2
        return None

    # ------------------------------------------------------------------
    # Gamma API — market discovery
    # ------------------------------------------------------------------

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
    ) -> list[dict]:
        """Fetch prediction markets from the Gamma API."""
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "active": active,
            "closed": closed,
        }
        return await self._get(f"{GAMMA_BASE}/markets", params) or []

    async def get_events(
        self, limit: int = 100, offset: int = 0, active: bool = True
    ) -> list[dict]:
        """Fetch events (groups of related markets)."""
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "active": active,
        }
        return await self._get(f"{GAMMA_BASE}/events", params) or []

    async def get_market(self, condition_id: str) -> Optional[dict]:
        """Fetch a single market by condition ID."""
        return await self._get(f"{GAMMA_BASE}/markets/{condition_id}")

    async def search_markets(self, query: str, limit: int = 20) -> list[dict]:
        """Search markets by keyword."""
        params = {"q": query, "limit": limit}
        return await self._get(f"{GAMMA_BASE}/public-search", params) or []

    # ------------------------------------------------------------------
    # CLOB API — order book & pricing
    # ------------------------------------------------------------------

    async def get_order_book(self, token_id: str) -> Optional[dict]:
        """Fetch live order book for a token."""
        return await self._get(f"{CLOB_BASE}/book", {"token_id": token_id})

    async def get_price(self, token_id: str) -> Optional[dict]:
        """Fetch current mid-price for a token."""
        return await self._get(f"{CLOB_BASE}/price", {"token_id": token_id})

    async def get_midpoint(self, token_id: str) -> Optional[dict]:
        """Fetch midpoint for a token."""
        return await self._get(f"{CLOB_BASE}/midpoint", {"token_id": token_id})

    async def get_prices_history(
        self,
        token_id: str,
        interval: str = "1d",
        fidelity: int = 60,
    ) -> list[dict]:
        """Fetch historical price data for a token."""
        params = {
            "market": token_id,
            "interval": interval,
            "fidelity": fidelity,
        }
        result = await self._get(f"{CLOB_BASE}/prices-history", params)
        if isinstance(result, dict):
            return result.get("history", [])
        return result or []

    # ------------------------------------------------------------------
    # Data API — trades, positions, user activity
    # ------------------------------------------------------------------

    async def get_trades(
        self,
        market: Optional[str] = None,
        maker: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Fetch trade history.

        Args:
            market: Filter by market/condition ID
            maker: Filter by wallet address
            limit: Max results (default 100)
            offset: Pagination offset
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        if maker:
            params["maker"] = maker
        result = await self._get(f"{DATA_BASE}/trades", params)
        if isinstance(result, dict):
            return result.get("data", result.get("trades", []))
        return result or []

    async def get_positions(
        self,
        address: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch open positions for a wallet address."""
        params: dict[str, Any] = {
            "user": address,
            "limit": limit,
            "offset": offset,
        }
        result = await self._get(f"{DATA_BASE}/positions", params)
        if isinstance(result, dict):
            return result.get("data", result.get("positions", []))
        return result or []

    async def get_closed_positions(
        self,
        address: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch closed/resolved positions for a wallet address."""
        params: dict[str, Any] = {
            "user": address,
            "limit": limit,
            "offset": offset,
        }
        result = await self._get(f"{DATA_BASE}/closed-positions", params)
        if isinstance(result, dict):
            return result.get("data", result.get("positions", []))
        return result or []

    # ------------------------------------------------------------------
    # Convenience — wallet trade history (paginated fetch-all)
    # ------------------------------------------------------------------

    async def get_all_wallet_trades(
        self,
        address: str,
        max_trades: int = 5000,
        page_size: int = 100,
    ) -> list[dict]:
        """
        Fetch all trades for a wallet address, paginating automatically.

        Args:
            address: Wallet address
            max_trades: Safety cap to prevent runaway pagination
            page_size: Trades per page (max 100)
        """
        all_trades: list[dict] = []
        offset = 0
        while len(all_trades) < max_trades:
            batch = await self.get_trades(
                maker=address, limit=page_size, offset=offset
            )
            if not batch:
                break
            all_trades.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
            # Small delay to respect rate limits
            await asyncio.sleep(0.1)
        return all_trades[:max_trades]

    async def get_all_wallet_positions(
        self,
        address: str,
        include_closed: bool = True,
        max_positions: int = 2000,
        page_size: int = 100,
    ) -> list[dict]:
        """Fetch all positions (open + optionally closed) for a wallet."""
        positions: list[dict] = []
        offset = 0
        while len(positions) < max_positions:
            batch = await self.get_positions(
                address=address, limit=page_size, offset=offset
            )
            if not batch:
                break
            positions.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
            await asyncio.sleep(0.1)

        if include_closed:
            offset = 0
            while len(positions) < max_positions:
                batch = await self.get_closed_positions(
                    address=address, limit=page_size, offset=offset
                )
                if not batch:
                    break
                positions.extend(batch)
                if len(batch) < page_size:
                    break
                offset += page_size
                await asyncio.sleep(0.1)

        return positions[:max_positions]


# Module-level singleton
_client: Optional[PolymarketClient] = None


def get_polymarket_client() -> PolymarketClient:
    """Return the module-level Polymarket client singleton."""
    global _client
    if _client is None:
        _client = PolymarketClient()
    return _client
