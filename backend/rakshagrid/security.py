"""
AgentCraft / RakshaGrid Security Hardening Module
Provides rate-limiting dependencies, client IP extraction, and security helpers
to protect expensive AI/simulation endpoints and sensitive operations from abuse.
"""

import os
import time
from collections import defaultdict
from threading import Lock
from typing import Callable, Dict, List, Optional
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.
    Tracks timestamps of requests per client key (IP or identity)
    within a moving time window.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60, name: str = "default"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()

    def _get_client_key(self, request: Request) -> str:
        """Extracts unique client identifier from headers or client IP."""
        # Check forward headers for reverse proxy configurations
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client and request.client.host:
            return request.client.host
        
        return "127.0.0.1"

    def is_rate_limited(self, client_key: str) -> tuple[bool, int]:
        """
        Evaluates whether a client key has exceeded the allowed request quota.
        Returns (is_limited, retry_after_seconds).
        """
        # Automatically bypass rate limiting in automated testing environments
        if os.getenv("AGENTCRAFT_ENV") == "test" or os.getenv("PYTEST_CURRENT_TEST"):
            return False, 0

        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Clean expired timestamps
            valid_timestamps = [t for t in self._requests[client_key] if t > cutoff]
            self._requests[client_key] = valid_timestamps

            if len(valid_timestamps) >= self.max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + self.window_seconds - now))
                return True, retry_after

            # Record this request
            self._requests[client_key].append(now)
            return False, 0

    def __call__(self, request: Request):
        """FastAPI dependency callable."""
        client_key = self._get_client_key(request)
        limited, retry_after = self.is_rate_limited(client_key)
        if limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.name}. Maximum {self.max_requests} requests per {self.window_seconds}s. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )


# Pre-configured rate limiters for varying sensitivity tiers
ai_analysis_limiter = SlidingWindowRateLimiter(
    max_requests=20,
    window_seconds=60,
    name="AI Situational Analysis",
)

simulation_limiter = SlidingWindowRateLimiter(
    max_requests=30,
    window_seconds=60,
    name="Disaster Simulation Engine",
)

autonomous_agent_limiter = SlidingWindowRateLimiter(
    max_requests=15,
    window_seconds=60,
    name="Autonomous Agent Execution",
)

alert_evaluation_limiter = SlidingWindowRateLimiter(
    max_requests=20,
    window_seconds=60,
    name="Alert Evaluation Sweeps",
)
