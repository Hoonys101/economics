from dataclasses import dataclass, field
from typing import Dict, List, Any
from modules.system.api import CurrencyCode # Added for Phase 33

@dataclass(frozen=True)
class FinanceStateDTO:
    balance: Dict[CurrencyCode, float] # Changed for Phase 33
    revenue_this_turn: Dict[CurrencyCode, float] # Changed for Phase 33
    expenses_this_tick: Dict[CurrencyCode, float] # Changed for Phase 33
    consecutive_loss_turns: int
    profit_history: List[float] # This might need to be Dict if it's total profit in a specific currency, but for now let's keep it simple or change to Dict
    altman_z_score: float
    valuation: Dict[CurrencyCode, float] # Changed for Phase 33
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    is_publicly_traded: bool

@dataclass(frozen=True)
class ProductionStateDTO:
    current_production: float
    productivity_factor: float
    production_target: float
    capital_stock: float
    base_quality: float
    automation_level: float
    specialization: str
    inventory: Dict[str, float]
    input_inventory: Dict[str, float]
    inventory_quality: Dict[str, float]

@dataclass(frozen=True)
class SalesStateDTO:
    inventory_last_sale_tick: Dict[str, int]
    price_history: Dict[str, float]
    brand_awareness: float
    perceived_quality: float
    marketing_budget: float

@dataclass(frozen=True)
class HRStateDTO:
    employees: List[int]
    employees_data: Dict[int, Dict[str, Any]]
