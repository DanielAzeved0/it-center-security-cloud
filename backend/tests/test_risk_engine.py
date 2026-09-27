import threading
import time
import pytest
from app.services.risk_engine import AttemptRecord, LoginRiskEngine, get_risk_engine


@pytest.fixture(autouse=True)
def clean_database():
    """No database needed for pure in-memory risk engine unit tests."""
    pass


def test_initial_client_not_blocked():
    engine = LoginRiskEngine()
    is_blocked, score, retry_after = engine.inspect_client("192.168.1.1")
    assert not is_blocked
    assert score == 0
    assert retry_after == 0


def test_accumulating_failures_reaches_score_100_and_blocks():
    engine = LoginRiskEngine()
    ip = "192.168.1.100"
    now = time.time()

    # 4 spaced attempts: 4 * 20 = 80 points (no burst)
    for i in range(4):
        # Spacing by 15s to avoid burst velocity (>3 attempts in 10s)
        t = now - 60 + (i * 15)
        score = engine.record_attempt(
            ip=ip,
            email="user@example.com",
            success=False,
            user_exists=True,
            timestamp=t,
        )
    assert score == 80
    is_blocked, current_score, retry_after = engine.inspect_client(ip, now=now)
    assert not is_blocked
    assert current_score == 80
    assert retry_after == 0

    # 5th attempt reaches 100 points -> triggers block
    t5 = now
    score = engine.record_attempt(
        ip=ip,
        email="user@example.com",
        success=False,
        user_exists=True,
        timestamp=t5,
    )
    assert score >= 100
    is_blocked, current_score, retry_after = engine.inspect_client(ip, now=t5)
    assert is_blocked
    assert current_score >= 100
    assert retry_after == 900


def test_burst_velocity_heuristic():
    engine = LoginRiskEngine()
    ip = "10.0.0.1"
    now = time.time()

    # 4 attempts within 2 seconds:
    # 4 * 20 (failures) + 35 (burst velocity: >3 in 10s) = 115 points
    for i in range(3):
        score = engine.record_attempt(
            ip=ip,
            email="victim@example.com",
            success=False,
            user_exists=True,
            timestamp=now + (i * 0.5),
        )
        assert score == (i + 1) * 20

    # 4th attempt in burst
    score = engine.record_attempt(
        ip=ip,
        email="victim@example.com",
        success=False,
        user_exists=True,
        timestamp=now + 1.5,
    )
    assert score == (4 * 20) + 35  # 115
    is_blocked, current_score, retry_after = engine.inspect_client(ip, now=now + 1.5)
    assert is_blocked
    assert current_score == 115
    assert retry_after > 0


def test_credential_stuffing_heuristics():
    engine = LoginRiskEngine()
    ip = "10.0.0.2"
    now = time.time()

    # 3 distinct emails spaced out (>10s apart):
    # 3 * 20 (failures) + 30 (>= 3 distinct emails) = 90
    emails = ["alice@example.com", "bob@example.com", "charlie@example.com"]
    for i, email in enumerate(emails):
        score = engine.record_attempt(
            ip=ip,
            email=email,
            success=False,
            user_exists=True,
            timestamp=now - 100 + (i * 15),
        )
    assert score == 90

    # 5 distinct emails:
    # 5 * 20 (failures) + 50 (>= 5 distinct emails) = 150 -> blocks!
    more_emails = ["david@example.com", "eve@example.com"]
    for i, email in enumerate(more_emails):
        score = engine.record_attempt(
            ip=ip,
            email=email,
            success=False,
            user_exists=True,
            timestamp=now - 50 + (i * 15),
        )
    assert score == 150
    is_blocked, current_score, retry_after = engine.inspect_client(ip, now=now)
    assert is_blocked
    assert current_score == 150
    assert retry_after > 0


def test_nonexistent_email_heuristic():
    engine = LoginRiskEngine()
    ip = "10.0.0.3"
    now = time.time()

    # 1 attempt on inexistent user: 20 (failure) + 15 (nonexistent) = 35
    score = engine.record_attempt(
        ip=ip,
        email="nobody@example.com",
        success=False,
        user_exists=False,
        timestamp=now - 60,
    )
    assert score == 35

    # 2nd attempt on another inexistent user: 2 * 20 + 2 * 15 = 70
    score = engine.record_attempt(
        ip=ip,
        email="nobody2@example.com",
        success=False,
        user_exists=False,
        timestamp=now - 40,
    )
    assert score == 70

    # 3rd attempt on 3rd inexistent user: 3 * 20 + 3 * 15 + 30 (credential stuffing >= 3) = 135 -> blocks
    score = engine.record_attempt(
        ip=ip,
        email="nobody3@example.com",
        success=False,
        user_exists=False,
        timestamp=now - 20,
    )
    assert score == 135
    is_blocked, current_score, retry_after = engine.inspect_client(ip, now=now)
    assert is_blocked
    assert current_score == 135


