# Pagination Utility Feature

## Overview
Added a reusable pagination utility module with offset/limit support for database queries, integrated into the existing transactions query endpoint.

## Implementation Details

### 1. Pagination Utility Module (`app/utils/pagination.py`)

Created a comprehensive pagination utility with:

#### Core Functions:
- **`paginate_query(query, offset, limit)`**: Apply pagination to SQLAlchemy queries
  - Returns tuple of (results, total_count)
  - Validates offset >= 0
  - Validates limit in range [1, 500]
  - Efficient: gets total count before applying pagination

- **`create_paginated_response(items, total, offset, limit)`**: Create standardized pagination response
  - Returns dict with pagination metadata
  - Includes `has_more`, `page_number`, `total_pages` calculations

#### Data Models:
- **`PaginationParams`**: Immutable Pydantic model for parameter validation
  - Default: offset=0, limit=50
  - Validates ranges

- **`PaginatedResult[T]`**: Generic Pydantic model for typed responses
  - Type-safe pagination wrapper
  - Computed properties: `has_more`, `page_number`, `total_pages`

### 2. Integration (`app/routes/transactions.py`)

Refactored `get_transactions()` endpoint to use the pagination utility:

**Before:**
```python
# Get total count
total = query.count()

# Apply pagination and ordering
transactions = query.order_by(desc(Transaction.timestamp)).offset(offset).limit(limit).all()
```

**After:**
```python
# Apply ordering and pagination using utility
query = query.order_by(desc(Transaction.timestamp))
transactions, total = paginate_query(query, offset=offset, limit=limit)
```

Benefits:
- Cleaner, more maintainable code
- Centralized pagination logic
- Consistent validation across all endpoints
- Easy to reuse in other query endpoints

### 3. Comprehensive Test Suite (`tests/test_pagination.py`)

Created 25+ test cases covering:

#### `TestPaginateQuery` (10 tests):
- First page pagination
- Second page with offset
- Partial last page
- Empty results
- Offset beyond results
- Pagination with filters
- Validation (negative offset, invalid limits)
- Default parameters

#### `TestCreatePaginatedResponse` (4 tests):
- First page metadata
- Last page metadata
- Empty results
- Exact page boundaries

#### `TestPaginationParams` (3 tests):
- Default values
- Custom values
- Immutability

#### `TestPaginatedResult` (6 tests):
- `has_more` property
- `page_number` calculation
- `total_pages` calculation
- Edge cases (empty, exact multiples)

#### `TestPaginationIntegration` (2 tests):
- End-to-end API pagination
- Pagination with filters

## Files Modified

### Created:
1. **`backend/app/utils/pagination.py`** (111 lines)
   - Core pagination utility module
   - 4 public functions/classes

2. **`backend/tests/test_pagination.py`** (448 lines)
   - Comprehensive test coverage
   - 25 test functions across 5 test classes

### Updated:
3. **`backend/app/routes/transactions.py`**
   - Added pagination import
   - Refactored `get_transactions()` to use utility
   - Maintains backward compatibility

## Usage Examples

### In Routes:
```python
from app.utils.pagination import paginate_query

@router.get("/items")
def get_items(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Item).filter(Item.active == True)
    items, total = paginate_query(query, offset=offset, limit=limit)
    
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit
    }
```

### With Helper Function:
```python
from app.utils.pagination import paginate_query, create_paginated_response

query = db.query(Item)
items, total = paginate_query(query, offset=0, limit=10)
response = create_paginated_response(items, total, offset=0, limit=10)
# Returns: {"items": [...], "total": X, "has_more": bool, "page_number": 1, ...}
```

### With Pydantic Models:
```python
from app.utils.pagination import PaginationParams, PaginatedResult

params = PaginationParams(offset=10, limit=20)
query = db.query(Item)
items, total = paginate_query(query, offset=params.offset, limit=params.limit)

result = PaginatedResult(items=items, total=total, offset=params.offset, limit=params.limit)
print(f"Page {result.page_number} of {result.total_pages}")
print(f"Has more: {result.has_more}")
```

## API Behavior

The existing `/api/v1/transactions` endpoint maintains full backward compatibility:

```bash
# Get first page (default: 50 items)
GET /api/v1/transactions

# Custom pagination
GET /api/v1/transactions?limit=10&offset=20

# Pagination with filters
GET /api/v1/transactions?status=HELD&limit=25&offset=0
```

Response format (unchanged):
```json
{
  "transactions": [...],
  "total": 150,
  "limit": 25,
  "offset": 0
}
```

## Validation

Input validation ensures:
- `offset >= 0` (raises ValueError otherwise)
- `1 <= limit <= 500` (raises ValueError otherwise)
- FastAPI query params enforce these at the endpoint level

## Testing

Run the tests:
```bash
cd backend
pytest tests/test_pagination.py -v
```

Run verification (no dependencies needed):
```bash
python verify_pagination.py
```

## Design Decisions

1. **Separate utility module**: Follows existing codebase pattern (see `app/utils/`)
2. **Tuple return**: `paginate_query` returns `(results, total)` for simplicity
3. **Validation in utility**: Centralized validation logic, not just in routes
4. **Generic models**: `PaginatedResult[T]` provides type safety
5. **Immutable params**: `PaginationParams` is frozen for safety
6. **Default limit=50**: Matches existing API default
7. **Max limit=500**: Prevents excessive database load

## Future Enhancements

Potential improvements:
- Cursor-based pagination for very large datasets
- Configurable max limit per endpoint
- Page token support for stateless pagination
- Pagination metadata in response headers
- Link headers for next/prev pages (RFC 8288)

## Conventions Followed

- Matches existing codebase style
- Uses SQLAlchemy Query patterns
- Pydantic models for validation
- pytest test structure
- Type hints throughout
- Comprehensive docstrings
- Error handling with clear messages
