import json
from collections import deque, defaultdict
from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Any

class SimulationEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder for Simulation DTOs and Types.
    Handles deque, defaultdict, Enum, and Dataclasses.
    """
    def default(self, obj: Any) -> Any:
        if isinstance(obj, deque):
            return list(obj)
        if isinstance(obj, defaultdict):
            return dict(obj)
        if isinstance(obj, Enum):
            return obj.name  # Store Enum name for readability and stability
        if hasattr(obj, "get_all_balances"): # Wallet
             return obj.get_all_balances()
        if hasattr(obj, "holdings"): # Portfolio
             return obj.holdings
        if is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)

def serialize_state(state_obj: Any) -> str:
    """Serializes a state object (DTO) to a JSON string."""
    return json.dumps(state_obj, cls=SimulationEncoder)

def deserialize_state(json_str: str, target_cls: Any) -> Any:
    """
    Deserializes a JSON string to a target DTO class.
    Note: Deep reconstruction of Enums/Deques from JSON dicts requires
    specific `from_dict` logic on DTOs or a sophisticated decoder.
    For this implementation, we rely on standard dict hydration and
    Agent-side logic to convert lists back to deques if needed.
    """
    if not json_str:
        return None
    data = json.loads(json_str)
    # Basic reconstruction - Agent classes must handle dict-to-object conversion
    # or we trust the Agent's restore method to handle the dict structure.
    return data
