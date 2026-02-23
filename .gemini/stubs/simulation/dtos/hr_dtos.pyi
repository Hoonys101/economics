from dataclasses import dataclass, field
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.models import Transaction as Transaction

@dataclass(frozen=True)
class TaxPolicyDTO:
    """Snapshot of government tax policy."""
    income_tax_rate: float
    survival_cost: int
    government_agent_id: int

@dataclass(frozen=True)
class HRPayrollContextDTO:
    """Context required for payroll processing without passing agent handles."""
    exchange_rates: dict[CurrencyCode, float]
    tax_policy: TaxPolicyDTO | None
    current_time: int
    firm_id: int
    wallet_balances: dict[CurrencyCode, int]
    labor_market_min_wage: int = ...
    ticks_per_year: int = ...
    severance_pay_weeks: float = ...

@dataclass(frozen=True)
class EmployeeUpdateDTO:
    """Data instructing the Orchestrator on how to update an employee agent."""
    employee_id: int
    net_income: int = ...
    fire_employee: bool = ...
    severance_pay: int = ...

@dataclass(frozen=True)
class HRPayrollResultDTO:
    """Encapsulates all outcomes from the payroll process."""
    transactions: list[Transaction] = field(default_factory=list)
    employee_updates: list[EmployeeUpdateDTO] = field(default_factory=list)
