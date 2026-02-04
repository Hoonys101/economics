from typing import Dict, List
import logging
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class MonetaryLedger:
    """
    Tracks monetary policy metrics (M2 Delta, Credit Creation/Destruction).
    Decomposed from Government agent.
    """
    def __init__(self):
        # Money Tracking (Gold Standard & Fractional Reserve)
        self.total_money_issued: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.total_money_destroyed: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

        # Snapshots for Tick Delta
        self.start_tick_money_issued: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}
        self.start_tick_money_destroyed: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

        # WO-024: Fractional Reserve Credit Tracking
        self.credit_delta_this_tick: Dict[CurrencyCode, float] = {DEFAULT_CURRENCY: 0.0}

    def reset_tick_flow(self):
        """
        Called at the start of every tick to reset flow counters and snapshot totals.
        """
        self.credit_delta_this_tick = {}

        # Snapshot for delta calculation
        self.start_tick_money_issued = self.total_money_issued.copy()
        self.start_tick_money_destroyed = self.total_money_destroyed.copy()

    def process_transactions(self, transactions: List[Transaction]):
        """
        Processes transactions related to monetary policy (Credit Creation/Destruction).
        """
        for tx in transactions:
            cur = getattr(tx, 'currency', DEFAULT_CURRENCY)

            if tx.transaction_type == "credit_creation":
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_issued: self.total_money_issued[cur] = 0.0

                self.credit_delta_this_tick[cur] += tx.price
                self.total_money_issued[cur] += tx.price
                logger.debug(f"MONETARY_EXPANSION | Credit created: {tx.price:.2f} {cur}")

            elif tx.transaction_type == "credit_destruction":
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0.0

                self.credit_delta_this_tick[cur] -= tx.price
                self.total_money_destroyed[cur] += tx.price
                logger.debug(f"MONETARY_CONTRACTION | Credit destroyed: {tx.price:.2f} {cur}")

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """
        Returns the net change in the money supply authorized this tick for a specific currency.
        """
        issued_delta = self.total_money_issued.get(currency, 0.0) - self.start_tick_money_issued.get(currency, 0.0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0.0) - self.start_tick_money_destroyed.get(currency, 0.0)
        return issued_delta - destroyed_delta
