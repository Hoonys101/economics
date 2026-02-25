from modules.finance.api import IFinancialAgent as IFinancialAgent, IMonetaryLedger as IMonetaryLedger
from modules.finance.sagas.housing_api import HousingTransactionSagaStateDTO as HousingTransactionSagaStateDTO, IHousingTransactionSagaHandler as IHousingTransactionSagaHandler
from modules.system.api import CurrencyCode as CurrencyCode, DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.finance.api import ITransaction as ITransaction
from typing import Any, Protocol
from uuid import UUID

class ISagaOrchestrator(Protocol):
    """
    Manages the lifecycle of long-running, multi-step business transactions (Sagas).
    This service is the single source of truth for saga state.
    """
    def submit_saga(self, saga: HousingTransactionSagaStateDTO) -> bool:
        """Submits a new saga to be processed."""
    def process_sagas(self) -> None:
        """
        Iterates through all active sagas and executes their next step.
        This is the main entry point called by the simulation's tick orchestrator.
        """
    def find_and_compensate_by_agent(self, agent_id: int, handler: IHousingTransactionSagaHandler) -> None:
        """
        Finds all sagas involving a specific agent and triggers their compensation/rollback.
        Used for cleanup when an agent is removed from the simulation (e.g., death).
        """
    def get_active_sagas(self) -> dict[UUID, HousingTransactionSagaStateDTO]:
        """Returns a view of the currently active sagas."""

class ISettlementSystem(Protocol):
    """
    The transactional kernel for all financial operations. It is stateless regarding
    high-level business processes like Sagas. Its sole focus is on the atomic
    execution of fund transfers.
    """
    def transfer(self, debit_agent: IFinancialAgent, credit_agent: IFinancialAgent, amount: int, memo: str, debit_context: dict[str, Any] | None = None, credit_context: dict[str, Any] | None = None, tick: int = 0, currency: CurrencyCode = ...) -> ITransaction | None: ...
    def settle_atomic(self, debit_agent: IFinancialAgent, credits_list: list[tuple[IFinancialAgent, int, str]], tick: int) -> bool: ...
    def execute_multiparty_settlement(self, transfers: list[tuple[IFinancialAgent, IFinancialAgent, int]], tick: int) -> bool: ...
    def create_and_transfer(self, source_authority: IFinancialAgent, destination: IFinancialAgent, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> ITransaction | None: ...
    def transfer_and_destroy(self, source: IFinancialAgent, sink_authority: IFinancialAgent, amount: int, reason: str, tick: int, currency: CurrencyCode = ...) -> ITransaction | None: ...
    def record_liquidation(self, agent: IFinancialAgent, inventory_value: int, capital_value: int, recovered_cash: int, reason: str, tick: int, government_agent: IFinancialAgent | None = None) -> None: ...
    def create_settlement(self, agent: Any, tick: int) -> Any: ...
    def execute_settlement(self, account_id: int, distribution_plan: list[tuple[Any, int, str, str]], tick: int) -> list[ITransaction]: ...
    def verify_and_close(self, account_id: int, tick: int) -> bool: ...
