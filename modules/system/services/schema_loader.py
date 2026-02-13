import yaml
import logging
from pathlib import Path
from typing import List
from simulation.dtos.registry_dtos import ParameterSchemaDTO

logger = logging.getLogger(__name__)

class SchemaLoader:
    """
    Loads registry schema from YAML configuration.
    """

    # Resolve absolute path relative to project root
    # modules/system/services/schema_loader.py -> parent x 4 = root
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    DEFAULT_SCHEMA_PATH = str(_PROJECT_ROOT / "config" / "domains" / "registry_schema.yaml")

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
