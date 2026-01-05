"""
Markets API endpoints.

Provides endpoints for managing market metadata including coins,
exchanges, and trading pairs.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import JSONResponse

from database.connection import get_db_context
from database.repositories.market import (
    CoinRepository,
    ExchangeRepository,
    MarketPairRepository,
    StoredPriceDataRepository,
)
from models.market import (
    Coin,
    Exchange,
    MarketPair,
    StoredPriceData,
    MarketOverview,
    CoinSearchResult,
    MarketSyncRequest,
    MarketSyncResponse,
    AssetType,
    ExchangeType,
)
from services.market_data_manager import get_market_data_manager

router = APIRouter(prefix="/markets", tags=["markets"])


# ============================================================================
# Market Overview
# ============================================================================


@router.get("", response_model=MarketOverview)
async def get_markets():
    """
    Get overview of all markets.

    Returns summary statistics and top performing assets.

    Returns:
        MarketOverview with market statistics
    """
    manager = get_market_data_manager()
    return manager.get_market_overview()


# ============================================================================
# Coins
# ============================================================================


@router.get("/coins", response_model=List[Coin])
async def get_coins(
    asset_type: Optional[AssetType] = Query(default=None, description="Filter by asset type"),
    exchange: Optional[str] = Query(default=None, description="Filter by exchange"),
    active_only: bool = Query(default=True, description="Only return active coins"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum results"),
    sort_by: str = Query(default="market_cap", description="Sort by: market_cap, volume, symbol"),
):
    """
    Get list of coins with optional filtering.

    Args:
        asset_type: Filter by asset type (crypto, stock, forex, etc.)
        exchange: Filter by exchange
        active_only: Only return active coins
        limit: Maximum number of results
        sort_by: Sort field

    Returns:
        List of coins
    """
    with get_db_context() as session:
        coin_repo = CoinRepository(session)

        if asset_type:
            coins = coin_repo.get_coins_by_type(asset_type.value, limit=limit)
        elif exchange:
            coins = coin_repo.get_coins_by_exchange(exchange, limit=limit)
        elif active_only:
            if sort_by == "volume":
                coins = coin_repo.get_top_by_volume(limit=limit)
            elif sort_by == "symbol":
                coins = coin_repo.get_active_coins(limit=limit)
            else:
                coins = coin_repo.get_top_by_market_cap(limit=limit)
        else:
            coins = coin_repo.get_all(limit=limit)

        return [
            Coin(
                symbol=c.symbol,
                name=c.name,
                type=c.type,  # type: ignore
                base_currency=c.base_currency,
                quote_currency=c.quote_currency,
                exchange=c.exchange,
                is_active=c.is_active,
                coingecko_id=c.coingecko_id,
                coinmarketcap_id=c.coinmarketcap_id,
                market_cap=c.market_cap,
                volume_24h=c.volume_24h,
                circulating_supply=c.circulating_supply,
                total_supply=c.total_supply,
                logo_url=c.logo_url,
                website=c.website,
                description=c.description,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in coins
        ]


@router.get("/coins/{symbol}", response_model=Coin)
async def get_coin(symbol: str):
    """
    Get details for a specific coin.

    Args:
        symbol: Coin symbol (e.g., BTC, ETH)

    Returns:
        Coin details

    Raises:
        HTTPException: If coin not found
    """
    with get_db_context() as session:
        coin_repo = CoinRepository(session)
        coin = coin_repo.get_by_symbol(symbol)

        if not coin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Coin not found: {symbol}"
            )

        return Coin(
            symbol=coin.symbol,
            name=coin.name,
            type=coin.type,  # type: ignore
            base_currency=coin.base_currency,
            quote_currency=coin.quote_currency,
            exchange=coin.exchange,
            is_active=coin.is_active,
            coingecko_id=coin.coingecko_id,
            coinmarketcap_id=coin.coinmarketcap_id,
            market_cap=coin.market_cap,
            volume_24h=coin.volume_24h,
            circulating_supply=coin.circulating_supply,
            total_supply=coin.total_supply,
            logo_url=coin.logo_url,
            website=coin.website,
            description=coin.description,
            created_at=coin.created_at,
            updated_at=coin.updated_at,
        )


@router.get("/coins/{symbol}/pairs", response_model=List[MarketPair])
async def get_coin_pairs(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=200),
):
    """
    Get all trading pairs for a coin.

    Returns pairs where the coin is either base or quote.

    Args:
        symbol: Coin symbol
        limit: Maximum results

    Returns:
        List of trading pairs
    """
    with get_db_context() as session:
        pair_repo = MarketPairRepository(session)
        pairs = pair_repo.get_pairs_for_coin(symbol)[:limit]

        return [
            MarketPair(
                id=p.id,
                exchange_id=p.exchange_id,
                base_coin_id=p.base_coin_id,
                quote_coin_id=p.quote_coin_id,
                symbol=p.symbol,
                min_tick_size=p.min_tick_size,
                min_lot_size=p.min_lot_size,
                max_lot_size=p.max_lot_size,
                current_price=p.current_price,
                volume_24h=p.volume_24h,
                price_change_24h_percent=p.price_change_24h_percent,
                is_active=p.is_active,
                is_trading=p.is_trading,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in pairs
        ]


@router.get("/coins/search/{query}")
async def search_coins_endpoint(
    query: str,
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    Search coins by symbol or name.

    Args:
        query: Search query
        limit: Maximum results

    Returns:
        List of matching coins
    """
    manager = get_market_data_manager()
    return manager.search_coins(query, limit=limit)


