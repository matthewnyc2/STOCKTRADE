"""
Seed market metadata with initial data.

Populates the coins, exchanges, and market_pairs tables with
common cryptocurrency data for development and testing.
"""

from decimal import Decimal
from database.connection import get_db_session
from database.repositories.market import (
    CoinRepository,
    ExchangeRepository,
    MarketPairRepository,
)


def seed_exchanges():
    """Seed exchanges table with common cryptocurrency exchanges."""
    exchanges_data = [
        {
            "id": "coingecko",
            "name": "CoinGecko",
            "type": "cex",
            "api_endpoint": "https://api.coingecko.com/api/v3",
            "is_active": True,
            "supports_rest": True,
            "supports_historical": True,
            "website": "https://www.coingecko.com",
            "description": "Cryptocurrency data aggregator",
        },
        {
            "id": "binance",
            "name": "Binance",
            "type": "cex",
            "api_endpoint": "https://api.binance.com",
            "websocket_endpoint": "wss://stream.binance.com:9443",
            "is_active": True,
            "supports_rest": True,
            "supports_websocket": True,
            "supports_historical": True,
            "website": "https://www.binance.com",
            "description": "World's largest cryptocurrency exchange",
            "rate_limit_per_minute": 1200,
        },
        {
            "id": "uniswap_v3",
            "name": "Uniswap V3",
            "type": "dex",
            "is_active": True,
            "supports_rest": False,
            "supports_websocket": True,
            "website": "https://uniswap.org",
            "description": "Leading decentralized exchange on Ethereum",
        },
    ]

    with get_db_session() as session:
        repo = ExchangeRepository(session)
        for exchange_data in exchanges_data:
            repo.upsert_exchange(exchange_data)
        session.commit()
        print(f"Seeded {len(exchanges_data)} exchanges")


def seed_coins():
    """Seed coins table with popular cryptocurrencies."""
    coins_data = [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "type": "crypto",
            "coingecko_id": "bitcoin",
            "is_active": True,
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "type": "crypto",
            "coingecko_id": "ethereum",
            "is_active": True,
        },
        {
            "symbol": "BNB",
            "name": "BNB",
            "type": "crypto",
            "coingecko_id": "binancecoin",
            "is_active": True,
        },
        {
            "symbol": "SOL",
            "name": "Solana",
            "type": "crypto",
            "coingecko_id": "solana",
            "is_active": True,
        },
        {
            "symbol": "XRP",
            "name": "XRP",
            "type": "crypto",
            "coingecko_id": "ripple",
            "is_active": True,
        },
        {
            "symbol": "ADA",
            "name": "Cardano",
            "type": "crypto",
            "coingecko_id": "cardano",
            "is_active": True,
        },
        {
            "symbol": "DOGE",
            "name": "Dogecoin",
            "type": "crypto",
            "coingecko_id": "dogecoin",
            "is_active": True,
        },
        {
            "symbol": "DOT",
            "name": "Polkadot",
            "type": "crypto",
            "coingecko_id": "polkadot",
            "is_active": True,
        },
        {
            "symbol": "MATIC",
            "name": "Polygon",
            "type": "crypto",
            "coingecko_id": "matic-network",
            "is_active": True,
        },
        {
            "symbol": "AVAX",
            "name": "Avalanche",
            "type": "crypto",
            "coingecko_id": "avalanche-2",
            "is_active": True,
        },
        {
            "symbol": "LINK",
            "name": "Chainlink",
            "type": "crypto",
            "coingecko_id": "chainlink",
            "is_active": True,
        },
        {
            "symbol": "UNI",
            "name": "Uniswap",
            "type": "crypto",
            "coingecko_id": "uniswap",
            "is_active": True,
        },
        {
            "symbol": "USDT",
            "name": "Tether",
            "type": "crypto",
            "coingecko_id": "tether",
            "is_active": True,
        },
        {
            "symbol": "USDC",
            "name": "USD Coin",
            "type": "crypto",
            "coingecko_id": "usd-coin",
            "is_active": True,
        },
        {
            "symbol": "BUSD",
            "name": "Binance USD",
            "type": "crypto",
            "coingecko_id": "binance-usd",
            "is_active": True,
        },
    ]

    with get_db_session() as session:
        repo = CoinRepository(session)
        for coin_data in coins_data:
            repo.upsert_coin(coin_data)
        session.commit()
        print(f"Seeded {len(coins_data)} coins")


def seed_market_pairs():
    """Seed market_pairs table with common trading pairs."""
    pairs_data = [
        # Binance pairs
        {
            "id": "pair_binance_btc_usdt",
            "exchange_id": "binance",
            "base_coin_id": "BTC",
            "quote_coin_id": "USDT",
            "symbol": "BTC/USDT",
            "min_tick_size": Decimal("0.01"),
            "min_lot_size": Decimal("0.00001"),
            "is_active": True,
            "is_trading": True,
        },
        {
            "id": "pair_binance_eth_usdt",
            "exchange_id": "binance",
            "base_coin_id": "ETH",
            "quote_coin_id": "USDT",
            "symbol": "ETH/USDT",
            "min_tick_size": Decimal("0.01"),
            "min_lot_size": Decimal("0.0001"),
            "is_active": True,
            "is_trading": True,
        },
        {
            "id": "pair_binance_sol_usdt",
            "exchange_id": "binance",
            "base_coin_id": "SOL",
            "quote_coin_id": "USDT",
            "symbol": "SOL/USDT",
            "min_tick_size": Decimal("0.001"),
            "min_lot_size": Decimal("0.01"),
            "is_active": True,
            "is_trading": True,
        },
        {
            "id": "pair_binance_bnb_usdt",
            "exchange_id": "binance",
            "base_coin_id": "BNB",
            "quote_coin_id": "USDT",
            "symbol": "BNB/USDT",
            "min_tick_size": Decimal("0.001"),
            "min_lot_size": Decimal("0.01"),
            "is_active": True,
            "is_trading": True,
        },
        # Uniswap pairs
        {
            "id": "pair_uniswap_eth_usdc",
            "exchange_id": "uniswap_v3",
            "base_coin_id": "ETH",
            "quote_coin_id": "USDC",
            "symbol": "ETH/USDC",
            "min_tick_size": Decimal("0.000001"),
            "min_lot_size": Decimal("0.000000000000000001"),
            "is_active": True,
            "is_trading": True,
        },
        {
            "id": "pair_uniswap_wbtc_eth",
            "exchange_id": "uniswap_v3",
            "base_coin_id": "BTC",
            "quote_coin_id": "ETH",
            "symbol": "BTC/ETH",
            "min_tick_size": Decimal("0.000000001"),
            "min_lot_size": Decimal("0.000000000000000001"),
            "is_active": True,
            "is_trading": True,
        },
    ]

    with get_db_session() as session:
        repo = MarketPairRepository(session)
        for pair_data in pairs_data:
            repo.upsert_pair(pair_data)
        session.commit()
        print(f"Seeded {len(pairs_data)} market pairs")


def seed_all():
    """Seed all market metadata."""
    print("Seeding market metadata...")
    seed_exchanges()
    seed_coins()
    seed_market_pairs()
    print("Market metadata seeding complete!")


if __name__ == "__main__":
    seed_all()
