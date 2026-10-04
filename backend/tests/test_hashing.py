import pytest
from app.utils.hashing import make_hashable

@pytest.mark.unit
def test_make_hashable_basic():
    """Test basic conversion of unhashable types."""
    assert make_hashable([1, 2, 3]) == (1, 2, 3)
    assert make_hashable({"a": 1, "b": 2}) == (("a", 1), ("b", 2))
    assert make_hashable({3, 1, 2}) == (1, 2, 3)

@pytest.mark.unit
def test_make_hashable_nested():
    """Test nested structures."""
    nested = {"key": [1, 2, {"inner": 3}]}
    result = make_hashable(nested)
    assert result == (("key", (1, 2, (("inner", 3),))),)

@pytest.mark.unit
def test_make_hashable_sort_keys_true():
    """Test that dict keys are sorted when sort_keys=True (default)."""
    obj = {"z": 1, "a": 2, "m": 3}
    result = make_hashable(obj, sort_keys=True)
    # Keys should be sorted: a, m, z
    assert result == (("a", 2), ("m", 3), ("z", 1))

@pytest.mark.unit
def test_make_hashable_sort_keys_false():
    """Test that dict keys are not sorted when sort_keys=False."""
    obj = {"z": 1, "a": 2, "m": 3}
    result = make_hashable(obj, sort_keys=False)
    # Keys should be in insertion order (Python 3.7+)
    assert result == (("z", 1), ("a", 2), ("m", 3))

@pytest.mark.unit
def test_make_hashable_set_sort_keys_true():
    """Test that set elements are sorted when sort_keys=True (default)."""
    obj = {3, 1, 2}
    result = make_hashable(obj, sort_keys=True)
    assert result == (1, 2, 3)

@pytest.mark.unit
def test_make_hashable_set_sort_keys_false():
    """Test that set elements are not sorted when sort_keys=False."""
    obj = {3, 1, 2}
    result = make_hashable(obj, sort_keys=False)
    # Order is not deterministic, but all elements should be present
    assert sorted(result) == [1, 2, 3]
    assert len(result) == 3

@pytest.mark.unit
def test_make_hashable_nested_sort_keys():
    """Test that sort_keys is propagated through nested structures."""
    obj = {"outer": {"z": 1, "a": 2}}
    
    # With sort_keys=True
    result_sorted = make_hashable(obj, sort_keys=True)
    assert result_sorted == (("outer", (("a", 2), ("z", 1))),)
    
    # With sort_keys=False
    result_unsorted = make_hashable(obj, sort_keys=False)
    assert result_unsorted == (("outer", (("z", 1), ("a", 2))),)

@pytest.mark.unit
def test_make_hashable_already_hashable():
    """Test that already hashable objects are returned unchanged."""
    assert make_hashable(42) == 42
    assert make_hashable("string") == "string"
    assert make_hashable((1, 2, 3)) == (1, 2, 3)
