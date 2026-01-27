from __future__ import annotations
from typing import TypedDict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class TransactionResult:
    """Result of a transaction processing attempt."""
    success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    amount_processed: float = 0.0

class TransactionContext(TypedDict):
    """Context passed to transaction handlers."""
    simulation_state: Any # SimulationState
    current_time: int
