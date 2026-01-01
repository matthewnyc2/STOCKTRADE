"""
Settings-related Pydantic models.

Defines user and system settings configuration.
"""

from typing import Optional

from enum import Enum

from pydantic import BaseModel, Field


class UIMode(str, Enum):
    """Enum for UI mode settings."""

    GAME = "game"
    PRO = "pro"


class RiskParameters(BaseModel):
    """Risk management parameters."""

    max_position_size: float = Field(ge=0.0, le=1.0, default=0.1)
    max_daily_loss: float = Field(ge=0.0, le=1.0, default=0.05)
    stop_loss_enabled: bool = Field(default=True)
    max_open_positions: int = Field(ge=1, default=10)


class NotificationSettings(BaseModel):
    """Notification configuration."""

    email_enabled: bool = Field(default=False)
    slack_enabled: bool = Field(default=False)
    alert_types: list[str] = Field(default_factory=list)


class Settings(BaseModel):
    """
    Represents user and system settings.

    Contains UI preferences, risk parameters, and notification settings.
    """

    ui_mode: UIMode = Field(default=UIMode.PRO)
    risk_parameters: RiskParameters = Field(default_factory=RiskParameters)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    timezone: str = Field(default="UTC")
    currency: str = Field(default="USD")
    metadata: dict = Field(default_factory=dict)
