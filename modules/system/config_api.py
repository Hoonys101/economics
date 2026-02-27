"""
modules/system/config_api.py

Defines the ConfigProxy and Configuration Registry APIs.
Resolves TD-CONF-GHOST-BIND by enabling lazy-loading and runtime overrides of configuration constants.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union, TYPE_CHECKING, List, Callable
from dataclasses import dataclass, field
from modules.system.api import IConfigurationRegistry, RegistryValueDTO, OriginType, RegistryObserver
from modules.system.registry import GlobalRegistry
import importlib
import types
import threading

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

class ConfigProxy(IConfigurationRegistry):
    """
    A Singleton Proxy that provides dynamic access to configuration values.

    It wraps the GlobalRegistry to ensure runtime binding while providing
    a dot-notation interface and maintaining backward compatibility.

    Usage:
        from modules.system.config_api import current_config
        tax_rate = current_config.TAX_RATE  # Resolved at runtime

    Legacy Compatibility:
        This proxy can be injected or aliased, but legacy 'from config import CONST'
        will still bind early. This class is the enabler for the refactor.
    """

    def __init__(self):
        # The internal store of all config values
        self._registry = GlobalRegistry()
        # Metadata for validation
        self._metadata: Dict[str, ConfigKeyMeta] = {}
        # Fallback module (legacy config/defaults.py)
        self._defaults_module: Optional[ModuleType] = None
        # Lazy Loading Callbacks
        self._lazy_loaders: List[Callable[[], None]] = []
        self._initialized = False
        self._init_lock = threading.RLock()

    def register_lazy_loader(self, loader: Callable[[], None]) -> None:
        """Registers a callback to load configuration lazily."""
        self._lazy_loaders.append(loader)

    def _ensure_initialized(self) -> None:
        """
        Executes all registered lazy loaders if not already initialized.
        Uses double-checked locking for thread safety and prevents recursion.
        """
        if not self._initialized:
            with self._init_lock:
                if not self._initialized:
                    # RECURSION GUARD: Set initialized to True BEFORE running loaders
                    # to prevent infinite recursion if a loader calls current_config.set/get
                    self._initialized = True
                    try:
                        for loader in self._lazy_loaders:
                            loader()
                    except Exception as e:
                        # Fallback: if loading fails, reset initialized flag or log it
                        # For now, we prefer to keep it True to avoid repeated hangs
                        sys.stderr.write(f"Error during ConfigProxy initialization: {e}\n")

    def bootstrap_from_module(self, module: ModuleType) -> None:
        """
        Loads initial values from a Python module (e.g., config.defaults).
        """
        self._defaults_module = module
        # Populate registry with SYSTEM origin
        for key in dir(module):
            if key.isupper():
                val = getattr(module, key)
                self._registry.set(key, val, OriginType.SYSTEM)

            # Explicitly handle EngineType Enum
            if key == "EngineType":
                val = getattr(module, key)
                self._registry.set(key, val, OriginType.SYSTEM)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value. Delegate to GlobalRegistry.
        """
        self._ensure_initialized() # Ensure config is loaded before access
        return self._registry.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """
        Enables dot-access (current_config.TAX_RATE).
        """
        # Avoid recursion for internal attributes
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        self._ensure_initialized() # Ensure config is loaded before access

        # Check registry first using get_entry to differentiate None value from missing key
        entry = self._registry.get_entry(name)
        if entry is not None:
            return entry.value

        # Fallback to defaults module directly if not in registry?
        # bootstrap_from_module should have populated it.
        # But just in case:
        if self._defaults_module and hasattr(self._defaults_module, name):
            return getattr(self._defaults_module, name)

        raise AttributeError(f"Config key '{name}' not found.")

    def set(self, key: str, value: Any, origin: OriginType = OriginType.USER) -> None:
        """
        Updates a value with origin tracking. Delegate to GlobalRegistry.
        """
        self._ensure_initialized() # Ensure config is loaded before set.

        # Validate if metadata exists
        if key in self._metadata:
            meta = self._metadata[key]
            if not isinstance(value, meta.value_type) and meta.value_type is not Any:
                 # Try casting if it's a simple type mismatch
                 try:
                     value = meta.value_type(value)
                 except (ValueError, TypeError):
                     pass # Let it fail or be strictly checked? strict for now.

        self._registry.set(key, value, origin)

    def snapshot(self) -> Dict[str, Any]:
        """Returns a dict of current effective values."""
        self._ensure_initialized()
        # GlobalRegistry.snapshot returns Dict[str, RegistryValueDTO]
        # We need to return Dict[str, Any] (values) to match IConfigurationRegistry signature if it implies values
        # RegistryValueDTO is Any.

        # Let's map it to values to be consistent with previous implementation
        snapshot_dtos = self._registry.snapshot()
        result = {}
        for key, dto in snapshot_dtos.items():
            result[key] = dto.value
        return result

    def register_observer(self, observer: RegistryObserver) -> None:
        self._registry.subscribe(observer)

    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults.
        """
        self._registry.reset_to_defaults()

    def get_registry(self) -> GlobalRegistry:
        """
        Returns the underlying GlobalRegistry instance.
        """
        return self._registry

# Singleton Instance
current_config = ConfigProxy()
