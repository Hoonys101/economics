from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.core_agents import Household

@dataclass
class TransactionData:
    run_id: int
    time: int
    buyer_id: int
    seller_id: int
    item_id: str
    quantity: float
    price: float
    market_id: str
    transaction_type: str

@dataclass
class AgentStateData:
    run_id: int
    time: int
    agent_id: int
    agent_type: str
    assets: float
    is_active: bool
    is_employed: Optional[bool] = None
    employer_id: Optional[int] = None
    needs_survival: Optional[float] = None
    needs_labor: Optional[float] = None
    inventory_food: Optional[float] = None
    current_production: Optional[float] = None
    num_employees: Optional[int] = None

@dataclass
class EconomicIndicatorData:
    run_id: int
    time: int
    unemployment_rate: Optional[float] = None
    avg_wage: Optional[float] = None
    food_avg_price: Optional[float] = None
    food_trade_volume: Optional[float] = None
    avg_goods_price: Optional[float] = None
    total_production: Optional[float] = None
    total_consumption: Optional[float] = None
    total_household_assets: Optional[float] = None
    total_firm_assets: Optional[float] = None
    total_food_consumption: Optional[float] = None
    total_inventory: Optional[float] = None

@dataclass
class MarketHistoryData:
    time: int
    market_id: str
    item_id: Optional[str] = None
    avg_price: Optional[float] = None
    trade_volume: Optional[float] = None
    best_ask: Optional[float] = None
    best_bid: Optional[float] = None
    avg_ask: Optional[float] = None
    avg_bid: Optional[float] = None
    worst_ask: Optional[float] = None
    worst_bid: Optional[float] = None

@dataclass
class AIDecisionData:
    run_id: int
    tick: int
    agent_id: int
    decision_type: str
    decision_details: Optional[Dict[str, Any]] = None
    predicted_reward: Optional[float] = None
    actual_reward: Optional[float] = None

@dataclass
class DecisionContext:

    markets: Dict[str, Any]
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    household: Optional[Any] = None # Avoid circular import if possible, or use TYPE_CHECKING
    firm: Optional[Any] = None
