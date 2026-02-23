import abc
from abc import ABC, abstractmethod
from modules.common.dtos import Claim as Claim
from modules.finance.api import IFinancialAgent as IFinancialAgent
from simulation.firms import Firm as Firm
from typing import Protocol

class IHRService(ABC, metaclass=abc.ABCMeta):
    @abstractmethod
    def calculate_liquidation_employee_claims(self, firm: Firm, current_tick: int) -> list[Claim]:
        """Calculates all employee-related claims (wages, severance) for a firm in liquidation."""

class IEmployeeDataProvider(IFinancialAgent, Protocol):
    """
    Protocol for accessing employee data and managing employment lifecycle.
    Decouples HR/Finance departments from the concrete Household agent.
    Inherits IFinancialAgent to support wage/severance payments.
    MIGRATION: Monetary values are integers (pennies).
    """
    id: int
    employer_id: int | None
    is_employed: bool
    @property
    def labor_skill(self) -> float:
        """The employee's current labor skill multiplier."""
    @property
    def education_level(self) -> int:
        """The employee's education level (0-N)."""
    @property
    def labor_income_this_tick(self) -> int:
        """Cumulative labor income earned in the current tick (pennies)."""
    @labor_income_this_tick.setter
    def labor_income_this_tick(self, value: int) -> None:
        """Updates the cumulative labor income (pennies)."""
    @property
    def employment_start_tick(self) -> int:
        """The tick when the current employment started."""
    @employment_start_tick.setter
    def employment_start_tick(self, value: int) -> None:
        """Sets the employment start tick."""
    def quit(self) -> None:
        """
        Executes the resignation process for the employee.
        Sets is_employed to False and clears employer_id.
        """
