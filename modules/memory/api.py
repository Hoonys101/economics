from abc import ABC, abstractmethod
from typing import List
from .V2.dtos import MemoryRecordDTO, QueryDTO

class MemoryV2Interface(ABC):
    @abstractmethod
    def add_record(self, record: MemoryRecordDTO) -> None:
        pass

    @abstractmethod
    def query_records(self, query: QueryDTO) -> List[MemoryRecordDTO]:
        pass
