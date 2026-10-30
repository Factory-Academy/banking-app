from app.utils.cache import ttl_cache
from app.utils.hashing import make_hashable


class TestMakeHashable:
    def test_list_becomes_tuple(self):
        assert make_hashable([1, 2, 3]) == (1, 2, 3)

    def test_nested_structures(self):
        assert make_hashable([1, [2, 3]]) == (1, (2, 3))

    def test_dict_is_order_stable(self):
        a = make_hashable({"b": 1, "a": 2})
        b = make_hashable({"a": 2, "b": 1})
        assert a == b

    def test_set_is_order_stable(self):
        assert make_hashable({3, 1, 2}) == (1, 2, 3)

    def test_result_is_hashable(self):
        hash(make_hashable({"a": [1, 2], "b": {3, 4}}))


class TestTtlCache:
    def test_caches_results(self):
        calls = {"n": 0}

        @ttl_cache(ttl=3600, maxsize=8)
        def double(x):
            calls["n"] += 1
            return x * 2

        assert double(5) == 10
        assert double(5) == 10
        assert calls["n"] == 1
        assert double.cache_info().hits == 1
        assert double.cache_info().misses == 1

    def test_handles_unhashable_arguments_by_recomputing(self):
        # dict args are normalised to a hashable key, so they are still cached.
        calls = {"n": 0}

        @ttl_cache(ttl=3600, maxsize=8)
        def size(d):
            calls["n"] += 1
            return len(d)

        assert size({"a": 1}) == 1
        assert size({"a": 1}) == 1
        assert calls["n"] == 1

    def test_lru_eviction_respects_maxsize(self):
        @ttl_cache(ttl=3600, maxsize=2)
        def identity(x):
            return x

        identity(1)
        identity(2)
        identity(3)  # evicts least-recently-used (1)
        assert identity.cache_info().currsize == 2

    def test_expired_entries_recompute(self):
        calls = {"n": 0}

        @ttl_cache(ttl=0, maxsize=8)
        def double(x):
            calls["n"] += 1
            return x * 2

        # ttl=0 means nothing is retained.
        double(5)
        double(5)
        assert calls["n"] == 2

    def test_cache_clear_resets(self):
        @ttl_cache(ttl=3600, maxsize=8)
        def double(x):
            return x * 2

        double(5)
        double(5)
        double.cache_clear()
        info = double.cache_info()
        assert info.hits == 0
        assert info.misses == 0
        assert info.currsize == 0

    def test_maxsize_zero_disables_cache(self):
        calls = {"n": 0}

        @ttl_cache(ttl=3600, maxsize=0)
        def double(x):
            calls["n"] += 1
            return x * 2

        double(5)
        double(5)
        assert calls["n"] == 2
