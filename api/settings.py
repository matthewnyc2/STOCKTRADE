"""
Settings API router.

Endpoints for user and system settings management.
"""

import logging
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from models import Settings, UIMode
from services.strategy_manager import get_strategy_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

# In-memory settings store (in production, use database)
_user_settings = {
    "ui_mode": UIMode.PRO,
    "theme": "dark",
    "timezone": "UTC",
    "currency": "USD",
    "risk_parameters": {
        "max_position_size": 0.1,
        "max_daily_loss": 0.05,
        "stop_loss_enabled": True,
        "take_profit_enabled": True,
    },
    "notifications": {
        "email_enabled": False,
        "slack_enabled": False,
        "signal_alerts": True,
        "trade_executions": True,
    },
}


@router.get("/", response_model=Settings)
async def get_settings() -> Settings:
    """
    Get current user settings.

    Returns:
        Settings: Current user settings.
    """
    return Settings(
        ui_mode=_user_settings.get("ui_mode", UIMode.PRO),
        risk_parameters=_user_settings.get("risk_parameters", {}),
        notifications=_user_settings.get("notifications", {}),
    )


@router.put("/", response_model=Settings)
async def update_settings(settings_data: dict[str, Any]) -> Settings:
    """
    Update user settings.

    Args:
        settings_data: The settings to update.

    Returns:
        Settings: Updated settings.
    """
    # Update UI mode if provided
    if "ui_mode" in settings_data:
        try:
            _user_settings["ui_mode"] = UIMode(settings_data["ui_mode"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UI mode: {settings_data['ui_mode']}",
            )

    # Update risk parameters if provided
    if "risk_parameters" in settings_data:
        risk_params = settings_data["risk_parameters"]
        # Validate risk parameters
        if "max_position_size" in risk_params:
            if not 0 < risk_params["max_position_size"] <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="max_position_size must be between 0 and 1",
                )
        if "max_daily_loss" in risk_params:
            if not 0 < risk_params["max_daily_loss"] <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="max_daily_loss must be between 0 and 1",
                )

        _user_settings["risk_parameters"].update(risk_params)

    # Update notifications if provided
    if "notifications" in settings_data:
        _user_settings["notifications"].update(settings_data["notifications"])

    # Update other settings
    for key in ["theme", "timezone", "currency"]:
        if key in settings_data:
            _user_settings[key] = settings_data[key]

    logger.info(f"Settings updated: {list(settings_data.keys())}")

    return Settings(
        ui_mode=_user_settings["ui_mode"],
        risk_parameters=_user_settings["risk_parameters"],
        notifications=_user_settings["notifications"],
    )


@router.get("/risk", response_model=dict[str, Any])
async def get_risk_parameters() -> dict[str, Any]:
    """
    Get current risk management parameters.

    Returns:
        dict: Risk parameter configuration.
    """
    return _user_settings.get(
        "risk_parameters",
        {
            "max_position_size": 0.1,
            "max_daily_loss": 0.05,
            "stop_loss_enabled": True,
            "take_profit_enabled": True,
        },
    )


@router.put("/risk", response_model=dict[str, Any])
async def update_risk_parameters(risk_data: dict[str, Any]) -> dict[str, Any]:
    """
    Update risk management parameters.

    Args:
        risk_data: The risk parameters to update.

    Returns:
        dict: Updated risk parameters.
    """
    # Validate risk parameters
    if "max_position_size" in risk_data:
        if not 0 < risk_data["max_position_size"] <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_position_size must be between 0 and 1",
            )

    if "max_daily_loss" in risk_data:
        if not 0 < risk_data["max_daily_loss"] <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_daily_loss must be between 0 and 1",
            )

    # Update risk parameters
    _user_settings["risk_parameters"].update(risk_data)

    logger.info(f"Risk parameters updated: {risk_data}")

    return _user_settings["risk_parameters"]


@router.get("/all")
async def get_all_settings() -> dict[str, Any]:
    """
    Get all settings including UI, risk, and notification preferences.

    Returns:
        dict: All user settings
    """
    return {
        "ui_mode": _user_settings.get("ui_mode", UIMode.PRO),
        "theme": _user_settings.get("theme", "dark"),
        "timezone": _user_settings.get("timezone", "UTC"),
        "currency": _user_settings.get("currency", "USD"),
        "risk_parameters": _user_settings.get("risk_parameters", {}),
        "notifications": _user_settings.get("notifications", {}),
    }


@router.post("/reset")
async def reset_settings() -> dict[str, str]:
    """
    Reset settings to defaults.

    Returns:
        dict: Confirmation message
    """
    global _user_settings
    _user_settings = {
        "ui_mode": UIMode.PRO,
        "theme": "dark",
        "timezone": "UTC",
        "currency": "USD",
        "risk_parameters": {
            "max_position_size": 0.1,
            "max_daily_loss": 0.05,
            "stop_loss_enabled": True,
            "take_profit_enabled": True,
        },
        "notifications": {
            "email_enabled": False,
            "slack_enabled": False,
            "signal_alerts": True,
            "trade_executions": True,
        },
    }

    logger.info("Settings reset to defaults")

    return {"message": "Settings reset to defaults"}
