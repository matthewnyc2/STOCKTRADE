"""
Seed data for user-created strategies.

This module provides sample strategies that can be loaded into the database
for testing and demonstration purposes.
"""

from datetime import datetime
from uuid import uuid4

from database.connection import get_db_context
from database.repositories import StrategyRepository, StrategyLayerRepository


def seed_user_strategies() -> None:
    """
    Seed sample user-created strategies into the database.

    Creates a variety of strategies with different configurations,
    parameters, and statuses for testing and demonstration.
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Check if strategies already exist
        if strategy_repo.count() > 0:
            print("Strategies already exist, skipping seed.")
            return

        # Strategy 1: Simple RSI Mean Reversion
        strat1_id = f"strat_{uuid4().hex[:12]}"
        layer1_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat1_id,
            name="RSI Mean Reversion",
            description="Simple mean reversion strategy using RSI indicator. Buys when RSI is oversold and sells when overbought.",
            type="composed",
            parameters={
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70,
                "position_size": 0.1,
            },
            layers=[layer1_id],
            status="active",
            is_template=False,
        )
        layer_repo.create(
            id=layer1_id,
            strategy_id=strat1_id,
            layer_order=0,
            weight=1.0,
            config={
                "type": "rsi_signal",
                "period": 14,
                "thresholds": {"low": 30, "high": 70},
            },
        )

        # Strategy 2: Dual SMA Crossover
        strat2_id = f"strat_{uuid4().hex[:12]}"
        layer2a_id = f"layer_{uuid4().hex[:12]}"
        layer2b_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat2_id,
            name="Dual SMA Crossover",
            description="Classic moving average crossover strategy. Uses fast and slow SMAs to generate buy/sell signals.",
            type="composed",
            parameters={
                "fast_period": 10,
                "slow_period": 30,
                "position_size": 0.15,
            },
            layers=[layer2a_id, layer2b_id],
            status="active",
            is_template=False,
        )
        layer_repo.create(
            id=layer2a_id,
            strategy_id=strat2_id,
            layer_order=0,
            weight=0.5,
            config={"type": "sma_signal", "period": 10},
        )
        layer_repo.create(
            id=layer2b_id,
            strategy_id=strat2_id,
            layer_order=1,
            weight=0.5,
            config={"type": "sma_signal", "period": 30},
        )

        # Strategy 3: MACD Momentum (Draft)
        strat3_id = f"strat_{uuid4().hex[:12]}"
        layer3_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat3_id,
            name="MACD Momentum Strategy",
            description="Momentum-based strategy using MACD indicator for trend following.",
            type="composed",
            parameters={
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "position_size": 0.2,
            },
            layers=[layer3_id],
            status="draft",
            is_template=False,
        )
        layer_repo.create(
            id=layer3_id,
            strategy_id=strat3_id,
            layer_order=0,
            weight=1.0,
            config={
                "type": "macd_signal",
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
        )

        # Strategy 4: Bollinger Band Breakout (Inactive)
        strat4_id = f"strat_{uuid4().hex[:12]}"
        layer4_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat4_id,
            name="Bollinger Band Breakout",
            description="Volatility breakout strategy using Bollinger Bands. Trades breakouts from the bands.",
            type="composed",
            parameters={
                "bb_period": 20,
                "bb_std": 2,
                "position_size": 0.1,
            },
            layers=[layer4_id],
            status="inactive",
            is_template=False,
        )
        layer_repo.create(
            id=layer4_id,
            strategy_id=strat4_id,
            layer_order=0,
            weight=1.0,
            config={
                "type": "bollinger_signal",
                "period": 20,
                "std_dev": 2,
            },
        )

        # Strategy 5: Multi-Layer Combined (Active)
        strat5_id = f"strat_{uuid4().hex[:12]}"
        layer5a_id = f"layer_{uuid4().hex[:12]}"
        layer5b_id = f"layer_{uuid4().hex[:12]}"
        layer5c_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat5_id,
            name="Multi-Indicator Fusion",
            description="Combines RSI, MACD, and SMA signals for more robust trading decisions.",
            type="composed",
            parameters={
                "rsi_weight": 0.3,
                "macd_weight": 0.4,
                "sma_weight": 0.3,
                "min_signals": 2,
            },
            layers=[layer5a_id, layer5b_id, layer5c_id],
            status="active",
            is_template=False,
        )
        layer_repo.create(
            id=layer5a_id,
            strategy_id=strat5_id,
            layer_order=0,
            weight=0.3,
            config={"type": "rsi_signal", "period": 14},
        )
        layer_repo.create(
            id=layer5b_id,
            strategy_id=strat5_id,
            layer_order=1,
            weight=0.4,
            config={"type": "macd_signal", "fast_period": 12, "slow_period": 26},
        )
        layer_repo.create(
            id=layer5c_id,
            strategy_id=strat5_id,
            layer_order=2,
            weight=0.3,
            config={"type": "sma_signal", "period": 20},
        )

        # Strategy 6: Stochastic Oscillator (Draft)
        strat6_id = f"strat_{uuid4().hex[:12]}"
        layer6_id = f"layer_{uuid4().hex[:12]}"
        strategy_repo.create(
            id=strat6_id,
            name="Stochastic Strategy",
            description="Uses stochastic oscillator to identify overbought and oversold conditions.",
            type="composed",
            parameters={
                "k_period": 14,
                "d_period": 3,
                "oversold": 20,
                "overbought": 80,
            },
            layers=[layer6_id],
            status="draft",
            is_template=False,
        )
        layer_repo.create(
            id=layer6_id,
            strategy_id=strat6_id,
            layer_order=0,
            weight=1.0,
            config={
                "type": "stochastic_signal",
                "k_period": 14,
                "d_period": 3,
            },
        )

        print(f"Seeded {6} user-created strategies.")


if __name__ == "__main__":
    seed_user_strategies()
