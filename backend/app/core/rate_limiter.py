"""
Rate Limiting for API Endpoints

Implements simple in-memory rate limiting using dictionaries.
For production, consider using Redis for distributed rate limiting.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass
from threading import Lock


@dataclass
class RateLimitRecord:
    """Track rate limit for a specific key"""
    count: int
    window_start: float


class RateLimiter:
    """
    Simple in-memory rate limiter
    
    Thread-safe rate limiting with sliding window.
    Suitable for single-instance deployments or low-traffic scenarios.
    
    For production with multiple instances, use Redis-based rate limiting.
    """
    
    def __init__(self):
        """Initialize rate limiter with empty cache"""
        self._records: Dict[str, RateLimitRecord] = {}
        self._lock = Lock()
    
    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Optional[int]]:
        """
        Check if key has exceeded rate limit
        
        Args:
            key: Unique identifier (usually IP address)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_limited, retry_after_seconds)
            - is_limited: True if rate limit exceeded
            - retry_after_seconds: Seconds until limit resets (None if not limited)
        """
        with self._lock:
            now = time.time()
            
            # Get or create record
            if key not in self._records:
                self._records[key] = RateLimitRecord(count=1, window_start=now)
                return False, None
            
            record = self._records[key]
            window_elapsed = now - record.window_start
            
            # If window expired, reset
            if window_elapsed >= window_seconds:
                self._records[key] = RateLimitRecord(count=1, window_start=now)
                return False, None
            
            # Increment count
            record.count += 1
            
            # Check if limit exceeded
            if record.count > max_requests:
                retry_after = int(window_seconds - window_elapsed)
                return True, retry_after
            
            return False, None
    
    def cleanup_expired(self, window_seconds: int):
        """
        Remove expired records (for memory management)
        
        Args:
            window_seconds: Window duration for cleanup
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, record in self._records.items()
                if now - record.window_start >= window_seconds
            ]
            for key in expired_keys:
                del self._records[key]


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
