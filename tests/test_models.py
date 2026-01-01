"""
Tests for all Pydantic models.

Tests validate model creation, validation, serialization, and enum handling.
"""

import json
from datetime import datetime
from decimal import Decimal

import pytest

from models.backtest import BacktestResult, EquityPoint, Trade
from models.ml import MLModel, ModelStatus, ModelType
from models.portfolio import Portfolio, PortfolioMetrics, Position
from models.settings import Settings, UIMode
from models.signal import LayerSignal, Signal, SignalType
from models.strategy import Strategy, StrategyLayer, StrategyType, Status
from models.whale import (
    Whale,
    WhaleActivity,
    WhaleAction,
    WhaleConstellation,
    WhaleConstellationType,
    PatternType,
    WhaleTier,
)


class TestStrategyModels:
    """Test Strategy and StrategyLayer models."""

    def test_strategy_minimal_creation(self):
        """Test creating a strategy with minimal required fields."""
        strategy = Strategy(
            name="Test Strategy",
            type=StrategyType.COMPOSED,
        )
        assert strategy.name == "Test Strategy"
        assert strategy.type == StrategyType.COMPOSED
        assert strategy.status == Status.DRAFT

    def test_strategy_full_creation(self):
        """Test creating a strategy with all fields."""
        now = datetime.now()
        strategy = Strategy(
            id="strat_123",
            name="Test Strategy",
            description="A test strategy",
            type=StrategyType.ML,
            parameters={"lookback": 20, "threshold": 0.5},
            layers=["layer_1", "layer_2"],
            status=Status.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert strategy.id == "strat_123"
        assert strategy.description == "A test strategy"
        assert strategy.parameters["lookback"] == 20
        assert len(strategy.layers) == 2

    def test_strategy_type_enum(self):
        """Test StrategyType enum values."""
        assert StrategyType.COMPOSED.value == "composed"
        assert StrategyType.GENETIC.value == "genetic"
        assert StrategyType.ML.value == "ml"
        assert StrategyType.TEMPLATE.value == "template"

    def test_status_enum(self):
        """Test Status enum values."""
        assert Status.ACTIVE.value == "active"
        assert Status.INACTIVE.value == "inactive"
        assert Status.DRAFT.value == "draft"

    def test_strategy_layer_creation(self):
        """Test StrategyLayer model."""
        layer = StrategyLayer(
            id="layer_1",
            strategy_id="strat_123",
            layer_order=1,
            weight=0.5,
            config={"indicator": "RSI", "period": 14},
        )
        assert layer.id == "layer_1"
        assert layer.layer_order == 1
        assert layer.weight == 0.5


class TestSignalModels:
    """Test Signal and LayerSignal models."""

    def test_signal_creation(self):
        """Test Signal model creation."""
        now = datetime.now()
        signal = Signal(
            id="sig_123",
            strategy_id="strat_123",
            symbol="BTC/USDT",
            signal_type=SignalType.LONG,
            confidence=0.85,
            price=Decimal("45000.50"),
            timestamp=now,
            reasoning="Strong bullish momentum",
            layer_breakdown=[
                {"layer_id": "layer_1", "signal": "LONG", "weight": 0.6},
                {"layer_id": "layer_2", "signal": "NEUTRAL", "weight": 0.4},
            ],
        )
        assert signal.id == "sig_123"
        assert signal.symbol == "BTC/USDT"
        assert signal.signal_type == SignalType.LONG
        assert signal.confidence == 0.85
        assert signal.price == Decimal("45000.50")

    def test_signal_type_enum(self):
        """Test SignalType enum values."""
        assert SignalType.LONG.value == "long"
        assert SignalType.SHORT.value == "short"
        assert SignalType.CLOSE.value == "close"
        assert SignalType.NEUTRAL.value == "neutral"

    def test_layer_signal_creation(self):
        """Test LayerSignal model."""
        layer_signal = LayerSignal(
            layer_id="layer_1",
            signal_type=SignalType.LONG,
            confidence=0.9,
            weight=0.5,
            reasoning="RSI oversold",
        )
        assert layer_signal.layer_id == "layer_1"
        assert layer_signal.confidence == 0.9


class TestBacktestModels:
    """Test BacktestResult, EquityPoint, and Trade models."""

    def test_backtest_result_creation(self):
        """Test BacktestResult model."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        backtest = BacktestResult(
            id="bt_123",
            strategy_id="strat_123",
            start_date=start,
            end_date=end,
            initial_capital=Decimal("100000.00"),
            final_capital=Decimal("125000.00"),
            total_return=Decimal("0.25"),
            sharpe_ratio=Decimal("1.5"),
            sortino_ratio=Decimal("2.0"),
            max_drawdown=Decimal("-0.15"),
            win_rate=Decimal("0.6"),
            profit_factor=Decimal("1.8"),
            total_trades=100,
            equity_curve=[
                EquityPoint(timestamp=start, equity=Decimal("100000.00"), drawdown=Decimal("0.0"))
            ],
            trades=[],
        )
        assert backtest.id == "bt_123"
        assert backtest.total_return == Decimal("0.25")
        assert backtest.sharpe_ratio == Decimal("1.5")

    def test_equity_point_creation(self):
        """Test EquityPoint model."""
        now = datetime.now()
        point = EquityPoint(
            timestamp=now,
            equity=Decimal("105000.00"),
            drawdown=Decimal("-0.02"),
        )
        assert point.equity == Decimal("105000.00")
        assert point.drawdown == Decimal("-0.02")

    def test_trade_creation(self):
        """Test Trade model."""
        entry = datetime(2024, 6, 1)
        exit_date = datetime(2024, 6, 15)
        trade = Trade(
            id="trade_123",
            symbol="ETH/USDT",
            entry_date=entry,
            exit_date=exit_date,
            entry_price=Decimal("3000.00"),
            exit_price=Decimal("3200.00"),
            quantity=Decimal("10.0"),
            side="LONG",
            pnl=Decimal("200.00"),
            pnl_percent=Decimal("0.0667"),
            exit_reason="TAKE_PROFIT",
        )
        assert trade.id == "trade_123"
        assert trade.side == "LONG"
        assert trade.pnl == Decimal("200.00")


class TestPortfolioModels:
    """Test Portfolio, Position, and PortfolioMetrics models."""

    def test_portfolio_creation(self):
        """Test Portfolio model."""
        portfolio = Portfolio(
            total_equity=Decimal("150000.00"),
            starting_balance=Decimal("100000.00"),
            total_pnl=Decimal("50000.00"),
            total_pnl_percent=Decimal("0.50"),
            open_pnl=Decimal("5000.00"),
            positions=[],
            metrics=PortfolioMetrics(
                sharpe_ratio=Decimal("1.8"),
                sortino_ratio=Decimal("2.2"),
                max_drawdown=Decimal("-0.12"),
                win_rate=Decimal("0.65"),
                profit_factor=Decimal("2.0"),
            ),
        )
        assert portfolio.total_equity == Decimal("150000.00")
        assert portfolio.total_pnl_percent == Decimal("0.50")

    def test_position_creation(self):
        """Test Position model."""
        now = datetime.now()
        position = Position(
            id="pos_123",
            symbol="BTC/USDT",
            side="LONG",
            quantity=Decimal("1.5"),
            entry_price=Decimal("45000.00"),
            current_price=Decimal("46000.00"),
            unrealized_pnl=Decimal("1500.00"),
            unrealized_pnl_percent=Decimal("0.022"),
            stop_loss=Decimal("44000.00"),
            take_profit=Decimal("48000.00"),
            entry_timestamp=now,
        )
        assert position.id == "pos_123"
        assert position.side == "LONG"
        assert position.unrealized_pnl == Decimal("1500.00")

    def test_portfolio_metrics_creation(self):
        """Test PortfolioMetrics model."""
        metrics = PortfolioMetrics(
            sharpe_ratio=Decimal("2.0"),
            sortino_ratio=Decimal("2.5"),
            max_drawdown=Decimal("-0.10"),
            win_rate=Decimal("0.70"),
            profit_factor=Decimal("2.5"),
        )
        assert metrics.sharpe_ratio == Decimal("2.0")
        assert metrics.win_rate == Decimal("0.70")


class TestWhaleModels:
    """Test Whale, WhaleActivity, and WhaleConstellation models."""

    def test_whale_creation(self):
        """Test Whale model."""
        now = datetime.now()
        whale = Whale(
            address="0x1234567890abcdef",
            label="Known Accumulator",
            tier=WhaleTier.MEGA,
            holdings_usd=Decimal("50000000.00"),
            holdings_24h_change=Decimal("0.05"),
            historical_accuracy=Decimal("0.75"),
            pattern_type=PatternType.ACCUMULATOR,
            last_activity=now,
            preferred_tokens=["BTC", "ETH"],
        )
        assert whale.address == "0x1234567890abcdef"
        assert whale.tier == WhaleTier.MEGA
        assert whale.pattern_type == PatternType.ACCUMULATOR

    def test_whale_tier_enum(self):
        """Test WhaleTier enum values."""
        assert WhaleTier.MEGA.value == "mega"
        assert WhaleTier.LARGE.value == "large"
        assert WhaleTier.SMART_MONEY.value == "smart_money"

    def test_pattern_type_enum(self):
        """Test PatternType enum values."""
        assert PatternType.ACCUMULATOR.value == "accumulator"
        assert PatternType.SNIPER.value == "sniper"
        assert PatternType.DISTRIBUTOR.value == "distributor"
        assert PatternType.MANIPULATOR.value == "manipulator"

    def test_whale_activity_creation(self):
        """Test WhaleActivity model."""
        now = datetime.now()
        activity = WhaleActivity(
            id="act_123",
            whale_address="0x1234567890abcdef",
            symbol="BTC/USDT",
            action=WhaleAction.BOUGHT,
            amount_usd=Decimal("1000000.00"),
            timestamp=now,
            transaction_hash="0xabcdef123456",
        )
        assert activity.id == "act_123"
        assert activity.action == WhaleAction.BOUGHT
        assert activity.amount_usd == Decimal("1000000.00")

    def test_whale_action_enum(self):
        """Test WhaleAction enum values."""
        assert WhaleAction.BOUGHT.value == "bought"
        assert WhaleAction.SOLD.value == "sold"
        assert WhaleAction.TRANSFERRED.value == "transferred"

    def test_whale_constellation_creation(self):
        """Test WhaleConstellation model."""
        now = datetime.now()
        constellation = WhaleConstellation(
            id="const_123",
            type=WhaleConstellationType.TEMPORAL,
            symbol="BTC/USDT",
            whale_addresses=["0x123", "0x456"],
            confidence=Decimal("0.90"),
            detected_at=now,
        )
        assert constellation.id == "const_123"
        assert constellation.type == WhaleConstellationType.TEMPORAL

    def test_constellation_type_enum(self):
        """Test WhaleConstellationType enum values."""
        assert WhaleConstellationType.TEMPORAL.value == "temporal"
        assert WhaleConstellationType.WALLET_NETWORK.value == "wallet_network"
        assert WhaleConstellationType.CROSS_CHAIN.value == "cross_chain"
        assert WhaleConstellationType.SMART_MONEY.value == "smart_money"


class TestMLModels:
    """Test MLModel model."""

    def test_ml_model_creation(self):
        """Test MLModel model creation."""
        now = datetime.now()
        model = MLModel(
            id="ml_123",
            name="Price Predictor",
            model_type=ModelType.LSTM,
            features=["RSI", "MACD", "volume", "price_change"],
            training_start=datetime(2023, 1, 1),
            training_end=datetime(2024, 1, 1),
            accuracy=Decimal("0.85"),
            created_at=now,
            status=ModelStatus.DEPLOYED,
        )
        assert model.id == "ml_123"
        assert model.model_type == ModelType.LSTM
        assert model.accuracy == Decimal("0.85")

    def test_model_type_enum(self):
        """Test ModelType enum values."""
        assert ModelType.LSTM.value == "lstm"
        assert ModelType.TRANSFORMER.value == "transformer"
        assert ModelType.XGBOOST.value == "xgboost"
        assert ModelType.ENSEMBLE.value == "ensemble"

    def test_model_status_enum(self):
        """Test ModelStatus enum values."""
        assert ModelStatus.TRAINING.value == "training"
        assert ModelStatus.READY.value == "ready"
        assert ModelStatus.DEPLOYED.value == "deployed"
        assert ModelStatus.FAILED.value == "failed"


class TestSettingsModels:
    """Test Settings model."""

    def test_settings_creation(self):
        """Test Settings model creation."""
        settings = Settings(
            ui_mode=UIMode.PRO,
            risk_parameters={
                "max_position_size": 0.1,
                "max_daily_loss": 0.05,
                "stop_loss_enabled": True,
            },
            notifications={
                "email_enabled": False,
                "slack_enabled": True,
                "alert_types": ["SIGNAL", "TRADE"],
            },
        )
        assert settings.ui_mode == UIMode.PRO
        assert settings.risk_parameters.max_position_size == 0.1

    def test_ui_mode_enum(self):
        """Test UIMode enum values."""
        assert UIMode.GAME.value == "game"
        assert UIMode.PRO.value == "pro"


class TestModelSerialization:
    """Test model serialization to JSON."""

    def test_strategy_serialization(self):
        """Test Strategy model serialization."""
        strategy = Strategy(
            id="strat_123",
            name="Test Strategy",
            type=StrategyType.COMPOSED,
            status=Status.ACTIVE,
        )
        data = strategy.model_dump()
        assert data["id"] == "strat_123"
        assert data["name"] == "Test Strategy"
        assert data["type"] == "composed"

    def test_strategy_json_serialization(self):
        """Test Strategy model JSON serialization."""
        strategy = Strategy(
            id="strat_123",
            name="Test Strategy",
            type=StrategyType.COMPOSED,
            parameters={"key": "value"},
        )
        json_str = strategy.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == "strat_123"
        assert parsed["parameters"] == {"key": "value"}

    def test_portfolio_with_positions_serialization(self):
        """Test Portfolio with nested Position serialization."""
        now = datetime.now()
        portfolio = Portfolio(
            total_equity=Decimal("100000.00"),
            starting_balance=Decimal("100000.00"),
            total_pnl=Decimal("0.00"),
            total_pnl_percent=Decimal("0.0"),
            open_pnl=Decimal("0.00"),
            positions=[
                Position(
                    id="pos_1",
                    symbol="BTC/USDT",
                    side="LONG",
                    quantity=Decimal("1.0"),
                    entry_price=Decimal("45000.00"),
                    current_price=Decimal("45000.00"),
                    unrealized_pnl=Decimal("0.00"),
                    unrealized_pnl_percent=Decimal("0.0"),
                    entry_timestamp=now,
                )
            ],
            metrics=PortfolioMetrics(
                sharpe_ratio=Decimal("1.0"),
                sortino_ratio=Decimal("1.0"),
                max_drawdown=Decimal("0.0"),
                win_rate=Decimal("0.5"),
                profit_factor=Decimal("1.0"),
            ),
        )
        data = portfolio.model_dump()
        assert len(data["positions"]) == 1
        assert data["positions"][0]["symbol"] == "BTC/USDT"


class TestModelValidation:
    """Test model validation rules."""

    def test_signal_confidence_range(self):
        """Test Signal confidence must be between 0 and 1."""
        with pytest.raises(ValueError):
            Signal(
                id="sig_123",
                strategy_id="strat_123",
                symbol="BTC/USDT",
                signal_type=SignalType.LONG,
                confidence=1.5,  # Invalid
                price=Decimal("45000.00"),
                timestamp=datetime.now(),
            )

    def test_backtest_negative_metrics(self):
        """Test backtest can have negative metrics."""
        backtest = BacktestResult(
            id="bt_123",
            strategy_id="strat_123",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=Decimal("100000.00"),
            final_capital=Decimal("90000.00"),
            total_return=Decimal("-0.10"),
            sharpe_ratio=Decimal("-0.5"),
            sortino_ratio=Decimal("-0.3"),
            max_drawdown=Decimal("-0.20"),
            win_rate=Decimal("0.4"),
            profit_factor=Decimal("0.8"),
            total_trades=50,
            equity_curve=[],
            trades=[],
        )
        assert backtest.total_return == Decimal("-0.10")

    def test_position_side_validation(self):
        """Test Position side must be LONG or SHORT."""
        with pytest.raises(ValueError):
            Position(
                id="pos_123",
                symbol="BTC/USDT",
                side="INVALID",  # Invalid side
                quantity=Decimal("1.0"),
                entry_price=Decimal("45000.00"),
                current_price=Decimal("45000.00"),
                unrealized_pnl=Decimal("0.00"),
                unrealized_pnl_percent=Decimal("0.0"),
                entry_timestamp=datetime.now(),
            )


class TestAllModelsExportable:
    """Test that all models are exportable from models/__init__.py."""

    def test_all_models_importable(self):
        """Test all contract models can be imported."""
        from models import (
            BacktestResult,
            EquityPoint,
            LayerSignal,
            MLModel,
            ModelStatus,
            ModelType,
            Portfolio,
            PortfolioMetrics,
            Position,
            Settings,
            Signal,
            SignalType,
            Status,
            Strategy,
            StrategyLayer,
            StrategyType,
            Trade,
            UIMode,
            Whale,
            WhaleActivity,
            WhaleAction,
            WhaleConstellation,
            WhaleConstellationType,
            PatternType,
            WhaleTier,
        )

        # Verify all imports worked
        assert Strategy is not None
        assert StrategyLayer is not None
        assert Signal is not None
        assert BacktestResult is not None
        assert EquityPoint is not None
        assert Trade is not None
        assert Portfolio is not None
        assert Position is not None
        assert Whale is not None
        assert WhaleActivity is not None
        assert WhaleConstellation is not None
        assert MLModel is not None
        assert Settings is not None

        # Verify all enums
        assert StrategyType is not None
        assert SignalType is not None
        assert Status is not None
        assert ModelStatus is not None
        assert ModelType is not None
        assert UIMode is not None
        assert WhaleAction is not None
        assert WhaleConstellationType is not None
        assert PatternType is not None
        assert WhaleTier is not None