@router.get("/coins/popular")
async def get_popular_coins_endpoint(
    by: str = Query(default="market_cap", description="Sort by: market_cap, volume, gainers, losers"),
    limit: int = Query(default=100, ge=1, le=200),
):
    """
    Get popular coins by various metrics.

    Args:
        by: Sort metric
        limit: Maximum results

    Returns:
        List of popular coins
    """
    manager = get_market_data_manager()
    return manager.get_popular_coins(by=by, limit=limit)


# ============================================================================
# Exchanges
# ============================================================================


@router.get("/exchanges", response_model=List[Exchange])
async def get_exchanges(
    exchange_type: Optional[ExchangeType] = Query(default=None, description="Filter by type (CEX/DEX)"),
    active_only: bool = Query(default=True, description="Only return active exchanges"),
):
    """
    Get list of exchanges.

    Args:
        exchange_type: Filter by exchange type
        active_only: Only return active exchanges

    Returns:
        List of exchanges
    """
    manager = get_market_data_manager()
    return manager.get_exchanges(exchange_type=exchange_type.value if exchange_type else None, active_only=active_only)


@router.get("/exchanges/{exchange_id}", response_model=Exchange)
async def get_exchange(exchange_id: str):
    """
    Get details for a specific exchange.

    Args:
        exchange_id: Exchange identifier

    Returns:
        Exchange details

    Raises:
        HTTPException: If exchange not found
    """
    with get_db_context() as session:
        exchange_repo = ExchangeRepository(session)
        exchange = exchange_repo.get(exchange_id)

        if not exchange:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exchange not found: {exchange_id}"
            )

        return Exchange(
            id=exchange.id,
            name=exchange.name,
            type=exchange.type,  # type: ignore
            api_endpoint=exchange.api_endpoint,
            websocket_endpoint=exchange.websocket_endpoint,
            is_active=exchange.is_active,
            api_key=exchange.api_key,
            api_secret=exchange.api_secret,
            rate_limit_per_minute=exchange.rate_limit_per_minute,
            rate_limit_per_second=exchange.rate_limit_per_second,
            supports_websocket=exchange.supports_websocket,
            supports_rest=exchange.supports_rest,
            supports_historical=exchange.supports_historical,
            logo_url=exchange.logo_url,
            website=exchange.website,
            description=exchange.description,
            created_at=exchange.created_at,
            updated_at=exchange.updated_at,
        )


# ============================================================================
# Trading Pairs
# ============================================================================


