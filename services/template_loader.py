"""
Strategy Template Loader Service.

Loads, validates, and provides access to strategy templates from JSON storage.
Templates can be filtered by category, difficulty, and retrieved by ID.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class TemplateDifficulty(str, Enum):
    """Template difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TemplateCategory(str, Enum):
    """Template category types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    SENTIMENT = "sentiment"
    EVENT_DRIVEN = "event_driven"


# Required fields for a valid template
REQUIRED_TEMPLATE_FIELDS = {
    "id", "name", "category", "description", "difficulty",
    "parameters", "layers", "default_config"
}

# Optional fields
OPTIONAL_TEMPLATE_FIELDS = {
    "game_mode_metadata", "pro_mode_metadata", "backtest_metrics"
}


class TemplateValidationError(Exception):
    """Raised when template validation fails."""
    pass


def validate_template(template: dict[str, Any]) -> bool:
    """
    Validate a strategy template structure.

    Args:
        template: Template dictionary to validate

    Returns:
        True if valid

    Raises:
        TemplateValidationError: If template is invalid
    """
    # Check required fields
    missing_fields = REQUIRED_TEMPLATE_FIELDS - set(template.keys())
    if missing_fields:
        raise TemplateValidationError(
            f"Template missing required fields: {missing_fields}"
        )

    # Validate ID format
    template_id = template.get("id", "")
    if not template_id or not isinstance(template_id, str):
        raise TemplateValidationError("Template ID must be a non-empty string")

    # Validate name
    name = template.get("name", "")
    if not name or not isinstance(name, str):
        raise TemplateValidationError("Template name must be a non-empty string")

    # Validate category
    category = template.get("category", "")
    try:
        TemplateCategory(category)
    except ValueError:
        valid_categories = [c.value for c in TemplateCategory]
        raise TemplateValidationError(
            f"Invalid category '{category}'. Must be one of: {valid_categories}"
        )

    # Validate difficulty
    difficulty = template.get("difficulty", "")
    try:
        TemplateDifficulty(difficulty)
    except ValueError:
        valid_difficulties = [d.value for d in TemplateDifficulty]
        raise TemplateValidationError(
            f"Invalid difficulty '{difficulty}'. Must be one of: {valid_difficulties}"
        )

    # Validate parameters
    parameters = template.get("parameters", {})
    if not isinstance(parameters, dict):
        raise TemplateValidationError("Template parameters must be a dictionary")

    # Validate layers
    layers = template.get("layers", [])
    if not isinstance(layers, list):
        raise TemplateValidationError("Template layers must be a list")

    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            raise TemplateValidationError(f"Layer {i} must be a dictionary")

        required_layer_fields = {"id", "layer_order", "weight", "config"}
        missing_layer_fields = required_layer_fields - set(layer.keys())
        if missing_layer_fields:
            raise TemplateValidationError(
                f"Layer {i} missing required fields: {missing_layer_fields}"
            )

        # Validate weight range
        weight = layer.get("weight", 0)
        if not isinstance(weight, (int, float)) or not (0 <= weight <= 1):
            raise TemplateValidationError(
                f"Layer {i} weight must be between 0 and 1, got {weight}"
            )

    # Validate default_config
    default_config = template.get("default_config", {})
    if not isinstance(default_config, dict):
        raise TemplateValidationError("Template default_config must be a dictionary")

    # Validate game_mode_metadata if present
    if "game_mode_metadata" in template:
        gmm = template["game_mode_metadata"]
        if gmm is not None and not isinstance(gmm, dict):
            raise TemplateValidationError("game_mode_metadata must be a dictionary or null")

        if gmm and "stars" in gmm:
            stars = gmm["stars"]
            if not isinstance(stars, int) or not (1 <= stars <= 5):
                raise TemplateValidationError("game_mode_metadata stars must be 1-5")

    # Validate pro_mode_metadata if present
    if "pro_mode_metadata" in template:
        pmm = template["pro_mode_metadata"]
        if pmm is not None and not isinstance(pmm, dict):
            raise TemplateValidationError("pro_mode_metadata must be a dictionary or null")

    # Validate backtest_metrics if present
    if "backtest_metrics" in template:
        bm = template["backtest_metrics"]
        if bm is not None and not isinstance(bm, dict):
            raise TemplateValidationError("backtest_metrics must be a dictionary or null")

        if bm:
            for field in ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]:
                if field in bm and bm[field] is not None:
                    if not isinstance(bm[field], (int, float)):
                        raise TemplateValidationError(f"backtest_metrics.{field} must be a number")

    return True


def load_templates(
    file_path: Optional[str | Path] = None
) -> dict[str, dict[str, Any]]:
    """
    Load all strategy templates from JSON file.

    Args:
        file_path: Path to templates JSON file. Defaults to data/strategy_templates.json

    Returns:
        Dictionary mapping template IDs to template dictionaries

    Raises:
        FileNotFoundError: If template file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        TemplateValidationError: If any template is invalid
    """
    if file_path is None:
        # Default to data/strategy_templates.json relative to project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent
        file_path = project_root / "data" / "strategy_templates.json"

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in template file: {e}")
        raise

    # Validate structure
    if "templates" not in data:
        raise TemplateValidationError("Missing 'templates' key in template file")

    if not isinstance(data["templates"], list):
        raise TemplateValidationError("'templates' must be a list")

    # Validate each template and build index
    templates = {}
    for template in data["templates"]:
        try:
            validate_template(template)
            template_id = template["id"]
            if template_id in templates:
                logger.warning(f"Duplicate template ID: {template_id}. Using first occurrence.")
                continue
            templates[template_id] = template
        except TemplateValidationError as e:
            logger.error(f"Invalid template {template.get('id', 'unknown')}: {e}")
            raise

    logger.info(f"Loaded {len(templates)} strategy templates from {path}")
    return templates


def get_template(
    template_id: str,
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> Optional[dict[str, Any]]:
    """
    Get a specific template by ID.

    Args:
        template_id: ID of the template to retrieve
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        Template dictionary or None if not found
    """
    if templates is None:
        templates = load_templates()

    return templates.get(template_id)


def get_templates_by_category(
    category: str,
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> list[dict[str, Any]]:
    """
    Get templates filtered by category.

    Args:
        category: Category to filter by (e.g., "trend_following")
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        List of templates matching the category
    """
    if templates is None:
        templates = load_templates()

    return [
        template for template in templates.values()
        if template.get("category") == category
    ]


def get_templates_by_difficulty(
    difficulty: str,
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> list[dict[str, Any]]:
    """
    Get templates filtered by difficulty level.

    Args:
        difficulty: Difficulty level to filter by ("beginner", "intermediate", "advanced")
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        List of templates matching the difficulty
    """
    if templates is None:
        templates = load_templates()

    return [
        template for template in templates.values()
        if template.get("difficulty") == difficulty
    ]


def get_template_categories(
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> list[str]:
    """
    Get list of all unique categories in templates.

    Args:
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        List of unique category values
    """
    if templates is None:
        templates = load_templates()

    categories = set(template.get("category") for template in templates.values())
    return sorted(categories)


def get_template_difficulties(
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> list[str]:
    """
    Get list of all unique difficulty levels in templates.

    Args:
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        List of unique difficulty values
    """
    if templates is None:
        templates = load_templates()

    difficulties = set(template.get("difficulty") for template in templates.values())
    return sorted(difficulties)


def search_templates(
    query: str,
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> list[dict[str, Any]]:
    """
    Search templates by name or description.

    Args:
        query: Search query string
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        List of templates matching the search query
    """
    if templates is None:
        templates = load_templates()

    query_lower = query.lower()

    return [
        template for template in templates.values()
        if query_lower in template.get("name", "").lower()
        or query_lower in template.get("description", "").lower()
    ]


def get_template_summary(
    templates: Optional[dict[str, dict[str, Any]]] = None
) -> dict[str, Any]:
    """
    Get summary statistics about available templates.

    Args:
        templates: Pre-loaded templates dict. If None, loads from file.

    Returns:
        Dictionary with template statistics
    """
    if templates is None:
        templates = load_templates()

    summary = {
        "total_templates": len(templates),
        "categories": {},
        "difficulties": {}
    }

    for template in templates.values():
        category = template.get("category", "unknown")
        difficulty = template.get("difficulty", "unknown")

        summary["categories"][category] = summary["categories"].get(category, 0) + 1
        summary["difficulties"][difficulty] = summary["difficulties"].get(difficulty, 0) + 1

    return summary


# Cache for loaded templates
_template_cache: Optional[dict[str, dict[str, Any]]] = None


def get_cached_templates() -> dict[str, dict[str, Any]]:
    """
    Get templates from cache, loading if necessary.

    Returns:
        Cached templates dictionary
    """
    global _template_cache

    if _template_cache is None:
        _template_cache = load_templates()

    return _template_cache


def clear_template_cache() -> None:
    """Clear the template cache. Forces reload on next access."""
    global _template_cache
    _template_cache = None
    logger.info("Template cache cleared")
