from _typeshed import Incomplete
from simulation.dtos.registry_dtos import ParameterSchemaDTO as ParameterSchemaDTO

logger: Incomplete

class SchemaLoader:
    """
    Loads registry schema from YAML configuration.
    """
    DEFAULT_SCHEMA_PATH: Incomplete
    @staticmethod
    def load_schema(filepath: str = ...) -> list[ParameterSchemaDTO]: ...
