from abc import ABC, abstractmethod
from typing import List
from ..dtos import MemoryRecordDTO, QueryDTO

class StorageInterface(ABC):
    @abstractmethod
    def save(self, record: MemoryRecordDTO) -> None:
        pass

    @abstractmethod
    def load(self, query: QueryDTO) -> List[MemoryRecordDTO]:
        pass
