from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RetryError(RuntimeError):
    """Raised when an operation exceeds retry budget."""


def with_retries(operation: Callable[[], T], retries: int = 3, base_delay_seconds: float = 0.5) -> T:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - generic retry utility
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(base_delay_seconds * (2**attempt))

    raise RetryError(f"Operation failed after {retries + 1} attempts") from last_error