def test_successful_login_resets_client():
    engine = LoginRiskEngine()
    ip = "10.0.0.4"
    now = time.time()

    engine.record_attempt(ip=ip, email="user@example.com", success=False, user_exists=True, timestamp=now)
    engine.record_attempt(ip=ip, email="user@example.com", success=False, user_exists=True, timestamp=now + 1)
    is_blocked, score, _ = engine.inspect_client(ip, now=now + 1)
    assert score > 0

    engine.reset_client(ip)
    is_blocked, score, retry_after = engine.inspect_client(ip, now=now + 2)
    assert not is_blocked
    assert score == 0
    assert retry_after == 0


def test_record_attempt_with_success_resets_client():
    engine = LoginRiskEngine()
    ip = "10.0.0.5"
    now = time.time()

    engine.record_attempt(ip=ip, email="user@example.com", success=False, user_exists=True, timestamp=now)
    score = engine.record_attempt(ip=ip, email="user@example.com", success=True, user_exists=True, timestamp=now + 1)
    assert score == 0

    is_blocked, inspect_score, _ = engine.inspect_client(ip, now=now + 2)
    assert not is_blocked
    assert inspect_score == 0


def test_expired_attempts_roll_off_after_window():
    engine = LoginRiskEngine()
    ip = "10.0.0.6"
    t0 = 1000000.0

    # Record attempts at t0
    engine.record_attempt(ip=ip, email="u1@example.com", success=False, user_exists=True, timestamp=t0)
    engine.record_attempt(ip=ip, email="u2@example.com", success=False, user_exists=True, timestamp=t0 + 1)

    # Within 3600 seconds
    _, score_within, _ = engine.inspect_client(ip, now=t0 + 3500)
    assert score_within > 0

    # Outside 3600 seconds
    _, score_after, _ = engine.inspect_client(ip, now=t0 + 3602)
    assert score_after == 0

    # cleanup_expired cleans storage
    engine.cleanup_expired(now=t0 + 3602)
    assert ip not in engine._attempts


def test_expired_block_unblocks_client():
    engine = LoginRiskEngine()
    ip = "10.0.0.7"
    t0 = 1000000.0

    # Trigger block (4 attempts in burst = 115)
    for i in range(4):
        engine.record_attempt(ip=ip, email="user@example.com", success=False, user_exists=True, timestamp=t0 + i)

    is_blocked, _, retry_after = engine.inspect_client(ip, now=t0 + 10)
    assert is_blocked
    assert retry_after == 893 or retry_after == 894

    # At t0 + 904 (> 903.0 expiration): block expires
    is_blocked, _, retry_after = engine.inspect_client(ip, now=t0 + 905)
    assert not is_blocked
    assert retry_after == 0


def test_composite_key_with_fingerprint():
    engine = LoginRiskEngine()
    ip = "10.0.0.8"
    fp1 = "fp-device-1"
    fp2 = "fp-device-2"
    now = time.time()

    # fp1 fails 4 times in burst -> blocked
    for i in range(4):
        engine.record_attempt(ip=ip, fingerprint=fp1, email="user@example.com", success=False, user_exists=True, timestamp=now + i)

    is_blocked_1, _, _ = engine.inspect_client(ip, fp1, now=now + 5)
    assert is_blocked_1

    # fp2 on same IP is NOT blocked
    is_blocked_2, _, _ = engine.inspect_client(ip, fp2, now=now + 5)
    assert not is_blocked_2


def test_singleton_get_risk_engine():
    engine1 = get_risk_engine()
    engine2 = get_risk_engine()
    assert engine1 is engine2


def test_concurrent_access_thread_safety():
    engine = LoginRiskEngine()
    threads = []

    def worker(client_id: int):
        ip = f"192.168.2.{client_id % 5}"
        for _ in range(20):
            engine.record_attempt(ip=ip, fingerprint="test", email=f"user{client_id}@example.com", success=False, user_exists=True)
            engine.inspect_client(ip, "test")

    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
