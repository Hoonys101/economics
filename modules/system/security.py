import secrets
import logging
from typing import Optional

logger = logging.getLogger("security")

def verify_god_mode_token(provided_token: Optional[str], expected_token: str) -> bool:
    """
    Verifies the provided token against the expected token using constant-time comparison.
    If either token is missing or empty, returns False.
    """
    if not provided_token or not expected_token:
        return False
    return secrets.compare_digest(provided_token, expected_token)
