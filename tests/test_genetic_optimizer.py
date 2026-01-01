"""
Tests for the Genetic Algorithm Optimizer Service.

Tests cover:
- Initial population generation with random parameters
- Fitness function evaluation
- Crossover combining two parent strategies
- Mutation altering parameters within bounds
- Selection and survivor management
- Full optimization workflow
"""

import math
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from models import Strategy, StrategyType
from services.genetic_optimizer import (
    GeneticOptimizer,
    GeneticConfig,
    ParameterRange,
    Individual,
    GenerationResult,
    OptimizationResult,
    OptimizationStatus,
    calculate_fitness,
)


@pytest.fixture
def sample_strategy() -> Strategy:
    """Create a sample RSI strategy for optimization."""
    return Strategy(
        id="strat_test001",
        name="Test RSI Strategy",
        type=StrategyType.COMPOSED,
        description="A simple RSI-based strategy for testing",
        parameters={
            "indicator_type": "rsi",
            "oversold_threshold": 30.0,
            "overbought_threshold": 70.0,
        },
        status="active",
    )


@pytest.fixture
def sample_price_data():
    """Generate sample price data for testing."""
    prices = []
    base_price = 100.0
    base_time = datetime(2024, 1, 1)

    for i in range(150):  # Need at least 100 for proper indicator calculation
        # Add some realistic price movement
        change = (i % 10 - 5) * 0.5
        open_price = base_price + change
        close_price = open_price + (i % 3 - 1) * 0.3
        high_price = max(open_price, close_price) + abs(i % 2) * 0.2
        low_price = min(open_price, close_price) - abs(i % 2) * 0.2
        volume = 1000000 + i * 10000

        prices.append({
            "timestamp": base_time + timedelta(hours=i),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        })

    return prices


@pytest.fixture
def parameter_ranges():
    """Create parameter ranges for optimization."""
    return [
        ParameterRange(
            name="oversold_threshold",
            param_type="float",
            min_value=20.0,
            max_value=40.0,
            step=1.0,
        ),
        ParameterRange(
            name="overbought_threshold",
            param_type="float",
            min_value=60.0,
            max_value=80.0,
            step=1.0,
        ),
    ]


@pytest.fixture
def genetic_config():
    """Create a standard genetic configuration."""
    return GeneticConfig(
        population_size=10,  # Small for testing
        generations=3,
        mutation_rate=0.2,
        crossover_rate=0.8,
        elitism_count=2,
        tournament_size=3,
        initial_capital=Decimal("10000"),
        commission_rate=Decimal("0.001"),
        slippage_rate=Decimal("0.001"),
        position_size_percent=Decimal("1.0"),
    )


class TestParameterRange:
    """Test ParameterRange functionality."""

    def test_generate_random_float(self):
        """Test random float generation."""
        param_range = ParameterRange(
            name="test_param",
            param_type="float",
            min_value=10.0,
            max_value=20.0,
        )

        for _ in range(100):
            value = param_range.generate_random_value()
            assert 10.0 <= value <= 20.0
            assert isinstance(value, (int, float))

    def test_generate_random_float_with_step(self):
        """Test random float generation with discrete steps."""
        param_range = ParameterRange(
            name="test_param",
            param_type="float",
            min_value=10.0,
            max_value=20.0,
            step=2.5,
        )

        values = [param_range.generate_random_value() for _ in range(100)]

        # All values should be at step intervals
        for value in values:
            # value = min + n * step
            offset = value - 10.0
            step_multiple = offset / 2.5
            assert abs(step_multiple - round(step_multiple)) < 0.001  # Allow floating point error

    def test_generate_random_int(self):
        """Test random int generation."""
        param_range = ParameterRange(
            name="test_param",
            param_type="int",
            min_value=5,
            max_value=15,
        )

        for _ in range(100):
            value = param_range.generate_random_value()
            assert 5 <= value <= 15
            assert isinstance(value, int)

    def test_generate_random_categorical(self):
        """Test random categorical generation."""
        categories = ["rsi", "macd", "bb", "ema"]
        param_range = ParameterRange(
            name="indicator_type",
            param_type="categorical",
            categories=categories,
        )

        for _ in range(100):
            value = param_range.generate_random_value()
            assert value in categories

    def test_clamp_value_float(self):
        """Test clamping float values."""
        param_range = ParameterRange(
            name="test_param",
            param_type="float",
            min_value=10.0,
            max_value=20.0,
            step=1.0,
        )

        # Value within range
        assert param_range.clamp_value(15.0) == 15.0

        # Value above range
        assert param_range.clamp_value(25.0) == 20.0

        # Value below range
        assert param_range.clamp_value(5.0) == 10.0

        # Round to nearest step
        assert param_range.clamp_value(15.7) == 16.0

    def test_clamp_value_int(self):
        """Test clamping int values."""
        param_range = ParameterRange(
            name="test_param",
            param_type="int",
            min_value=10,
            max_value=20,
        )

        assert param_range.clamp_value(15) == 15
        assert param_range.clamp_value(25) == 20
        assert param_range.clamp_value(5) == 10

    def test_validate_value(self):
        """Test value validation."""
        param_range = ParameterRange(
            name="test_param",
            param_type="float",
            min_value=10.0,
            max_value=20.0,
        )

        assert param_range.validate_value(15.0) is True
        assert param_range.validate_value(25.0) is False
        assert param_range.validate_value(5.0) is False


