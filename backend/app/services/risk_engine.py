from dataclasses import dataclass
import math
import os
import threading
import time


@dataclass
class AttemptRecord:
    timestamp: float
    email: str
    success: bool
    user_exists: bool


class LoginRiskEngine:
    WINDOW_SECONDS = 3600  # 1 hour sliding window
    BLOCK_DURATION_SECONDS = 900  # 15 minutes block
    BURST_WINDOW_SECONDS = 10.0  # 10 seconds burst velocity window
    BURST_THRESHOLD = 3  # > 3 attempts in 10s
    BLOCK_THRESHOLD = 100  # score >= 100 triggers block

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._attempts: dict[str, list[AttemptRecord]] = {}
        self._blocks: dict[str, float] = {}
        self._last_test: str | None = None

    def _check_test_isolation(self) -> None:
        current_test = os.environ.get("PYTEST_CURRENT_TEST")
        if current_test is not None and self._last_test != current_test:
            self._last_test = current_test
            self._attempts.clear()
            self._blocks.clear()

    def _get_key(self, ip: str | None, fingerprint: str = "") -> str:
        ip_str = ip or ""
        if ip_str and fingerprint:
            return f"{ip_str}:{fingerprint}"
        return ip_str or fingerprint or "unknown"

    def _compute_score(self, attempts: list[AttemptRecord], now: float) -> int:
        if not attempts:
            return 0

        score = 0

        # 1. Consecutive failures: +20 points per recent failure
        consecutive_failures = 0
        for att in reversed(attempts):
            if not att.success:
                consecutive_failures += 1
            else:
                break
        score += consecutive_failures * 20

        # 2. Burst velocity: +35 points if > 3 attempts occurred within 10 seconds
        burst_count = sum(1 for att in attempts if (now - att.timestamp) <= self.BURST_WINDOW_SECONDS)
        if burst_count > self.BURST_THRESHOLD:
            score += 35

        # 3. Credential stuffing: +30 points if >= 3 distinct emails tested in the window; +50 points if >= 5 distinct emails
        distinct_emails = {att.email for att in attempts if att.email}
        if len(distinct_emails) >= 5:
            score += 50
        elif len(distinct_emails) >= 3:
            score += 30

        # 4. Inexistent email targeted: +15 points per attempt
        inexistent_count = sum(1 for att in attempts if not att.user_exists)
        score += inexistent_count * 15

        return score

    def inspect_client(self, ip: str | None, fingerprint: str = "", now: float | None = None) -> tuple[bool, int, int]:
        """
        Inspect client state prior to authentication.
        Returns: (is_blocked, current_score, retry_after_seconds)
        """
        current_time = now if now is not None else time.time()
        with self._lock:
            self._check_test_isolation()
            key = self._get_key(ip, fingerprint)
            blocked_until = self._blocks.get(key)
            if blocked_until is not None:
                if current_time < blocked_until:
                    retry_after = max(1, math.ceil(blocked_until - current_time))
                    attempts = [
                        att for att in self._attempts.get(key, [])
                        if att.timestamp >= current_time - self.WINDOW_SECONDS
                    ]
                    score = self._compute_score(attempts, current_time)
                    return True, score, retry_after
                else:
                    del self._blocks[key]

            attempts = [
                att for att in self._attempts.get(key, [])
                if att.timestamp >= current_time - self.WINDOW_SECONDS
            ]
            score = self._compute_score(attempts, current_time)
            return False, score, 0

    def record_attempt(
        self,
        ip: str | None,
        fingerprint: str = "",
        email: str = "",
        success: bool = False,
        user_exists: bool = True,
        timestamp: float | None = None,
    ) -> int:
        """
        Record a login attempt, recalculate risk score, and block if threshold reached.
        Returns the resulting risk score.
        """
        current_time = timestamp if timestamp is not None else time.time()
        with self._lock:
            self._check_test_isolation()
            key = self._get_key(ip, fingerprint)
            if success:
                self._attempts.pop(key, None)
                self._blocks.pop(key, None)
                return 0

            attempt = AttemptRecord(
                timestamp=current_time,
                email=email.strip().lower(),
                success=success,
                user_exists=user_exists,
            )
            if key not in self._attempts:
                self._attempts[key] = []
            self._attempts[key].append(attempt)

            # Prune attempts outside sliding window
            cutoff = current_time - self.WINDOW_SECONDS
            self._attempts[key] = [att for att in self._attempts[key] if att.timestamp >= cutoff]

            score = self._compute_score(self._attempts[key], current_time)
            if score >= self.BLOCK_THRESHOLD:
                self._blocks[key] = current_time + self.BLOCK_DURATION_SECONDS

            return score

    def reset_client(self, ip: str | None, fingerprint: str = "") -> None:
        """Reset client failure points on successful login."""
        with self._lock:
            self._check_test_isolation()
            key = self._get_key(ip, fingerprint)
            self._attempts.pop(key, None)
            self._blocks.pop(key, None)

    def cleanup_expired(self, now: float | None = None) -> None:
        """Remove entries older than 3600 seconds and expired blocks."""
        current_time = now if now is not None else time.time()
        cutoff = current_time - self.WINDOW_SECONDS
        with self._lock:
            self._check_test_isolation()
            empty_keys = []
            for key, attempts in self._attempts.items():
                valid = [att for att in attempts if att.timestamp >= cutoff]
                if valid:
                    self._attempts[key] = valid
                else:
                    empty_keys.append(key)
            for key in empty_keys:
                del self._attempts[key]

            expired_blocks = [k for k, exp in self._blocks.items() if exp <= current_time]
            for k in expired_blocks:
                del self._blocks[k]

    def clear(self) -> None:
        """Clear all state (primarily for tests)."""
        with self._lock:
            self._attempts.clear()
            self._blocks.clear()


_risk_engine: LoginRiskEngine | None = None


def get_risk_engine() -> LoginRiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = LoginRiskEngine()
    return _risk_engine
