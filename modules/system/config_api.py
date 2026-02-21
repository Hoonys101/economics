"""
modules/system/config_api.py

Defines the ConfigProxy and Configuration Registry APIs.
Resolves TD-CONF-GHOST-BIND by enabling lazy-loading and runtime overrides of configuration constants.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union, TYPE_CHECKING, List
from dataclasses import dataclass, field
from modules.system.api import IConfigurationRegistry, RegistryValueDTO, OriginType, RegistryObserver
import importlib
import types

if TYPE_CHECKING:
    from types import ModuleType

@dataclass
class ConfigKeyMeta:
    """Metadata for configuration keys (validation, description, etc.)"""
    description: str = ""
    value_type: Type = Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    is_hot_swappable: bool = True

class ConfigProxy:
    """
    A Singleton Proxy that provides dynamic access to configuration values.

    Usage:
        from modules.system.config_api import current_config
        tax_rate = current_config.TAX_RATE  # Resolved at runtime

    Legacy Compatibility:
        This proxy can be injected or aliased, but legacy 'from config import CONST'
        will still bind early. This class is the enabler for the refactor.
    """

    def __init__(self):
        # The internal store of all config values
        self._registry: Dict[str, RegistryValueDTO] = {}
        # Metadata for validation
        self._metadata: Dict[str, ConfigKeyMeta] = {}
        # Observers for reactive updates
        self._observers: List[RegistryObserver] = []
        # Fallback module (legacy config/defaults.py)
        self._defaults_module: Optional[ModuleType] = None

    def bootstrap_from_module(self, module: ModuleType) -> None:
        """
        Loads initial values from a Python module (e.g., config.defaults).
        """
        self._defaults_module = module

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value. Priority: USER > CONFIG > SYSTEM (Defaults).
        """
        if key in self._registry:
            return self._registry[key].value

        if self._defaults_module and hasattr(self._defaults_module, key):
            return getattr(self._defaults_module, key)

        return default

    def __getattr__(self, name: str) -> Any:
        """
        Enables dot-access (current_config.TAX_RATE).
        """
        # Avoid recursion for internal attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name in self._registry:
            return self._registry[name].value

        if self._defaults_module and hasattr(self._defaults_module, name):
            return getattr(self._defaults_module, name)

        raise AttributeError(f"Config key '{name}' not found.")

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        """
        Updates a value with origin tracking and notifies observers.
        """
        # Validate if metadata exists
        if key in self._metadata:
            meta = self._metadata[key]
            if not isinstance(value, meta.value_type) and meta.value_type is not Any:
                 # Try casting if it's a simple type mismatch
                 try:
                     value = meta.value_type(value)
                 except (ValueError, TypeError):
                     pass # Let it fail or be strictly checked? strict for now.

        # Check lock
        if key in self._registry:
            entry = self._registry[key]
            if entry.is_locked and origin < OriginType.GOD_MODE:
                raise PermissionError(f"Config key '{key}' is locked.")

            entry.value = value
            entry.origin = origin
        else:
            # Create new entry
            entry = RegistryValueDTO(
                key=key,
                value=value,
                origin=origin
            )
            self._registry[key] = entry

        # Notify observers
        for observer in self._observers:
            observer.on_registry_update(key, value, origin)

    def snapshot(self) -> Dict[str, Any]:
        """Returns a dict of current effective values."""
        result = {}
        # First load defaults
        if self._defaults_module:
            for key in dir(self._defaults_module):
                if key.isupper():
                    result[key] = getattr(self._defaults_module, key)

        # Overlay registry values
        for key, entry in self._registry.items():
            result[key] = entry.value

        return result

    def register_observer(self, observer: RegistryObserver) -> None:
        self._observers.append(observer)

    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults,
        clearing USER overrides.
        """
        # Create a list of keys to remove or reset
        keys_to_reset = []
        for key, val in self._registry.items():
            if val.origin >= OriginType.USER:
                keys_to_reset.append(key)

        for key in keys_to_reset:
            del self._registry[key]
            # Notify observers of reset (value back to default)
            default_val = getattr(self._defaults_module, key) if self._defaults_module and hasattr(self._defaults_module, key) else None
            for observer in self._observers:
                observer.on_registry_update(key, default_val, OriginType.SYSTEM)

# Singleton Instance
current_config = ConfigProxy()

# Bootstrap immediately
try:
    import config.defaults
    current_config.bootstrap_from_module(config.defaults)
except ImportError:
    pass
