from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class SettlementResultDTO:
    """
    Result of a settlement execution.
    Used for recording revenue and auditing.
    """
    original_transaction: Any # Transaction
    success: bool
    amount_settled: int
    error: Optional[str] = None
