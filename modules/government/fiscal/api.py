# modules/government/fiscal/api.py
from typing import Protocol, List, Tuple, Optional, Any
from simulation.models import Transaction
from modules.finance.api import BailoutLoanDTO

class IFiscalService(Protocol):
    """
    Interface for fiscal policy actions like bailouts and infrastructure investment.
    """

    def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> Tuple[Optional[BailoutLoanDTO], List[Transaction]]:
        """
        Evaluates and provides a bailout loan to a firm.
        Returns the loan details and settlement transactions.
        """
        ...

    def invest_infrastructure(self, current_tick: int, households: List[Any]) -> List[Transaction]:
        """
        Executes infrastructure investment, potentially boosting productivity.
        Returns a list of payment transactions.
        """
        ...

    def get_stimulus_spending_this_tick(self) -> float:
        """Returns total stimulus spending for the current tick."""
        ...

    def get_infrastructure_level(self) -> int:
        """Returns the current national infrastructure level."""
        ...

    def reset_tick_flow(self) -> None:
        """Resets the per-tick spending accumulators."""
        ...
