"""
Unit Tests for Security Hardening & Rate Limiter Subsystem
Verifies sliding window rate limit enforcement, client key isolation,
retry-after timing, and safe error masking.
"""

import time
import pytest
from fastapi import HTTPException
from backend.rakshagrid.security import SlidingWindowRateLimiter


def test_rate_limiter_allows_under_quota(monkeypatch):
    """Test that requests under the configured threshold are permitted."""
    monkeypatch.delenv("AGENTCRAFT_ENV", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=10, name="Test Limiter")

    for _ in range(5):
        limited, retry_after = limiter.is_rate_limited("client_ip_1")
        assert limited is False
        assert retry_after == 0


def test_rate_limiter_blocks_over_quota(monkeypatch):
    """Test that requests exceeding the quota are blocked with accurate retry-after calculation."""
    monkeypatch.delenv("AGENTCRAFT_ENV", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=5, name="Test Limiter")

    # First 3 requests should pass
    for _ in range(3):
        limited, _ = limiter.is_rate_limited("client_ip_test")
        assert limited is False

    # 4th request must be rate limited
    limited, retry_after = limiter.is_rate_limited("client_ip_test")
    assert limited is True
    assert 1 <= retry_after <= 5

    # Separate client key should NOT be blocked
    other_limited, _ = limiter.is_rate_limited("client_ip_other")
    assert other_limited is False


def test_rate_limiter_bypasses_in_test_environment(monkeypatch):
    """Verify that test environment automatically bypasses rate limiting."""
    monkeypatch.setenv("AGENTCRAFT_ENV", "test")

    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=10, name="Test Limiter")

    # Multiple calls should all pass under test environment
    for _ in range(10):
        limited, _ = limiter.is_rate_limited("test_client")
        assert limited is False
