from dataclasses import dataclass
from typing import Any

@dataclass
class SettlementResultDTO:
    """
    Result of a settlement execution.
    Used for recording revenue and auditing.
    """
    original_transaction: Any
    success: bool
    amount_settled: int
    error: str | None = ...
