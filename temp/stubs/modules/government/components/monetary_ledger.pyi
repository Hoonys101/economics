from _typeshed import Incomplete
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from modules.system.constants import ID_CENTRAL_BANK as ID_CENTRAL_BANK, ID_PUBLIC_MANAGER as ID_PUBLIC_MANAGER
from simulation.models import Transaction as Transaction

logger: Incomplete

class MonetaryLedger:
    """
    Tracks monetary policy metrics (M2 Delta, Credit Creation/Destruction).
    Decomposed from Government agent.
    """
    total_money_issued: dict[CurrencyCode, int]
    total_money_destroyed: dict[CurrencyCode, int]
    base_m2: dict[CurrencyCode, int]
    start_tick_money_issued: dict[CurrencyCode, int]
    start_tick_money_destroyed: dict[CurrencyCode, int]
    credit_delta_this_tick: dict[CurrencyCode, int]
    total_system_debt: dict[CurrencyCode, int]
    def __init__(self) -> None: ...
    def get_system_debt_pennies(self, currency: CurrencyCode = ...) -> int: ...
    def record_system_debt_increase(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
    def record_system_debt_decrease(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
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
    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Sets the baseline M2 (e.g. at genesis)."""
    def get_expected_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """Returns the authorized baseline money supply including all expansions."""
    def get_total_m2_pennies(self, currency: CurrencyCode = ...) -> int:
        """Calculates total M2 = Circulating Cash + Total Deposits."""
