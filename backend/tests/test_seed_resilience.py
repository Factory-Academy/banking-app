"""Integration tests for the resilient client call in the seed script."""

import httpx
import pytest

from app.utils.resilience import BackoffPolicy, CircuitBreaker, ResilientCaller
from app.utils.seed_data import DataGenerator, TransientAPIError

URL = "http://localhost:8000/api/v1/transactions"


def _response(status_code: int, *, json=None, text: str = ""):
    request = httpx.Request("POST", URL)
    if json is not None:
        return httpx.Response(status_code, json=json, request=request)
    return httpx.Response(status_code, text=text, request=request)


class ScriptedClient:
    """Fake httpx client that replays a queue of responses/exceptions."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.post_calls = 0

    def post(self, url, json=None):
        self.post_calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def close(self):
        pass


@pytest.fixture
def generator():
    gen = DataGenerator()
    # Deterministic, instant retries: no jitter, no real sleeping.
    gen._caller = ResilientCaller(
        policy=BackoffPolicy(max_attempts=4, base_delay=0.1, jitter=False),
        breaker=CircuitBreaker(failure_threshold=8, recovery_timeout=15.0),
        retryable_exceptions=(TransientAPIError, httpx.TransportError),
        sleep_func=lambda _: None,
    )
    return gen


PAYLOAD = {"account_number": "**** 4500", "amount": "100.00"}


def test_success_on_first_try(generator):
    generator.client = ScriptedClient([_response(200, json={"id": "TXN-1"})])
    result = generator.create_transaction_via_api(PAYLOAD)
    assert result == {"id": "TXN-1"}
    assert generator.client.post_calls == 1


def test_retries_transient_connect_error_then_succeeds(generator):
    generator.client = ScriptedClient([
        httpx.ConnectError("connection refused"),
        httpx.ConnectError("connection refused"),
        _response(200, json={"id": "TXN-2"}),
    ])
    result = generator.create_transaction_via_api(PAYLOAD)
    assert result == {"id": "TXN-2"}
    assert generator.client.post_calls == 3


def test_retries_server_error_then_succeeds(generator):
    generator.client = ScriptedClient([
        _response(503, text="unavailable"),
        _response(200, json={"id": "TXN-3"}),
    ])
    result = generator.create_transaction_via_api(PAYLOAD)
    assert result == {"id": "TXN-3"}
    assert generator.client.post_calls == 2


def test_timeout_is_retried(generator):
    generator.client = ScriptedClient([
        httpx.ReadTimeout("timed out"),
        _response(200, json={"id": "TXN-4"}),
    ])
    result = generator.create_transaction_via_api(PAYLOAD)
    assert result == {"id": "TXN-4"}
    assert generator.client.post_calls == 2


def test_client_error_is_not_retried_and_exits(generator):
    generator.client = ScriptedClient([_response(400, text="bad request")])
    with pytest.raises(SystemExit):
        generator.create_transaction_via_api(PAYLOAD)
    # 4xx is permanent: exactly one attempt, no retries.
    assert generator.client.post_calls == 1


def test_persistent_transient_failure_exhausts_retries_and_exits(generator):
    generator.client = ScriptedClient([httpx.ConnectError("down")] * 4)
    with pytest.raises(SystemExit):
        generator.create_transaction_via_api(PAYLOAD)
    assert generator.client.post_calls == 4  # max_attempts


def test_open_circuit_stops_hammering_the_api(generator):
    # Small threshold so the breaker opens quickly, then rejects instantly.
    generator._caller = ResilientCaller(
        policy=BackoffPolicy(max_attempts=2, base_delay=0.1, jitter=False),
        breaker=CircuitBreaker(failure_threshold=2, recovery_timeout=15.0),
        retryable_exceptions=(TransientAPIError, httpx.TransportError),
        sleep_func=lambda _: None,
    )
    generator.client = ScriptedClient([httpx.ConnectError("down")] * 10)

    with pytest.raises(SystemExit):
        generator.create_transaction_via_api(PAYLOAD)

    # First call made 2 attempts and tripped the breaker.
    assert generator.client.post_calls == 2

    # A subsequent call is rejected immediately without touching the client.
    before = generator.client.post_calls
    with pytest.raises(SystemExit):
        generator.create_transaction_via_api(PAYLOAD)
    assert generator.client.post_calls == before
