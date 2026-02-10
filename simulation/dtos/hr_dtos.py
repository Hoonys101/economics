from dataclasses import dataclass, field
from typing import Dict, List, Optional
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode

@dataclass(frozen=True)
class TaxPolicyDTO:
    """Snapshot of government tax policy."""
    income_tax_rate: float
    survival_cost: float
    government_agent_id: int

@dataclass(frozen=True)
class HRPayrollContextDTO:
    """Context required for payroll processing without passing agent handles."""
    exchange_rates: Dict[CurrencyCode, float]
    tax_policy: Optional[TaxPolicyDTO]
    current_time: int
    firm_id: int
    wallet_balances: Dict[CurrencyCode, float]
    labor_market_min_wage: float = 10.0
    ticks_per_year: int = 365
    severance_pay_weeks: float = 2.0
