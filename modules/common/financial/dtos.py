from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class MoneyDTO:
    """
    Represents a monetary value with its associated currency.
    MIGRATION NOTE: Used to be float 'amount'. Now 'amount_pennies' (int).
    """
    amount_pennies: int
    currency: str = "USD"

@dataclass(frozen=True)
class Claim:
    """
    Represents a creditor's claim against a liquidating entity.
    Migrated from modules.common.dtos with Breaking Change: 'amount' (float) -> 'amount_pennies' (int).
    """
    creditor_id: Any
    amount_pennies: int
    tier: int
    description: str
