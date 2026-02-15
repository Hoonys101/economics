from dataclasses import dataclass, field
from typing import Dict, List, Optional
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from simulation.models import Transaction

@dataclass(frozen=True)
class TaxPolicyDTO:
    """Snapshot of government tax policy."""
    income_tax_rate: float
    survival_cost: int # Changed to int (pennies)
    government_agent_id: int

@dataclass(frozen=True)
class HRPayrollContextDTO:
    """Context required for payroll processing without passing agent handles."""
    exchange_rates: Dict[CurrencyCode, float]
    tax_policy: Optional[TaxPolicyDTO]
    current_time: int
    firm_id: int
    wallet_balances: Dict[CurrencyCode, int] # Changed to int (pennies)
    labor_market_min_wage: int = 1000 # Changed to int (pennies). Assuming 10.00 -> 1000
    ticks_per_year: int = 365
    severance_pay_weeks: float = 2.0

@dataclass(frozen=True)
class EmployeeUpdateDTO:
    """Data instructing the Orchestrator on how to update an employee agent."""
    employee_id: int
    net_income: int = 0 # Changed to int (pennies)
    fire_employee: bool = False
    severance_pay: int = 0 # Changed to int (pennies)

@dataclass(frozen=True)
class HRPayrollResultDTO:
    """Encapsulates all outcomes from the payroll process."""
    transactions: List[Transaction] = field(default_factory=list)
    employee_updates: List[EmployeeUpdateDTO] = field(default_factory=list)
