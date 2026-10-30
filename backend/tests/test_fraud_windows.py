from datetime import datetime, timedelta

from app.services.fraud.windows import iter_history, transactions_within


class _Item:
    def __init__(self, timestamp):
        self.timestamp = timestamp


REF = datetime(2025, 1, 1, 12, 0)


class TestTransactionsWithin:
    def test_filters_to_window(self):
        items = [
            _Item(REF - timedelta(minutes=30)),
            _Item(REF - timedelta(hours=2)),
            _Item(REF - timedelta(hours=10)),
        ]
        result = transactions_within(items, REF, timedelta(hours=1))
        assert result == [items[0]]

    def test_lower_bound_is_exclusive(self):
        on_start = _Item(REF - timedelta(hours=1))
        assert transactions_within([on_start], REF, timedelta(hours=1)) == []

    def test_inclusive_end_keeps_reference(self):
        at_ref = _Item(REF)
        assert transactions_within([at_ref], REF, timedelta(hours=1), inclusive_end=True) == [at_ref]

    def test_exclusive_end_drops_reference(self):
        at_ref = _Item(REF)
        assert transactions_within([at_ref], REF, timedelta(hours=1), inclusive_end=False) == []

    def test_skips_missing_and_malformed_timestamps(self):
        items = [_Item(None), _Item("2025-01-01"), _Item(REF - timedelta(minutes=5))]
        result = transactions_within(items, REF, timedelta(hours=1))
        assert result == [items[2]]

    def test_does_not_mutate_input(self):
        items = [_Item(REF - timedelta(minutes=5))]
        snapshot = list(items)
        transactions_within(items, REF, timedelta(hours=1))
        assert items == snapshot


class TestIterHistory:
    def test_none_becomes_empty(self):
        assert iter_history(None) == ()

    def test_list_passes_through_unchanged(self):
        data = [_Item(REF)]
        assert iter_history(data) is data

    def test_generator_is_materialised(self):
        gen = (_Item(REF) for _ in range(3))
        result = iter_history(gen)
        # Materialised once, so it can be scanned repeatedly.
        assert len(result) == 3
        assert len(list(result)) == 3

    def test_non_iterable_becomes_empty(self):
        assert iter_history(5) == ()
