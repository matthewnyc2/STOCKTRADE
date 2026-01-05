"""
Seed script to load strategy templates into the database.

This script reads templates from data/strategy_templates.json and creates
corresponding strategy records in the database marked as templates.

Usage:
    python -m scripts.seed_templates
"""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.connection import get_db_session
from database.repositories import StrategyRepository, StrategyLayerRepository
from models import StrategyType, Status
from services.template_loader import load_templates, validate_template


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_templates(
    clear_existing: bool = False,
    template_file: str = None
) -> int:
    """
    Seed strategy templates into the database.

    Args:
        clear_existing: If True, delete existing templates first
        template_file: Path to template JSON file (uses default if None)

    Returns:
        Number of templates created

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    # Load templates from JSON
    logger.info(f"Loading templates from {template_file or 'default location'}...")
    templates = load_templates(template_file)

    logger.info(f"Loaded {len(templates)} templates from file")

    with get_db_session() as session:
        strategy_repo = StrategyRepository(session)
        layer_repo = StrategyLayerRepository(session)

        # Clear existing templates if requested
        if clear_existing:
            existing_templates = session.query(strategy_repo.model).filter_by(is_template=True).all()
            count = len(existing_templates)
            for template in existing_templates:
                # Delete layers first
                layer_repo.delete_by_strategy(template.id)
                session.delete(template)
            session.commit()
            logger.info(f"Cleared {count} existing templates from database")

        # Create template records
        created_count = 0
        updated_count = 0

        for template_id, template_data in templates.items():
            try:
                # Validate template
                validate_template(template_data)

                # Check if template already exists
                existing = session.query(strategy_repo.model).filter_by(
                    id=template_id,
                    is_template=True
                ).first()

                # Prepare metadata - flatten nested dicts into individual columns
                game_mode_metadata = template_data.get("game_mode_metadata") or {}
                pro_mode_metadata = template_data.get("pro_mode_metadata") or {}
                backtest_metrics = template_data.get("backtest_metrics") or {}

                # Extract game_mode_metadata fields
                game_mode_display_name = game_mode_metadata.get("display_name")
                game_mode_stars = game_mode_metadata.get("stars")
                game_mode_flavor_text = game_mode_metadata.get("flavor_text")
                game_mode_emoji = game_mode_metadata.get("emoji")

                # Extract pro_mode_metadata fields
                pro_mode_technical_name = pro_mode_metadata.get("technical_name")
                pro_mode_category = pro_mode_metadata.get("category")
                pro_mode_complexity = pro_mode_metadata.get("complexity")

                # Extract backtest_metrics fields
                backtest_total_return = backtest_metrics.get("total_return")
                backtest_sharpe_ratio = backtest_metrics.get("sharpe_ratio")
                backtest_max_drawdown = backtest_metrics.get("max_drawdown")
                backtest_win_rate = backtest_metrics.get("win_rate")
                backtest_profit_factor = backtest_metrics.get("profit_factor")
                backtest_total_trades = backtest_metrics.get("total_trades")

                if existing:
                    # Update existing template
                    existing.name = template_data["name"]
                    existing.description = template_data["description"]
                    existing.parameters = template_data["parameters"]
                    existing.game_mode_display_name = game_mode_display_name
                    existing.game_mode_stars = game_mode_stars
                    existing.game_mode_flavor_text = game_mode_flavor_text
                    existing.game_mode_emoji = game_mode_emoji
                    existing.pro_mode_technical_name = pro_mode_technical_name
                    existing.pro_mode_category = pro_mode_category
                    existing.pro_mode_complexity = pro_mode_complexity
                    existing.backtest_total_return = backtest_total_return
                    existing.backtest_sharpe_ratio = backtest_sharpe_ratio
                    existing.backtest_max_drawdown = backtest_max_drawdown
                    existing.backtest_win_rate = backtest_win_rate
                    existing.backtest_profit_factor = backtest_profit_factor
                    existing.backtest_total_trades = backtest_total_trades

                    # Update layers
                    layer_repo.delete_by_strategy(template_id)

                    import uuid
                    layer_ids = []
                    for layer_data in template_data["layers"]:
                        layer_id = f"layer_{uuid.uuid4().hex[:8]}"
                        layer = layer_repo.create(
                            id=layer_id,
                            strategy_id=template_id,
                            layer_order=layer_data["layer_order"],
                            weight=layer_data["weight"],
                            config=layer_data["config"]
                        )
                        layer_ids.append(layer.id)

                    existing.layers = layer_ids
                    updated_count += 1
                    logger.info(f"Updated template: {template_data['name']} ({template_id})")

                else:
                    # Create new template
                    strategy = strategy_repo.create(
                        id=template_id,
                        name=template_data["name"],
                        description=template_data["description"],
                        type=StrategyType.TEMPLATE,
                        parameters=template_data["parameters"],
                        status=Status.ACTIVE,  # Templates are active by default
                        is_template=True,
                        game_mode_display_name=game_mode_display_name,
                        game_mode_stars=game_mode_stars,
                        game_mode_flavor_text=game_mode_flavor_text,
                        game_mode_emoji=game_mode_emoji,
                        pro_mode_technical_name=pro_mode_technical_name,
                        pro_mode_category=pro_mode_category,
                        pro_mode_complexity=pro_mode_complexity,
                        backtest_total_return=backtest_total_return,
                        backtest_sharpe_ratio=backtest_sharpe_ratio,
                        backtest_max_drawdown=backtest_max_drawdown,
                        backtest_win_rate=backtest_win_rate,
                        backtest_profit_factor=backtest_profit_factor,
                        backtest_total_trades=backtest_total_trades
                    )

                    # Create layers
                    import uuid
                    layer_ids = []
                    for layer_data in template_data["layers"]:
                        layer_id = f"layer_{uuid.uuid4().hex[:8]}"
                        layer = layer_repo.create(
                            id=layer_id,
                            strategy_id=strategy.id,
                            layer_order=layer_data["layer_order"],
                            weight=layer_data["weight"],
                            config=layer_data["config"]
                        )
                        layer_ids.append(layer.id)

                    strategy.layers = layer_ids
                    created_count += 1
                    logger.info(f"Created template: {template_data['name']} ({template_id})")

                session.commit()

            except Exception as e:
                logger.error(f"Error seeding template {template_id}: {e}")
                session.rollback()
                continue

        logger.info(f"Seeding complete: {created_count} created, {updated_count} updated")

        # Print summary
        total_templates = session.query(strategy_repo.model).filter_by(is_template=True).count()
        logger.info(f"Total templates in database: {total_templates}")

        return created_count


def main():
    """Main entry point for the seed script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed strategy templates into the database"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing templates before seeding"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to template JSON file (default: data/strategy_templates.json)"
    )

    args = parser.parse_args()

    try:
        count = seed_templates(clear_existing=args.clear, template_file=args.file)
        logger.info(f"Successfully seeded {count} templates")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Template file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error seeding templates: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
