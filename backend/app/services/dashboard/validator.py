"""
Dashboard URL validator for security and compatibility
"""

from typing import List, Optional
from urllib.parse import urlparse
import re
import os


class DashboardURLValidator:
    """
    Validate dashboard URLs for security and compatibility

    Security Rules:
    1. Must be HTTPS (HTTP allowed in development only)
    2. No localhost/127.0.0.1 in production
    3. Optional domain whitelist
    4. No malicious patterns (XSS, etc.)
    """

    # Supported dashboard providers
    KNOWN_PROVIDERS = {
        "looker": ["looker.com", "looker"],
        "tableau": ["tableau.com", "tableauserver"],
        "powerbi": ["powerbi.com", "app.powerbi"],
        "metabase": ["metabase"],
        "custom": []  # Any domain allowed
    }

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        allow_http: bool = False
    ):
        """
        Initialize validator

        Args:
            allowed_domains: Optional whitelist of allowed domains
            allow_http: Allow HTTP (default: False, only HTTPS)
        """
        self.allowed_domains = allowed_domains
        self.allow_http = allow_http or self._is_development()

    def validate_url(
        self,
        url: str,
        dashboard_type: Optional[str] = None
    ) -> bool:
        """
        Validate dashboard URL

        Args:
            url: Dashboard URL to validate
            dashboard_type: Optional dashboard type for provider-specific validation

        Returns:
            True if valid

        Raises:
            ValueError: If URL is invalid with reason
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        url = url.strip()

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {str(e)}")

        # Validate scheme
        self._validate_scheme(parsed)

        # Validate hostname
        self._validate_hostname(parsed)

        # Validate against whitelist if provided
        if self.allowed_domains:
            self._validate_domain_whitelist(parsed)

        # Validate for known provider if type specified
        if dashboard_type:
            self._validate_provider(parsed, dashboard_type)

        # Check for malicious patterns
        self._validate_no_malicious_patterns(url)

        return True

    def _validate_scheme(self, parsed: urlparse) -> None:
        """Validate URL scheme (HTTP/HTTPS)"""
        if not parsed.scheme:
            raise ValueError("URL must include protocol (https://)")

        if parsed.scheme == "http":
            if not self.allow_http:
                raise ValueError("HTTP not allowed - use HTTPS")
        elif parsed.scheme != "https":
            raise ValueError(f"Invalid protocol: {parsed.scheme}. Use https://")

    def _validate_hostname(self, parsed: urlparse) -> None:
        """Validate hostname"""
        if not parsed.hostname:
            raise ValueError("URL must include hostname")

        hostname_lower = parsed.hostname.lower()

        # Check for localhost (not allowed in production)
        if not self._is_development():
            localhost_patterns = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "::1"
            ]

            if any(pattern in hostname_lower for pattern in localhost_patterns):
                raise ValueError("Localhost URLs not allowed in production")

        # Validate hostname format
        if not self._is_valid_hostname(parsed.hostname):
            raise ValueError(f"Invalid hostname format: {parsed.hostname}")

    def _validate_domain_whitelist(self, parsed: urlparse) -> None:
        """Validate against domain whitelist"""
        hostname_lower = parsed.hostname.lower()

        # Check if hostname matches any whitelisted domain
        is_whitelisted = any(
            domain.lower() in hostname_lower
            for domain in self.allowed_domains
        )

        if not is_whitelisted:
            raise ValueError(
                f"Domain not whitelisted: {parsed.hostname}. "
                f"Allowed domains: {', '.join(self.allowed_domains)}"
            )

    def _validate_provider(self, parsed: urlparse, dashboard_type: str) -> None:
        """Validate URL matches expected provider"""
        if dashboard_type == "custom":
            return  # No provider-specific validation for custom

        provider_domains = self.KNOWN_PROVIDERS.get(dashboard_type, [])
        if not provider_domains:
            return  # Unknown provider type

        hostname_lower = parsed.hostname.lower()

        is_provider_match = any(
            domain.lower() in hostname_lower
            for domain in provider_domains
        )

        if not is_provider_match:
            raise ValueError(
                f"URL does not match expected provider: {dashboard_type}. "
                f"Expected domains: {', '.join(provider_domains)}"
            )

    def _validate_no_malicious_patterns(self, url: str) -> None:
        """Check for malicious patterns"""
        malicious_patterns = [
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'<script',
            r'onerror=',
            r'onload=',
            r'onclick='
        ]

        url_lower = url.lower()

        for pattern in malicious_patterns:
            if re.search(pattern, url_lower):
                raise ValueError(f"Malicious pattern detected: {pattern}")

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Validate hostname format"""
        # Basic hostname validation
        # Must contain at least one dot (unless localhost)
        # Must contain only valid characters

        if hostname == "localhost":
            return True

        # Check for valid characters
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'

        return bool(re.match(hostname_pattern, hostname))

    def _is_development(self) -> bool:
        """Check if running in development environment"""
        env = os.getenv("ENVIRONMENT", "production").lower()
        return env in ["development", "dev", "local"]

    def sanitize_url(self, url: str) -> str:
        """
        Sanitize URL for safe storage

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        # Trim whitespace
        url = url.strip()

        # Ensure lowercase scheme
        if url.startswith("HTTP"):
            url = url.replace("HTTP", "http", 1)
        if url.startswith("HTTPS"):
            url = url.replace("HTTPS", "https", 1)

        return url

    def extract_embed_url(
        self,
        dashboard_url: str,
        dashboard_type: str
    ) -> str:
        """
        Extract or generate embed-friendly URL

        Some dashboard providers have different URLs for embedding

        Args:
            dashboard_url: Original dashboard URL
            dashboard_type: Dashboard type

        Returns:
            Embed-friendly URL
        """
        # Provider-specific embed URL transformations
        if dashboard_type == "looker":
            # Looker embed URLs typically add /embed/
            if "/embed/" not in dashboard_url:
                parsed = urlparse(dashboard_url)
                path = parsed.path.replace("/dashboards/", "/embed/dashboards/")
                return f"{parsed.scheme}://{parsed.netloc}{path}"

        elif dashboard_type == "tableau":
            # Tableau embed URLs use /views/ path
            if "?:embed=y" not in dashboard_url:
                return f"{dashboard_url}?:embed=y&:showVizHome=no"

        elif dashboard_type == "powerbi":
            # Power BI embed URLs already work as-is
            return dashboard_url

        # Return original URL if no transformation needed
        return dashboard_url

    def get_sandbox_attributes(self, dashboard_type: str) -> List[str]:
        """
        Get recommended iframe sandbox attributes for dashboard type

        Args:
            dashboard_type: Dashboard type

        Returns:
            List of sandbox attributes
        """
        # Base sandbox attributes
        base_attrs = [
            "allow-scripts",
            "allow-same-origin",
            "allow-forms"
        ]

        # Provider-specific additions
        provider_attrs = {
            "looker": ["allow-popups", "allow-downloads"],
            "tableau": ["allow-popups", "allow-modals"],
            "powerbi": ["allow-popups"],
            "metabase": ["allow-downloads"],
            "custom": []
        }

        additional_attrs = provider_attrs.get(dashboard_type, [])

        return base_attrs + additional_attrs
