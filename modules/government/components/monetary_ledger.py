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
        from modules.system.constants import ID_CENTRAL_BANK

        for tx in transactions:
            cur = getattr(tx, 'currency', DEFAULT_CURRENCY)
            is_expansion = False
            is_contraction = False

            # 1. Explicit Expansion
            # TD-034: Removed internal transfers (interest, profit) from expansion.
            # TD-030 Revert: Since M2 definition now excludes Bank Reserves, transfers from Bank to Public (Interest/Profit)
            # must be tracked as M2 Expansion.
            if tx.transaction_type in ["credit_creation", "money_creation", "deposit_interest", "bank_profit_remittance"]:
                is_expansion = True

            # 2. CB Buying (OMO Purchase / Bond Purchase) -> Expansion
            elif tx.transaction_type in ["bond_purchase", "omo_purchase"]:
                if str(tx.buyer_id) == str(ID_CENTRAL_BANK):
                    is_expansion = True
                # WO-220: Commercial Bank buying bonds is expansion (Reserves -> M2)
                elif tx.metadata and tx.metadata.get("is_monetary_expansion"):
                    is_expansion = True

            # 3. Explicit Contraction
            # TD-034: Removed internal transfers from contraction.
            # TD-030 Revert: Transfers from Public to Bank (Loan Interest, Repayment) are M2 Contraction.
            if tx.transaction_type in ["credit_destruction", "money_destruction", "loan_interest", "loan_default_recovery", "loan"]:
                is_contraction = True

            # 4. CB Selling (OMO Sale / Bond Repayment) -> Contraction
            elif tx.transaction_type in ["bond_repayment", "omo_sale"]:
                # Bond Repayment: Seller is Bond Holder (CB). Buyer is Gov. Money goes to CB (Destruction).
                # OMO Sale: Seller is CB. Buyer is Market. Money goes to CB (Destruction).
                if str(tx.seller_id) == str(ID_CENTRAL_BANK):
                    is_contraction = True

            if is_expansion:
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_issued: self.total_money_issued[cur] = 0.0

                self.credit_delta_this_tick[cur] += tx.price
                self.total_money_issued[cur] += tx.price
                logger.debug(f"MONETARY_EXPANSION | {tx.transaction_type}: {tx.price:.2f} {cur}")

            elif is_contraction:
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0.0
                if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0.0

                self.credit_delta_this_tick[cur] -= tx.price
                self.total_money_destroyed[cur] += tx.price
                logger.debug(f"MONETARY_CONTRACTION | {tx.transaction_type}: {tx.price:.2f} {cur}")

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """
        Returns the net change in the money supply authorized this tick for a specific currency.
        """
        issued_delta = self.total_money_issued.get(currency, 0.0) - self.start_tick_money_issued.get(currency, 0.0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0.0) - self.start_tick_money_destroyed.get(currency, 0.0)
        return issued_delta - destroyed_delta
