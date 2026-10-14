"""Pagination utilities for database queries"""
from typing import TypeVar, Generic, List, Tuple
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Query

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""
    offset: int = 0
    limit: int = 50
    
    class Config:
        frozen = True
    
    @field_validator('offset')
    @classmethod
    def validate_offset(cls, v: int) -> int:
        if v < 0:
            raise ValueError("offset must be >= 0")
        return v
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if v < 1 or v > 500:
            raise ValueError("limit must be between 1 and 500")
        return v


class PaginatedResult(BaseModel, Generic[T]):
    """Generic paginated result wrapper"""
    items: List[T]
    total: int
    offset: int
    limit: int
    
    @field_validator('total', 'offset')
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("value must be >= 0")
        return v
    
    @field_validator('limit')
    @classmethod
    def validate_limit_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("limit must be >= 1")
        return v
    
    @property
    def has_more(self) -> bool:
        """Check if there are more items beyond current page"""
        return self.offset + self.limit < self.total
    
    @property
    def page_number(self) -> int:
        """Calculate current page number (1-indexed)"""
        if self.limit <= 0:
            return 1
        return (self.offset // self.limit) + 1
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages"""
        if self.limit <= 0 or self.total == 0:
            return 1
        return (self.total + self.limit - 1) // self.limit


def paginate_query(query: Query, offset: int = 0, limit: int = 50) -> Tuple[list, int]:
    """
    Apply pagination to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy Query object
        offset: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 50)
    
    Returns:
        tuple: (list of results, total count)
    
    Raises:
        ValueError: If offset < 0 or limit not in [1, 500]
    """
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
    
    # Get total count before applying pagination
    total = query.count()
    
    # Apply pagination
    results = query.offset(offset).limit(limit).all()
    
    return results, total


def create_paginated_response(
    items: list,
    total: int,
    offset: int,
    limit: int
) -> dict:
    """
    Create a standardized pagination response dict.
    
    Args:
        items: List of items for current page
        total: Total number of items across all pages
        offset: Current offset value
        limit: Current limit value
    
    Returns:
        dict with items, total, offset, limit, has_more, and page info
    
    Raises:
        ValueError: If total or offset are negative, or limit is < 1
    """
    if total < 0:
        raise ValueError("total must be >= 0")
    if offset < 0:
        raise ValueError("offset must be >= 0")
    if limit < 1:
        raise ValueError("limit must be >= 1")
    
    has_more = offset + limit < total
    page_number = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 and total > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "page_number": page_number,
        "total_pages": total_pages
    }
