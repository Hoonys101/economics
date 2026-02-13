import inspect
import os
from functools import wraps
import logging

logger = logging.getLogger(__name__)

AUTHORIZED_MODULES = [
    "modules/finance/",
    "modules/governance/",
    "modules/government/",
    "modules/inventory/",
    "simulation/systems/",
    "simulation/agents/",
    "simulation/firms.py",
    "simulation/core_agents.py",
    "simulation/bank.py",
    "tests/",
]

IS_PURITY_CHECK_ENABLED = os.environ.get("ENABLE_PURITY_CHECKS", "false").lower() == "true"

class ProtocolViolationError(Exception):
    """Raised when an unauthorized module attempts to call a protected method."""
    pass

def enforce_purity(allowed_modules: list = AUTHORIZED_MODULES):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not IS_PURITY_CHECK_ENABLED:
                return func(*args, **kwargs)

            # Get caller frame
            stack = inspect.stack()
            if len(stack) < 2:
                # Should not happen in normal execution
                return func(*args, **kwargs)

            caller_frame = stack[1]
            caller_filepath = os.path.abspath(caller_frame.filename)

            # Normalize path relative to repo root (heuristic)
            # Assuming we are running from repo root or similar structure
            # We check if 'caller_filepath' contains any of the allowed modules as a substring path
            # or if relative path matches.

            # Simple check: does the absolute path contain the relative path string?
            # This is a bit loose but works for "modules/finance/" in "/app/modules/finance/..."

            is_authorized = False
            for mod in allowed_modules:
                # Normalize mod path (remove trailing slash for check if file)
                mod_clean = os.path.normpath(mod.rstrip("/"))
                if mod_clean in caller_filepath:
                    is_authorized = True
                    break

            if not is_authorized:
                logger.error(f"PURITY_VIOLATION | Unauthorized call to '{func.__name__}' from '{caller_filepath}'")
                raise ProtocolViolationError(f"Unauthorized call to '{func.__name__}' from '{caller_filepath}'")

            return func(*args, **kwargs)
        return wrapper
    return decorator
