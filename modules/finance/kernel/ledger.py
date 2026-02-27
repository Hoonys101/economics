from typing import List, Any, Optional, Dict, TYPE_CHECKING
from uuid import UUID
from simulation.models import Transaction
from modules.finance.kernel.api import IMonetaryLedger
from modules.finance.api import ISettlementSystem, IFinancialAgent, IMonetaryAuthority
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, AgentID
from modules.system.constants import ID_CENTRAL_BANK
import logging

if TYPE_CHECKING:
    from simulation.dtos.api import CommandBatchDTO

logger = logging.getLogger(__name__)

class SettlementFailError(Exception):
    """Raised when a batch settlement operation fails."""
    pass

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

    def execute_batch(self, batch: 'CommandBatchDTO') -> None:
        """
        Executes a batch of financial commands.
        Enforces strict Zero-Sum constraints and type safety.
        """
        if not self.settlement_system:
            raise SettlementFailError("SettlementSystem not injected into MonetaryLedger.")

        # 1. Process Transfers (P2P)
        for transfer_dto in batch.transfers:
            if not isinstance(transfer_dto.amount_pennies, int):
                raise TypeError(f"Float Incursion in transfer amount: {transfer_dto.amount_pennies}")

            source_agent = self._resolve_agent(transfer_dto.source_id)
            target_agent = self._resolve_agent(transfer_dto.target_id)

            if not source_agent or not target_agent:
                logger.error(f"EXECUTE_BATCH_FAIL | Agent lookup failed. Source: {transfer_dto.source_id}, Target: {transfer_dto.target_id}")
                raise SettlementFailError(f"Agent lookup failed for transfer from {transfer_dto.source_id} to {transfer_dto.target_id}")

            tx = self.settlement_system.transfer(
                debit_agent=source_agent,
                credit_agent=target_agent,
                amount=transfer_dto.amount_pennies,
                memo=transfer_dto.reason,
                tick=batch.tick,
                currency=transfer_dto.currency
            )

            if not tx:
                raise SettlementFailError(f"Transfer failed from {transfer_dto.source_id} to {transfer_dto.target_id}")

        # 2. Process Mutations (System Mint/Burn)
        for mutation_dto in batch.mutations:
            if not isinstance(mutation_dto.amount_pennies, int):
                raise TypeError(f"Float Incursion in mutation amount: {mutation_dto.amount_pennies}")

            # Check if Settlement System supports monetary authority operations
            # We check for the method presence or type to be safe
            if not isinstance(self.settlement_system, IMonetaryAuthority):
                 # Fallback: check if method exists (duck typing for mocks/non-strict scenarios)
                 if not hasattr(self.settlement_system, 'mint_and_distribute'):
                     raise SettlementFailError("SettlementSystem does not support Monetary Authority operations (mint/burn).")

            # Cast for type safety in IDEs
            monetary_authority: IMonetaryAuthority = self.settlement_system # type: ignore

            if mutation_dto.amount_pennies > 0:
                # Minting (M2 Expansion)
                success = monetary_authority.mint_and_distribute(
                    target_agent_id=mutation_dto.target_id,
                    amount=mutation_dto.amount_pennies,
                    tick=batch.tick,
                    reason=mutation_dto.reason
                )
                if not success:
                    raise SettlementFailError(f"Minting failed for target {mutation_dto.target_id}")

            elif mutation_dto.amount_pennies < 0:
                # Burning (M2 Contraction)
                target_agent = self._resolve_agent(mutation_dto.target_id)
                central_bank = self._resolve_agent(ID_CENTRAL_BANK) # Sink

                if not target_agent:
                    raise SettlementFailError(f"Burn target agent {mutation_dto.target_id} not found.")
                if not central_bank:
                    raise SettlementFailError(f"Central Bank (Sink) not found for burn operation.")

                burn_amount = abs(mutation_dto.amount_pennies)
                tx = monetary_authority.transfer_and_destroy(
                    source=target_agent,
                    sink_authority=central_bank,
                    amount=burn_amount,
                    reason=mutation_dto.reason,
                    tick=batch.tick,
                    currency=mutation_dto.currency
                )
                if not tx:
                    raise SettlementFailError(f"Burn failed from {mutation_dto.target_id}")

    def _resolve_agent(self, agent_id: AgentID) -> Optional[IFinancialAgent]:
        """
        Helper to resolve an Agent ID to an IFinancialAgent object.
        Tries SettlementSystem's registry first, then fallback to time_provider's agent list.
        """
        # 1. Try SettlementSystem's internal registry (if exposed or accessible)
        # Note: ISettlementSystem inherits IAccountRegistry, but we need IAgentRegistry access.
        # Ideally, SettlementSystem implementation has `agent_registry`.
        if hasattr(self.settlement_system, 'agent_registry') and self.settlement_system.agent_registry:
            agent = self.settlement_system.agent_registry.get_agent(agent_id)
            if agent:
                return agent

        # 2. Fallback to Time Provider (SimulationState) if it has agent storage
        if hasattr(self.time_provider, 'agents'):
            # SimulationState.agents is Dict[AgentID, Any]
            agent = self.time_provider.agents.get(agent_id)
            if agent:
                return agent

        # 3. Fallback: Check if time_provider IS the registry (WorldState)
        if hasattr(self.time_provider, 'get_agent'):
             agent = self.time_provider.get_agent(agent_id)
             if agent:
                 return agent

        return None
