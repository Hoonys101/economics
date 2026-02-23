import abc
from .V2.dtos import MemoryRecordDTO as MemoryRecordDTO, QueryDTO as QueryDTO
from abc import ABC, abstractmethod

class MemoryV2Interface(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def add_record(self, record: MemoryRecordDTO) -> None: ...
    @abstractmethod
    def query_records(self, query: QueryDTO) -> list[MemoryRecordDTO]: ...
