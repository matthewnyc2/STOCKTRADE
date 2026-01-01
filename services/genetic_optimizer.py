"""
Genetic Algorithm Optimizer for Trading Strategies.

Evolves strategy parameters using evolutionary methods to find optimal configurations.
Implements selection, crossover, mutation, and fitness evaluation for strategy optimization.

Key Features:
- Population-based evolution with configurable size
- Fitness evaluation using Sharpe * Sortino / Max Drawdown
- Tournament selection for parent selection
- Parameter-aware crossover and mutation
- Elitism to preserve best performers
- Background execution with progress tracking
"""

import asyncio
import logging
import math
import random
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from models import BacktestResult, Strategy
from services.backtest_engine import BacktestEngine, BacktestConfig


logger = logging.getLogger(__name__)


class OptimizationStatus(str, Enum):
    """Status of a genetic optimization run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParameterRange:
    """
    Defines the valid range for a strategy parameter.

    Supports float, int, and categorical parameters.
    """

    name: str
    param_type: str  # "float", "int", "categorical"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    categories: Optional[list[Any]] = None

    def generate_random_value(self) -> Any:
        """Generate a random value within the parameter range."""
        if self.param_type == "float":
            if self.step:
                # Discrete steps
                num_steps = int((self.max_value - self.min_value) / self.step)
                step_idx = random.randint(0, num_steps)
                return self.min_value + (step_idx * self.step)
            else:
                # Continuous range
                return random.uniform(self.min_value, self.max_value)

        elif self.param_type == "int":
            if self.step:
                step = int(self.step)
                num_steps = int((self.max_value - self.min_value) / step)
                step_idx = random.randint(0, num_steps)
                return int(self.min_value + (step_idx * step))
            else:
                return random.randint(int(self.min_value), int(self.max_value))

        elif self.param_type == "categorical":
            return random.choice(self.categories)

        raise ValueError(f"Unknown parameter type: {self.param_type}")

    def validate_value(self, value: Any) -> bool:
        """Check if a value is within valid range."""
        if self.param_type == "float":
            try:
                val = float(value)
                return self.min_value <= val <= self.max_value
            except (ValueError, TypeError):
                return False

        elif self.param_type == "int":
            try:
                val = int(value)
                return self.min_value <= val <= self.max_value
            except (ValueError, TypeError):
                return False

        elif self.param_type == "categorical":
            return value in self.categories

        return False

    def clamp_value(self, value: Any) -> Any:
        """Clamp a value to valid range."""
        if self.param_type == "float":
            val = float(value)
            clamped = max(self.min_value, min(self.max_value, val))
            if self.step:
                # Round to nearest step
                step_offset = clamped - self.min_value
                step_idx = round(step_offset / self.step)
                clamped = self.min_value + (step_idx * self.step)
            return clamped

        elif self.param_type == "int":
            val = int(value)
            clamped = max(int(self.min_value), min(int(self.max_value), val))
            if self.step:
                step = int(self.step)
                step_offset = clamped - int(self.min_value)
                step_idx = round(step_offset / step)
                clamped = int(self.min_value) + (step_idx * step)
            return clamped

        elif self.param_type == "categorical":
            if value not in self.categories:
                return self.categories[0] if self.categories else value
            return value

        return value


@dataclass
class GeneticConfig:
    """Configuration for genetic algorithm optimization."""

    population_size: int = 50
    generations: int = 30
    mutation_rate: float = 0.15
    crossover_rate: float = 0.8
    elitism_count: int = 3  # Number of top individuals to preserve
    tournament_size: int = 5  # For tournament selection
    initial_capital: Decimal = Decimal("10000")
    commission_rate: Decimal = Decimal("0.001")
    slippage_rate: Decimal = Decimal("0.001")
    position_size_percent: Decimal = Decimal("1.0")
    risk_free_rate: float = 0.02


@dataclass
class Individual:
    """Represents a single strategy configuration in the population."""

    id: str = field(default_factory=lambda: f"ind_{uuid4().hex[:8]}")
    parameters: dict[str, Any] = field(default_factory=dict)
    fitness: Optional[float] = None
    backtest_result: Optional[BacktestResult] = None
    generation: int = 0

    def __hash__(self) -> int:
        """Make individual hashable for set operations."""
        return hash(self.id)


@dataclass
class GenerationResult:
    """Results from a single generation of evolution."""

    generation: int
    best_fitness: float
    worst_fitness: float
    avg_fitness: float
    best_individual: Individual
    population: list[Individual]


@dataclass
class OptimizationResult:
    """Final results of genetic optimization."""

    id: str
    status: OptimizationStatus
    strategy_id: str
    symbol: str
    start_date: datetime
    end_date: datetime

    # Configuration
    config: GeneticConfig
    parameter_ranges: list[ParameterRange]

    # Results
    generations_completed: int
    generations: list[GenerationResult]
    best_individual: Individual
    top_individuals: list[Individual]  # Top N performers

    # Metadata
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Progress tracking
    total_fitness_evaluations: int = 0
    total_backtests_run: int = 0


def calculate_fitness(
    backtest_result: BacktestResult,
    risk_free_rate: float = 0.02,
) -> float:
    """
    Calculate fitness score from backtest result.

    Fitness = Sharpe Ratio * Sortino Ratio / Max Drawdown

    This formula rewards strategies with:
    - High risk-adjusted returns (Sharpe, Sortino)
    - Low maximum drawdown (denominator makes lower DD better)

    Args:
        backtest_result: The backtest result to evaluate
        risk_free_rate: Risk-free rate for ratio calculations

    Returns:
        Fitness score (higher is better). Returns negative infinity for invalid results.
    """
    # Handle invalid results
    if backtest_result.total_trades == 0:
        return float("-inf")

    # Get Sharpe and Sortino ratios
    sharpe = float(backtest_result.sharpe_ratio) if backtest_result.sharpe_ratio else 0.0
    sortino = float(backtest_result.sortino_ratio) if backtest_result.sortino_ratio else 0.0
    max_dd = float(backtest_result.max_drawdown)

    # Penalize very high drawdowns severely
    if max_dd <= -0.5:  # More than 50% drawdown
        return float("-inf")

    # Avoid division by zero
    if abs(max_dd) < 0.001:
        max_dd = -0.001

    # Calculate fitness
    # Max DD is negative, so we negate it to get positive value
    # Lower drawdown magnitude = higher fitness
    fitness = (sharpe * sortino) / abs(max_dd)

    # Apply additional penalties
    # Penalize low win rates
    win_rate = float(backtest_result.win_rate)
    if win_rate < 0.3:
        fitness *= 0.5

    # Penalize strategies with too few trades
    if backtest_result.total_trades < 10:
        fitness *= 0.7

    return fitness


class GeneticOptimizer:
    """
    Genetic Algorithm optimizer for trading strategy parameters.

    Evolves a population of strategy configurations through selection,
    crossover, and mutation to find optimal parameters.
    """

    def __init__(
        self,
        config: GeneticConfig,
        price_data: list[dict[str, Any]],
        symbol: str,
        strategy_template: Strategy,
        parameter_ranges: list[ParameterRange],
        progress_callback: Optional[Callable[[GenerationResult], None]] = None,
    ) -> None:
        """
        Initialize the genetic optimizer.

        Args:
            config: Genetic algorithm configuration
            price_data: Historical price data for backtesting
            symbol: Trading symbol
            strategy_template: Base strategy template (parameters will be overridden)
            parameter_ranges: Ranges for parameters to optimize
            progress_callback: Optional callback for generation updates
        """
        self.config = config
        self.price_data = price_data
        self.symbol = symbol
        self.strategy_template = strategy_template
        self.parameter_ranges = {pr.name: pr for pr in parameter_ranges}
        self.progress_callback = progress_callback

        # Backtest engine (shared across evaluations)
        backtest_config = BacktestConfig(
            initial_capital=config.initial_capital,
            commission_rate=config.commission_rate,
            slippage_rate=config.slippage_rate,
            position_size_percent=config.position_size_percent,
            risk_free_rate=config.risk_free_rate,
        )
        self.backtest_engine = BacktestEngine(backtest_config)

        # State
        self._current_generation = 0
        self._is_cancelled = False
        self._fitness_evaluations = 0
        self._backtests_run = 0

    def run_optimization(self) -> OptimizationResult:
        """
        Run the full genetic optimization.

        Returns:
            OptimizationResult with evolved strategies
        """
        result_id = f"opt_{uuid4().hex[:8]}"
        start_time = datetime.utcnow()

        logger.info(
            f"Starting genetic optimization {result_id}: "
            f"{self.config.population_size} population, {self.config.generations} generations"
        )

        generations_history = []

        try:
            # Initialize population
            population = self._create_initial_population()

            # Evaluate initial population
            population = self._evaluate_population(population, 0)

            # Record initial generation
            gen_result = self._create_generation_result(0, population)
            generations_history.append(gen_result)

            if self.progress_callback:
                self.progress_callback(gen_result)

            # Evolution loop
            for gen in range(1, self.config.generations + 1):
                if self._is_cancelled:
                    logger.info(f"Optimization {result_id} cancelled at generation {gen}")
                    break

                self._current_generation = gen

                # Selection
                parents = self._select_parents(population)

                # Crossover
                offspring = self._crossover_population(parents)

                # Mutation
                offspring = self._mutate_population(offspring)

                # Evaluate offspring
                offspring = self._evaluate_population(offspring, gen)

                # Survivor selection (combine parents and offspring, keep best)
                population = self._select_survivors(population + offspring)

                # Record generation
                gen_result = self._create_generation_result(gen, population)
                generations_history.append(gen_result)

                if self.progress_callback:
                    self.progress_callback(gen_result)

                logger.info(
                    f"Generation {gen}/{self.config.generations}: "
                    f"Best fitness={gen_result.best_fitness:.4f}, "
                    f"Avg fitness={gen_result.avg_fitness:.4f}"
                )

            # Determine final status
            if self._is_cancelled:
                status = OptimizationStatus.CANCELLED
            else:
                status = OptimizationStatus.COMPLETED

            # Get top performers
            sorted_population = sorted(
                population, key=lambda ind: ind.fitness or float("-inf"), reverse=True
            )
            top_individuals = sorted_population[:10]  # Top 10

            result = OptimizationResult(
                id=result_id,
                status=status,
                strategy_id=self.strategy_template.id,
                symbol=self.symbol,
                start_date=start_time,
                end_date=datetime.utcnow(),
                config=self.config,
                parameter_ranges=list(self.parameter_ranges.values()),
                generations_completed=self._current_generation,
                generations=generations_history,
                best_individual=sorted_population[0] if sorted_population else Individual(),
                top_individuals=top_individuals,
                created_at=start_time,
                completed_at=datetime.utcnow() if status == OptimizationStatus.COMPLETED else None,
                total_fitness_evaluations=self._fitness_evaluations,
                total_backtests_run=self._backtests_run,
            )

            logger.info(
                f"Optimization {result_id} completed: "
                f"Best fitness={result.best_individual.fitness:.4f}"
            )

            return result

        except Exception as e:
            logger.error(f"Optimization {result_id} failed: {e}", exc_info=True)
            return OptimizationResult(
                id=result_id,
                status=OptimizationStatus.FAILED,
                strategy_id=self.strategy_template.id,
                symbol=self.symbol,
                start_date=start_time,
                end_date=datetime.utcnow(),
                config=self.config,
                parameter_ranges=list(self.parameter_ranges.values()),
                generations_completed=self._current_generation,
                generations=generations_history,
                best_individual=Individual(),
                top_individuals=[],
                created_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e),
                total_fitness_evaluations=self._fitness_evaluations,
                total_backtests_run=self._backtests_run,
            )

    def cancel(self) -> None:
        """Cancel the running optimization."""
        self._is_cancelled = True

    def _create_initial_population(self) -> list[Individual]:
        """Create initial population with random parameters."""
        population = []

        for _ in range(self.config.population_size):
            # Generate random parameters
            parameters = {}
            for param_name, param_range in self.parameter_ranges.items():
                parameters[param_name] = param_range.generate_random_value()

            individual = Individual(
                parameters=parameters,
                generation=0,
            )
            population.append(individual)

        return population

    def _evaluate_population(
        self, population: list[Individual], generation: int
    ) -> list[Individual]:
        """Evaluate fitness of all individuals in the population."""
        evaluated = []

        for individual in population:
            if individual.fitness is None:
                # Run backtest
                backtest_result = self._run_backtest(individual.parameters)
                individual.backtest_result = backtest_result
                individual.fitness = calculate_fitness(backtest_result)
                individual.generation = generation
                self._fitness_evaluations += 1
                self._backtests_run += 1

            evaluated.append(individual)

        return evaluated

    def _run_backtest(self, parameters: dict[str, Any]) -> BacktestResult:
        """Run a backtest with the given parameters."""
        # Create strategy with evolved parameters
        strategy = Strategy(
            id=self.strategy_template.id,
            name=self.strategy_template.name,
            type=self.strategy_template.type,
            description=self.strategy_template.description,
            parameters={**self.strategy_template.parameters, **parameters},
            layers=self.strategy_template.layers,
            status=self.strategy_template.status,
            logic_gate=self.strategy_template.logic_gate,
        )

        return self.backtest_engine.run_backtest(
            strategy=strategy,
            price_data=self.price_data,
            symbol=self.symbol,
        )

    def _select_parents(self, population: list[Individual]) -> list[Individual]:
        """
        Select parents using tournament selection.

        Returns twice the population size for generating offspring.
        """
        # Sort by fitness for elitism
        sorted_pop = sorted(
            population, key=lambda ind: ind.fitness or float("-inf"), reverse=True
        )

        # Preserve elite individuals
        elite = sorted_pop[: self.config.elitism_count]

        # Select remaining parents via tournament
        num_parents = (self.config.population_size - self.config.elitism_count) * 2
        parents = elite.copy()

        while len(parents) < num_parents:
            # Tournament selection
            tournament = random.sample(population, min(self.config.tournament_size, len(population)))
            winner = max(tournament, key=lambda ind: ind.fitness or float("-inf"))
            parents.append(winner)

        return parents[:num_parents]

    def _crossover_population(self, parents: list[Individual]) -> list[Individual]:
        """Perform crossover on parent pairs to create offspring."""
        offspring = []

        # Shuffle parents for random pairing
        shuffled = parents.copy()
        random.shuffle(shuffled)

        # Pair up parents and crossover
        for i in range(0, len(shuffled) - 1, 2):
            parent1 = shuffled[i]
            parent2 = shuffled[i + 1]

            # Check if crossover should occur
            if random.random() < self.config.crossover_rate:
                child = self._crossover(parent1, parent2)
            else:
                # No crossover, pass on one parent
                child = deepcopy(parent1)
                child.id = f"ind_{uuid4().hex[:8]}"

            offspring.append(child)

        # Fill remaining slots if needed
        while len(offspring) < self.config.population_size:
            parent = random.choice(parents)
            child = deepcopy(parent)
            child.id = f"ind_{uuid4().hex[:8]}"
            offspring.append(child)

        return offspring

    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """
        Combine two parent strategies using parameter-wise crossover.

        Uses uniform crossover - each parameter has 50% chance from each parent.
        """
        child_parameters = {}

        for param_name in self.parameter_ranges.keys():
            # Randomly choose parameter from either parent
            if random.random() < 0.5:
                child_parameters[param_name] = parent1.parameters.get(param_name)
            else:
                child_parameters[param_name] = parent2.parameters.get(param_name)

            # For numeric parameters, also do arithmetic crossover (average)
            param_range = self.parameter_ranges[param_name]
            if param_range.param_type in ("float", "int"):
                if random.random() < 0.3:  # 30% chance of averaging
                    val1 = parent1.parameters.get(param_name, param_range.min_value)
                    val2 = parent2.parameters.get(param_name, param_range.min_value)
                    avg = (val1 + val2) / 2
                    child_parameters[param_name] = param_range.clamp_value(avg)

        return Individual(
            parameters=child_parameters,
            generation=self._current_generation + 1,
        )

    def _mutate_population(self, population: list[Individual]) -> list[Individual]:
        """Apply mutation to individuals in the population."""
        mutated = []

        for individual in population:
            if random.random() < self.config.mutation_rate:
                mutated_individual = self._mutate(individual)
                mutated.append(mutated_individual)
            else:
                mutated.append(individual)

        return mutated

    def _mutate(self, individual: Individual) -> Individual:
        """
        Mutate an individual's parameters.

        Each parameter has a chance to be mutated based on mutation rate.
        """
        mutated_params = individual.parameters.copy()

        # Determine how many parameters to mutate (at least 1)
        num_params = len(self.parameter_ranges)
        num_to_mutate = max(1, int(num_params * self.config.mutation_rate))

        # Randomly select parameters to mutate
        params_to_mutate = random.sample(list(self.parameter_ranges.keys()), num_to_mutate)

        for param_name in params_to_mutate:
            param_range = self.parameter_ranges[param_name]
            current_value = mutated_params.get(param_name)

            if param_range.param_type == "float":
                # Gaussian mutation around current value
                if current_value is not None and param_range.step is None:
                    # Continuous: add Gaussian noise
                    sigma = (param_range.max_value - param_range.min_value) * 0.1
                    new_value = current_value + random.gauss(0, sigma)
                else:
                    # Discrete: random step
                    if current_value is not None:
                        step = param_range.step or ((param_range.max_value - param_range.min_value) / 20)
                        direction = random.choice([-1, 1])
                        new_value = current_value + (direction * step)
                    else:
                        new_value = param_range.generate_random_value()
                mutated_params[param_name] = param_range.clamp_value(new_value)

            elif param_range.param_type == "int":
                # Integer mutation
                if current_value is not None:
                    step = int(param_range.step) if param_range.step else 1
                    direction = random.choice([-1, 1])
                    new_value = int(current_value) + (direction * step)
                else:
                    new_value = param_range.generate_random_value()
                mutated_params[param_name] = param_range.clamp_value(new_value)

            elif param_range.param_type == "categorical":
                # Categorical: pick different category
                current_categories = param_range.categories or []
                if current_categories and len(current_categories) > 1:
                    # Pick a different category
                    available = [c for c in current_categories if c != current_value]
                    mutated_params[param_name] = random.choice(available) if available else current_value

        return Individual(
            id=f"ind_{uuid4().hex[:8]}",
            parameters=mutated_params,
            generation=individual.generation,
        )

    def _select_survivors(self, population: list[Individual]) -> list[Individual]:
        """Select survivors for next generation (keep best performers)."""
        # Sort by fitness
        sorted_pop = sorted(
            population, key=lambda ind: ind.fitness or float("-inf"), reverse=True
        )

        # Keep top individuals
        return sorted_pop[: self.config.population_size]

    def _create_generation_result(
        self, generation: int, population: list[Individual]
    ) -> GenerationResult:
        """Create a generation summary result."""
        valid_fitness = [ind.fitness for ind in population if ind.fitness is not None and ind.fitness != float("-inf")]

        if not valid_fitness:
            best_fitness = worst_fitness = avg_fitness = 0.0
            best_ind = Individual()
        else:
            best_fitness = max(valid_fitness)
            worst_fitness = min(valid_fitness)
            avg_fitness = sum(valid_fitness) / len(valid_fitness)
            best_ind = max(population, key=lambda ind: ind.fitness or float("-inf"))

        return GenerationResult(
            generation=generation,
            best_fitness=best_fitness,
            worst_fitness=worst_fitness,
            avg_fitness=avg_fitness,
            best_individual=best_ind,
            population=population,
        )


# In-memory storage for running optimizations
_running_optimizations: dict[str, GeneticOptimizer] = {}


def run_optimization_background(
    optimization_id: str,
    optimizer: GeneticOptimizer,
    result_future: asyncio.Future,
) -> None:
    """
    Run optimization in background and set result on completion.

    This is designed to be run in a thread pool executor.
    """
    try:
        result = optimizer.run_optimization()
        # Set result on the future (will be retrieved by main thread)
        if not result_future.done():
            result_future.set_result(result)
    except Exception as e:
        if not result_future.done():
            result_future.set_exception(e)
    finally:
        # Clean up
        _running_optimizations.pop(optimization_id, None)


def cancel_optimization(optimization_id: str) -> bool:
    """Cancel a running optimization."""
    optimizer = _running_optimizations.get(optimization_id)
    if optimizer:
        optimizer.cancel()
        return True
    return False


def get_optimizer(optimization_id: str) -> Optional[GeneticOptimizer]:
    """Get a running optimizer by ID."""
    return _running_optimizations.get(optimization_id)
