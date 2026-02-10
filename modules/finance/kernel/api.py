from typing import Protocol, Dict, Any, List, Tuple, Optional
from uuid import UUID

from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO, IHousingTransactionSagaHandler
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY
from simulation.finance.api import IFinancialEntity, ITransaction

# --- 1. Saga Orchestration ---

class ISagaOrchestrator(Protocol):
    """
    Manages the lifecycle of long-running, multi-step business transactions (Sagas).
    This service is the single source of truth for saga state.
    """

    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """Submits a new saga to be processed."""
        ...

    def process_sagas(self) -> None:
        """
        Iterates through all active sagas and executes their next step.
        This is the main entry point called by the simulation's tick orchestrator.
        """
        ...

    def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None:
        """
        Finds all sagas involving a specific agent and triggers their compensation/rollback.
        Used for cleanup when an agent is removed from the simulation (e.g., death).
        """
        ...

    def get_active_sagas(self) -> Dict[UUID, HousingTransactionSagaStateDTO]:
        """Returns a view of the currently active sagas."""
        ...


# --- 2. Monetary Policy Ledger ---

class IMonetaryLedger(Protocol):
    """
    An observational service that records events impacting the money supply (M2)
    which are not direct mint/burn actions by the Central Bank.
    e.g., fractional reserve banking via mortgage disbursal.
    """

    def record_credit_expansion(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that new credit has been extended, increasing the money supply.
        This creates an observational Transaction record, it does not move funds.
        """
        ...

    def record_credit_destruction(self, amount: float, saga_id: UUID, loan_id: Any, reason: str) -> None:
        """
        Records that credit has been paid back or rolled back, decreasing the money supply.
        This creates an observational Transaction record.
        """
        ...


# --- 3. Refactored Settlement System ---

class ISettlementSystem(Protocol):
    """
    The transactional kernel for all financial operations. It is stateless regarding
    high-level business processes like Sagas. Its sole focus is on the atomic
    execution of fund transfers.
    """

    # --- Core Transfer APIs (Unchanged) ---
    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY,
    ) -> Optional[ITransaction]: ...

    def settle_atomic(
        self,
        debit_agent: IFinancialEntity,
        credits_list: List[Tuple[IFinancialEntity, float, str]],
        tick: int,
    ) -> bool: ...

    def execute_multiparty_settlement(
        self,
        transfers: List[Tuple[IFinancialEntity, IFinancialEntity, float]],
        tick: int,
    ) -> bool: ...

    # --- Mint/Burn APIs (Unchanged) ---
    def create_and_transfer(
        self,
        source_authority: IFinancialEntity,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY,
    ) -> Optional[ITransaction]: ...

    def transfer_and_destroy(
        self,
        source: IFinancialEntity,
        sink_authority: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY,
    ) -> Optional[ITransaction]: ...

    # --- Other Settlement Logic (Unchanged) ---
    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialEntity] = None
    ) -> None: ...

    def create_settlement(self, agent: Any, tick: int) -> Any: ...

    def execute_settlement(
        self,
        account_id: int,
        distribution_plan: List[Tuple[Any, float, str, str]], # (Recipient, Amount, Memo, TxType)
        tick: int
    ) -> List[ITransaction]: ...

    def verify_and_close(self, account_id: int, tick: int) -> bool: ...
