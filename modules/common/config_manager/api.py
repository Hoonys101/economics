from __future__ import annotations
from typing import Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Manages loading configuration from YAML files and provides a unified access interface.
    It supports a hybrid mode, falling back to a legacy config module for values
    not found in the YAML files. This class is designed as a leaf node and should not
    have dependencies on other simulation modules.
    """

    def __init__(self, config_dir: Path, legacy_config: Optional[Any] = None):
        """
        Initializes the ConfigManager, loading all YAML files from the specified directory.

        Args:
            config_dir: The directory path containing .yaml configuration files.
            legacy_config: An optional legacy config module (e.g., config.py) to use as a fallback.
        """
        ...

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value using dot notation.

        It first searches the loaded YAML configuration. If not found, it attempts
        to retrieve the value from the legacy config module (if provided).
        If still not found, it returns the default value.

        Example:
            config.get('simulation.batch_save_interval', 50)
            config.get('finance.bank_defaults.credit_spread_base')

        Args:
            key: The dot-separated key for the configuration value.
            default: The value to return if the key is not found anywhere.

        Returns:
            The requested configuration value.
        """
        ...

    def set_value_for_test(self, key: str, value: Any) -> None:
        """
        Dynamically sets or overrides a configuration value for testing purposes.
        This method should ONLY be used in test suites to avoid file I/O.
        It allows monkey-patching configuration at runtime.

        Example (in a pytest test):
            config_manager.set_value_for_test('ai.epsilon_decay.initial', 0.99)

        Args:
            key: The dot-separated key to set.
            value: The value to assign to the key.
        """
        ...
