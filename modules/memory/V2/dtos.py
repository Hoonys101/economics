from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class MemoryRecordDTO:
    tick: int
    agent_id: int
    event_type: str
    data: Dict[str, Any]

@dataclass
class QueryDTO:
    agent_id: Optional[int] = None
    start_tick: Optional[int] = None
    end_tick: Optional[int] = None
    event_type: Optional[str] = None
    limit: Optional[int] = None
