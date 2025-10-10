"""
Token Blacklist for One-Time Use Enforcement

Uses Redis to track used JWT tokens (by JTI claim) to prevent replay attacks
on temporary authentication tokens used in tenant discovery flow.
"""

import redis
from app.core.config import settings


class TokenBlacklist:
    """Redis-based token blacklist for one-time use enforcement"""

    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True
        )

    def add_to_blacklist(self, jti: str, ttl: int = 300):
        """
        Add token JTI to blacklist with expiration

        Args:
            jti: JWT ID (unique token identifier)
            ttl: Time to live in seconds (default 5 minutes)

        The TTL should match or exceed the token's expiration time
        to ensure the blacklist entry persists for the token's lifetime.
        """
        key = f"blacklist:token:{jti}"
        self.redis_client.setex(key, ttl, "1")

    def is_blacklisted(self, jti: str) -> bool:
        """
        Check if token JTI is in blacklist

        Args:
            jti: JWT ID to check

        Returns:
            True if token has been used (blacklisted), False otherwise
        """
        key = f"blacklist:token:{jti}"
        return self.redis_client.exists(key) > 0


# Global instance
_token_blacklist = None


def get_token_blacklist() -> TokenBlacklist:
    """
    Get or create token blacklist instance

    Returns:
        TokenBlacklist instance
    """
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist
