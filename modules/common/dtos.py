from dataclasses import dataclass
from typing import Any

@dataclass
class Claim:
    """Represents a creditor's claim against a liquidating entity."""
    creditor_id: Any
    amount: float
    tier: int
    description: str
