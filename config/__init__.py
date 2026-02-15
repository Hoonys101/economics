import os
import sys
from modules.system.registry import GlobalRegistry, OriginType
from config import defaults

# ==============================================================================
# FOUND-01: GlobalRegistry Integration
# ==============================================================================
_registry = GlobalRegistry()

def _init_registry():
    """
    Moves all uppercase constants from defaults module to GlobalRegistry.
    This ensures SSoT and enables hot-swapping.
    """
    # Load defaults from config.defaults
    for k in dir(defaults):
        # Heuristic: Uppercase constants are config parameters
        if k.isupper():
            val = getattr(defaults, k)
            # Exclude types/classes if any match the heuristic (though unlikely for uppercase)
            if isinstance(val, type):
                continue

            _registry.set(k, val, OriginType.SYSTEM)

_init_registry()

# Load simulation.yaml
try:
    import yaml
    yaml_path = os.path.join(os.path.dirname(__file__), "simulation.yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                for k, v in yaml_config.items():
                    # Update registry with CONFIG origin
                    # This overrides SYSTEM defaults if key exists, or adds new one
                    _registry.set(k.upper(), v, OriginType.CONFIG)
except Exception as e:
    # Fail silently or log error to stderr
    sys.stderr.write(f"Warning: Failed to load simulation.yaml: {e}\n")

# Proxy for access
def __getattr__(name):
    # 1. Check Registry (Dynamic Config)
    val = _registry.get(name)
    if val is not None:
        return val

    # 2. Check Defaults (Static Classes/Enums like EngineType)
    if hasattr(defaults, name):
        return getattr(defaults, name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__():
    # Merge registry keys and defaults keys for autocomplete/inspection
    registry_keys = list(_registry.snapshot().keys())
    default_keys = [k for k in dir(defaults) if not k.startswith("_")]
    return list(set(registry_keys + default_keys))

# Expose registry instance
registry = _registry
