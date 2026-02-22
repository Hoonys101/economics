from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Deque
from collections import deque
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from modules.hr.api import IEmployeeDataProvider

@dataclass
class HRState:
    """State for HR operations."""
    employees: List[IEmployeeDataProvider] = field(default_factory=list)
    employee_wages: Dict[int, int] = field(default_factory=dict) # MIGRATION: Wages in int pennies
    employees_data: Dict[int, Dict[str, Any]] = field(default_factory=dict) # Metadata (e.g. productivity_modifier)
    unpaid_wages: Dict[int, List[Tuple[int, int]]] = field(default_factory=dict) # MIGRATION: Wages in int pennies

    # Adaptive Learning / Bargaining Memory
    hires_this_tick: int = 0
    hires_prev_tick: int = 0

    target_hires_this_tick: int = 0
    target_hires_prev_tick: int = 0

    wage_offer_this_tick: int = 0
    wage_offer_prev_tick: int = 0

    @property
    def hires_last_tick(self) -> int:
        """Deprecated alias for backward compatibility."""
        return self.hires_this_tick

    @hires_last_tick.setter
    def hires_last_tick(self, value: int):
        self.hires_this_tick = value

@dataclass
class FinanceState:
    """
    State for Finance operations.
    MIGRATION: All monetary values are now integers (pennies).
    """
    retained_earnings_pennies: int = 0
    dividends_paid_last_tick_pennies: int = 0
    consecutive_loss_turns: int = 0
    current_profit: Dict[CurrencyCode, int] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0})

    revenue_this_turn: Dict[CurrencyCode, int] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0})
    cost_this_turn: Dict[CurrencyCode, int] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0})
    revenue_this_tick: Dict[CurrencyCode, int] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0})
    expenses_this_tick: Dict[CurrencyCode, int] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0})

    profit_history: Deque[int] = field(default_factory=lambda: deque(maxlen=50))
    last_revenue_pennies: int = 0
    last_marketing_spend_pennies: int = 0

    last_daily_expenses_pennies: int = 1000 # Default 10.00
    last_sales_volume: float = 1.0
    sales_volume_this_tick: float = 0.0

    is_distressed: bool = False
    distress_tick_counter: int = 0

    # Moved from Firm
    total_debt_pennies: int = 0
    average_interest_rate: float = 0.0
    total_shares: float = 0.0
    treasury_shares: float = 0.0
    dividend_rate: float = 0.0
    valuation_pennies: int = 0
    has_bailout_loan: bool = False
    is_bankrupt: bool = False

    # Real Estate Assets (IPropertyOwner)
    owned_properties: List[int] = field(default_factory=list)

    # For IPO initialization
    is_publicly_traded: bool = True
    founder_id: Optional[int] = None

    def reset_tick_counters(self, primary_currency: CurrencyCode):
        """Resets tick-specific counters."""
        self.sales_volume_this_tick = 0.0
        self.expenses_this_tick = {primary_currency: 0}
        self.revenue_this_tick = {primary_currency: 0}

@dataclass
class ProductionState:
    """State for Production operations."""
    capital_stock: int = 10000 # MIGRATION: int pennies. Default 100.00
    production_target: float = 0.0
    current_production: float = 0.0
    productivity_factor: float = 1.0
    automation_level: float = 0.0

    # Inventory quality tracking
    base_quality: float = 1.0
    inventory_quality: Dict[str, float] = field(default_factory=dict)

    # Research
    research_history: Dict[str, Any] = field(default_factory=lambda: {
        "total_spent": 0.0,
        "success_count": 0,
        "last_success_tick": -1
    })

    sector: str = "FOOD"
    specialization: str = "GENERIC"

@dataclass
class SalesState:
    """State for Sales operations."""
    marketing_budget: float = 0.0 # This is usually a budget limit or target. Should be int? Yes.
    # But SalesEngine treats it as an allocation. Let's make it float for now if it's a 'rate' derived value, but if it's absolute, int.
    # Firm.marketing_budget property delegates here.
    # Let's check Usage. SalesEngine.adjust_marketing_budget returns a budget amount.
    # I will change it to pennies.
    marketing_budget_pennies: int = 0

    marketing_budget_rate: float = 0.05
    prev_awareness: float = 0.0

    # Brand State
    adstock: float = 0.0
    brand_awareness: float = 0.0
    perceived_quality: float = 0.0

    last_prices: Dict[str, int] = field(default_factory=dict) # MIGRATION: int pennies.

    inventory_last_sale_tick: Dict[str, int] = field(default_factory=dict)

    # Metrics for rewards/tracking
    prev_market_share: float = 0.0
    prev_assets: float = 0.0
    prev_avg_quality: float = 1.0
