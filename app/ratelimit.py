"""MP2plus S2: login rate limit, keyed on the user's email, not the IP.

After MAX_FAILURES failed logins for one email within WINDOW_SECONDS, further
attempts for that email are refused until the oldest failure ages out, even
with the right password. Refused attempts are not counted as failures, so the
lockout ends one window after the failures that caused it.

State is in memory, per process: it resets on restart, which is fine for a
single-user local admin console. The route gets the limiter through the
`get_login_limiter` dependency, so tests can pass in one built on a frozen
clock (`app.dependency_overrides`).
"""
from __future__ import annotations

import time
from collections.abc import Callable

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class LoginLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self._failures: dict[str, list[float]] = {}

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def _recent(self, key: str) -> list[float]:
        cutoff = self.clock() - WINDOW_SECONDS
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def is_locked(self, email: str) -> bool:
        return len(self._recent(self._key(email))) >= MAX_FAILURES

    def record_failure(self, email: str) -> None:
        key = self._key(email)
        self._failures[key] = self._recent(key) + [self.clock()]

    def reset(self) -> None:
        self._failures.clear()


login_limiter = LoginLimiter()


def get_login_limiter() -> LoginLimiter:
    return login_limiter
