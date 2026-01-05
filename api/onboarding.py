"""
Onboarding API router.

Handles initial data collection, API keys, and system configuration.
"""

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, SecretStr


# ============================================================================
# Pydantic Models
# ============================================================================

class APIKeysInput(BaseModel):
    """API keys for external services."""

    binance_api_key: SecretStr | None = Field(default=None, description="Binance API Key")
    binance_api_secret: SecretStr | None = Field(default=None, description="Binance API Secret")
    coingecko_api_key: SecretStr | None = Field(default=None, description="CoinGecko Pro API Key")
    etherscan_api_key: SecretStr | None = Field(default=None, description="Etherscan API Key")
    whale_alert_api_key: SecretStr | None = Field(default=None, description="Whale Alert API Key")
    openai_api_key: SecretStr | None = Field(default=None, description="OpenAI API Key for AI reasoning")
    anthropic_api_key: SecretStr | None = Field(default=None, description="Anthropic API Key for AI reasoning")


class TradingPreferences(BaseModel):
    """Trading configuration preferences."""

    default_symbols: list[str] = Field(
        default_factory=lambda: ["BTCUSDT", "ETHUSDT"],
        description="Default trading symbols"
    )
    default_timeframe: str = Field(default="1h", description="Default timeframe for analysis")
    max_position_size: float = Field(ge=0.0, le=1.0, default=0.1, description="Max position size as % of portfolio")
    max_daily_loss: float = Field(ge=0.0, le=1.0, default=0.05, description="Max daily loss as % of portfolio")
    stop_loss_enabled: bool = Field(default=True, description="Enable automatic stop-loss")
    take_profit_enabled: bool = Field(default=True, description="Enable automatic take-profit")


class UserPreferences(BaseModel):
    """User experience preferences."""

    ui_mode: str = Field(default="pro", description="UI mode: 'game' or 'pro'")
    timezone: str = Field(default="UTC", description="User timezone")
    currency: str = Field(default="USD", description="Preferred currency for display")
    email_notifications: bool = Field(default=False, description="Enable email notifications")
    slack_notifications: bool = Field(default=False, description="Enable Slack notifications")


class OnboardingData(BaseModel):
    """Complete onboarding data submission."""

    api_keys: APIKeysInput
    trading_preferences: TradingPreferences
    user_preferences: UserPreferences
    skip_exchanges: bool = Field(default=False, description="Skip exchange configuration")


class OnboardingStatus(BaseModel):
    """Onboarding completion status."""

    completed: bool
    steps_completed: list[str]
    steps_remaining: list[str]
    configured_apis: list[str]


class DataCollectionResponse(BaseModel):
    """Response for data collection submission."""

    success: bool
    message: str
    saved_keys: list[str]
    warnings: list[str] = Field(default_factory=list)


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# Store onboarding status in memory (in production, use database)
_onboarding_completed = False
_configured_apis = set()


def _get_env_path() -> Path:
    """Get the .env file path."""
    return Path(__file__).parent.parent / ".env"


