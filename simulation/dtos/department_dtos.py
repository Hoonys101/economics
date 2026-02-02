from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class FinanceStateDTO:
    balance: float
    revenue_this_turn: float
    expenses_this_tick: float
    consecutive_loss_turns: int
    profit_history: List[float]
    altman_z_score: float
    valuation: float
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    is_publicly_traded: bool

@dataclass
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

@dataclass
class SalesStateDTO:
    inventory_last_sale_tick: Dict[str, int]
    price_history: Dict[str, float]
    brand_awareness: float
    perceived_quality: float
    marketing_budget: float

@dataclass
class HRStateDTO:
    employees: List[int]
    employees_data: Dict[int, Dict[str, Any]]