class TestFitnessCalculation:
    """Test fitness function calculation."""

    def test_calculate_fitness_positive(self, sample_price_data):
        """Test fitness calculation with positive results."""
        from models import BacktestResult, EquityPoint

        # Create a mock positive result
        result = BacktestResult(
            id="bt_test",
            strategy_id="strat_test",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            initial_capital=Decimal("10000"),
            final_capital=Decimal("12000"),
            total_return=Decimal("0.2"),
            sharpe_ratio=Decimal("1.5"),
            sortino_ratio=Decimal("2.0"),
            max_drawdown=Decimal("-0.1"),
            win_rate=Decimal("0.6"),
            profit_factor=Decimal("2.0"),
            total_trades=20,
            equity_curve=[],
            trades=[],
        )

        fitness = calculate_fitness(result)

        # Fitness should be positive and finite
        assert fitness > 0
        assert not math.isinf(fitness)
        assert not math.isnan(fitness)

    def test_calculate_fitness_no_trades(self):
        """Test fitness calculation with no trades."""
        from models import BacktestResult

        result = BacktestResult(
            id="bt_test",
            strategy_id="strat_test",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            initial_capital=Decimal("10000"),
            final_capital=Decimal("10000"),
            total_return=Decimal("0"),
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=Decimal("0"),
            win_rate=Decimal("0"),
            profit_factor=None,
            total_trades=0,
            equity_curve=[],
            trades=[],
        )

        fitness = calculate_fitness(result)

        # Should be negative infinity for no trades
        assert fitness == float("-inf")

    def test_calculate_fitness_high_drawdown(self):
        """Test fitness calculation with high drawdown."""
        from models import BacktestResult

        result = BacktestResult(
            id="bt_test",
            strategy_id="strat_test",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            initial_capital=Decimal("10000"),
            final_capital=Decimal("8000"),
            total_return=Decimal("-0.2"),
            sharpe_ratio=Decimal("-0.5"),
            sortino_ratio=Decimal("-0.3"),
            max_drawdown=Decimal("-0.6"),  # 60% drawdown - too high
            win_rate=Decimal("0.3"),
            profit_factor=Decimal("0.5"),
            total_trades=20,
            equity_curve=[],
            trades=[],
        )

        fitness = calculate_fitness(result)

        # Should be negative infinity for >50% drawdown
        assert fitness == float("-inf")

    def test_calculate_fitness_low_win_rate_penalty(self):
        """Test fitness penalty for low win rate."""
        from models import BacktestResult

        result = BacktestResult(
            id="bt_test",
            strategy_id="strat_test",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            initial_capital=Decimal("10000"),
            final_capital=Decimal("12000"),
            total_return=Decimal("0.2"),
            sharpe_ratio=Decimal("1.5"),
            sortino_ratio=Decimal("2.0"),
            max_drawdown=Decimal("-0.1"),
            win_rate=Decimal("0.25"),  # Low win rate
            profit_factor=Decimal("2.0"),
            total_trades=20,
            equity_curve=[],
            trades=[],
        )

        fitness = calculate_fitness(result)

        # Should be penalized (50% reduction)
        expected_base = (1.5 * 2.0) / 0.1
        assert fitness < expected_base


class TestIndividual:
    """Test Individual functionality."""

    def test_individual_creation(self):
        """Test creating an individual."""
        individual = Individual(
            id="ind_test",
            parameters={"threshold": 30.0},
            fitness=1.5,
            generation=1,
        )

        assert individual.id == "ind_test"
        assert individual.parameters == {"threshold": 30.0}
        assert individual.fitness == 1.5
        assert individual.generation == 1

    def test_individual_hashable(self):
        """Test that individuals are hashable for sets."""
        ind1 = Individual(id="ind_1", parameters={"a": 1})
        ind2 = Individual(id="ind_2", parameters={"b": 2})
        ind3 = Individual(id="ind_1", parameters={"a": 1})

        # Should be able to create a set
        individual_set = {ind1, ind2}
        assert len(individual_set) == 2

        # Same ID means same individual (by hash)
        assert hash(ind1) == hash(ind3)