def _save_to_env(api_keys: APIKeysInput) -> list[str]:
    """
    Save API keys to .env file.

    Returns:
        List of successfully saved key names.
    """
    env_path = _get_env_path()
    saved_keys = []

    # Read existing .env content
    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text().splitlines()

    # Create a set of existing key names
    existing_keys = set()
    for line in existing_lines:
        if line and not line.startswith("#") and "=" in line:
            existing_keys.add(line.split("=")[0])

    # Prepare new lines to add
    new_lines = []
    key_mapping = {
        "binance_api_key": "BINANCE_API_KEY",
        "binance_api_secret": "BINANCE_API_SECRET",
        "coingecko_api_key": "COINGECKO_API_KEY",
        "etherscan_api_key": "ETHERSCAN_API_KEY",
        "whale_alert_api_key": "WHALE_ALERT_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
    }

    for field_name, env_name in key_mapping.items():
        secret_value = getattr(api_keys, field_name)
        if secret_value and secret_value.get_secret_value():
            value = secret_value.get_secret_value()
            # Update if exists, otherwise add
            line_to_add = f"{env_name}={value}"

            # Check if this key already exists
            key_exists = False
            for i, line in enumerate(existing_lines):
                if line.startswith(f"{env_name}="):
                    existing_lines[i] = line_to_add
                    key_exists = True
                    break

            if not key_exists:
                new_lines.append(line_to_add)

            saved_keys.append(env_name)

    # Write back to .env
    if saved_keys or new_lines:
        with open(env_path, "w") as f:
            f.write("\n".join(existing_lines + new_lines))

    return saved_keys


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status() -> OnboardingStatus:
    """
    Get current onboarding status.

    Returns:
        OnboardingStatus: Current status of onboarding process.
    """
    env_path = _get_env_path()
    configured = set()

    if env_path.exists():
        content = env_path.read_text()
        keys_to_check = [
            "BINANCE_API_KEY",
            "COINGECKO_API_KEY",
            "ETHERSCAN_API_KEY",
            "WHALE_ALERT_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]
        for key in keys_to_check:
            if key in content:
                configured.add(key.lower().replace("_api_key", "").replace("_", " "))

    steps = ["api_keys", "trading_preferences", "user_preferences"]
    completed = [s for s in steps if s in configured or _onboarding_completed]
    remaining = [s for s in steps if s not in completed]

    return OnboardingStatus(
        completed=_onboarding_completed or len(completed) == len(steps),
        steps_completed=completed,
        steps_remaining=remaining,
        configured_apis=list(configured),
    )


@router.post("/submit", response_model=DataCollectionResponse)
async def submit_onboarding_data(data: OnboardingData) -> DataCollectionResponse:
    """
    Submit onboarding data and save configuration.

    Args:
        data: Complete onboarding data including API keys and preferences.

    Returns:
        DataCollectionResponse: Success status with details of saved data.
    """
    global _onboarding_completed, _configured_apis

    warnings = []
    saved_keys = []

    # Save API keys
    if not data.skip_exchanges:
        saved_keys = _save_to_env(data.api_keys)
        _configured_apis.update(saved_keys)

        # Validate which APIs were configured
        if not any([
            data.api_keys.binance_api_key.get_secret_value() if data.api_keys.binance_api_key else False,
            data.api_keys.coingecko_api_key.get_secret_value() if data.api_keys.coingecko_api_key else False,
        ]):
            warnings.append("No exchange API keys provided. Some features may not work.")

        if not any([
            data.api_keys.openai_api_key.get_secret_value() if data.api_keys.openai_api_key else False,
            data.api_keys.anthropic_api_key.get_secret_value() if data.api_keys.anthropic_api_key else False,
        ]):
            warnings.append("No AI API keys provided. AI reasoning features will not work.")

    # Store preferences (in production, save to database)
    # For now, we'll just validate the data
    if data.trading_preferences.max_position_size > 0.5:
        warnings.append("High max position size may increase risk.")

    if data.trading_preferences.max_daily_loss > 0.1:
        warnings.append("High max daily loss threshold may lead to significant losses.")

    # Update status
    _onboarding_completed = True

    return DataCollectionResponse(
        success=True,
        message="Configuration saved successfully",
        saved_keys=saved_keys,
        warnings=warnings,
    )


@router.post("/api-keys", response_model=DataCollectionResponse)
async def save_api_keys(api_keys: APIKeysInput) -> DataCollectionResponse:
    """
    Save API keys separately.

    Args:
        api_keys: API keys for external services.

    Returns:
        DataCollectionResponse: Success status with saved key names.
    """
    saved_keys = _save_to_env(api_keys)
    global _configured_apis
    _configured_apis.update(saved_keys)

    return DataCollectionResponse(
        success=True,
        message=f"Saved {len(saved_keys)} API key(s)",
        saved_keys=saved_keys,
    )


@router.get("/api-keys/validate")
async def validate_api_keys() -> dict[str, Any]:
    """
    Validate currently configured API keys.

    Returns:
        Dict with validation results for each API.
    """
    env_path = _get_env_path()
    results = {}

    if not env_path.exists():
        return {"valid": False, "apis": {}}

    content = env_path.read_text()

    # Check for presence of each API key
    apis_to_check = {
        "binance": "BINANCE_API_KEY",
        "coingecko": "COINGECKO_API_KEY",
        "etherscan": "ETHERSCAN_API_KEY",
        "whale_alert": "WHALE_ALERT_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }

    for api_name, env_key in apis_to_check.items():
        key_present = env_key in content and content.split(f"{env_key}=")[1].split("\n")[0].strip()
        results[api_name] = {
            "configured": bool(key_present),
            "key_length": len(key_present) if key_present else 0,
        }

    return {
        "valid": any(v["configured"] for v in results.values()),
        "apis": results,
    }


@router.post("/reset")
async def reset_onboarding() -> dict[str, str]:
    """
    Reset onboarding status (for testing/reconfiguration).

    Returns:
        Confirmation message.
    """
    global _onboarding_completed, _configured_apis
    _onboarding_completed = False
    _configured_apis.clear()

    return {"message": "Onboarding reset successfully"}


@router.post("/skip")
async def skip_onboarding() -> dict[str, str]:
    """
    Skip onboarding and proceed with defaults.

    Returns:
        Confirmation message.
    """
    global _onboarding_completed
    _onboarding_completed = True

    return {"message": "Onboarding skipped. Using default configuration."}
