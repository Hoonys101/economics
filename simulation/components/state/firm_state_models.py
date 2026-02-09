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
    employee_wages: Dict[int, float] = field(default_factory=dict)
    unpaid_wages: Dict[int, List[Tuple[int, float]]] = field(default_factory=dict)
    hires_last_tick: int = 0

@dataclass
class FinanceState:
    """State for Finance operations."""
    retained_earnings: float = 0.0
    dividends_paid_last_tick: float = 0.0
    consecutive_loss_turns: int = 0
    current_profit: Dict[CurrencyCode, float] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0.0})

    revenue_this_turn: Dict[CurrencyCode, float] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0.0})
    cost_this_turn: Dict[CurrencyCode, float] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0.0})
    revenue_this_tick: Dict[CurrencyCode, float] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0.0})
    expenses_this_tick: Dict[CurrencyCode, float] = field(default_factory=lambda: {DEFAULT_CURRENCY: 0.0})

    profit_history: Deque[float] = field(default_factory=lambda: deque(maxlen=50))
    last_revenue: float = 0.0
    last_marketing_spend: float = 0.0

    last_daily_expenses: float = 10.0
    last_sales_volume: float = 1.0
    sales_volume_this_tick: float = 0.0

    is_distressed: bool = False
    distress_tick_counter: int = 0

    # Moved from Firm
    total_debt: float = 0.0
    total_shares: float = 0.0
    treasury_shares: float = 0.0
    dividend_rate: float = 0.0
    valuation: float = 0.0
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
        self.expenses_this_tick = {primary_currency: 0.0}
        self.revenue_this_tick = {primary_currency: 0.0}

@dataclass
class ProductionState:
    """State for Production operations."""
    capital_stock: float = 100.0
    production_target: float = 0.0
    current_production: float = 0.0
    productivity_factor: float = 1.0
    automation_level: float = 0.0

    # Inventory quality tracking
    base_quality: float = 1.0
    inventory_quality: Dict[str, float] = field(default_factory=dict)

    # Raw Materials (WO-030)
    input_inventory: Dict[str, float] = field(default_factory=dict)

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
    marketing_budget: float = 0.0
    marketing_budget_rate: float = 0.05
    prev_awareness: float = 0.0

    last_prices: Dict[str, float] = field(default_factory=dict)
    inventory_last_sale_tick: Dict[str, int] = field(default_factory=dict)

    # Metrics for rewards/tracking
    prev_market_share: float = 0.0
    prev_assets: float = 0.0
    prev_avg_quality: float = 1.0
