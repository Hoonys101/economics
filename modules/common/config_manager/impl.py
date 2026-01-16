from __future__ import annotations
from typing import Any, Optional
import yaml
from pathlib import Path
import logging

from modules.common.config_manager.api import ConfigManager

logger = logging.getLogger(__name__)

class ConfigManagerImpl(ConfigManager):
    def __init__(self, config_dir: Path, legacy_config: Optional[Any] = None):
        self._config = {}
        self._legacy_config = legacy_config
        if not config_dir.exists():
            logger.warning(f"Config directory '{config_dir}' not found. Continuing with empty config.")
            return

        for config_file in config_dir.glob('*.yaml'):
            try:
                with open(config_file, 'r') as f:
                    data = yaml.safe_load(f)
                    config_key = config_file.stem
                    self._config[config_key] = data
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file '{config_file}': {e}")
            except Exception as e:
                logger.error(f"Error loading config file '{config_file}': {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        parts = key.split('.')
        value = self._config
        try:
            for part in parts:
                value = value[part]
            return value
        except (KeyError, TypeError):
            if self._legacy_config:
                legacy_key = key.replace('.', '_').upper()
                return getattr(self._legacy_config, legacy_key, default)
            return default

    def set_value_for_test(self, key: str, value: Any) -> None:
        parts = key.split('.')
        node = self._config
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
