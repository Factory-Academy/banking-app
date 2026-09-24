# Pagination Utility Usage Examples

This document provides examples of how to use the pagination utilities in this application.

## Overview

The pagination utility provides three main components:

1. **PaginationParams**: A Pydantic model for validating pagination parameters
2. **PaginatedResponse**: A generic response wrapper with pagination metadata
3. **paginate_query**: A convenience function for applying pagination to SQLAlchemy queries

## Basic Usage

### Using `paginate_query` function

The simplest way to paginate a query:

```python
from app.utils.pagination import paginate_query
from app.models.transaction import Transaction

def get_transactions(db: Session, offset: int = 0, limit: int = 50):
    query = db.query(Transaction)
    items, total = paginate_query(query, offset=offset, limit=limit)
    return {"items": items, "total": total}
```

### Using `PaginationParams` class

For more structured pagination with validation:

```python
from app.utils.pagination import PaginationParams
from app.models.transaction import Transaction

def get_transactions(db: Session, pagination: PaginationParams):
    query = db.query(Transaction)
    
    # Apply pagination to query
    paginated_query = pagination.apply_to_query(query)
    
    # Get total count
    total = query.count()
    
    # Get results
    items = paginated_query.all()
    
    return {"items": items, "total": total, "offset": pagination.offset, "limit": pagination.limit}
```

### Using `PaginatedResponse` wrapper

For a standardized response format with helpful metadata:

```python
from app.utils.pagination import paginate_query, PaginatedResponse
from app.models.transaction import Transaction

def get_transactions(db: Session, offset: int = 0, limit: int = 50) -> PaginatedResponse[Transaction]:
    query = db.query(Transaction)
    items, total = paginate_query(query, offset=offset, limit=limit)
    
    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )

# The response includes useful properties:
# - has_next: bool - whether there are more items
# - has_previous: bool - whether there are previous items
# - page_count: int - total number of pages
# - current_page: int - current page number (1-indexed)
```

## Validation

`PaginationParams` automatically validates:

- **offset**: Must be >= 0 (default: 0)
- **limit**: Must be between 1 and 500 (default: 50)

```python
from pydantic import ValidationError
from app.utils.pagination import PaginationParams

# Valid
params = PaginationParams(offset=10, limit=20)

# Invalid - raises ValidationError
try:
    params = PaginationParams(offset=-1)  # offset must be >= 0
except ValidationError:
    print("Invalid offset")

try:
    params = PaginationParams(limit=0)  # limit must be >= 1
except ValidationError:
    print("Invalid limit")

try:
    params = PaginationParams(limit=1000)  # limit must be <= 500
except ValidationError:
    print("Limit too high")
```

## FastAPI Integration

In FastAPI route handlers:

```python
from fastapi import Query
from app.utils.pagination import paginate_query

@router.get("/transactions")
def get_transactions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction).filter(...)
    transactions, total = paginate_query(query, offset=offset, limit=limit)
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

## Complete Example

Here's a complete example with filters and pagination:

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.transaction import Transaction, TransactionStatus
from app.utils.pagination import paginate_query

router = APIRouter()

@router.get("/transactions")
def get_transactions(
    status: Optional[TransactionStatus] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters and pagination."""
    # Build query with filters
    query = db.query(Transaction)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    # Apply ordering
    query = query.order_by(desc(Transaction.timestamp))
    
    # Apply pagination
    transactions, total = paginate_query(query, offset=offset, limit=limit)
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }
```

## Testing

Example test for pagination:

```python
def test_pagination(db_session):
    # Create test data
    for i in range(30):
        transaction = Transaction(
            id=f"TXN-{i}",
            # ... other fields
        )
        db_session.add(transaction)
    db_session.commit()
    
    # Test pagination
    query = db_session.query(Transaction)
    items, total = paginate_query(query, offset=10, limit=5)
    
    assert len(items) == 5
    assert total == 30
```
