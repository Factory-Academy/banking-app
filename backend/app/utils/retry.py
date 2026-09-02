from typing import Callable, TypeVar


T = TypeVar("T")
RetryOn = type[BaseException] | tuple[type[BaseException], ...]


def retry(
    fn: Callable[[], T],
    attempts: int = 3,
    retry_on: RetryOn = Exception,
) -> T:
    """Run a callable with a tiny retry loop."""
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    if isinstance(retry_on, tuple) and not retry_on:
        raise ValueError("retry_on must not be an empty tuple")

    last_error: BaseException | None = None

    for _ in range(attempts):
        try:
            return fn()
        except retry_on as exc:
            last_error = exc

    if last_error is None:
        raise RuntimeError("retry failed without capturing an exception")
    raise last_error
