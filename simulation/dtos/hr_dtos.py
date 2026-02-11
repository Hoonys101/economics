from dataclasses import dataclass, field
from typing import Dict, List, Optional
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.models import Transaction

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

@dataclass(frozen=True)
class EmployeeUpdateDTO:
    """Data instructing the Orchestrator on how to update an employee agent."""
    employee_id: int
    net_income: float = 0.0
    fire_employee: bool = False
    severance_pay: float = 0.0

@dataclass(frozen=True)
class HRPayrollResultDTO:
    """Encapsulates all outcomes from the payroll process."""
    transactions: List[Transaction] = field(default_factory=list)
    employee_updates: List[EmployeeUpdateDTO] = field(default_factory=list)
