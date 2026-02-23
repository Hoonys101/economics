from _typeshed import Incomplete
from dataclasses import dataclass, field as field
from modules.system.api import IConfigurationRegistry as IConfigurationRegistry, OriginType as OriginType, RegistryObserver as RegistryObserver, RegistryValueDTO as RegistryValueDTO
from modules.system.registry import GlobalRegistry as GlobalRegistry
from types import ModuleType
from typing import Any

@dataclass
class ConfigKeyMeta:
    """Metadata for configuration keys (validation, description, etc.)"""
    description: str = ...
    value_type: type = ...
    min_value: int | float | None = ...
    max_value: int | float | None = ...
    is_hot_swappable: bool = ...

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
    def __init__(self) -> None: ...
    def bootstrap_from_module(self, module: ModuleType) -> None:
        """
        Loads initial values from a Python module (e.g., config.defaults).
        """
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a value. Delegate to GlobalRegistry.
        """
    def __getattr__(self, name: str) -> Any:
        """
        Enables dot-access (current_config.TAX_RATE).
        """
    def set(self, key: str, value: Any, origin: OriginType = ...) -> None:
        """
        Updates a value with origin tracking. Delegate to GlobalRegistry.
        """
    def snapshot(self) -> dict[str, Any]:
        """Returns a dict of current effective values."""
    def register_observer(self, observer: RegistryObserver) -> None: ...
    def reset_to_defaults(self) -> None:
        """
        Resets all configuration values to their SYSTEM or CONFIG defaults.
        """
    def get_registry(self) -> GlobalRegistry:
        """
        Returns the underlying GlobalRegistry instance.
        """

current_config: Incomplete