@router.get("/pairs", response_model=List[MarketPair])
async def get_pairs(
    base_coin: Optional[str] = Query(default=None, description="Filter by base coin"),
    quote_coin: Optional[str] = Query(default=None, description="Filter by quote coin"),
    exchange: Optional[str] = Query(default=None, description="Filter by exchange"),
    limit: int = Query(default=100, ge=1, le=500),
):
    """
    Get list of trading pairs.

    Args:
        base_coin: Filter by base coin symbol
        quote_coin: Filter by quote coin symbol
        exchange: Filter by exchange ID
        limit: Maximum results

    Returns:
        List of trading pairs
    """
    manager = get_market_data_manager()
    return manager.get_available_pairs(
        base_coin=base_coin,
        quote_coin=quote_coin,
        exchange=exchange,
        limit=limit,
    )


@router.get("/pairs/{pair_id}", response_model=MarketPair)
async def get_pair(pair_id: str):
    """
    Get details for a specific trading pair.

    Args:
        pair_id: Pair identifier

    Returns:
        Trading pair details

    Raises:
        HTTPException: If pair not found
    """
    with get_db_context() as session:
        pair_repo = MarketPairRepository(session)
        pair = pair_repo.get(pair_id)

        if not pair:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trading pair not found: {pair_id}"
            )

        return MarketPair(
            id=pair.id,
            exchange_id=pair.exchange_id,
            base_coin_id=pair.base_coin_id,
            quote_coin_id=pair.quote_coin_id,
            symbol=pair.symbol,
            min_tick_size=pair.min_tick_size,
            min_lot_size=pair.min_lot_size,
            max_lot_size=pair.max_lot_size,
            current_price=pair.current_price,
            volume_24h=pair.volume_24h,
            price_change_24h_percent=pair.price_change_24h_percent,
            is_active=pair.is_active,
            is_trading=pair.is_trading,
            created_at=pair.created_at,
            updated_at=pair.updated_at,
        )


# ============================================================================
# Sync Operations
# ============================================================================


@router.post("/sync", response_model=MarketSyncResponse)
async def sync_market_data(request: MarketSyncRequest):
    """
    Sync market data from exchanges.

    Fetches latest coin and exchange metadata from external APIs.

    Args:
        request: Sync request parameters

    Returns:
        Sync response with results
    """
    manager = get_market_data_manager()
    return manager.sync_coins_from_exchange(
        exchange=request.exchange,
        force_refresh=request.force_refresh,
    )


@router.post("/cache/update")
async def update_price_cache(
    symbols: Optional[List[str]] = Query(default=None, description="Symbols to update (None = all)"),
):
    """
    Update cached price data.

    Fetches latest prices from external APIs and updates the cache.

    Args:
        symbols: List of symbols to update

    Returns:
        Update results
    """
    manager = get_market_data_manager()
    updated = manager.update_price_cache(symbols=symbols)

    return {
        "success": True,
        "updated_count": updated,
        "message": f"Updated {updated} price cache entries",
    }


# ============================================================================
# Price Cache
# ============================================================================


@router.get("/cache/{symbol}", response_model=StoredPriceData)
async def get_cached_price(
    symbol: str,
    exchange: Optional[str] = Query(default=None, description="Exchange name"),
):
    """
    Get cached price data for a symbol.

    Returns the most recently cached price data.

    Args:
        symbol: Trading symbol
        exchange: Optional exchange filter

    Returns:
        Cached price data

    Raises:
        HTTPException: If no cached data found
    """
    with get_db_context() as session:
        cache_repo = StoredPriceDataRepository(session)
        cached = cache_repo.get_latest_price(symbol, exchange=exchange)

        if not cached:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cached price data for: {symbol}"
            )

        return StoredPriceData(
            id=cached.id,
            symbol=cached.symbol,
            exchange=cached.exchange,
            price=cached.price,
            bid_price=cached.bid_price,
            ask_price=cached.ask_price,
            volume_24h=cached.volume_24h,
            price_change_24h=cached.price_change_24h,
            price_change_percent_1h=cached.price_change_percent_1h,
            price_change_percent_24h=cached.price_change_percent_24h,
            price_change_percent_7d=cached.price_change_percent_7d,
            market_cap=cached.market_cap,
            market_cap_rank=cached.market_cap_rank,
            ttl_seconds=cached.ttl_seconds,
            created_at=cached.created_at,
            updated_at=cached.updated_at,
        )
