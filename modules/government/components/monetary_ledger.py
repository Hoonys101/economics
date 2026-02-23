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
        from modules.system.constants import ID_CENTRAL_BANK, ID_PUBLIC_MANAGER

        for tx in transactions:
            cur = getattr(tx, 'currency', DEFAULT_CURRENCY)
            is_expansion = False
            is_contraction = False

            # Strict Monetary SSoT (Wave 5 Hardening)
            # Any transaction originating from a System Agent (CB/PM) into the public is Expansion.
            # Any transaction returning to a System Agent from the public is Contraction.
            
            # IDs can be int or string
            buyer_id = str(tx.buyer_id)
            seller_id = str(tx.seller_id)
            cb_id = str(ID_CENTRAL_BANK)
            pm_id = str(ID_PUBLIC_MANAGER)

            # Expansion: System -> Public (Money Injection)
            if buyer_id in [cb_id, pm_id] and seller_id not in [cb_id, pm_id]:
                is_expansion = True
            
            # Contraction: Public -> System (Money Drain)
            elif seller_id in [cb_id, pm_id] and buyer_id not in [cb_id, pm_id]:
                is_contraction = True
            
            # Explicit types as fallback for non-agent minting (e.g. credit creation by banks if not seller=PM)
            if not is_expansion and not is_contraction:
                if tx.transaction_type in ["credit_creation", "money_creation", "lender_of_last_resort"]:
                    is_expansion = True
                elif tx.transaction_type in ["credit_destruction", "money_destruction"]:
                    is_contraction = True

            if is_expansion:
                amount = tx.price * tx.quantity
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_issued: self.total_money_issued[cur] = 0.0

                self.credit_delta_this_tick[cur] += amount
                self.total_money_issued[cur] += amount
                logger.debug(f"MONETARY_EXPANSION | {tx.transaction_type} (from {tx.buyer_id}): {amount:.2f}")

            elif is_contraction:
                amount = tx.price * tx.quantity

                # WO-WAVE5-MONETARY-FIX: Support for Split Repayment (Principal vs Interest)
                if tx.transaction_type == "bond_repayment" and tx.metadata:
                    repayment_details = tx.metadata.get("repayment_details")
                    if repayment_details and "principal" in repayment_details:
                        amount = float(repayment_details["principal"])

                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0.0

                self.credit_delta_this_tick[cur] -= amount
                self.total_money_destroyed[cur] += amount
                logger.debug(f"MONETARY_CONTRACTION | {tx.transaction_type} (to {tx.seller_id}): {amount:.2f}")

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """
        Returns the net change in the money supply authorized this tick for a specific currency.
        """
        issued_delta = self.total_money_issued.get(currency, 0.0) - self.start_tick_money_issued.get(currency, 0.0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0.0) - self.start_tick_money_destroyed.get(currency, 0.0)
        return issued_delta - destroyed_delta
