from _typeshed import Incomplete

logger: Incomplete
AUTHORIZED_MODULES: Incomplete
IS_PURITY_CHECK_ENABLED: Incomplete

class ProtocolViolationError(Exception):
    """Raised when an unauthorized module attempts to call a protected method."""

def enforce_purity(allowed_modules: list = ...): ...