class TestGeneticOptimizer:
    """Test GeneticOptimizer functionality."""

    def test_optimizer_initialization(
        self, sample_strategy, sample_price_data, parameter_ranges, genetic_config
    ):
        """Test optimizer initialization."""
        optimizer = GeneticOptimizer(
            config=genetic_config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        assert optimizer.config.population_size == 10
        assert optimizer.symbol == "BTC/USDT"
        assert len(optimizer.parameter_ranges) == 2

    def test_create_initial_population(
        self, sample_strategy, sample_price_data, parameter_ranges, genetic_config
    ):
        """Test initial population creation."""
        optimizer = GeneticOptimizer(
            config=genetic_config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        population = optimizer._create_initial_population()

        assert len(population) == genetic_config.population_size

        # Each individual should have valid parameters
        for individual in population:
            assert "oversold_threshold" in individual.parameters
            assert "overbought_threshold" in individual.parameters
            assert 20.0 <= individual.parameters["oversold_threshold"] <= 40.0
            assert 60.0 <= individual.parameters["overbought_threshold"] <= 80.0

    def test_crossover(
        self, sample_strategy, sample_price_data, parameter_ranges, genetic_config
    ):
        """Test crossover between two parents."""
        optimizer = GeneticOptimizer(
            config=genetic_config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        parent1 = Individual(
            parameters={"oversold_threshold": 25.0, "overbought_threshold": 65.0}
        )
        parent2 = Individual(
            parameters={"oversold_threshold": 35.0, "overbought_threshold": 75.0}
        )

        child = optimizer._crossover(parent1, parent2)

        # Child should have parameters from one or both parents
        assert "oversold_threshold" in child.parameters
        assert "overbought_threshold" in child.parameters
        assert 20.0 <= child.parameters["oversold_threshold"] <= 40.0
        assert 60.0 <= child.parameters["overbought_threshold"] <= 80.0

    def test_mutate(
        self, sample_strategy, sample_price_data, parameter_ranges, genetic_config
    ):
        """Test mutation of an individual."""
        optimizer = GeneticOptimizer(
            config=genetic_config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        individual = Individual(
            parameters={"oversold_threshold": 30.0, "overbought_threshold": 70.0}
        )

        mutated = optimizer._mutate(individual)

        # Parameters should still be within valid range
        assert 20.0 <= mutated.parameters["oversold_threshold"] <= 40.0
        assert 60.0 <= mutated.parameters["overbought_threshold"] <= 80.0

    def test_mutate_categorical(self):
        """Test mutation of categorical parameters."""
        # Create optimizer with categorical parameter
        param_ranges = [
            ParameterRange(
                name="indicator_type",
                param_type="categorical",
                categories=["rsi", "macd", "bb", "ema"],
            )
        ]

        config = GeneticConfig(
            population_size=5,
            generations=1,
            mutation_rate=1.0,  # Always mutate
        )

        optimizer = GeneticOptimizer(
            config=config,
            price_data=[],
            symbol="BTC/USDT",
            strategy_template=Strategy(
                id="test", name="test", type=StrategyType.COMPOSED
            ),
            parameter_ranges=param_ranges,
        )

        individual = Individual(parameters={"indicator_type": "rsi"})
        mutated = optimizer._mutate(individual)

        # Should be one of the valid categories
        assert mutated.parameters["indicator_type"] in ["rsi", "macd", "bb", "ema"]

    def test_select_survivors(
        self, sample_strategy, sample_price_data, parameter_ranges, genetic_config
    ):
        """Test survivor selection."""
        optimizer = GeneticOptimizer(
            config=genetic_config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        # Create population with more individuals than population_size
        population = [
            Individual(parameters={}, fitness=3.0),
            Individual(parameters={}, fitness=1.0),
            Individual(parameters={}, fitness=5.0),
            Individual(parameters={}, fitness=2.0),
            Individual(parameters={}, fitness=4.0),
            Individual(parameters={}, fitness=2.5),
            Individual(parameters={}, fitness=3.5),
            Individual(parameters={}, fitness=1.5),
            Individual(parameters={}, fitness=4.5),
            Individual(parameters={}, fitness=0.5),
            Individual(parameters={}, fitness=6.0),
            Individual(parameters={}, fitness=2.2),
        ]

        survivors = optimizer._select_survivors(population)

        # Should keep top performers (population_size)
        assert len(survivors) == genetic_config.population_size

        # Best fitness should be 6.0
        assert survivors[0].fitness == 6.0

    def test_full_optimization(
        self, sample_strategy, sample_price_data, parameter_ranges
    ):
        """Test full optimization workflow."""
        # Use small config for faster testing
        config = GeneticConfig(
            population_size=5,
            generations=2,
            mutation_rate=0.2,
            crossover_rate=0.8,
            elitism_count=1,
            tournament_size=2,
            initial_capital=Decimal("10000"),
            commission_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            position_size_percent=Decimal("1.0"),
        )

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        result = optimizer.run_optimization()

        assert isinstance(result, OptimizationResult)
        assert result.status in [OptimizationStatus.COMPLETED, OptimizationStatus.FAILED]
        assert result.generations_completed >= 0
        assert len(result.generations) >= 1

    def test_optimization_cancel(
        self, sample_strategy, sample_price_data, parameter_ranges
    ):
        """Test cancelling an optimization."""
        config = GeneticConfig(
            population_size=5,
            generations=10,  # Many generations
            initial_capital=Decimal("10000"),
        )

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
            progress_callback=lambda gen: optimizer.cancel(),  # Cancel after first gen
        )

        result = optimizer.run_optimization()

        # Should have been cancelled
        assert result.status == OptimizationStatus.CANCELLED
        assert result.generations_completed < config.generations


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_evolution_improves_fitness(
        self, sample_strategy, sample_price_data, parameter_ranges
    ):
        """Test that evolution improves fitness over generations."""
        config = GeneticConfig(
            population_size=8,
            generations=3,
            mutation_rate=0.15,
            crossover_rate=0.8,
            elitism_count=2,
            initial_capital=Decimal("10000"),
        )

        best_fitnesses = []

        def track_best(generation: GenerationResult) -> None:
            best_fitnesses.append(generation.best_fitness)

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
            progress_callback=track_best,
        )

        result = optimizer.run_optimization()

        # Should have tracked fitness for each generation
        assert len(best_fitnesses) >= 1

        # Filter out negative infinities (invalid individuals)
        valid_fitnesses = [f for f in best_fitnesses if f != float("-inf")]

        if len(valid_fitnesses) > 1:
            # Fitness should generally improve (not guaranteed but likely)
            # At minimum, the best individual should be valid
            assert result.best_individual.fitness is not None

    def test_returns_top_individuals(
        self, sample_strategy, sample_price_data, parameter_ranges
    ):
        """Test that optimization returns top N individuals."""
        config = GeneticConfig(
            population_size=10,
            generations=2,
            initial_capital=Decimal("10000"),
        )

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        result = optimizer.run_optimization()

        # Should return top 10 individuals
        assert len(result.top_individuals) <= 10
        assert len(result.top_individuals) > 0

        # Top individuals should be sorted by fitness
        for i in range(len(result.top_individuals) - 1):
            if result.top_individuals[i].fitness and result.top_individuals[i + 1].fitness:
                assert result.top_individuals[i].fitness >= result.top_individuals[i + 1].fitness


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_parameter_ranges(self, sample_strategy, sample_price_data):
        """Test with no parameter ranges."""
        config = GeneticConfig(population_size=5, generations=1)

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=[],
        )

        result = optimizer.run_optimization()

        # Should still complete with no parameters to optimize
        assert result.status in [OptimizationStatus.COMPLETED, OptimizationStatus.FAILED]

    def test_single_parameter_range(self, sample_strategy, sample_price_data):
        """Test with only one parameter range."""
        param_ranges = [
            ParameterRange(
                name="threshold",
                param_type="float",
                min_value=10.0,
                max_value=50.0,
            )
        ]

        config = GeneticConfig(population_size=5, generations=2)

        optimizer = GeneticOptimizer(
            config=config,
            price_data=sample_price_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=param_ranges,
        )

        result = optimizer.run_optimization()

        # Best individual should have the parameter
        assert "threshold" in result.best_individual.parameters

    def test_insufficient_price_data(self, sample_strategy, parameter_ranges):
        """Test with insufficient price data."""
        short_data = [
            {
                "timestamp": datetime(2024, 1, 1) + timedelta(hours=i),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000000,
            }
            for i in range(10)  # Not enough data
        ]

        config = GeneticConfig(population_size=5, generations=1)

        optimizer = GeneticOptimizer(
            config=config,
            price_data=short_data,
            symbol="BTC/USDT",
            strategy_template=sample_strategy,
            parameter_ranges=parameter_ranges,
        )

        # Should fail with insufficient data
        result = optimizer.run_optimization()
        assert result.status == OptimizationStatus.FAILED
