import yaml
import logging
from typing import List
from dashboard.dtos import ParameterSchemaDTO

logger = logging.getLogger(__name__)

class SchemaLoader:
    """
    Loads registry schema from YAML configuration.
    """

    DEFAULT_SCHEMA_PATH = "config/domains/registry_schema.yaml"

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
