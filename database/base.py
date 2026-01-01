"""
Base repository classes for database operations.

Provides generic CRUD operations and common query patterns.
All domain-specific repositories should inherit from BaseRepository.
"""

from typing import Any, Generic, Optional, Type, TypeVar, List

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from database.models import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with generic CRUD operations.

    Provides common database operations for all models.
    Domain-specific repositories inherit from this class.

    Type Parameters:
        ModelType: The SQLAlchemy model class (must inherit from BaseModel)
    """

    def __init__(self, model: Type[ModelType], session: Session) -> None:
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    def create(self, **kwargs: Any) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def get(self, id: str) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None if not found
        """
        return self.session.get(self.model, id)

    def get_by(self, **filters: Any) -> Optional[ModelType]:
        """
        Get a single record by filters.

        Args:
            **filters: Field filters

        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_many(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        **filters: Any,
    ) -> List[ModelType]:
        """
        Get multiple records with optional filters.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            **filters: Field filters

        Returns:
            List of model instances
        """
        stmt = select(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).scalars().all())

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        Get all records.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of all model instances
        """
        return self.get_many(limit=limit, offset=offset)

    def update(self, id: str, **kwargs: Any) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        obj = self.get(id)
        if obj is None:
            return None

        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        self.session.flush()
        self.session.refresh(obj)
        return obj

    def delete(self, id: str) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        obj = self.get(id)
        if obj is None:
            return False

        self.session.delete(obj)
        self.session.flush()
        return True

    def count(self, **filters: Any) -> int:
        """
        Count records matching filters.

        Args:
            **filters: Field filters

        Returns:
            Number of matching records
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)

        return self.session.execute(stmt).scalar() or 0

    def exists(self, **filters: Any) -> bool:
        """
        Check if any records match filters.

        Args:
            **filters: Field filters

        Returns:
            True if matching records exist
        """
        return self.count(**filters) > 0

    def query(self) -> Select:
        """
        Create a new query for the model.

        Returns:
            SQLAlchemy Select statement
        """
        return select(self.model)
