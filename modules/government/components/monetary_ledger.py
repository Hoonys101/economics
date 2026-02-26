from typing import Dict, List, Any
import logging
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.models import Transaction
from modules.system.constants import ID_CENTRAL_BANK, ID_PUBLIC_MANAGER

logger = logging.getLogger(__name__)

class MonetaryLedger:
    """
    Tracks monetary policy metrics (M2 Delta, Credit Creation/Destruction).
    Decomposed from Government agent.
    """
    def __init__(self):
        # Money Tracking (Gold Standard & Fractional Reserve)
        self.total_money_issued: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.total_money_destroyed: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        # WO-LIQUIDATE-FINANCE: Base M2 for non-negative tracking
        self.base_m2: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        # Snapshots for Tick Delta
        self.start_tick_money_issued: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.start_tick_money_destroyed: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        # WO-024: Fractional Reserve Credit Tracking
        self.credit_delta_this_tick: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        # WO-IMPL-SYSTEM-DEBT: System Debt Tracking
        self.total_system_debt: Dict[CurrencyCode, int] = {}

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
            is_expansion = False
            is_contraction = False

            # Strict Monetary SSoT (Wave 5 Hardening)
            # Any transaction originating from a System Agent (CB/PM) into the public is Expansion.
            # Any transaction returning to a System Agent from the public is Contraction.
            
            # IDs can be int or string. Normalize to int for comparison.
            def normalize_id(agent_id: Any) -> int:
                try:
                    return int(agent_id)
                except (ValueError, TypeError):
                    return -1 # Invalid ID, won't match system IDs (which are >= 0)

            buyer_id = normalize_id(tx.buyer_id)
            seller_id = normalize_id(tx.seller_id)

            # Expansion: System -> Public (Money Injection)
            if buyer_id in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER] and seller_id not in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER]:
                is_expansion = True
            
            # Contraction: Public -> System (Money Drain)
            elif seller_id in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER] and buyer_id not in [ID_CENTRAL_BANK, ID_PUBLIC_MANAGER]:
                is_contraction = True
            
            # Explicit types as fallback for non-agent minting (e.g. credit creation by banks if not seller=PM)
            if not is_expansion and not is_contraction:
                if tx.transaction_type in ["credit_creation", "money_creation", "lender_of_last_resort"]:
                    is_expansion = True
                elif tx.transaction_type in ["credit_destruction", "money_destruction"]:
                    is_contraction = True

            amount = int(tx.total_pennies)

            if is_expansion:
                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0
                if cur not in self.total_money_issued: self.total_money_issued[cur] = 0

                self.credit_delta_this_tick[cur] += amount
                self.total_money_issued[cur] += amount
                logger.debug(f"MONETARY_EXPANSION | {tx.transaction_type} (from {tx.buyer_id}): {amount}")

            elif is_contraction:
                contraction_amount = amount

                if tx.transaction_type == "bond_repayment":
                    # metadata가 None일 수 있음을 방어하고, 안전하게 principal 추출
                    metadata = getattr(tx, 'metadata', None) or {}
                    principal_raw = metadata.get('principal', 0)

                    try:
                        principal = int(principal_raw)
                    except (TypeError, ValueError):
                        principal = 0 # 예기치 않은 타입의 경우 0 처리

                    # principal이 존재하는 경우 principal만큼만 contraction으로 처리
                    if principal > 0:
                        contraction_amount = principal

                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0
                if cur not in self.total_money_destroyed: self.total_money_destroyed[cur] = 0

                self.credit_delta_this_tick[cur] -= contraction_amount
                self.total_money_destroyed[cur] += contraction_amount
                logger.debug(f"MONETARY_CONTRACTION | {tx.transaction_type} (to {tx.seller_id}): {contraction_amount}")

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Returns the net change in the money supply authorized this tick for a specific currency (in pennies).
        """
        issued_delta = self.total_money_issued.get(currency, 0) - self.start_tick_money_issued.get(currency, 0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0) - self.start_tick_money_destroyed.get(currency, 0)
        return issued_delta - destroyed_delta

    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Sets the baseline M2 (e.g. at genesis)."""
        if currency not in self.base_m2:
            self.base_m2[currency] = 0
        self.base_m2[currency] = amount_pennies

    def get_expected_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the authorized baseline money supply including all expansions."""
        base = self.base_m2.get(currency, 0)
        issued = self.total_money_issued.get(currency, 0)
        destroyed = self.total_money_destroyed.get(currency, 0)
        # Use max(0, ...) to strictly prevent negative anomalies
        return max(0, base + issued - destroyed)

    def get_total_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Calculates total M2 = Circulating Cash + Total Deposits."""
        return self.get_expected_m2_pennies(currency)
