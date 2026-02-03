from typing import Type, TypeVar, Dict, Any, Optional
import importlib
import logging
import dataclasses
from pathlib import Path
from modules.common.config.api import IConfigManager, BaseConfigDTO, T_ConfigDTO

logger = logging.getLogger(__name__)

class ConfigManagerImpl(IConfigManager):
    """
    Implementation of IConfigManager that loads configuration from python files
    in config/domains/.
    """

    def __init__(self, config_dir: Path = Path("config"), legacy_config: Optional[Any] = None):
        self._configs: Dict[str, BaseConfigDTO] = {}
        self._legacy_config = legacy_config
        self._config_dir = config_dir

        # Pre-load known domains
        # We assume the files exist in config/domains/ and export a variable named <domain>_config
        self._load_domain("government", "config.domains.government", "government_config")
        self._load_domain("finance", "config.domains.finance", "finance_config")
        self._load_domain("stock_market", "config.domains.stock_market", "stock_market_config")
        self._load_domain("household", "config.domains.household", "household_config")

    def _load_domain(self, domain_name: str, module_path: str, variable_name: str):
        try:
            module = importlib.import_module(module_path)
            config = getattr(module, variable_name)
            self._configs[domain_name] = config
            logger.debug(f"Loaded config domain: {domain_name}")
        except ImportError as e:
            logger.warning(f"Could not load config domain {domain_name} from {module_path}: {e}")
        except AttributeError as e:
            logger.warning(f"Could not find {variable_name} in {module_path}: {e}")

    def get_config(self, domain_name: str, dto_class: Type[T_ConfigDTO]) -> T_ConfigDTO:
        if domain_name not in self._configs:
            raise KeyError(f"Configuration domain '{domain_name}' not found.")

        config = self._configs[domain_name]
        if not isinstance(config, dto_class):
             raise TypeError(f"Config for domain '{domain_name}' is not of type {dto_class.__name__}, got {type(config).__name__}")

        return config

    def update_config(self, domain_name: str, new_config_dto: BaseConfigDTO) -> None:
        if domain_name not in self._configs:
            raise KeyError(f"Cannot update unknown domain '{domain_name}'.")
        # In a real implementation, we might validate the new config here
        self._configs[domain_name] = new_config_dto
        logger.info(f"Updated configuration for domain: {domain_name}")

    def get_all_configs(self) -> Dict[str, BaseConfigDTO]:
        return self._configs.copy()

    def register_domain(self, domain_name: str, dto_class: Type[T_ConfigDTO], default_data: Dict[str, Any]) -> None:
        try:
            config = dto_class(**default_data)
            self._configs[domain_name] = config
            logger.info(f"Registered new domain: {domain_name}")
        except TypeError as e:
            raise ValueError(f"Failed to create {dto_class.__name__} from default data: {e}")

    # --- Legacy Support ---
    def get(self, key: str, default: Any = None) -> Any:
        """
        Legacy get method for dot-notation access.
        Tries to resolve against loaded domains first, then legacy config.
        Example: "finance.initial_base_annual_rate"
        """
        parts = key.split('.')
        if len(parts) > 1 and parts[0] in self._configs:
            domain = parts[0]
            attr = parts[1]
            config = self._configs[domain]
            if hasattr(config, attr):
                return getattr(config, attr)

        # Fallback to legacy config
        if self._legacy_config:
            # First try direct attribute if key has no dots
            if hasattr(self._legacy_config, key):
                return getattr(self._legacy_config, key)

            # If key implies nested structure that legacy config might not have directly,
            # but legacy config is usually flat constants.
            pass

        return default

    def set_value_for_test(self, key: str, value: Any) -> None:
        """
        Legacy method for setting values during tests.
        """
        self.override(key, value)

    def override(self, key: str, value: Any) -> None:
        """
        Overrides a configuration value for testing purposes.
        Supports both dot notation for DTOs and direct attribute setting for legacy config.
        """
        parts = key.split('.')
        if len(parts) > 1 and parts[0] in self._configs:
            domain = parts[0]
            attr = parts[1]
            current_config = self._configs[domain]
            # Create a new config with the updated value (since they are frozen)
            new_config = dataclasses.replace(current_config, **{attr: value})
            self._configs[domain] = new_config
            return

        # Fallback for legacy keys (just set on legacy config if possible, or ignore/mock)
        if self._legacy_config:
            setattr(self._legacy_config, key, value)

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to legacy config to support 'config.SOME_CONSTANT' usage.
        """
        if self._legacy_config and hasattr(self._legacy_config, name):
            return getattr(self._legacy_config, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
