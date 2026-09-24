"""Tests for pagination utilities."""

import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from app.utils.pagination import (
    PaginationParams,
    PaginatedResponse,
    paginate_query
)
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


class TestPaginationParams:
    """Test PaginationParams validation and functionality."""
    
    def test_default_values(self):
        """Test default pagination parameter values."""
        params = PaginationParams()
        assert params.offset == 0
        assert params.limit == 50
    
    def test_custom_values(self):
        """Test custom pagination parameter values."""
        params = PaginationParams(offset=10, limit=20)
        assert params.offset == 10
        assert params.limit == 20
    
    def test_negative_offset_raises_error(self):
        """Test that negative offset raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(offset=-1)
        assert "offset" in str(exc_info.value)
    
    def test_zero_limit_raises_error(self):
        """Test that zero limit raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=0)
        assert "limit" in str(exc_info.value)
    
    def test_negative_limit_raises_error(self):
        """Test that negative limit raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=-1)
        assert "limit" in str(exc_info.value)
    
    def test_limit_exceeds_max_raises_error(self):
        """Test that limit exceeding 500 raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=501)
        assert "limit" in str(exc_info.value)
    
    def test_limit_max_allowed(self):
        """Test that limit of 500 is allowed."""
        params = PaginationParams(limit=500)
        assert params.limit == 500
    
    def test_apply_to_query(self, db_session):
        """Test applying pagination parameters to a query."""
        # Create test data
        for i in range(10):
            transaction = Transaction(
                id=f"TXN-TEST-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Test Merchant",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=10
            )
            db_session.add(transaction)
        db_session.commit()
        
        # Test pagination
        query = db_session.query(Transaction)
        params = PaginationParams(offset=2, limit=3)
        paginated_query = params.apply_to_query(query)
        
        results = paginated_query.all()
        assert len(results) == 3


class TestPaginateQuery:
    """Test paginate_query function."""
    
    def test_paginate_query_with_defaults(self, db_session):
        """Test paginate_query with default parameters."""
        # Create test data
        for i in range(60):
            transaction = Transaction(
                id=f"TXN-TEST-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Test Merchant",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=10
            )
            db_session.add(transaction)
        db_session.commit()
        
        query = db_session.query(Transaction)
        items, total = paginate_query(query)
        
        assert len(items) == 50  # Default limit
        assert total == 60
    
    def test_paginate_query_with_custom_params(self, db_session):
        """Test paginate_query with custom offset and limit."""
        # Create test data
        for i in range(30):
            transaction = Transaction(
                id=f"TXN-TEST-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Test Merchant",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=10
            )
            db_session.add(transaction)
        db_session.commit()
        
        query = db_session.query(Transaction)
        items, total = paginate_query(query, offset=10, limit=5)
        
        assert len(items) == 5
        assert total == 30
    
    def test_paginate_query_with_filters(self, db_session):
        """Test paginate_query with filtered query."""
        # Create test data with different statuses
        for i in range(20):
            status = TransactionStatus.HELD if i % 2 == 0 else TransactionStatus.CLEARED
            transaction = Transaction(
                id=f"TXN-TEST-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Test Merchant",
                timestamp=datetime.utcnow(),
                status=status,
                risk_level=RiskLevel.LOW,
                risk_score=10
            )
            db_session.add(transaction)
        db_session.commit()
        
        # Query only HELD transactions
        query = db_session.query(Transaction).filter(
            Transaction.status == TransactionStatus.HELD
        )
        items, total = paginate_query(query, offset=0, limit=5)
        
        assert len(items) == 5
        assert total == 10  # Only half are HELD
        assert all(t.status == TransactionStatus.HELD for t in items)
    
    def test_paginate_query_empty_results(self, db_session):
        """Test paginate_query with no results."""
        query = db_session.query(Transaction)
        items, total = paginate_query(query, offset=0, limit=10)
        
        assert len(items) == 0
        assert total == 0
    
    def test_paginate_query_offset_beyond_total(self, db_session):
        """Test paginate_query with offset beyond total items."""
        # Create 5 transactions
        for i in range(5):
            transaction = Transaction(
                id=f"TXN-TEST-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Test Merchant",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=10
            )
            db_session.add(transaction)
        db_session.commit()
        
        query = db_session.query(Transaction)
        items, total = paginate_query(query, offset=10, limit=5)
        
        assert len(items) == 0  # No items at offset 10
        assert total == 5  # Total is still 5


class TestPaginatedResponse:
    """Test PaginatedResponse model and properties."""
    
    def test_basic_response(self):
        """Test basic paginated response creation."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}, {"id": 2}],
            total=100,
            offset=0,
            limit=10
        )
        assert len(response.items) == 2
        assert response.total == 100
        assert response.offset == 0
        assert response.limit == 10
    
    def test_has_next_true(self):
        """Test has_next property when there are more items."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}],
            total=100,
            offset=0,
            limit=10
        )
        assert response.has_next is True
    
    def test_has_next_false(self):
        """Test has_next property when there are no more items."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}],
            total=10,
            offset=0,
            limit=10
        )
        assert response.has_next is False
    
    def test_has_next_last_page(self):
        """Test has_next on the last page with partial results."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}, {"id": 2}],
            total=12,
            offset=10,
            limit=10
        )
        assert response.has_next is False
    
    def test_has_previous_true(self):
        """Test has_previous property when there are previous items."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}],
            total=100,
            offset=10,
            limit=10
        )
        assert response.has_previous is True
    
    def test_has_previous_false(self):
        """Test has_previous property on first page."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}],
            total=100,
            offset=0,
            limit=10
        )
        assert response.has_previous is False
    
    def test_page_count(self):
        """Test page_count calculation."""
        response = PaginatedResponse[dict](
            items=[],
            total=95,
            offset=0,
            limit=10
        )
        assert response.page_count == 10  # 95 items / 10 per page = 10 pages
    
    def test_page_count_exact_division(self):
        """Test page_count with exact division."""
        response = PaginatedResponse[dict](
            items=[],
            total=100,
            offset=0,
            limit=10
        )
        assert response.page_count == 10
    
    def test_page_count_single_item(self):
        """Test page_count with single item."""
        response = PaginatedResponse[dict](
            items=[{"id": 1}],
            total=1,
            offset=0,
            limit=10
        )
        assert response.page_count == 1
    
    def test_page_count_zero_total(self):
        """Test page_count with no items."""
        response = PaginatedResponse[dict](
            items=[],
            total=0,
            offset=0,
            limit=10
        )
        assert response.page_count == 0
    
    def test_current_page_first(self):
        """Test current_page on first page."""
        response = PaginatedResponse[dict](
            items=[],
            total=100,
            offset=0,
            limit=10
        )
        assert response.current_page == 1
    
    def test_current_page_second(self):
        """Test current_page on second page."""
        response = PaginatedResponse[dict](
            items=[],
            total=100,
            offset=10,
            limit=10
        )
        assert response.current_page == 2
    
    def test_current_page_middle(self):
        """Test current_page in the middle."""
        response = PaginatedResponse[dict](
            items=[],
            total=100,
            offset=50,
            limit=10
        )
        assert response.current_page == 6
    
    def test_current_page_last(self):
        """Test current_page on last page."""
        response = PaginatedResponse[dict](
            items=[],
            total=95,
            offset=90,
            limit=10
        )
        assert response.current_page == 10
