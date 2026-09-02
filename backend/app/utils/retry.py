from typing import Callable, TypeVar


T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    attempts: int = 3,
    retry_on: type[Exception] = Exception,
) -> T:
    """Run a callable with a tiny retry loop."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    last_error: Exception | None = None

    for _ in range(attempts):
        try:
            return fn()
        except retry_on as exc:
            last_error = exc

    if last_error is None:
        raise RuntimeError("retry failed without capturing an exception")
    raise last_error
