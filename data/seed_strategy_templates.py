"""
Seed strategy templates from JSON file into the database.

This script reads strategy templates from data/strategy_templates.json
and loads them into the database as template strategies.
"""

import json
import logging
from pathlib import Path
from uuid import uuid4

from database.connection import get_db_context
from database.repositories import StrategyRepository, StrategyLayerRepository


logger = logging.getLogger(__name__)


def load_template_templates() -> dict:
    """Load strategy templates from JSON file."""
    template_file = Path(__file__).parent / "strategy_templates.json"

    with open(template_file, "r") as f:
        return json.load(f)


def map_difficulty_to_risk(difficulty: str) -> str:
    """Map difficulty level to risk level."""
    mapping = {
        "beginner": "low",
        "intermediate": "medium",
        "advanced": "high",
    }
    return mapping.get(difficulty, "medium")


def seed_strategy_templates() -> None:
    """
    Seed strategy templates into the database.

    Reads templates from strategy_templates.json and creates
    template strategies in the database.
    """
    with get_db_context() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Load templates from JSON
        templates_data = load_template_templates()
        templates = templates_data.get("templates", [])

        if not templates:
            logger.warning("No templates found in strategy_templates.json")
            return

        # Check if templates already exist
        existing_templates = strategy_repo.get_templates()
        if existing_templates:
            logger.info(f"Found {len(existing_templates)} existing templates in database")
            # Could skip or update - for now we'll log and continue
            # Return early to avoid duplicates
            # logger.info("Templates already exist, skipping seed.")
            # return

        created_count = 0
        updated_count = 0

        for template_data in templates:
            template_id = template_data.get("id", f"tpl_{uuid4().hex[:12]}")

            # Check if template already exists
            existing = strategy_repo.get(template_id)

            # Extract data
            name = template_data.get("name")
            description = template_data.get("description")
            category = template_data.get("category", "")
            difficulty = template_data.get("difficulty", "intermediate")

            # Map category to tags
            tags = [category]
            if "tags" in template_data:
                tags.extend(template_data["tags"])

            # Add difficulty as a tag
            if difficulty:
                tags.append(difficulty)

            # Game Mode metadata
            game_mode = template_data.get("game_mode_metadata", {})
            pro_mode = template_data.get("pro_mode_metadata", {})
            backtest = template_data.get("backtest_metrics", {})

            # Risk level from difficulty
            risk_level = map_difficulty_to_risk(difficulty)

            # Strategy data
            strategy_data = {
                "id": template_id,
                "name": name,
                "description": description,
                "type": "composed",
                "parameters": template_data.get("parameters", {}),
                "layers": [],
                "status": "active",  # Templates are active by default
                "logic_gate": template_data.get("default_config", {}).get("logic_gate", "none"),
                "tags": tags,
                "risk_level": risk_level,
                # Game Mode fields
                "game_mode_display_name": game_mode.get("display_name"),
                "game_mode_stars": game_mode.get("stars"),
                "game_mode_flavor_text": game_mode.get("flavor_text"),
                "game_mode_emoji": game_mode.get("emoji"),
                # Pro Mode fields
                "pro_mode_technical_name": pro_mode.get("technical_name"),
                "pro_mode_category": pro_mode.get("category") or category,
                "pro_mode_complexity": pro_mode.get("complexity") or difficulty.title(),
                # Backtest metrics
                "backtest_total_return": backtest.get("total_return"),
                "backtest_sharpe_ratio": backtest.get("sharpe_ratio"),
                "backtest_max_drawdown": backtest.get("max_drawdown"),
                "backtest_win_rate": backtest.get("win_rate"),
                "backtest_profit_factor": backtest.get("profit_factor"),
                "backtest_total_trades": backtest.get("total_trades"),
                "is_template": True,
            }

            # Get layer data
            layers_data = template_data.get("layers", [])
            layer_ids = []

            if existing:
                # Update existing template
                strategy_repo.update(template_id, **strategy_data)
                updated_count += 1

                # Delete existing layers and recreate
                layer_repo.delete_by_strategy(template_id)
                session.flush()

                for layer_data in layers_data:
                    layer = layer_repo.create(
                        id=f"layer_{uuid4().hex[:12]}",
                        strategy_id=template_id,
                        layer_order=layer_data.get("layer_order", 0),
                        weight=layer_data.get("weight", 1.0),
                        config=layer_data.get("config", {}),
                    )
                    layer_ids.append(layer.id)

                if layer_ids:
                    strategy_repo.update(template_id, layers=layer_ids)

            else:
                # Create new template
                strategy = strategy_repo.create(**strategy_data)

                for layer_data in layers_data:
                    layer = layer_repo.create(
                        id=f"layer_{uuid4().hex[:12]}",
                        strategy_id=template_id,
                        layer_order=layer_data.get("layer_order", 0),
                        weight=layer_data.get("weight", 1.0),
                        config=layer_data.get("config", {}),
                    )
                    layer_ids.append(layer.id)

                if layer_ids:
                    strategy_repo.update(template_id, layers=layer_ids)

                created_count += 1

        logger.info(f"Seeded strategy templates: {created_count} created, {updated_count} updated")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_strategy_templates()
