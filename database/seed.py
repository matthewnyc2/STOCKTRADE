"""
Seed data for Crypto Quant Laboratory.

Populates the database with template strategies and test data.
"""

from decimal import Decimal
from datetime import datetime, timedelta

from database.connection import get_db_session
from database.repositories import (
    StrategyRepository,
    StrategyLayerRepository,
)


def seed_template_strategies() -> None:
    """
    Create template strategies for testing.

    These strategies can be used as starting points for user-created strategies.
    """
    from uuid import uuid4

    with get_db_session() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Check if templates already exist
        existing = strategy_repo.get_by_type("template")
        if existing:
            print(f"Found {len(existing)} existing template strategies, skipping seed")
            return

        # Template 1: Simple Moving Average Crossover
        sma_id = f"strat_{uuid4().hex[:8]}"
        sma_strategy = strategy_repo.create(
            id=sma_id,
            name="SMA Crossover",
            description="Simple moving average crossover strategy. Generates LONG signals when fast SMA crosses above slow SMA, and SHORT signals when it crosses below.",
            type="template",
            parameters={
                "fast_period": 10,
                "slow_period": 30,
                "signal_threshold": 0.02,
            },
            layers=[],
            status="inactive",
            # Game Mode metadata
            game_mode_display_name="Wave Rider",
            game_mode_stars=2,
            game_mode_flavor_text="Surf the waves of market trends",
            game_mode_emoji="🌊",
            # Pro Mode metadata
            pro_mode_technical_name="SMA_Crossover_v1",
            pro_mode_category="Trend Following",
            pro_mode_complexity="Basic",
            # Backtest metrics (12-month historical performance)
            backtest_total_return=0.089,
            backtest_sharpe_ratio=0.65,
            backtest_max_drawdown=-0.112,
            backtest_win_rate=0.52,
            backtest_profit_factor=1.32,
            backtest_total_trades=98,
            is_template=True,
        )

        # Add layers for SMA strategy
        fast_sma_layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=sma_strategy.id,
            layer_order=0,
            weight=0.5,
            config={
                "type": "sma",
                "period": 10,
                "source": "close",
            },
        )

        slow_sma_layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=sma_strategy.id,
            layer_order=1,
            weight=0.5,
            config={
                "type": "sma",
                "period": 30,
                "source": "close",
            },
        )

        strategy_repo.update(
            sma_strategy.id,
            layers=[fast_sma_layer.id, slow_sma_layer.id],
        )

        # Template 2: RSI Mean Reversion
        rsi_id = f"strat_{uuid4().hex[:8]}"
        rsi_strategy = strategy_repo.create(
            id=rsi_id,
            name="RSI Mean Reversion",
            description="RSI-based mean reversion strategy. Generates LONG signals when RSI is oversold (<30) and SHORT signals when overbought (>70).",
            type="template",
            parameters={
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70,
            },
            layers=[],
            status="inactive",
            # Game Mode metadata
            game_mode_display_name="RSI Warrior",
            game_mode_stars=3,
            game_mode_flavor_text="Buys dips, sells rips",
            game_mode_emoji="⚔️",
            # Pro Mode metadata
            pro_mode_technical_name="RSI_MeanReversion_v1",
            pro_mode_category="Mean Reversion",
            pro_mode_complexity="Basic",
            # Backtest metrics
            backtest_total_return=0.124,
            backtest_sharpe_ratio=0.82,
            backtest_max_drawdown=-0.083,
            backtest_win_rate=0.58,
            backtest_profit_factor=1.65,
            backtest_total_trades=127,
            is_template=True,
        )

        rsi_layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=rsi_strategy.id,
            layer_order=0,
            weight=1.0,
            config={
                "type": "rsi",
                "period": 14,
            },
        )

        strategy_repo.update(
            rsi_strategy.id,
            layers=[rsi_layer.id],
        )

        # Template 3: Momentum Breakout
        mom_id = f"strat_{uuid4().hex[:8]}"
        momentum_strategy = strategy_repo.create(
            id=mom_id,
            name="Momentum Breakout",
            description="Momentum-based breakout strategy. Identifies strong directional moves and enters in the direction of the breakout.",
            type="template",
            parameters={
                "lookback_period": 20,
                "breakout_multiplier": 2.0,
                "volume_threshold": 1.5,
            },
            layers=[],
            status="inactive",
            # Game Mode metadata
            game_mode_display_name="Momentum Sniper",
            game_mode_stars=4,
            game_mode_flavor_text="Strike when momentum breaks out",
            game_mode_emoji="🎯",
            # Pro Mode metadata
            pro_mode_technical_name="Momentum_Breakout_v1",
            pro_mode_category="Momentum",
            pro_mode_complexity="Intermediate",
            # Backtest metrics
            backtest_total_return=0.187,
            backtest_sharpe_ratio=1.12,
            backtest_max_drawdown=-0.145,
            backtest_win_rate=0.54,
            backtest_profit_factor=1.89,
            backtest_total_trades=73,
            is_template=True,
        )

        momentum_layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=momentum_strategy.id,
            layer_order=0,
            weight=0.7,
            config={
                "type": "momentum",
                "period": 20,
            },
        )

        volume_layer = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=momentum_strategy.id,
            layer_order=1,
            weight=0.3,
            config={
                "type": "volume_surge",
                "multiplier": 1.5,
            },
        )

        strategy_repo.update(
            momentum_strategy.id,
            layers=[momentum_layer.id, volume_layer.id],
        )

        # Template 4: Multi-Signal Composed
        comp_id = f"strat_{uuid4().hex[:8]}"
        composed_strategy = strategy_repo.create(
            id=comp_id,
            name="Multi-Signal Composed",
            description="Composed strategy combining RSI, MACD, and volume signals for higher confidence trading decisions.",
            type="template",
            parameters={
                "rsi_weight": 0.3,
                "macd_weight": 0.4,
                "volume_weight": 0.3,
                "min_confidence": 0.6,
            },
            layers=[],
            status="inactive",
            # Game Mode metadata
            game_mode_display_name="Triple Threat",
            game_mode_stars=5,
            game_mode_flavor_text="Three signals, one mission: profit",
            game_mode_emoji="🔥",
            # Pro Mode metadata
            pro_mode_technical_name="Multi_Signal_Composed_v1",
            pro_mode_category="Multi-Signal",
            pro_mode_complexity="Advanced",
            # Backtest metrics
            backtest_total_return=0.234,
            backtest_sharpe_ratio=1.45,
            backtest_max_drawdown=-0.098,
            backtest_win_rate=0.62,
            backtest_profit_factor=2.31,
            backtest_total_trades=89,
            is_template=True,
        )

        rsi_filter = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=composed_strategy.id,
            layer_order=0,
            weight=0.3,
            config={
                "type": "rsi",
                "period": 14,
            },
        )

        macd_signal = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=composed_strategy.id,
            layer_order=1,
            weight=0.4,
            config={
                "type": "macd",
                "fast": 12,
                "slow": 26,
                "signal": 9,
            },
        )

        volume_filter = layer_repo.create(
            id=f"layer_{uuid4().hex[:8]}",
            strategy_id=composed_strategy.id,
            layer_order=2,
            weight=0.3,
            config={
                "type": "volume_ma",
                "period": 20,
            },
        )

        strategy_repo.update(
            composed_strategy.id,
            layers=[rsi_filter.id, macd_signal.id, volume_filter.id],
        )

        print(f"Created 4 template strategies:")
        print(f"  - {sma_strategy.game_mode_display_name} ({sma_strategy.pro_mode_technical_name}): {sma_strategy.id}")
        print(f"  - {rsi_strategy.game_mode_display_name} ({rsi_strategy.pro_mode_technical_name}): {rsi_strategy.id}")
        print(f"  - {momentum_strategy.game_mode_display_name} ({momentum_strategy.pro_mode_technical_name}): {momentum_strategy.id}")
        print(f"  - {composed_strategy.game_mode_display_name} ({composed_strategy.pro_mode_technical_name}): {composed_strategy.id}")


def seed_all() -> None:
    """Run all seed operations."""
    print("Seeding database...")
    seed_template_strategies()
    print("Database seeding complete")


if __name__ == "__main__":
    seed_all()
