import json
import os
from typing import List
from ..dtos import MemoryRecordDTO, QueryDTO
from .base_storage import StorageInterface
from dataclasses import asdict

class FileStorage(StorageInterface):
    """
    WARNING: This implementation is for prototyping and testing only.
    It loads the entire JSON file into memory for every read/write operation.
    Scalability Limitation:
    - Performance degrades linearly with file size (O(N)).
    - Not concurrency-safe.
    - Should be replaced with a database (e.g., SQLite) for production or long simulations.
    """
    def __init__(self, filepath: str = "memory_store.json"):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def save(self, record: MemoryRecordDTO) -> None:
        records = self._read_all()
        records.append(asdict(record))
        with open(self.filepath, 'w') as f:
            json.dump(records, f)

    def load(self, query: QueryDTO) -> List[MemoryRecordDTO]:
        records_data = self._read_all()
        results = []
        for data in records_data:
            # Basic filtering logic
            if query.agent_id is not None and data['agent_id'] != query.agent_id:
                continue
            if query.event_type is not None and data['event_type'] != query.event_type:
                continue
            if query.start_tick is not None and data['tick'] < query.start_tick:
                continue
            if query.end_tick is not None and data['tick'] > query.end_tick:
                continue

            results.append(MemoryRecordDTO(**data))

        if query.limit:
            # Return most recent if sorting by time implicitly (append order)
            # Assuming we want recent ones? Or just first N?
            # Typically query implies "get me history", so usually strictly chronological.
            # But limit usually implies "last N".
            # I will return last N for now as that's typical for "memory context".
            results = results[-query.limit:]

        return results

    def _read_all(self) -> List[dict]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
