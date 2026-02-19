from typing import List, Any
from uuid import UUID
from simulation.models import Transaction
from modules.finance.kernel.api import IMonetaryLedger
import logging

logger = logging.getLogger(__name__)

class MonetaryLedger(IMonetaryLedger):
    """
    Implementation of IMonetaryLedger.
    Records observational transactions for credit expansion and destruction.
    """

    def __init__(self, transaction_log: List[Transaction], time_provider: Any):
        """
        Args:
            transaction_log: The central simulation transaction log list (modified in-place).
            time_provider: An object with a .time attribute (e.g. SimulationState).
        """
        self.transaction_log = transaction_log
        self.time_provider = time_provider

    @property
    def _current_tick(self) -> int:
        return self.time_provider.time if hasattr(self.time_provider, 'time') else 0

    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that new credit has been extended (M2 Expansion).
        Convention: buyer_id=-1 (System/Mint), seller_id=-1 (Recipient/Market).
        Note: Original saga handler used buyer_id=Bank.id. If strict analysis requires Bank ID,
        we might need to update this, but for M2 Delta tracking, usually the type/market matters.
        """
        tx = Transaction(
            buyer_id=-1,
            seller_id=-1,
            item_id=f"credit_expansion_{saga_id}",
            quantity=1.0,
            price=amount,
            market_id="monetary_policy",
            transaction_type="credit_creation",
            time=self._current_tick,
            metadata={
                "saga_id": str(saga_id),
                "loan_id": str(loan_id),
                "reason": reason,
                "executed": True,
                "is_monetary_expansion": True # Explicit tag
            }
        , total_pennies=int(amount * 1.0 * 100))
        self.transaction_log.append(tx)
        logger.debug(f"MONETARY_LEDGER | Credit Expansion: {amount:.2f} (Saga: {saga_id})")

    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that credit has been destroyed (M2 Contraction).
        """
        tx = Transaction(
            buyer_id=-1,
            seller_id=-1,
            item_id=f"credit_destruction_{saga_id}",
            quantity=1.0,
            price=amount,
            market_id="monetary_policy",
            transaction_type="credit_destruction",
            time=self._current_tick,
            metadata={
                "saga_id": str(saga_id),
                "loan_id": str(loan_id),
                "reason": reason,
                "executed": True,
                "is_monetary_destruction": True # Explicit tag
            }
        , total_pennies=int(amount * 1.0 * 100))
        self.transaction_log.append(tx)
        logger.debug(f"MONETARY_LEDGER | Credit Destruction: {amount:.2f} (Saga: {saga_id})")
