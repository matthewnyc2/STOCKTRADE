"""
Strategy Manager Service.

Provides high-level business logic for strategy management including
creation from templates, validation, performance calculation, and
import/export functionality.
"""

import json
import logging
import yaml
from typing import Any, Dict, List, Optional
from uuid import uuid4
from decimal import Decimal

from database.connection import get_db_context
from database.repositories import (
    StrategyRepository,
    StrategyLayerRepository,
    StrategyFavoriteRepository,
    StrategyVersionRepository,
)
from models import (
    Strategy,
    StrategyType,
    Status,
    RiskLevel,
    StrategyLayer,
    LogicGate,
    RiskLevel as RiskLevelEnum,
    GameModeMetadata,
    ProModeMetadata,
    BacktestMetrics,
)


logger = logging.getLogger(__name__)


class StrategyValidationError(Exception):
    """Raised when strategy validation fails."""

    pass


class StrategyManager:
    """
    High-level strategy management service.

    Handles strategy creation, validation, performance tracking,
    and import/export operations.
    """

    def __init__(self):
        """Initialize the strategy manager."""
        logger.info("StrategyManager initialized")

    def create_from_template(
        self,
        template_id: str,
        name: str,
        user_id: str = "default",
        custom_parameters: Optional[Dict[str, Any]] = None,
        custom_tags: Optional[List[str]] = None,
    ) -> Strategy:
        """
        Create a new strategy from a template.

        Args:
            template_id: Template strategy ID
            name: Name for the new strategy
            user_id: User creating the strategy
            custom_parameters: Optional parameter overrides
            custom_tags: Optional additional tags

        Returns:
            Created strategy

        Raises:
            StrategyValidationError: If template is invalid
        """
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)

            # Get the template
            template = strategy_repo.get(template_id)
            if not template:
                raise StrategyValidationError(f"Template {template_id} not found")

            if not getattr(template, "is_template", False):
                raise StrategyValidationError(f"Strategy {template_id} is not a template")

            # Merge parameters
            final_parameters = template.parameters.copy()
            if custom_parameters:
                final_parameters.update(custom_parameters)

            # Merge tags
            final_tags = getattr(template, "tags", []).copy()
            if custom_tags:
                final_tags.extend(custom_tags)

            # Create new strategy
            new_strategy_id = f"strat_{uuid4().hex[:12]}"
            new_strategy = strategy_repo.create(
                id=new_strategy_id,
                name=name,
                description=template.description,
                type="composed",
                parameters=final_parameters,
                layers=[],
                status=Status.DRAFT.value,
                template_id=template_id,
                tags=final_tags,
                risk_level=getattr(template, "risk_level", None),
                is_template=False,
            )

            # Copy layers from template
            template_layers = layer_repo.get_by_strategy(template_id)
            new_layer_ids = []
            for layer in template_layers:
                new_layer = layer_repo.create(
                    id=f"layer_{uuid4().hex[:12]}",
                    strategy_id=new_strategy_id,
                    layer_order=layer.layer_order,
                    weight=layer.weight,
                    config=layer.config.copy(),
                )
                new_layer_ids.append(new_layer.id)

            # Update strategy with layers
            strategy_repo.update(new_strategy_id, layers=new_layer_ids)

            logger.info(f"Created strategy '{name}' from template {template_id}")
            return self._model_to_pydantic(new_strategy)

    def validate_strategy(self, strategy: Strategy) -> tuple[bool, List[str]]:
        """
        Validate a strategy configuration.

        Args:
            strategy: Strategy to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Name validation
        if not strategy.name or not strategy.name.strip():
            errors.append("Strategy name cannot be empty")

        # Type validation
        if not isinstance(strategy.type, StrategyType):
            errors.append(f"Invalid strategy type: {strategy.type}")

        # Parameters validation based on type
        if strategy.type == StrategyType.COMPOSED:
            # Composed strategies should have layers or indicators defined
            if not strategy.layers and not strategy.parameters.get("indicators"):
                errors.append("Composed strategies must have layers or indicator parameters")

            # Validate common parameters
            required_params = []
            for param in required_params:
                if param not in strategy.parameters:
                    errors.append(f"Missing required parameter: {param}")

        elif strategy.type == StrategyType.GENETIC:
            # Genetic strategies need population and generation settings
            genetic_params = ["population_size", "generations"]
            for param in genetic_params:
                if param not in strategy.parameters:
                    errors.append(f"Genetic strategies require parameter: {param}")

        # Risk level validation
        if strategy.risk_level and strategy.risk_level not in RiskLevel:
            errors.append(f"Invalid risk level: {strategy.risk_level}")

        # Validate layer IDs exist if specified
        if strategy.layers:
            with get_db_context() as session:
                layer_repo = StrategyLayerRepository(session)
                for layer_id in strategy.layers:
                    if not layer_repo.get(layer_id):
                        errors.append(f"Layer not found: {layer_id}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def calculate_performance(self, strategy_id: str) -> Dict[str, Any]:
        """
        Calculate real-time performance metrics for a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with performance metrics
        """
        with get_db_context() as session:
            from database.repositories.signal import SignalRepository

            signal_repo = SignalRepository(session)
            strategy_repo = StrategyRepository(session)

            strategy = strategy_repo.get(strategy_id)
            if not strategy:
                return {"error": "Strategy not found"}

            # Get recent signals for this strategy
            recent_signals = signal_repo.get_by_strategy(strategy_id, limit=100)

            if not recent_signals:
                return {
                    "strategy_id": strategy_id,
                    "total_signals": 0,
                    "message": "No signals generated yet",
                }

            # Calculate metrics
            buy_signals = [s for s in recent_signals if s.signal_type == "buy"]
            sell_signals = [s for s in recent_signals if s.signal_type == "sell"]
            hold_signals = [s for s in recent_signals if s.signal_type == "hold"]

            avg_confidence = sum(s.confidence or 0 for s in recent_signals) / len(recent_signals)

            return {
                "strategy_id": strategy_id,
                "total_signals": len(recent_signals),
                "buy_signals": len(buy_signals),
                "sell_signals": len(sell_signals),
                "hold_signals": len(hold_signals),
                "average_confidence": round(avg_confidence, 3),
                "latest_signal": recent_signals[0].signal_type if recent_signals else None,
                "latest_signal_time": recent_signals[0].timestamp if recent_signals else None,
            }

    def get_strategy_recommendations(
        self,
        user_id: str = "default",
        risk_preference: Optional[RiskLevel] = None,
        preferred_tags: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get strategy recommendations based on user preferences.

        Args:
            user_id: User ID for personalization
            risk_preference: Preferred risk level
            preferred_tags: Preferred strategy tags
            limit: Maximum recommendations

        Returns:
            List of recommended strategies with reasons
        """
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            fav_repo = StrategyFavoriteRepository(session)

            recommendations = []
            templates = strategy_repo.get_templates()

            # Get user's favorites for personalization
            user_favorites = fav_repo.get_user_favorites(user_id)
            favorite_strategy_ids = [f.strategy_id for f in user_favorites]

            for template in templates:
                score = 0
                reasons = []

                # Risk level match
                template_risk = getattr(template, "risk_level", None)
                if risk_preference and template_risk == risk_preference.value:
                    score += 10
                    reasons.append(f"Matches your {risk_preference.value} risk preference")

                # Tag matches
                template_tags = getattr(template, "tags", [])
                if preferred_tags:
                    matching_tags = set(preferred_tags) & set(template_tags)
                    if matching_tags:
                        score += len(matching_tags) * 5
                        reasons.append(f"Matches tags: {', '.join(matching_tags)}")

                # Backtest performance
                sharpe = getattr(template, "backtest_sharpe_ratio", None)
                if sharpe and sharpe > 1.5:
                    score += 5
                    reasons.append("Strong historical performance")

                # Favorited similar strategies
                # (Simplified - would use more sophisticated logic in production)

                if score > 0 or not risk_preference and not preferred_tags:
                    recommendations.append(
                        {
                            "strategy": self._model_to_pydantic(template),
                            "score": score,
                            "reasons": reasons or "Popular template strategy",
                        }
                    )

            # Sort by score and return top recommendations
            recommendations.sort(key=lambda x: x["score"], reverse=True)
            return recommendations[:limit]

    def export_strategy(
        self,
        strategy_id: str,
        format: str = "json",
        include_metadata: bool = True,
    ) -> str:
        """
        Export a strategy to JSON or YAML format.

        Args:
            strategy_id: Strategy to export
            format: Export format (json or yaml)
            include_metadata: Include timestamps and metadata

        Returns:
            Exported strategy as string

        Raises:
            StrategyValidationError: If strategy not found
        """
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)

            strategy = strategy_repo.get(strategy_id)
            if not strategy:
                raise StrategyValidationError(f"Strategy {strategy_id} not found")

            # Build export data
            export_data = {
                "name": strategy.name,
                "description": strategy.description,
                "type": strategy.type,
                "parameters": strategy.parameters,
                "tags": getattr(strategy, "tags", []),
                "risk_level": getattr(strategy, "risk_level", None),
            }

            # Include layers
            layers = layer_repo.get_by_strategy(strategy_id)
            export_data["layers"] = [
                {
                    "order": layer.layer_order,
                    "weight": layer.weight,
                    "config": layer.config,
                }
                for layer in layers
            ]

            # Include metadata if requested
            if include_metadata:
                export_data["metadata"] = {
                    "version": getattr(strategy, "version", 1),
                    "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
                    "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None,
                    "template_id": getattr(strategy, "template_id", None),
                    "parent_id": getattr(strategy, "parent_id", None),
                }

            # Serialize to requested format
            if format.lower() == "yaml":
                return yaml.dump(export_data, default_flow_style=False)
            else:
                return json.dumps(export_data, indent=2, default=str)

    def import_strategy(
        self,
        data: Dict[str, Any],
        name: str,
        user_id: str = "default",
        format: str = "json",
    ) -> Strategy:
        """
        Import a strategy from JSON or YAML data.

        Args:
            data: Strategy data dictionary
            name: Name for the imported strategy
            user_id: User importing the strategy
            format: Import format (json or yaml)

        Returns:
            Imported strategy

        Raises:
            StrategyValidationError: If data is invalid
        """
        # Parse data if it's a string
        if isinstance(data, str):
            if format.lower() == "yaml":
                data = yaml.safe_load(data)
            else:
                data = json.loads(data)

        # Validate required fields
        required_fields = ["type"]
        for field in required_fields:
            if field not in data:
                raise StrategyValidationError(f"Missing required field: {field}")

        # Validate strategy type
        try:
            strategy_type = StrategyType(data["type"])
        except ValueError:
            raise StrategyValidationError(f"Invalid strategy type: {data['type']}")

        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)

            # Create strategy
            new_strategy_id = f"strat_{uuid4().hex[:12]}"
            strategy = strategy_repo.create(
                id=new_strategy_id,
                name=name,
                description=data.get("description"),
                type=strategy_type.value,
                parameters=data.get("parameters", {}),
                layers=[],
                status=Status.DRAFT.value,
                tags=data.get("tags", []),
                risk_level=data.get("risk_level"),
                is_template=False,
            )

            # Create layers if provided
            layer_ids = []
            for layer_data in data.get("layers", []):
                layer = layer_repo.create(
                    id=f"layer_{uuid4().hex[:12]}",
                    strategy_id=new_strategy_id,
                    layer_order=layer_data.get("order", 0),
                    weight=layer_data.get("weight", 1.0),
                    config=layer_data.get("config", {}),
                )
                layer_ids.append(layer.id)

            # Update with layer IDs
            if layer_ids:
                strategy_repo.update(new_strategy_id, layers=layer_ids)

            logger.info(f"Imported strategy '{name}' from {format}")
            return self._model_to_pydantic(strategy)

    def clone_strategy(
        self,
        strategy_id: str,
        new_name: str,
        user_id: str = "default",
        custom_parameters: Optional[Dict[str, Any]] = None,
    ) -> Strategy:
        """
        Clone an existing strategy.

        Args:
            strategy_id: Strategy to clone
            new_name: Name for the cloned strategy
            user_id: User creating the clone
            custom_parameters: Optional parameter overrides

        Returns:
            Cloned strategy

        Raises:
            StrategyValidationError: If source strategy not found
        """
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            layer_repo = StrategyLayerRepository(session)

            # Get source strategy
            source = strategy_repo.get(strategy_id)
            if not source:
                raise StrategyValidationError(f"Strategy {strategy_id} not found")

            # Merge parameters
            final_parameters = source.parameters.copy()
            if custom_parameters:
                final_parameters.update(custom_parameters)

            # Create clone
            clone_id = f"strat_{uuid4().hex[:12]}"
            clone = strategy_repo.create(
                id=clone_id,
                name=new_name,
                description=source.description,
                type=source.type,
                parameters=final_parameters,
                layers=[],
                status=Status.DRAFT.value,
                parent_id=strategy_id,
                tags=getattr(source, "tags", []).copy(),
                risk_level=getattr(source, "risk_level", None),
                is_template=False,
            )

            # Clone layers
            source_layers = layer_repo.get_by_strategy(strategy_id)
            new_layer_ids = []
            for layer in source_layers:
                new_layer = layer_repo.create(
                    id=f"layer_{uuid4().hex[:12]}",
                    strategy_id=clone_id,
                    layer_order=layer.layer_order,
                    weight=layer.weight,
                    config=layer.config.copy(),
                )
                new_layer_ids.append(new_layer.id)

            # Update clone with layers
            strategy_repo.update(clone_id, layers=new_layer_ids)

            logger.info(f"Cloned strategy {strategy_id} as '{new_name}'")
            return self._model_to_pydantic(clone)

    def create_version_snapshot(
        self,
        strategy_id: str,
        change_description: Optional[str] = None,
        created_by: str = "system",
    ) -> str:
        """
        Create a version snapshot of a strategy.

        Args:
            strategy_id: Strategy to version
            change_description: Description of changes
            created_by: User creating the version

        Returns:
            Version ID

        Raises:
            StrategyValidationError: If strategy not found
        """
        with get_db_context() as session:
            strategy_repo = StrategyRepository(session)
            version_repo = StrategyVersionRepository(session)

            strategy = strategy_repo.get(strategy_id)
            if not strategy:
                raise StrategyValidationError(f"Strategy {strategy_id} not found")

            version = version_repo.create_version(
                strategy, change_description=change_description, created_by=created_by
            )

            logger.info(f"Created version {version.version_number} for strategy {strategy_id}")
            return version.id

    def get_version_history(self, strategy_id: str) -> List[Dict[str, Any]]:
        """
        Get version history for a strategy.

        Args:
            strategy_id: Strategy ID

        Returns:
            List of version snapshots
        """
        with get_db_context() as session:
            version_repo = StrategyVersionRepository(session)
            versions = version_repo.get_version_history(strategy_id)

            return [
                {
                    "id": v.id,
                    "version_number": v.version_number,
                    "name": v.name,
                    "change_description": v.change_description,
                    "created_by": v.created_by,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ]

    def _model_to_pydantic(self, model) -> Strategy:
        """Convert database model to Pydantic model with enhanced fields."""
        from api.strategies import model_to_strategy

        return model_to_strategy(model)


# Global instance
_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """Get global strategy manager instance."""
    global _manager
    if _manager is None:
        _manager = StrategyManager()
    return _manager


def model_to_strategy(model) -> Strategy:
    """Convert database model to Pydantic model with template metadata."""
    strategy = Strategy(
        id=model.id,
        name=model.name,
        description=model.description,
        type=model.type,
        parameters=model.parameters,
        layers=model.layers,
        status=model.status,
        logic_gate=LogicGate(getattr(model, "logic_gate", "none")),
        is_template=getattr(model, "is_template", False),
        created_at=model.created_at,
        updated_at=model.updated_at,
        template_id=getattr(model, "template_id", None),
        parent_id=getattr(model, "parent_id", None),
        tags=getattr(model, "tags", []),
        risk_level=RiskLevelEnum(getattr(model, "risk_level", None))
        if getattr(model, "risk_level", None)
        else None,
        performance_summary=getattr(model, "performance_summary", None),
    )

    if hasattr(model, "game_mode_display_name") and model.game_mode_display_name:
        strategy.game_mode_metadata = GameModeMetadata(
            display_name=model.game_mode_display_name,
            stars=getattr(model, "game_mode_stars", None),
            flavor_text=getattr(model, "game_mode_flavor_text", None),
            emoji=getattr(model, "game_mode_emoji", None),
        )

    if hasattr(model, "pro_mode_technical_name") and model.pro_mode_technical_name:
        strategy.pro_mode_metadata = ProModeMetadata(
            technical_name=model.pro_mode_technical_name,
            category=getattr(model, "pro_mode_category", None),
            complexity=getattr(model, "pro_mode_complexity", None),
        )

    if hasattr(model, "backtest_total_return") and model.backtest_total_return is not None:
        strategy.backtest_metrics = BacktestMetrics(
            total_return=model.backtest_total_return,
            sharpe_ratio=getattr(model, "backtest_sharpe_ratio", None),
            max_drawdown=getattr(model, "backtest_max_drawdown", None),
            win_rate=getattr(model, "backtest_win_rate", None),
            profit_factor=getattr(model, "backtest_profit_factor", None),
            total_trades=getattr(model, "backtest_total_trades", None),
        )

    return strategy


def model_to_layer(model) -> StrategyLayer:
    """Convert database model to Pydantic model."""
    return StrategyLayer(
        id=model.id,
        strategy_id=model.strategy_id,
        layer_order=model.layer_order,
        weight=model.weight,
        config=model.config,
    )


def create_from_template(
    template_id: str,
    name: str,
    user_id: str = "default",
    custom_parameters: Optional[Dict[str, Any]] = None,
) -> Strategy:
    """
    Create a new strategy from a template.

    Args:
        template_id: Template strategy ID
        name: Name for new strategy
        user_id: User creating strategy
        custom_parameters: Optional parameter overrides

    Returns:
        Created strategy

    Raises:
        StrategyValidationError: If template is invalid
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        template = strategy_repo.get(template_id)
        if not template:
            raise StrategyValidationError(f"Template {template_id} not found")

        if not getattr(template, "is_template", False) and template.type != "template":
            raise StrategyValidationError(f"Strategy {template_id} is not a template")

        final_parameters = template.parameters.copy()
        if custom_parameters:
            final_parameters.update(custom_parameters)

        new_strategy = strategy_repo.create(
            id=f"strat_{uuid4().hex[:12]}",
            name=name,
            description=template.description,
            type="composed",
            parameters=final_parameters,
            layers=[],
            status=Status.DRAFT.value,
            is_template=False,
        )

        template_layers = layer_repo.get_by_strategy(template_id)
        new_layer_ids = []
        for layer in template_layers:
            new_layer = layer_repo.create(
                id=f"layer_{uuid4().hex[:12]}",
                strategy_id=new_strategy.id,
                layer_order=layer.layer_order,
                weight=layer.weight,
                config=layer.config.copy(),
            )
            new_layer_ids.append(new_layer.id)

        strategy_repo.update(new_strategy.id, layers=new_layer_ids)

        logger.info(f"Created strategy '{name}' from template {template_id}")
        return model_to_strategy(new_strategy)


def update_layer_weights(strategy_id: str, weights: dict[str, float]) -> Strategy:
    """
    Update the weights of layers in a strategy.

    Args:
        strategy_id: The strategy ID
        weights: Dictionary mapping layer_id to weight (0.0-1.0)

    Returns:
        Updated strategy

    Raises:
        StrategyValidationError: If strategy or layer not found
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        strategy = strategy_repo.get(strategy_id)
        if not strategy:
            raise StrategyValidationError(f"Strategy {strategy_id} not found")

        for layer_id, weight in weights.items():
            layer = layer_repo.get(layer_id)
            if layer is None or layer.strategy_id != strategy_id:
                raise StrategyValidationError(
                    f"Layer {layer_id} not found in strategy {strategy_id}"
                )

            from database.models.strategy import StrategyLayerModel

            session.query(StrategyLayerModel).filter(StrategyLayerModel.id == layer_id).update(
                {"weight": weight}
            )

        session.refresh(strategy)
        return model_to_strategy(strategy)
