"""
Settings repository implementations.
"""

from sqlalchemy.orm import Session

from database.base import BaseRepository
from database.models import SettingsModel


class SettingsRepository(BaseRepository[SettingsModel]):
    """Repository for settings operations."""

    def __init__(self, session: Session) -> None:
        super().__init__(SettingsModel, session)

    def get_settings(self) -> SettingsModel:
        """Get the current settings (creates default if doesn't exist)."""
        settings = self.get("default")
        if settings is None:
            # Create default settings
            settings = self.create(id="default")
        return settings

    def update_ui_mode(self, ui_mode: str) -> SettingsModel:
        """Update UI mode setting."""
        return self.update("default", ui_mode=ui_mode)

    def update_risk_parameters(self, risk_parameters: dict) -> SettingsModel:
        """Update risk parameters."""
        return self.update("default", risk_parameters=risk_parameters)

    def update_notifications(self, notifications: dict) -> SettingsModel:
        """Update notification settings."""
        return self.update("default", notifications=notifications)

    def update_timezone(self, timezone: str) -> SettingsModel:
        """Update timezone setting."""
        return self.update("default", timezone=timezone)

    def update_currency(self, currency: str) -> SettingsModel:
        """Update currency setting."""
        return self.update("default", currency=currency)
