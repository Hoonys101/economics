import yaml
import logging
import os
from typing import List
from simulation.dtos.registry_dtos import ParameterSchemaDTO

logger = logging.getLogger(__name__)

class SchemaLoader:
    """
    Loads registry schema from YAML configuration.
    """

    # Resolve absolute path relative to project root
    # File is in modules/system/services/schema_loader.py (depth 3 from modules, modules is depth 0 from root? No, modules is in root)
    # path: modules/system/services/schema_loader.py
    # dirname -> modules/system/services
    # dirname -> modules/system
    # dirname -> modules
    # dirname -> root
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DEFAULT_SCHEMA_PATH = os.path.join(_BASE_DIR, "config/domains/registry_schema.yaml")

    @staticmethod
    def load_schema(filepath: str = DEFAULT_SCHEMA_PATH) -> List[ParameterSchemaDTO]:
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                if not isinstance(data, list):
                    logger.error(f"Schema file {filepath} must contain a list of objects.")
                    return []
                # Validate minimal structure if needed, or rely on TypedDict typing (runtime doesn't enforce TypedDict)
                return data
        except FileNotFoundError:
            logger.error(f"Schema file not found at {filepath}")
            return []
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML schema: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading schema: {e}")
            return []
