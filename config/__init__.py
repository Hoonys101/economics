import os
import sys
from typing import TYPE_CHECKING

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from modules.system.registry import GlobalRegistry, OriginType
import config.defaults as defaults

# FOUND-01: GlobalRegistry Integration
_registry = GlobalRegistry()

def _init_registry():
    """
    Populates GlobalRegistry from defaults module and simulation.yaml.
    """
    # 1. Load System Defaults from config/defaults.py
    for key in dir(defaults):
        # Heuristic: Uppercase for constants
        if key.isupper():
            val = getattr(defaults, key)
            _registry.set(key, val, OriginType.SYSTEM)

        # Explicitly handle EngineType Enum
        if key == "EngineType":
            val = getattr(defaults, key)
            _registry.set(key, val, OriginType.SYSTEM)

    # 2. Load simulation.yaml
    try:
        import yaml
        yaml_path = os.path.join(os.path.dirname(__file__), "simulation.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    for k, v in yaml_config.items():
                        # Update registry with CONFIG origin
                        _registry.set(k.upper(), v, OriginType.CONFIG)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to load simulation.yaml: {e}\n")

_init_registry()

# Proxy for access
def __getattr__(name):
    val = _registry.get(name)
    if val is not None:
        return val
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__():
    return list(_registry.snapshot().keys())

# Expose registry instance for advanced usage
registry = _registry

# Type hinting support for static analysis (optional/partial)
if TYPE_CHECKING:
    from config.defaults import *
