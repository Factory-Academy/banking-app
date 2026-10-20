"""Tests for pagination utilities"""
import pytest
from decimal import Decimal
from datetime import datetime
from app.utils.pagination import (
    paginate_query,
    create_paginated_response,
    PaginationParams,
    PaginatedResult
)
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


class TestPaginateQuery:
    """Tests for paginate_query function"""
    
    def test_paginate_query_first_page(self, db_session):
        """Test pagination with first page"""
        # Create 10 test transactions
        for i in range(10):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query with pagination
        query = db_session.query(Transaction)
        results, total = paginate_query(query, offset=0, limit=5)
        
        assert len(results) == 5
        assert total == 10
    
    def test_paginate_query_second_page(self, db_session):
        """Test pagination with offset"""
        # Create 10 test transactions
        for i in range(10):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query second page
        query = db_session.query(Transaction)
        results, total = paginate_query(query, offset=5, limit=5)
        
        assert len(results) == 5
        assert total == 10
    
    def test_paginate_query_partial_page(self, db_session):
        """Test pagination when last page is partial"""
        # Create 7 test transactions
        for i in range(7):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query last partial page
        query = db_session.query(Transaction)
        results, total = paginate_query(query, offset=5, limit=5)
        
        assert len(results) == 2
        assert total == 7
    
    def test_paginate_query_empty_results(self, db_session):
        """Test pagination with no results"""
        query = db_session.query(Transaction)
        results, total = paginate_query(query, offset=0, limit=10)
        
        assert len(results) == 0
        assert total == 0
    
    def test_paginate_query_offset_beyond_results(self, db_session):
        """Test pagination with offset beyond available results"""
        # Create 5 transactions
        for i in range(5):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query with offset beyond results
        query = db_session.query(Transaction)
        results, total = paginate_query(query, offset=10, limit=5)
        
        assert len(results) == 0
        assert total == 5
    
    def test_paginate_query_with_filters(self, db_session):
        """Test pagination works with filtered queries"""
        # Create transactions with different statuses
        for i in range(10):
            status = TransactionStatus.HELD if i < 3 else TransactionStatus.CLEARED
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=status,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query with filter
        query = db_session.query(Transaction).filter(Transaction.status == TransactionStatus.HELD)
        results, total = paginate_query(query, offset=0, limit=10)
        
        assert len(results) == 3
        assert total == 3
    
    def test_paginate_query_invalid_offset(self, db_session):
        """Test pagination with negative offset raises error"""
        query = db_session.query(Transaction)
        
        with pytest.raises(ValueError, match="offset must be >= 0"):
            paginate_query(query, offset=-1, limit=10)

    def test_paginate_query_none_query(self):
        """Test paginate_query rejects None query"""
        with pytest.raises(ValueError, match="query cannot be None"):
            paginate_query(None, offset=0, limit=10)
    
    def test_paginate_query_invalid_limit_too_low(self, db_session):
        """Test pagination with limit < 1 raises error"""
        query = db_session.query(Transaction)
        
        with pytest.raises(ValueError, match="limit must be between 1 and 500"):
            paginate_query(query, offset=0, limit=0)
    
    def test_paginate_query_invalid_limit_too_high(self, db_session):
        """Test pagination with limit > 500 raises error"""
        query = db_session.query(Transaction)
        
        with pytest.raises(ValueError, match="limit must be between 1 and 500"):
            paginate_query(query, offset=0, limit=501)

    def test_paginate_query_custom_max_limit(self, db_session):
        """Test pagination with custom max_limit keyword argument"""
        query = db_session.query(Transaction)

        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            paginate_query(query, offset=0, limit=101, max_limit=100)
    
    def test_paginate_query_default_parameters(self, db_session):
        """Test pagination with default parameters"""
        # Create 100 transactions
        for i in range(100):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query with defaults (offset=0, limit=50)
        query = db_session.query(Transaction)
        results, total = paginate_query(query)
        
        assert len(results) == 50
        assert total == 100


class TestCreatePaginatedResponse:
    """Tests for create_paginated_response function"""
    
    def test_create_paginated_response_first_page(self):
        """Test creating response for first page"""
        items = ["item1", "item2", "item3"]
        response = create_paginated_response(items, total=10, offset=0, limit=3)
        
        assert response["items"] == items
        assert response["total"] == 10
        assert response["offset"] == 0
        assert response["limit"] == 3
        assert response["has_more"] is True
        assert response["page_number"] == 1
        assert response["total_pages"] == 4
    
    def test_create_paginated_response_last_page(self):
        """Test creating response for last page"""
        items = ["item8", "item9", "item10"]
        response = create_paginated_response(items, total=10, offset=9, limit=3)
        
        assert response["items"] == items
        assert response["total"] == 10
        assert response["offset"] == 9
        assert response["limit"] == 3
        assert response["has_more"] is False
        assert response["page_number"] == 4
        assert response["total_pages"] == 4
    
    def test_create_paginated_response_no_results(self):
        """Test creating response with no results"""
        response = create_paginated_response([], total=0, offset=0, limit=10)
        
        assert response["items"] == []
        assert response["total"] == 0
        assert response["has_more"] is False
        assert response["page_number"] == 1
        assert response["total_pages"] == 1
    
    def test_create_paginated_response_exact_page_boundary(self):
        """Test response when total is exact multiple of limit"""
        items = ["item6", "item7", "item8", "item9", "item10"]
        response = create_paginated_response(items, total=10, offset=5, limit=5)
        
        assert response["total"] == 10
        assert response["has_more"] is False
        assert response["page_number"] == 2
        assert response["total_pages"] == 2
    
    def test_create_paginated_response_negative_total(self):
        """Test create_paginated_response rejects negative total"""
        with pytest.raises(ValueError, match="total must be >= 0"):
            create_paginated_response([], total=-1, offset=0, limit=10)
    
    def test_create_paginated_response_negative_offset(self):
        """Test create_paginated_response rejects negative offset"""
        with pytest.raises(ValueError, match="offset must be >= 0"):
            create_paginated_response([], total=0, offset=-1, limit=10)
    
    def test_create_paginated_response_invalid_limit(self):
        """Test create_paginated_response rejects limit < 1"""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            create_paginated_response([], total=0, offset=0, limit=0)

    def test_create_paginated_response_none_items(self):
        """Test create_paginated_response rejects None items"""
        with pytest.raises(ValueError, match="items cannot be None"):
            create_paginated_response(None, total=0, offset=0, limit=10)


