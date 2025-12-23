"""URL validation utilities for SSRF protection."""

import ipaddress
from urllib.parse import urlparse


def validate_safe_url(url: str) -> None:
    """Validate that a URL is safe for server-side requests (SSRF protection).

    Checks that the URL:
    - Uses http or https scheme
    - Does not point to private/internal IP ranges
    - Does not point to localhost

    Args:
        url: The URL to validate

    Raises:
        ValueError: If the URL is not safe for server-side requests
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}") from e

    # Check scheme
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Must be http or https.")

    # Check hostname exists
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a hostname")

    # Check for localhost variations
    localhost_names = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
    if hostname.lower() in localhost_names:
        raise ValueError("URLs pointing to localhost are not allowed")

    # Try to parse as IP address and check if private
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private:
            raise ValueError("URLs pointing to private IP addresses are not allowed")
        if ip.is_loopback:
            raise ValueError("URLs pointing to loopback addresses are not allowed")
        if ip.is_link_local:
            raise ValueError("URLs pointing to link-local addresses are not allowed")
        if ip.is_multicast:
            raise ValueError("URLs pointing to multicast addresses are not allowed")
        if ip.is_reserved:
            raise ValueError("URLs pointing to reserved addresses are not allowed")
    except ValueError as e:
        # Not an IP address, check for suspicious hostnames
        if "not allowed" in str(e):
            raise
        # It's a hostname, not an IP - that's fine
        pass

    # Check for internal domain patterns (common internal TLDs)
    internal_tlds = {".local", ".internal", ".corp", ".lan", ".home"}
    hostname_lower = hostname.lower()
    for tld in internal_tlds:
        if hostname_lower.endswith(tld):
            raise ValueError(f"URLs with internal TLD '{tld}' are not allowed")
