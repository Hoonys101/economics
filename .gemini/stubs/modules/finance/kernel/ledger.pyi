from _typeshed import Incomplete
from modules.finance.api import ISettlementSystem as ISettlementSystem
from modules.finance.kernel.api import IMonetaryLedger as IMonetaryLedger
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.models import Transaction
from typing import Any
from uuid import UUID

logger: Incomplete

class MonetaryLedger(IMonetaryLedger):
    """
    Implementation of IMonetaryLedger.
    Records observational transactions for credit expansion and destruction.
    Acts as the Single Source of Truth (SSoT) for M2 Money Supply tracking.
    """
    transaction_log: Incomplete
    time_provider: Incomplete
    settlement_system: Incomplete
    expected_m2_pennies: int
    total_system_debt: dict[CurrencyCode, int]
    def __init__(self, transaction_log: list[Transaction], time_provider: Any, settlement_system: ISettlementSystem | None = None) -> None:
        """
        Args:
            transaction_log: The central simulation transaction log list (modified in-place).
            time_provider: An object with a .time attribute (e.g. SimulationState).
            settlement_system: The settlement system to query for actual M2.
        """
    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = ...) -> None: ...
    def get_total_m2_pennies(self, currency: CurrencyCode = ...) -> int: ...
    def get_expected_m2_pennies(self, currency: CurrencyCode = ...) -> int: ...
    def get_system_debt_pennies(self, currency: CurrencyCode = ...) -> int: ...
    def record_system_debt_increase(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
    def record_system_debt_decrease(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
    def record_monetary_expansion(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
    def record_monetary_contraction(self, amount_pennies: int, source: str, currency: CurrencyCode = ...) -> None: ...
    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...
    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None: ...
