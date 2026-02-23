from dataclasses import dataclass, field as field
from typing import Any

@dataclass
class MemoryRecordDTO:
    tick: int
    agent_id: int
    event_type: str
    data: dict[str, Any]

@dataclass
class QueryDTO:
    agent_id: int | None = ...
    start_tick: int | None = ...
    end_tick: int | None = ...
    event_type: str | None = ...
    limit: int | None = ...
