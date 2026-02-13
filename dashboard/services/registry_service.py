from typing import List, Optional
from dashboard.dtos import ParameterSchemaDTO
from modules.system.services.schema_loader import SchemaLoader

class RegistryService:
    """
    Service to provide metadata for simulation parameters.
    Loads from schema configuration via SchemaLoader.
    """

    def __init__(self):
        self._schema_cache: Optional[List[ParameterSchemaDTO]] = None

    def get_all_metadata(self) -> List[ParameterSchemaDTO]:
        if self._schema_cache is None:
            self._schema_cache = SchemaLoader.load_schema()
        return self._schema_cache

    def get_metadata(self, key: str) -> Optional[ParameterSchemaDTO]:
        metadata_list = self.get_all_metadata()
        for meta in metadata_list:
            if meta['key'] == key:
                return meta
        return None
