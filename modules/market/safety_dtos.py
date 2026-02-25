from dataclasses import dataclass
from typing import Literal, Optional

@dataclass(frozen=True)
class PriceLimitConfigDTO:
    """
    Configuration for price limits in a specific market.
    Enforces Penny Standard (int) for static ceilings and floors.
    """
    id: str
    is_enabled: bool
    mode: Literal["DYNAMIC", "STATIC"]
    base_limit: float = 0.30  # Default 30%
    static_ceiling: Optional[int] = None
    static_floor: Optional[int] = None

@dataclass(frozen=True)
class MarketSafetyStateDTO:
    """
    Current state of market safety mechanisms for a given market.
    """
    market_id: str
    reference_price: int
    is_halted: bool = False
    last_halt_tick: int = -1

@dataclass(frozen=True)
class ValidationResultDTO:
    """
    Result of an order validation check by the price limit enforcer.
    """
    is_valid: bool
    reason: Optional[str] = None
    adjusted_price: Optional[int] = None
