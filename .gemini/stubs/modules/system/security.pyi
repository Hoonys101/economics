from _typeshed import Incomplete

logger: Incomplete

def verify_god_mode_token(provided_token: str | None, expected_token: str) -> bool:
    """
    Verifies the provided token against the expected token using constant-time comparison.
    If either token is missing or empty, returns False.
    """
