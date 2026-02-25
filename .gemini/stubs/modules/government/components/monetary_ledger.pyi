from _typeshed import Incomplete
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.models import Transaction as Transaction

logger: Incomplete

class MonetaryLedger:
    """
    Tracks monetary policy metrics (M2 Delta, Credit Creation/Destruction).
    Decomposed from Government agent.
    """
    total_money_issued: dict[CurrencyCode, int]
    total_money_destroyed: dict[CurrencyCode, int]
    start_tick_money_issued: dict[CurrencyCode, int]
    start_tick_money_destroyed: dict[CurrencyCode, int]
    credit_delta_this_tick: dict[CurrencyCode, int]
    def __init__(self) -> None: ...
    def reset_tick_flow(self) -> None:
        """
        Called at the start of every tick to reset flow counters and snapshot totals.
        """
    def process_transactions(self, transactions: list[Transaction]):
        """
        Processes transactions related to monetary policy (Credit Creation/Destruction).
        """
    def get_monetary_delta(self, currency: CurrencyCode = ...) -> int:
        """
        Returns the net change in the money supply authorized this tick for a specific currency (in pennies).
        """
