from dataclasses import dataclass, field
from typing import Dict, List, Any
from modules.system.api import CurrencyCode # Added for Phase 33

@dataclass(frozen=True)
class FinanceStateDTO:
    balance: Dict[CurrencyCode, int] # Changed to int (pennies)
    revenue_this_turn: Dict[CurrencyCode, int] # Changed to int (pennies)
    expenses_this_tick: Dict[CurrencyCode, int] # Changed to int (pennies)
    consecutive_loss_turns: int
    profit_history: List[int] # Changed to int (pennies)
    altman_z_score: float
    valuation: Dict[CurrencyCode, int] # Changed to int (pennies)
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    is_publicly_traded: bool

@dataclass(frozen=True)
class ProductionStateDTO:
    current_production: float
    productivity_factor: float
    production_target: float
    capital_stock: int # Changed to int (pennies)
    base_quality: float
    automation_level: float
    specialization: str
    inventory: Dict[str, float]
    input_inventory: Dict[str, float]
    inventory_quality: Dict[str, float]

@dataclass(frozen=True)
class SalesStateDTO:
    inventory_last_sale_tick: Dict[str, int]
    price_history: Dict[str, int] # Changed to int (pennies)
    brand_awareness: float
    perceived_quality: float
    marketing_budget: int # Changed to int (pennies)

@dataclass(frozen=True)
class HRStateDTO:
    employees: List[int]
    employees_data: Dict[int, Dict[str, Any]]