class TestPaginationParams:
    """Tests for PaginationParams model"""
    
    def test_pagination_params_defaults(self):
        """Test PaginationParams with default values"""
        params = PaginationParams()
        
        assert params.offset == 0
        assert params.limit == 50
    
    def test_pagination_params_custom_values(self):
        """Test PaginationParams with custom values"""
        params = PaginationParams(offset=10, limit=25)
        
        assert params.offset == 10
        assert params.limit == 25
    
    def test_pagination_params_immutable(self):
        """Test that PaginationParams is immutable"""
        params = PaginationParams(offset=0, limit=50)
        
        with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
            params.offset = 10
    
    def test_pagination_params_negative_offset(self):
        """Test PaginationParams rejects negative offset"""
        with pytest.raises(ValueError, match="offset must be >= 0"):
            PaginationParams(offset=-1, limit=50)
    
    def test_pagination_params_invalid_limit_too_low(self):
        """Test PaginationParams rejects limit < 1"""
        with pytest.raises(ValueError, match="limit must be between 1 and 500"):
            PaginationParams(offset=0, limit=0)
    
    def test_pagination_params_invalid_limit_too_high(self):
        """Test PaginationParams rejects limit > 500"""
        with pytest.raises(ValueError, match="limit must be between 1 and 500"):
            PaginationParams(offset=0, limit=501)


class TestPaginatedResult:
    """Tests for PaginatedResult model"""
    
    def test_paginated_result_has_more_true(self):
        """Test has_more property when there are more items"""
        result = PaginatedResult(items=[1, 2, 3], total=10, offset=0, limit=3)
        
        assert result.has_more is True
    
    def test_paginated_result_has_more_false(self):
        """Test has_more property when no more items"""
        result = PaginatedResult(items=[8, 9, 10], total=10, offset=9, limit=3)
        
        assert result.has_more is False
    
    def test_paginated_result_page_number(self):
        """Test page_number calculation"""
        result = PaginatedResult(items=[6, 7, 8, 9, 10], total=10, offset=5, limit=5)
        
        assert result.page_number == 2
    
    def test_paginated_result_total_pages(self):
        """Test total_pages calculation"""
        result = PaginatedResult(items=[1, 2, 3], total=10, offset=0, limit=3)
        
        assert result.total_pages == 4
    
    def test_paginated_result_total_pages_exact_multiple(self):
        """Test total_pages when total is exact multiple of limit"""
        result = PaginatedResult(items=[1, 2, 3, 4, 5], total=10, offset=0, limit=5)
        
        assert result.total_pages == 2
    
    def test_paginated_result_empty(self):
        """Test PaginatedResult with empty results"""
        result = PaginatedResult(items=[], total=0, offset=0, limit=10)
        
        assert result.has_more is False
        assert result.page_number == 1
        assert result.total_pages == 1
    
    def test_paginated_result_negative_total(self):
        """Test PaginatedResult rejects negative total"""
        with pytest.raises(ValueError, match="value must be >= 0"):
            PaginatedResult(items=[], total=-1, offset=0, limit=10)
    
    def test_paginated_result_negative_offset(self):
        """Test PaginatedResult rejects negative offset"""
        with pytest.raises(ValueError, match="value must be >= 0"):
            PaginatedResult(items=[], total=0, offset=-1, limit=10)
    
    def test_paginated_result_invalid_limit(self):
        """Test PaginatedResult rejects limit < 1"""
        with pytest.raises(ValueError, match="limit must be >= 1"):
            PaginatedResult(items=[], total=0, offset=0, limit=0)


class TestPaginationIntegration:
    """Integration tests with actual API endpoint"""
    
    def test_api_pagination_integration(self, client, db_session):
        """Test pagination works end-to-end through API"""
        # Create 15 transactions
        for i in range(15):
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/v1/transactions?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5
        assert data["total"] == 15
        assert data["offset"] == 0
        assert data["limit"] == 5
        
        # Test second page
        response = client.get("/api/v1/transactions?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5
        assert data["total"] == 15
        assert data["offset"] == 5
        
        # Test last partial page
        response = client.get("/api/v1/transactions?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5
        assert data["total"] == 15
    
    def test_api_pagination_with_filters(self, client, db_session):
        """Test pagination works with filters"""
        # Create transactions with different statuses
        for i in range(10):
            status = TransactionStatus.HELD if i < 3 else TransactionStatus.CLEARED
            txn = Transaction(
                id=f"TXN-{i:03d}",
                account_number="**** 4521",
                account_holder_name="John Smith",
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow(),
                status=status,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            db_session.add(txn)
        db_session.commit()
        
        # Query HELD transactions only
        response = client.get("/api/v1/transactions?status=HELD&limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 3
        assert data["total"] == 3
