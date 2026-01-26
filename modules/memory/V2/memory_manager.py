from typing import List, Optional
from modules.memory.api import MemoryV2Interface
from .dtos import MemoryRecordDTO, QueryDTO
from .storage.base_storage import StorageInterface

class MemoryManager(MemoryV2Interface):
    def __init__(self, storage: StorageInterface):
        self.storage = storage

    def add_record(self, record: MemoryRecordDTO) -> None:
        self.storage.save(record)

    def query_records(self, query: QueryDTO) -> List[MemoryRecordDTO]:
        return self.storage.load(query)
