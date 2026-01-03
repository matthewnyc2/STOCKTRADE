"""
Trader Repository for database operations.

Handles all database interactions related to the Trader models.
"""
from typing import Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from database.models.trader import Trader, TraderActivity, TraderProfile
from models.trader import Trader as TraderModel

class TraderRepository:
    """Repository for Trader-related database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get(self, trader_id: str) -> Trader | None:
        """Get a trader by their ID."""
        return self.session.query(Trader).filter(Trader.id == trader_id).first()

    def get_by_username(self, username: str, exchange: str) -> Trader | None:
        """Get a trader by their username and exchange."""
        return self.session.query(Trader).filter(
            Trader.username == username, Trader.exchange == exchange
        ).first()

    def get_all(self, limit: int = 100) -> list[Trader]:
        """Get all tracked traders."""
        return self.session.query(Trader).limit(limit).all()

    def get_by_exchange(self, exchange: str, limit: int = 100) -> list[Trader]:
        """Get traders by exchange."""
        return self.session.query(Trader).filter(Trader.exchange == exchange).limit(limit).all()

    def create(self, **kwargs: Any) -> Trader:
        """Create a new tracked trader."""
        trader = Trader(**kwargs)
        self.session.add(trader)
        self.session.commit()
        return trader

    def update(self, trader_id: str, **kwargs: Any) -> Trader | None:
        """Update a trader's details."""
        trader = self.get(trader_id)
        if trader:
            for key, value in kwargs.items():
                setattr(trader, key, value)
            self.session.commit()
        return trader

    def get_activity(self, trader_id: str, limit: int = 50) -> list[TraderActivity]:
        """Get a trader's recent activity."""
        return self.session.query(TraderActivity).filter(
            TraderActivity.trader_id == trader_id
        ).order_by(TraderActivity.timestamp.desc()).limit(limit).all()

    def add_activity(self, **kwargs: Any) -> TraderActivity:
        """Add a new activity record for a trader."""
        activity = TraderActivity(**kwargs)
        self.session.add(activity)
        self.session.commit()
        
        # Update trader's last activity timestamp
        self.update(kwargs['trader_id'], last_activity=datetime.utcnow())
        
        return activity

    def get_profile(self, trader_id: str) -> TraderProfile | None:
        """Get a trader's profile."""
        return self.session.query(TraderProfile).filter(TraderProfile.trader_id == trader_id).first()

    def update_profile(self, trader_id: str, profile_data: dict[str, Any]) -> TraderProfile:
        """Create or update a trader's profile."""
        stmt = insert(TraderProfile).values(
            trader_id=trader_id, **profile_data
        ).on_conflict_do_update(
            index_elements=['trader_id'],
            set_=profile_data
        )
        self.session.execute(stmt)
        self.session.commit()
        return self.get_profile(trader_id)
