"""
Repository for user operations.
"""

from typing import Optional

from sqlalchemy.orm import Session

from database.models.user import UserModel
from database.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """
    Repository for managing user data.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize user repository.

        Args:
            session: Database session
        """
        super().__init__(UserModel, session)

    def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        Get a user by email.

        Args:
            email: User email address

        Returns:
            User model or None if not found
        """
        return self.get_by(email=email)

    def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        Get a user by username.

        Args:
            username: Username

        Returns:
            User model or None if not found
        """
        return self.get_by(username=username)
