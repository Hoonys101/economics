from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass(frozen=True)
class MarketStateDTO:
    """Read-only snapshot of a market's state for DTO-based decoupling."""
    market_id: str
    price_history: Dict[str, List[int]]  # Penny-based price history
    volume_history: Dict[str, List[float]]
    current_bids: int
    current_asks: int
    is_halted: bool = False
    avg_price: int = 0

@dataclass(frozen=True)
class AgentContextDTO:
    """Thin context DTO to replace full WorldState injection into agents."""
    tick: int
    market_configs: Dict[str, Any]
    global_params: Dict[str, Any]
    is_crisis_mode: bool = False
