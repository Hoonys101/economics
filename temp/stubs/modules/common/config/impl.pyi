from _typeshed import Incomplete
from modules.common.config.api import BaseConfigDTO as BaseConfigDTO, IConfigManager as IConfigManager, T_ConfigDTO as T_ConfigDTO
from pathlib import Path
from typing import Any

logger: Incomplete

class ConfigManagerImpl(IConfigManager):
    """
    Implementation of IConfigManager that loads configuration from python files
    in config/domains/.
    """
    def __init__(self, config_dir: Path = ..., legacy_config: Any | None = None) -> None: ...
    def get_config(self, domain_name: str, dto_class: type[T_ConfigDTO]) -> T_ConfigDTO: ...
    def update_config(self, domain_name: str, new_config_dto: BaseConfigDTO) -> None: ...
    def get_all_configs(self) -> dict[str, BaseConfigDTO]: ...
    def register_domain(self, domain_name: str, dto_class: type[T_ConfigDTO], default_data: dict[str, Any]) -> None: ...
    def get(self, key: str, default: Any = None) -> Any:
        '''
        Legacy get method for dot-notation access.
        Tries to resolve against loaded domains first, then legacy config.
        Example: "finance.initial_base_annual_rate"
        '''
    def set_value_for_test(self, key: str, value: Any) -> None:
        """
        Legacy method for setting values during tests.
        """
    def override(self, key: str, value: Any) -> None:
        """
        Overrides a configuration value for testing purposes.
        Supports both dot notation for DTOs and direct attribute setting for legacy config.
        """
    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to legacy config to support 'config.SOME_CONSTANT' usage.
        """
