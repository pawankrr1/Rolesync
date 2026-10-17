"""Lightweight In-Memory Sliding-Window Rate Limiter.

Protects critical API endpoints (e.g. document parsing, talent ranking, matching)
against denial-of-service (DoS) and automated brute-force attacks.
Zero external dependencies required.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from threading import Lock
from fastapi import Request, HTTPException, status


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self):
        # Maps client_identifier -> list of request timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = Lock()
        self._last_cleanup = time.time()

    def _get_client_identifier(self, request: Request) -> str:
        """Extract client IP from request, respecting X-Forwarded-For if behind a proxy."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take first IP in chain
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

        if request.client and request.client.host:
            return request.client.host

        return "unknown_client"

    def _cleanup_stale_entries(self, current_time: float, max_window: int = 300) -> None:
        """Purge entries older than max_window to avoid memory leaks."""
        if current_time - self._last_cleanup < 60:
            return
        
        self._last_cleanup = current_time
        cutoff = current_time - max_window
        stale_keys = []
        for key, timestamps in list(self._requests.items()):
            valid = [ts for ts in timestamps if ts > cutoff]
            if valid:
                self._requests[key] = valid
            else:
                stale_keys.append(key)
        for key in stale_keys:
            self._requests.pop(key, None)

    def check(
        self,
        request: Request,
        max_requests: int = 30,
        window_seconds: int = 60,
        endpoint_tag: str = "general",
    ) -> None:
        """Evaluate rate limit for the requesting client.
        
        Raises HTTP 429 Too Many Requests if client exceeds max_requests within window_seconds.
        """
        client_id = f"{self._get_client_identifier(request)}:{endpoint_tag}"
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            self._cleanup_stale_entries(now)
            timestamps = self._requests[client_id]
            # Retain only timestamps within active window
            recent = [ts for ts in timestamps if ts > window_start]
            self._requests[client_id] = recent

            if len(recent) >= max_requests:
                earliest = recent[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Rate limit exceeded. Please wait before retrying.",
                    headers={"Retry-After": str(retry_after)},
                )

            self._requests[client_id].append(now)

    def reset(self) -> None:
        """Reset rate limiter state (useful for test isolation)."""
        with self._lock:
            self._requests.clear()


# Global rate limiter instance
rate_limiter = SlidingWindowRateLimiter()


def rate_limit(max_requests: int = 30, window_seconds: int = 60, endpoint_tag: str = "general"):
    """FastAPI dependency factory for endpoint-level rate limiting."""
    async def dependency(request: Request):
        rate_limiter.check(
            request=request,
            max_requests=max_requests,
            window_seconds=window_seconds,
            endpoint_tag=endpoint_tag,
        )
    return dependency
