"""Pagination utilities for query operations."""

from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Query


# Type variable for generic pagination response
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters with validation."""
    
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum number of items to return")
    
    def apply_to_query(self, query: Query) -> Query:
        """Apply pagination parameters to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            Query object with offset and limit applied
        """
        return query.offset(self.offset).limit(self.limit)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper.
    
    Provides a consistent pagination response structure across endpoints.
    """
    
    items: List[T]
    total: int = Field(description="Total number of items across all pages")
    offset: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum number of items returned")
    
    @property
    def has_next(self) -> bool:
        """Check if there are more items after the current page."""
        return self.offset + self.limit < self.total
    
    @property
    def has_previous(self) -> bool:
        """Check if there are items before the current page."""
        return self.offset > 0
    
    @property
    def page_count(self) -> int:
        """Calculate the total number of pages."""
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit
    
    @property
    def current_page(self) -> int:
        """Calculate the current page number (1-indexed)."""
        if self.limit == 0:
            return 0
        return (self.offset // self.limit) + 1


def paginate_query(query: Query, offset: int = 0, limit: int = 50) -> tuple[List, int]:
    """Apply pagination to a query and return results with total count.
    
    This is a convenience function that combines counting and pagination
    into a single operation.
    
    Args:
        query: SQLAlchemy query object
        offset: Number of items to skip (default: 0)
        limit: Maximum number of items to return (default: 50)
        
    Returns:
        Tuple of (paginated_items, total_count)
        
    Example:
        >>> query = db.query(Transaction)
        >>> items, total = paginate_query(query, offset=10, limit=20)
    """
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    items = query.offset(offset).limit(limit).all()
    
    return items, total
