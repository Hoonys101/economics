import os
import sys
from typing import TYPE_CHECKING

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from modules.system.config_api import current_config, OriginType
import config.defaults as defaults

# Bootstrap defaults into the global registry
current_config.bootstrap_from_module(defaults)

# Expose registry instance for advanced usage (legacy support)
registry = current_config.get_registry()

def _load_simulation_yaml():
    """
    Loads simulation.yaml into the configuration.
    """
    try:
        import yaml
        yaml_path = os.path.join(os.path.dirname(__file__), "simulation.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    for k, v in yaml_config.items():
                        # Update registry with CONFIG origin
                        current_config.set(k.upper(), v, OriginType.CONFIG)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to load simulation.yaml: {e}\n")

# Load YAML immediately
_load_simulation_yaml()

# Proxy for access
def __getattr__(name):
    # Delegate to ConfigProxy which handles None values correctly via get_entry
    # We must call getattr directly on the instance to trigger its __getattr__
    try:
        return getattr(current_config, name)
    except AttributeError:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def __dir__():
    return list(current_config.snapshot().keys()) + ["registry"]

# Type hinting support for static analysis (optional/partial)
if TYPE_CHECKING:
    from config.defaults import *
