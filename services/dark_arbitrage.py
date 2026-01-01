"""
Dark Arbitrage Scanner Service.

Detects and evaluates arbitrage opportunities across venues including:
- Oracle latency arbitrage (CEX vs on-chain oracles)
- Funding rate arbitrage (spot vs perpetual futures)
- Cross-venue arbitrage (price differences between exchanges)
- Cross-chain arbitrage (same token, different chains)
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Set

import httpx

from core.websocket import get_websocket_manager
from models.arbitrage import (
    ArbitrageConfig,
    ArbitrageOpportunity,
    ArbitrageStatus,
    ArbitrageSummary,
    ArbitrageType,
    Chain,
    ExchangeVenue,
    FundingRateData,
    OraclePriceData,
    VenuePrice,
)


logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_CONFIG = ArbitrageConfig()


# Fee estimates (as percentage of trade value)
VENUE_FEES: Dict[ExchangeVenue, Decimal] = {
    ExchangeVenue.BINANCE: Decimal("0.001"),  # 0.1% maker
    ExchangeVenue.COINBASE: Decimal("0.005"),  # 0.5%
    ExchangeVenue.KRAKEN: Decimal("0.0026"),  # 0.26% maker
    ExchangeVenue.OKX: Decimal("0.001"),  # 0.1% maker
    ExchangeVenue.BYBIT: Decimal("0.001"),  # 0.1%
    ExchangeVenue.UNISWAP: Decimal("0.003"),  # 0.3%
    ExchangeVenue.SUSHISWAP: Decimal("0.003"),  # 0.3%
    ExchangeVenue.CURVE: Decimal("0.0004"),  # 0.04%
    ExchangeVenue.PANCAKESWAP: Decimal("0.0025"),  # 0.25%
}


# Gas costs by chain (estimated in USD)
CHAIN_GAS_COSTS: Dict[Chain, Decimal] = {
    Chain.ETHEREUM: Decimal("5"),  # Varies significantly
    Chain.BSC: Decimal("0.2"),
    Chain.POLYGON: Decimal("0.01"),
    Chain.ARBITRUM: Decimal("0.5"),
    Chain.OPTIMISM: Decimal("0.5"),
    Chain.SOLANA: Decimal("0.00025"),
}


# Simulated price storage for testing (in production, this would be from live feeds)
_price_cache: Dict[str, Dict[ExchangeVenue, VenuePrice]] = defaultdict(dict)
_funding_rate_cache: Dict[str, Dict[str, FundingRateData]] = defaultdict(dict)
_opportunities_cache: List[ArbitrageOpportunity] = []


async def detect_oracle_arbitrage(
    symbols: List[str],
    config: Optional[ArbitrageConfig] = None,
) -> List[ArbitrageOpportunity]:
    """
    Detect oracle latency arbitrage opportunities.

    Compares CEX prices with on-chain oracle prices to find lag opportunities.
    When oracles lag behind CEX, you can front-run the oracle update.

    Args:
        symbols: List of symbols to check
        config: Arbitrage configuration

    Returns:
        List of detected oracle latency arbitrage opportunities
    """
    config = config or DEFAULT_CONFIG
    opportunities: List[ArbitrageOpportunity] = []

    try:
        # In production, this would query actual on-chain oracles
        # For now, we simulate with mock data
        for symbol in symbols:
            # Get CEX price
            cex_price = await _get_cex_price(symbol)
            if not cex_price:
                continue

            # Simulate oracle data (in production: Chainlink, Pyth, etc.)
            oracle_data = await _get_oracle_price(symbol)
            if not oracle_data:
                continue

            # Calculate price difference
            price_diff_percent = (
                (cex_price - oracle_data.oracle_price) / oracle_data.oracle_price * 100
            )

            # Check if lag is significant enough
            if abs(price_diff_percent) < Decimal("0.1"):
                continue

            # Calculate position size
            position_size_usd = min(config.max_position_size_usd, Decimal("5000"))

            # Determine direction (buy from cheaper, sell to expensive)
            if cex_price > oracle_data.oracle_price:
                # CEX is higher -> Buy on DEX (using oracle price), Sell on CEX
                buy_price = oracle_data.oracle_price
                sell_price = cex_price
                buy_venue = "uniswap_v3"
                sell_venue = "binance"
            else:
                # Oracle is higher -> Buy on CEX, Sell on DEX
                buy_price = cex_price
                sell_price = oracle_data.oracle_price
                buy_venue = "binance"
                sell_venue = "uniswap_v3"

            # Calculate profit
            opportunity = _calculate_profit_potential(
                symbol=symbol,
                arb_type=ArbitrageType.ORACLE_LATENCY,
                buy_price=buy_price,
                sell_price=sell_price,
                buy_venue=buy_venue,
                sell_venue=sell_venue,
                position_size_usd=position_size_usd,
                config=config,
                metadata={
                    "oracle_lag_seconds": oracle_data.lag_seconds,
                    "oracle_address": oracle_data.oracle_address,
                },
            )

            if opportunity and opportunity.profit_percent >= config.min_profit_percent:
                opportunities.append(opportunity)
                logger.info(
                    f"Oracle arb detected: {symbol} - "
                    f"{opportunity.profit_percent:.2f}% profit"
                )

    except Exception as e:
        logger.error(f"Error detecting oracle arbitrage: {e}")

    return opportunities


async def detect_funding_arbitrage(
    symbols: List[str],
    config: Optional[ArbitrageConfig] = None,
) -> List[ArbitrageOpportunity]:
    """
    Detect funding rate arbitrage opportunities.

    When perpetual futures have negative funding, you can earn money by
    holding the opposite position in spot.

    Args:
        symbols: List of symbols to check
        config: Arbitrage configuration

    Returns:
        List of detected funding rate arbitrage opportunities
    """
    config = config or DEFAULT_CONFIG
    opportunities: List[ArbitrageOpportunity] = []

    try:
        for symbol in symbols:
            # Get funding rate data from multiple exchanges
            funding_data = await _get_funding_rates(symbol)
            if not funding_data:
                continue

            for exchange, data in funding_data.items():
                # Look for negative funding rates (you get paid to go long)
                if data.funding_rate >= config.min_funding_rate:
                    continue

                # Annualize funding rate (8 funding periods per day)
                daily_funding = abs(data.funding_rate) * 8
                annual_funding = daily_funding * 365

                # Use mark price for position
                spot_price = data.mark_price

                # Calculate position size
                position_size_usd = min(config.max_position_size_usd, Decimal("10000"))

                # Calculate daily profit from funding
                daily_profit = position_size_usd * daily_funding

                # Account for fees (perp opening + spot trading)
                perp_fee = position_size_usd * Decimal("0.0005")  # 0.05% perp fee
                spot_fee = position_size_usd * Decimal("0.001")  # 0.1% spot fee
                total_fees = perp_fee + spot_fee

                # Net daily profit
                net_daily_profit = daily_profit - total_fees

                if net_daily_profit <= 0:
                    continue

                # Calculate profit percentage (annualized)
                profit_percent = (net_daily_profit / position_size_usd) * 365

                opportunity = ArbitrageOpportunity(
                    type=ArbitrageType.FUNDING_RATE,
                    symbol=symbol,
                    buy_price=spot_price,
                    sell_price=spot_price,  # Same price for delta neutral
                    price_diff_percent=Decimal("0"),
                    buy_venue="spot",
                    sell_venue=f"{exchange}_perpetual",
                    funding_rate=data.funding_rate,
                    exchange=exchange,
                    gross_profit_usd=daily_profit,
                    estimated_fees_usd=total_fees,
                    net_profit_usd=net_daily_profit,
                    profit_percent=Decimal(f"{profit_percent:.4f}"),
                    detected_at=datetime.utcnow(),
                    expires_at=data.next_funding_time,
                    confidence=Decimal("0.85"),
                    metadata={
                        "daily_funding_rate": f"{daily_funding:.4f}",
                        "annual_funding_rate": f"{annual_funding:.4f}",
                        "next_funding_time": data.next_funding_time.isoformat() if data.next_funding_time else None,
                    },
                )

                if opportunity.profit_percent >= config.min_profit_percent:
                    opportunities.append(opportunity)
                    logger.info(
                        f"Funding arb detected: {symbol} on {exchange} - "
                        f"{data.funding_rate:.4f} funding, "
                        f"{opportunity.profit_percent:.2f}% annualized"
                    )

    except Exception as e:
        logger.error(f"Error detecting funding arbitrage: {e}")

    return opportunities


async def detect_cross_venue_arbitrage(
    symbols: List[str],
    config: Optional[ArbitrageConfig] = None,
) -> List[ArbitrageOpportunity]:
    """
    Detect cross-venue arbitrage opportunities.

    Finds price differences between exchanges (CEX and DEX).

    Args:
        symbols: List of symbols to check
        config: Arbitrage configuration

    Returns:
        List of detected cross-venue arbitrage opportunities
    """
    config = config or DEFAULT_CONFIG
    opportunities: List[ArbitrageOpportunity] = []

    try:
        for symbol in symbols:
            # Get prices from all configured venues
            venue_prices = await _get_prices_from_all_venues(symbol)
            if len(venue_prices) < 2:
                continue

            # Compare all pairs of venues
            for i, venue_a in enumerate(venue_prices):
                for venue_b in venue_prices[i + 1 :]:
                    price_a = venue_a.price
                    price_b = venue_b.price

                    # Calculate price difference
                    price_diff_percent = abs(price_a - price_b) / min(price_a, price_b) * 100

                    if price_diff_percent < config.min_profit_percent * 2:  # Need 2x to cover fees
                        continue

                    # Determine direction (buy from cheaper, sell to expensive)
                    if price_a < price_b:
                        buy_price = price_a
                        sell_price = price_b
                        buy_venue = venue_a.venue.value
                        sell_venue = venue_b.venue.value
                    else:
                        buy_price = price_b
                        sell_price = price_a
                        buy_venue = venue_b.venue.value
                        sell_venue = venue_a.venue.value

                    # Calculate position size based on volume
                    min_volume = min(
                        venue_a.volume_24h or Decimal("1000000"),
                        venue_b.volume_24h or Decimal("1000000"),
                    )
                    position_size_usd = min(
                        config.max_position_size_usd,
                        min_volume * Decimal("0.01"),  # Max 1% of volume
                    )

                    # Calculate profit
                    opportunity = _calculate_profit_potential(
                        symbol=symbol,
                        arb_type=ArbitrageType.CROSS_VENUE,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        buy_venue=buy_venue,
                        sell_venue=sell_venue,
                        position_size_usd=position_size_usd,
                        config=config,
                    )

                    if opportunity and opportunity.profit_percent >= config.min_profit_percent:
                        opportunities.append(opportunity)
                        logger.info(
                            f"Cross-venue arb detected: {symbol} - "
                            f"{buy_venue} ({buy_price:.2f}) -> {sell_venue} ({sell_price:.2f}) - "
                            f"{opportunity.profit_percent:.2f}% profit"
                        )

    except Exception as e:
        logger.error(f"Error detecting cross-venue arbitrage: {e}")

    return opportunities


async def detect_cross_chain_arbitrage(
    symbols: List[str],
    config: Optional[ArbitrageConfig] = None,
) -> List[ArbitrageOpportunity]:
    """
    Detect cross-chain arbitrage opportunities.

    Finds price differences for the same token across different chains.

    Args:
        symbols: List of symbols to check
        config: Arbitrage configuration

    Returns:
        List of detected cross-chain arbitrage opportunities
    """
    config = config or DEFAULT_CONFIG
    opportunities: List[ArbitrageOpportunity] = []

    try:
        for symbol in symbols:
            # Get prices from different chains
            chain_prices: Dict[Chain, tuple[Decimal, str]] = {}

            for chain in config.enabled_chains:
                price = await _get_chain_price(symbol, chain)
                if price:
                    chain_prices[chain] = price

            if len(chain_prices) < 2:
                continue

            # Compare all pairs of chains
            chains_list = list(chain_prices.keys())
            for i, chain_a in enumerate(chains_list):
                for chain_b in chains_list[i + 1 :]:
                    price_a, venue_a = chain_prices[chain_a]
                    price_b, venue_b = chain_prices[chain_b]

                    # Calculate price difference
                    price_diff_percent = abs(price_a - price_b) / min(price_a, price_b) * 100

                    # Account for bridging costs (bridge fees + gas)
                    bridge_cost = CHAIN_GAS_COSTS.get(chain_a, Decimal("1")) + CHAIN_GAS_COSTS.get(
                        chain_b, Decimal("1")
                    )
                    bridge_cost_percent = bridge_cost / config.max_position_size_usd * 100

                    effective_profit = price_diff_percent - bridge_cost_percent

                    if effective_profit < config.min_profit_percent:
                        continue

                    # Determine direction
                    if price_a < price_b:
                        buy_price = price_a
                        sell_price = price_b
                        buy_chain = chain_a
                        sell_chain = chain_b
                        buy_venue = venue_a
                        sell_venue = venue_b
                    else:
                        buy_price = price_b
                        sell_price = price_a
                        buy_chain = chain_b
                        sell_chain = chain_a
                        buy_venue = venue_b
                        sell_venue = venue_a

                    position_size_usd = config.max_position_size_usd

                    opportunity = _calculate_profit_potential(
                        symbol=symbol,
                        arb_type=ArbitrageType.CROSS_CHAIN,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        buy_venue=buy_venue,
                        sell_venue=sell_venue,
                        position_size_usd=position_size_usd,
                        config=config,
                        buy_chain=buy_chain,
                        sell_chain=sell_chain,
                        bridge_cost=bridge_cost,
                    )

                    if opportunity and opportunity.profit_percent >= config.min_profit_percent:
                        opportunities.append(opportunity)
                        logger.info(
                            f"Cross-chain arb detected: {symbol} - "
                            f"{buy_chain.value} ({buy_price:.2f}) -> {sell_chain.value} ({sell_price:.2f}) - "
                            f"{opportunity.profit_percent:.2f}% profit"
                        )

    except Exception as e:
        logger.error(f"Error detecting cross-chain arbitrage: {e}")

    return opportunities


def calculate_profit_potential(
    arb_opportunity: ArbitrageOpportunity,
    fees: Optional[Decimal] = None,
    slippage: Optional[Decimal] = None,
) -> Optional[ArbitrageOpportunity]:
    """
    Calculate profit potential for an arbitrage opportunity.

    Args:
        arb_opportunity: The arbitrage opportunity to calculate for
        fees: Override estimated fees
        slippage: Override estimated slippage

    Returns:
        Updated arbitrage opportunity with profit calculations, or None if calculation fails
    """
    config = DEFAULT_CONFIG

    # Use allow_negative=True to always get a result, even if unprofitable
    result = _calculate_profit_potential(
        symbol=arb_opportunity.symbol,
        arb_type=arb_opportunity.type,
        buy_price=arb_opportunity.buy_price,
        sell_price=arb_opportunity.sell_price,
        buy_venue=arb_opportunity.buy_venue,
        sell_venue=arb_opportunity.sell_venue,
        position_size_usd=Decimal("5000"),  # Default position size
        config=config,
        fees=fees,
        slippage=slippage,
        buy_chain=arb_opportunity.buy_chain,
        sell_chain=arb_opportunity.sell_chain,
        allow_negative=True,  # Always return a result for recalculation
    )

    return result


def _calculate_profit_potential(
    symbol: str,
    arb_type: ArbitrageType,
    buy_price: Decimal,
    sell_price: Decimal,
    buy_venue: str,
    sell_venue: str,
    position_size_usd: Decimal,
    config: ArbitrageConfig,
    fees: Optional[Decimal] = None,
    slippage: Optional[Decimal] = None,
    buy_chain: Optional[Chain] = None,
    sell_chain: Optional[Chain] = None,
    bridge_cost: Optional[Decimal] = None,
    metadata: Optional[Dict[str, Any]] = None,
    allow_negative: bool = False,
) -> Optional[ArbitrageOpportunity]:
    """
    Internal helper to calculate profit potential.

    Args:
        symbol: Trading symbol
        arb_type: Type of arbitrage
        buy_price: Price to buy at
        sell_price: Price to sell at
        buy_venue: Venue to buy from
        sell_venue: Venue to sell to
        position_size_usd: Position size in USD
        config: Arbitrage configuration
        fees: Override fees
        slippage: Override slippage
        buy_chain: Buy chain (for cross-chain)
        sell_chain: Sell chain (for cross-chain)
        bridge_cost: Bridge cost (for cross-chain)
        metadata: Additional metadata
        allow_negative: If True, allow negative profit (for recalculation/testing)

    Returns:
        ArbitrageOpportunity or None if not profitable (unless allow_negative=True)
    """
    # Calculate gross profit
    price_diff = sell_price - buy_price
    price_diff_percent = (price_diff / buy_price) * 100

    if price_diff <= 0 and not allow_negative:
        return None

    gross_profit = position_size_usd * (price_diff / buy_price)

    # Calculate fees
    if fees is not None:
        estimated_fees = fees
    else:
        # Estimate fees for each venue
        try:
            buy_fee_rate = VENUE_FEES.get(ExchangeVenue(buy_venue.lower()), Decimal("0.002"))
            sell_fee_rate = VENUE_FEES.get(ExchangeVenue(sell_venue.lower()), Decimal("0.002"))
        except ValueError:
            # If venue not in enum, use default
            buy_fee_rate = Decimal("0.002")
            sell_fee_rate = Decimal("0.002")

        estimated_fees = position_size_usd * (buy_fee_rate + sell_fee_rate)

        # Add gas costs for DEX
        if buy_venue in ["uniswap", "sushiswap", "curve", "pancakeswap", "uniswap_v3"]:
            estimated_fees += CHAIN_GAS_COSTS.get(buy_chain or Chain.ETHEREUM, Decimal("5"))
        if sell_venue in ["uniswap", "sushiswap", "curve", "pancakeswap", "uniswap_v3"]:
            estimated_fees += CHAIN_GAS_COSTS.get(sell_chain or Chain.ETHEREUM, Decimal("5"))

        # Add bridge cost for cross-chain
        if bridge_cost:
            estimated_fees += bridge_cost

    # Estimate slippage (higher for lower liquidity)
    if slippage is not None:
        estimated_slippage = slippage
    else:
        slippage_percent = config.max_slippage_percent
        estimated_slippage = position_size_usd * slippage_percent / 100

    # Calculate net profit
    net_profit = gross_profit - estimated_fees - estimated_slippage
    profit_percent = (net_profit / position_size_usd) * 100

    # Filter out unprofitable opportunities (unless allow_negative)
    if not allow_negative:
        if net_profit <= 0 or profit_percent < config.min_profit_percent:
            return None

    # Calculate confidence based on profit margin
    if profit_percent > 0:
        confidence = min(
            Decimal("0.95"),
            Decimal(str(min(0.5, float(profit_percent) / 5))) + Decimal("0.5")
        )
    else:
        confidence = Decimal("0.3")  # Low confidence for unprofitable

    # Set expiry (arbitrage windows are short)
    expires_at = datetime.utcnow() + timedelta(seconds=30)

    return ArbitrageOpportunity(
        type=arb_type,
        symbol=symbol,
        buy_price=buy_price,
        sell_price=sell_price,
        price_diff_percent=Decimal(f"{price_diff_percent:.4f}"),
        buy_venue=buy_venue,
        sell_venue=sell_venue,
        buy_chain=buy_chain,
        sell_chain=sell_chain,
        gross_profit_usd=gross_profit,
        estimated_fees_usd=estimated_fees,
        estimated_slippage_usd=estimated_slippage,
        net_profit_usd=net_profit,
        profit_percent=Decimal(f"{profit_percent:.4f}"),
        detected_at=datetime.utcnow(),
        expires_at=expires_at,
        execution_time_seconds=10.0,  # Estimated execution time
        confidence=Decimal(f"{confidence:.2f}"),
        metadata=metadata or {},
    )


async def scan_all_arbitrage(
    symbols: Optional[List[str]] = None,
    config: Optional[ArbitrageConfig] = None,
) -> List[ArbitrageOpportunity]:
    """
    Scan for all types of arbitrage opportunities.

    Args:
        symbols: List of symbols to scan (default: BTC, ETH, SOL)
        config: Arbitrage configuration

    Returns:
        List of all detected arbitrage opportunities
    """
    symbols = symbols or ["BTC", "ETH", "SOL", "LINK", "AVAX"]
    config = config or DEFAULT_CONFIG

    logger.info(f"Starting arbitrage scan for {len(symbols)} symbols")

    # Run all detection methods in parallel
    results = await asyncio.gather(
        detect_oracle_arbitrage(symbols, config),
        detect_funding_arbitrage(symbols, config),
        detect_cross_venue_arbitrage(symbols, config),
        detect_cross_chain_arbitrage(symbols, config),
        return_exceptions=True,
    )

    all_opportunities: List[ArbitrageOpportunity] = []

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Arbitrage detection error: {result}")
        elif isinstance(result, list):
            all_opportunities.extend(result)

    # Update global cache
    global _opportunities_cache
    _opportunities_cache = all_opportunities

    # Broadcast to WebSocket
    if all_opportunities:
        ws_manager = get_websocket_manager()
        await ws_manager.broadcast(
            "arbitrage",
            {
                "action": "opportunities_detected",
                "count": len(all_opportunities),
                "opportunities": [arb.model_dump(mode="json") for arb in all_opportunities[:10]],
            }
        )

    logger.info(f"Arbitrage scan complete: {len(all_opportunities)} opportunities found")

    return all_opportunities


def get_arbitrage_summary(opportunities: Optional[List[ArbitrageOpportunity]] = None) -> ArbitrageSummary:
    """
    Get a summary of arbitrage opportunities.

    Args:
        opportunities: List of opportunities (default: use cached)

    Returns:
        ArbitrageSummary with aggregated statistics
    """
    if opportunities is None:
        opportunities = _opportunities_cache

    # Filter active opportunities
    active = [o for o in opportunities if o.status == ArbitrageStatus.DETECTED]
    profitable = [o for o in active if o.net_profit_usd > 0]

    # Count by type
    by_type: Dict[str, int] = defaultdict(int)
    for o in active:
        by_type[o.type.value] += 1

    # Count by symbol
    by_symbol: Dict[str, int] = defaultdict(int)
    for o in active:
        by_symbol[o.symbol] += 1

    # Calculate statistics
    if profitable:
        avg_profit = sum(o.profit_percent for o in profitable) / len(profitable)
        max_profit = max(o.profit_percent for o in profitable)
    else:
        avg_profit = Decimal("0")
        max_profit = Decimal("0")

    return ArbitrageSummary(
        total_opportunities=len(opportunities),
        active_opportunities=len(active),
        profitable_opportunities=len(profitable),
        by_type=dict(by_type),
        by_symbol=dict(by_symbol),
        avg_profit_percent=Decimal(f"{avg_profit:.4f}"),
        max_profit_percent=Decimal(f"{max_profit:.4f}"),
        total_executed=0,
        successful_executions=0,
        total_profit_usd=Decimal("0"),
    )


async def _get_cex_price(symbol: str) -> Optional[Decimal]:
    """Get current CEX price for a symbol."""
    try:
        from services.market_data import get_current_price

        # Try to get from market data service
        data = await get_current_price(symbol)
        if data and data.get("price"):
            return data["price"]

        # Fallback to simulated data
        base_prices = {
            "BTC": Decimal("45000"),
            "ETH": Decimal("2500"),
            "SOL": Decimal("100"),
            "LINK": Decimal("15"),
            "AVAX": Decimal("40"),
        }

        # Add small random variation
        import random
        random.seed(int(datetime.utcnow().timestamp() / 60))  # Change per minute
        variation = Decimal(str(random.uniform(-0.002, 0.002)))  # +/- 0.2%

        return base_prices.get(symbol.upper(), Decimal("100")) * (1 + variation)

    except Exception as e:
        logger.error(f"Error getting CEX price for {symbol}: {e}")
        return None


async def _get_oracle_price(symbol: str) -> Optional[OraclePriceData]:
    """Get oracle price data (simulated)."""
    try:
        cex_price = await _get_cex_price(symbol)
        if not cex_price:
            return None

        # Simulate oracle lag (0-60 seconds)
        import random
        random.seed(int(datetime.utcnow().timestamp()))
        lag_seconds = random.uniform(0, 60)

        # Oracle price may be slightly stale
        oracle_price = cex_price * Decimal(str(random.uniform(0.998, 1.002)))

        return OraclePriceData(
            symbol=symbol,
            oracle_address=f"0x{'0'*40}",  # Placeholder
            oracle_price=oracle_price,
            oracle_timestamp=datetime.utcnow() - timedelta(seconds=lag_seconds),
            cex_price=cex_price,
            cex_timestamp=datetime.utcnow(),
            price_diff_percent=Decimal(f"{abs(cex_price - oracle_price) / oracle_price * 100:.4f}"),
            lag_seconds=lag_seconds,
        )

    except Exception as e:
        logger.error(f"Error getting oracle price for {symbol}: {e}")
        return None


async def _get_funding_rates(symbol: str) -> Optional[Dict[str, FundingRateData]]:
    """Get funding rates from exchanges (simulated)."""
    try:
        import random
        random.seed(int(datetime.utcnow().timestamp() / 3600))  # Change per hour

        cex_price = await _get_cex_price(symbol)
        if not cex_price:
            return None

        exchanges = ["binance", "bybit", "okx"]
        funding_data: Dict[str, FundingRateData] = {}

        for exchange in exchanges:
            # Simulate funding rate (-0.05% to +0.05% per 8 hours)
            funding_rate = Decimal(str(random.uniform(-0.0005, 0.0005)))

            funding_data[exchange] = FundingRateData(
                symbol=symbol,
                exchange=exchange,
                funding_rate=funding_rate,
                predicted_funding_rate=Decimal(str(random.uniform(-0.0005, 0.0005))),
                mark_price=cex_price,
                index_price=cex_price * Decimal(str(random.uniform(0.999, 1.001))),
                next_funding_time=datetime.utcnow() + timedelta(hours=1),
            )

        return funding_data

    except Exception as e:
        logger.error(f"Error getting funding rates for {symbol}: {e}")
        return None


async def _get_prices_from_all_venues(symbol: str) -> List[VenuePrice]:
    """Get prices from all configured venues (simulated)."""
    try:
        import random
        random.seed(int(datetime.utcnow().timestamp() / 10))  # Change every 10 seconds

        cex_price = await _get_cex_price(symbol)
        if not cex_price:
            return []

        venues: List[VenuePrice] = []

        # CEX venues
        for venue in [ExchangeVenue.BINANCE, ExchangeVenue.COINBASE, ExchangeVenue.BYBIT]:
            price_variation = Decimal(str(random.uniform(-0.001, 0.001)))  # +/- 0.1%
            venue_price = cex_price * (1 + price_variation)

            venues.append(
                VenuePrice(
                    venue=venue,
                    symbol=symbol,
                    price=venue_price,
                    volume_24h=Decimal(str(random.uniform(1000000, 10000000))),
                    is_dex=False,
                )
            )

        # DEX venues
        for venue in [ExchangeVenue.UNISWAP, ExchangeVenue.SUSHISWAP]:
            price_variation = Decimal(str(random.uniform(-0.002, 0.002)))  # +/- 0.2%
            venue_price = cex_price * (1 + price_variation)

            venues.append(
                VenuePrice(
                    venue=venue,
                    symbol=symbol,
                    price=venue_price,
                    volume_24h=Decimal(str(random.uniform(100000, 1000000))),
                    is_dex=True,
                    chain=Chain.ETHEREUM,
                )
            )

        return venues

    except Exception as e:
        logger.error(f"Error getting prices from venues for {symbol}: {e}")
        return []


async def _get_chain_price(symbol: str, chain: Chain) -> Optional[tuple[Decimal, str]]:
    """Get price on a specific chain (simulated)."""
    try:
        import random
        random.seed(int(datetime.utcnow().timestamp() / 15))

        cex_price = await _get_cex_price(symbol)
        if not cex_price:
            return None

        # Different chains may have different prices due to liquidity differences
        chain_multipliers = {
            Chain.ETHEREUM: 1.0,
            Chain.BSC: 0.998,
            Chain.POLYGON: 0.997,
            Chain.ARBITRUM: 0.999,
            Chain.OPTIMISM: 0.999,
        }

        multiplier = chain_multipliers.get(chain, 1.0)
        variation = Decimal(str(random.uniform(-0.001, 0.001)))
        chain_price = cex_price * Decimal(str(multiplier)) * (1 + variation)

        venues = {
            Chain.ETHEREUM: "uniswap_v3",
            Chain.BSC: "pancakeswap",
            Chain.POLYGON: "uniswap_v3",
            Chain.ARBITRUM: "uniswap_v3",
            Chain.OPTIMISM: "uniswap_v3",
        }

        return (chain_price, venues.get(chain, "uniswap_v3"))

    except Exception as e:
        logger.error(f"Error getting chain price for {symbol} on {chain}: {e}")
        return None


def get_cached_opportunities() -> List[ArbitrageOpportunity]:
    """Get cached arbitrage opportunities."""
    return _opportunities_cache.copy()


def clear_expired_opportunities() -> None:
    """Remove expired opportunities from cache."""
    global _opportunities_cache

    now = datetime.utcnow()
    _opportunities_cache = [
        o for o in _opportunities_cache
        if o.expires_at is None or o.expires_at > now
    ]


async def start_continuous_scanning(
    interval_seconds: int = 10,
    symbols: Optional[List[str]] = None,
    config: Optional[ArbitrageConfig] = None,
) -> None:
    """
    Start continuous arbitrage scanning in the background.

    Args:
        interval_seconds: Scan interval
        symbols: Symbols to scan
        config: Arbitrage configuration
    """
    while True:
        try:
            # Clear expired opportunities
            clear_expired_opportunities()

            # Scan for new opportunities
            await scan_all_arbitrage(symbols, config)

        except Exception as e:
            logger.error(f"Error in continuous scanning: {e}")

        await asyncio.sleep(interval_seconds)
