from typing import List, Any, Optional, Dict
from uuid import UUID
from simulation.models import Transaction
from modules.finance.kernel.api import IMonetaryLedger
from modules.finance.api import ISettlementSystem
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.system.constants import ID_CENTRAL_BANK, ID_PUBLIC_MANAGER
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
        self._currency_holder_registry: List[ICurrencyHolder] = []

        # Track total issued and destroyed
        self.total_money_issued: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.total_money_destroyed: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        # Snapshots for Tick Delta
        self.start_tick_money_issued: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}
        self.start_tick_money_destroyed: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

        self.credit_delta_this_tick: Dict[CurrencyCode, int] = {DEFAULT_CURRENCY: 0}

    @property
    def _current_tick(self) -> int:
        return self.time_provider.time if hasattr(self.time_provider, 'time') else 0

    def set_expected_m2(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies = amount_pennies
        logger.info(f"MONETARY_LEDGER | Baseline M2 set to: {amount_pennies}")

    def register_holder(self, agent: ICurrencyHolder) -> None:
        """Registers a currency holder."""
        if agent not in self._currency_holder_registry:
            self._currency_holder_registry.append(agent)

    def get_all(self) -> List[ICurrencyHolder]:
        """Returns all registered currency holders."""
        return self._currency_holder_registry

    def calculate_total_money(self) -> MoneySupplyDTO:
        """Calculates total M2 and System Debt based on registered holders."""
        total_m2 = 0
        total_debt = 0

        for agent in self._currency_holder_registry:
            balance = agent.get_balance(DEFAULT_CURRENCY)
            if balance > 0:
                total_m2 += balance
            else:
                total_debt += abs(balance)

        return MoneySupplyDTO(
            total_m2_pennies=total_m2,
            system_debt_pennies=total_debt,
            currency=DEFAULT_CURRENCY
        )

    def get_total_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        if self.settlement_system:
            return self.settlement_system.get_total_m2_pennies(currency)
        return 0

    def get_expected_m2_pennies(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        # In a unified system, we rely purely on expected_m2_pennies which is mutated directly
        return max(0, self.expected_m2_pennies)

    def record_monetary_expansion(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies += amount_pennies

        # Ensure we also record it for observational deltas if it wasn't picked up
        if currency not in self.total_money_issued:
            self.total_money_issued[currency] = 0
        self.total_money_issued[currency] += amount_pennies

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
        logger.info(f"MONETARY_LEDGER | M2 Expansion: +{amount_pennies} ({source}) | New Expected M2: {self.get_expected_m2_pennies(currency)}")

    def record_monetary_contraction(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies -= amount_pennies

        # Ensure we also record it for observational deltas
        if currency not in self.total_money_destroyed:
            self.total_money_destroyed[currency] = 0
        self.total_money_destroyed[currency] += amount_pennies

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
        logger.info(f"MONETARY_LEDGER | M2 Contraction: -{amount_pennies} ({source}) | New Expected M2: {self.get_expected_m2_pennies(currency)}")

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

                self.credit_delta_this_tick[cur] += amount
                logger.debug(f"MONETARY_EXPANSION | {tx.transaction_type} (from {tx.buyer_id}): {amount}")
                # Use standard method to keep `expected_m2_pennies` and `total_money_issued` in sync
                # But prevent recursive infinite loop by not recording another tx
                self.expected_m2_pennies += amount
                if cur not in self.total_money_issued:
                    self.total_money_issued[cur] = 0
                self.total_money_issued[cur] += amount

            elif is_contraction:
                contraction_amount = amount

                if tx.transaction_type == "bond_repayment":
                    metadata = getattr(tx, 'metadata', None) or {}
                    principal_raw = metadata.get('principal', 0)

                    try:
                        principal = int(principal_raw)
                    except (TypeError, ValueError):
                        principal = 0

                    if principal > 0:
                        contraction_amount = principal

                if cur not in self.credit_delta_this_tick: self.credit_delta_this_tick[cur] = 0

                self.credit_delta_this_tick[cur] -= contraction_amount
                logger.debug(f"MONETARY_CONTRACTION | {tx.transaction_type} (to {tx.seller_id}): {contraction_amount}")

                self.expected_m2_pennies -= contraction_amount
                if cur not in self.total_money_destroyed:
                    self.total_money_destroyed[cur] = 0
                self.total_money_destroyed[cur] += contraction_amount

    def get_monetary_delta(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Returns the net change in the money supply authorized this tick for a specific currency (in pennies).
        """
        issued_delta = self.total_money_issued.get(currency, 0) - self.start_tick_money_issued.get(currency, 0)
        destroyed_delta = self.total_money_destroyed.get(currency, 0) - self.start_tick_money_destroyed.get(currency, 0)
        return issued_delta - destroyed_delta

    def record_monetary_expansion(self, amount_pennies: int, source: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.expected_m2_pennies += amount_pennies

        if currency not in self.total_money_issued:
            self.total_money_issued[currency] = 0
        self.total_money_issued[currency] += amount_pennies

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

        if currency not in self.total_money_destroyed:
            self.total_money_destroyed[currency] = 0
        self.total_money_destroyed[currency] += amount_pennies

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
