from typing import List, Any, Optional, Dict
from uuid import UUID
from simulation.models import Transaction
from modules.finance.kernel.api import IMonetaryLedger
from modules.finance.api import ISettlementSystem
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
import logging

logger = logging.getLogger(__name__)

class MonetaryLedger(IMonetaryLedger):
    """
    Implementation of IMonetaryLedger.
    Records observational transactions for credit expansion and destruction.
    Acts as the Single Source of Truth (SSoT) for M2 Money Supply tracking.
    """

    def __init__(self, transaction_log: List[Transaction], time_provider: Any, settlement_system: Optional[ISettlementSystem] = None):
        """
        Args:
            transaction_log: The central simulation transaction log list (modified in-place).
            time_provider: An object with a .time attribute (e.g. SimulationState).
            settlement_system: The settlement system to query for actual M2.
        """
        self.transaction_log = transaction_log
        self.time_provider = time_provider
        self.settlement_system = settlement_system
        self.expected_m2_pennies = 0
        self.total_system_debt: Dict[CurrencyCode, int] = {}

    @property
    def _current_tick(self) -> int:
        return self.time_provider.time if hasattr(self.time_provider, 'time') else 0

    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies = amount_pennies
        logger.info(f"MONETARY_LEDGER | Baseline M2 set to: {amount_pennies}")

    def get_total_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        if self.settlement_system:
            return self.settlement_system.get_total_m2_pennies(currency)
        return 0

    def get_expected_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.expected_m2_pennies

    def get_system_debt_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self.total_system_debt.get(currency, 0)

    def record_system_debt_increase(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if currency not in self.total_system_debt:
            self.total_system_debt[currency] = 0
        self.total_system_debt[currency] += amount_pennies
        logger.debug(f"SYSTEM_DEBT_INCREASE | +{amount_pennies} ({source}) | Total Debt: {self.total_system_debt[currency]}")

    def record_system_debt_decrease(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if currency not in self.total_system_debt:
            self.total_system_debt[currency] = 0
        self.total_system_debt[currency] -= amount_pennies
        # Floor at 0 to prevent negative debt anomalies
        if self.total_system_debt[currency] < 0:
            logger.warning(f"SYSTEM_DEBT_UNDERFLOW | Attempted to decrease debt below zero via {source}. Resetting to 0.")
            self.total_system_debt[currency] = 0
        logger.debug(f"SYSTEM_DEBT_DECREASE | -{amount_pennies} ({source}) | Total Debt: {self.total_system_debt[currency]}")

    def record_monetary_expansion(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies += amount_pennies

        tx = Transaction(
            buyer_id=-1,
            seller_id=-1,
            item_id=f"monetary_expansion_{self._current_tick}",
            quantity=1.0,
            price=amount_pennies / 100.0,
            market_id="monetary_policy",
            transaction_type="monetary_expansion",
            time=self._current_tick,
            metadata={
                "source": source,
                "currency": currency,
                "is_monetary_expansion": True,
                "executed": True,
                "is_audit": True
            },
            total_pennies=amount_pennies
        )
        self.transaction_log.append(tx)
        logger.info(f"MONETARY_LEDGER | M2 Expansion: +{amount_pennies} ({source}) | New Expected M2: {self.expected_m2_pennies}")

    def record_monetary_contraction(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies -= amount_pennies

        tx = Transaction(
            buyer_id=-1,
            seller_id=-1,
            item_id=f"monetary_contraction_{self._current_tick}",
            quantity=1.0,
            price=amount_pennies / 100.0,
            market_id="monetary_policy",
            transaction_type="monetary_contraction",
            time=self._current_tick,
            metadata={
                "source": source,
                "currency": currency,
                "is_monetary_destruction": True,
                "executed": True,
                "is_audit": True
            },
            total_pennies=amount_pennies
        )
        self.transaction_log.append(tx)
        logger.info(f"MONETARY_LEDGER | M2 Contraction: -{amount_pennies} ({source}) | New Expected M2: {self.expected_m2_pennies}")

    # Legacy wrappers
    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        # Convert float amount to pennies
        amount_pennies = int(amount * 100)
        source = f"saga_{saga_id}_loan_{loan_id}_{reason}"
        self.record_monetary_expansion(amount_pennies, source)

    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        # Convert float amount to pennies
        amount_pennies = int(amount * 100)
        source = f"saga_{saga_id}_loan_{loan_id}_{reason}"
        self.record_monetary_contraction(amount_pennies, source)
