import time
import pytest
from app.utils.cache import ttl_cache

@pytest.mark.unit
def test_ttl_cache_basic():
    call_count = 0
    
    @ttl_cache(ttl=60, maxsize=128)
    def get_data(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    assert get_data(1) == 2
    assert call_count == 1
    
    # Second call should be cached
    assert get_data(1) == 2
    assert call_count == 1
    
    # Different arg should not be cached
    assert get_data(2) == 4
    assert call_count == 2

@pytest.mark.unit
def test_ttl_cache_expiration():
    call_count = 0
    
    # Small TTL for testing
    @ttl_cache(ttl=0.1, maxsize=128)
    def get_data(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    assert get_data(1) == 2
    assert call_count == 1
    
    # Still cached
    assert get_data(1) == 2
    assert call_count == 1
    
    # Wait for expiration
    time.sleep(0.2)
    
    # Should be re-calculated
    assert get_data(1) == 2
    assert call_count == 2

@pytest.mark.unit
def test_ttl_cache_maxsize():
    call_count = 0
    
    @ttl_cache(ttl=60, maxsize=2)
    def get_data(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    get_data(1) # [1]
    get_data(2) # [1, 2]
    assert call_count == 2
    
    get_data(3) # [2, 3] (1 evicted)
    assert call_count == 3
    
    # 1 should be re-calculated
    get_data(1)
    assert call_count == 4
    
    # 2 should still be cached if we access it to move it to end
    get_data(3) # [1, 3]
    get_data(3)
    assert call_count == 4

@pytest.mark.unit
def test_ttl_cache_clear():
    call_count = 0
    
    @ttl_cache(ttl=60, maxsize=128)
    def get_data(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    get_data(1)
    assert call_count == 1
    
    get_data.cache_clear()
    
    get_data(1)
    assert call_count == 2
