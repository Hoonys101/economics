# modules/government/welfare/api.py
from typing import Protocol, List, Dict, Any
from simulation.models import Transaction

class IWelfareService(Protocol):
    """
    Interface for the welfare service.
    Handles social safety nets and support for households.
    """

    def get_survival_cost(self, market_data: Dict[str, Any]) -> float:
        """Calculates current survival cost based on market prices."""
        ...

    def run_welfare_check(self, households: List[Any], market_data: Dict[str, Any], current_tick: int) -> List[Transaction]:
        """
        Identifies households in need and provides basic support.
        Returns a list of payment transactions.
        """
        ...

    def provide_household_support(self, household: Any, amount: float, current_tick: int) -> List[Transaction]:
        """
        Provides a direct subsidy to a specific household.
        Returns a list of payment transactions.
        """
        ...

    def get_spending_this_tick(self) -> float:
        """Returns total welfare spending for the current tick."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulator."""
        ...
