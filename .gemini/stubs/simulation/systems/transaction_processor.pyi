from _typeshed import Incomplete
from simulation.dtos.api import SimulationState as SimulationState
from simulation.dtos.settlement_dtos import SettlementResultDTO as SettlementResultDTO
from simulation.models import Transaction as Transaction
from simulation.systems.api import ITransactionHandler as ITransactionHandler, SystemInterface as SystemInterface, TransactionContext as TransactionContext
from typing import Any, Iterable

logger: Incomplete

class TransactionProcessor(SystemInterface):
    """
    Dispatcher-based Transaction Processor.
    Delegates transaction processing to registered handlers based on transaction type.
    Refactored from monolithic implementation (TD-191).
    """
    config_module: Incomplete
    def __init__(self, config_module: Any) -> None: ...
    def register_handler(self, transaction_type: str, handler: ITransactionHandler):
        """Registers a handler for a specific transaction type."""
    def register_public_manager_handler(self, handler: ITransactionHandler):
        """Registers a handler for Public Manager transactions (seller check)."""
    def execute(self, state: SimulationState, transactions: Iterable[Transaction] | None = None) -> list[SettlementResultDTO]:
        """
        Dispatches transactions to registered handlers.

        Args:
            state: The current simulation state DTO.
            transactions: Optional iterable of transactions to process.
                          Note: This parameter supports single-pass iterators (e.g., itertools.chain).
                          Avoid multiple passes or sequence-specific operations (len, indexing).
                          If provided, this is used instead of state.transactions.

        Returns:
            List[SettlementResultDTO]: Results of executed transactions.
        """
    def rollback_transaction(self, tx: Transaction, state: SimulationState) -> bool:
        """
        Rolls back a transaction using the registered handler.
        """
