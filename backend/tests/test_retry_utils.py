import pytest
from app.utils.retry import retry

@pytest.mark.unit
def test_retry_success_first_attempt():
    call_count = 0
    
    @retry(max_attempts=3, delay=0.01)
    def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = successful_func()
    assert result == "success"
    assert call_count == 1

@pytest.mark.unit
def test_retry_success_after_failures():
    call_count = 0
    
    @retry(max_attempts=3, delay=0.01)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"
    
    result = flaky_func()
    assert result == "success"
    assert call_count == 3

@pytest.mark.unit
def test_retry_exhausted():
    call_count = 0
    
    @retry(max_attempts=3, delay=0.01)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError, match="Always fails"):
        always_fails()
    
    assert call_count == 3

@pytest.mark.unit
def test_retry_specific_exception():
    call_count = 0
    
    @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
    def func_with_specific_error():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Retry this")
        return "success"
    
    result = func_with_specific_error()
    assert result == "success"
    assert call_count == 2

@pytest.mark.unit
def test_retry_different_exception_not_caught():
    call_count = 0
    
    @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
    def func_with_different_error():
        nonlocal call_count
        call_count += 1
        raise TypeError("Not caught")
    
    with pytest.raises(TypeError, match="Not caught"):
        func_with_different_error()
    
    # Should fail immediately, not retry
    assert call_count == 1

@pytest.mark.unit
def test_retry_with_args_and_kwargs():
    call_count = 0
    
    @retry(max_attempts=2, delay=0.01)
    def func_with_params(x, y, z=10):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First attempt")
        return x + y + z
    
    result = func_with_params(1, 2, z=3)
    assert result == 6
    assert call_count == 2

@pytest.mark.unit
def test_retry_min_attempts():
    call_count = 0
    
    @retry(max_attempts=0, delay=0.01)  # Should normalize to 1
    def func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Error")
    
    with pytest.raises(ValueError):
        func()
    
    assert call_count == 1

@pytest.mark.unit
def test_retry_zero_delay():
    call_count = 0
    
    @retry(max_attempts=2, delay=0)
    def func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("First")
        return "success"
    
    result = func()
    assert result == "success"
    assert call_count == 2
