"""
Settings-related SQLAlchemy ORM models.
"""

from typing import Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.models import BaseModel


class SettingsModel(BaseModel):
    """
    SQLAlchemy model for application settings.

    Stores user and system settings configuration.
    Uses a single row with id='default' for the settings.
    """

    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    ui_mode: Mapped[str] = mapped_column(String(50), default="pro")  # UIMode enum
    risk_parameters: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "max_position_size": 0.1,
            "max_daily_loss": 0.05,
            "stop_loss_enabled": True,
            "max_open_positions": 10,
        }
    )
    notifications: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "email_enabled": False,
            "slack_enabled": False,
            "alert_types": [],
        }
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
