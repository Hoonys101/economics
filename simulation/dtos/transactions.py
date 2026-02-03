from __future__ import annotations
from typing import TypedDict, List, Any, Optional
from dataclasses import dataclass

# Avoid circular import by using TYPE_CHECKING or just relying on users to import Transaction from models if they need the full class.
# But for DTO alias, we need the class.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.models import Transaction

# Alias for Spec Compliance
# At runtime, users should use simulation.models.Transaction
TransactionDTO = Any

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
