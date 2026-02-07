from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING, List, Optional
import logging

from simulation.systems.api import SystemInterface, ITransactionHandler, TransactionContext
from simulation.dtos.settlement_dtos import SettlementResultDTO

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.models import Transaction

logger = logging.getLogger(__name__)

class TransactionProcessor(SystemInterface):
    """
    Dispatcher-based Transaction Processor.
    Delegates transaction processing to registered handlers based on transaction type.
    Refactored from monolithic implementation (TD-191).
    """

    def __init__(self, config_module: Any):
        self.config_module = config_module
        self._handlers: Dict[str, ITransactionHandler] = {}
        # Special handlers that might be triggered by condition rather than type
        self._public_manager_handler: ITransactionHandler = None

    def register_handler(self, transaction_type: str, handler: ITransactionHandler):
        """Registers a handler for a specific transaction type."""
        self._handlers[transaction_type] = handler

    def register_public_manager_handler(self, handler: ITransactionHandler):
        """Registers a handler for Public Manager transactions (seller check)."""
        self._public_manager_handler = handler

    def execute(self, state: SimulationState, transactions: Optional[List[Transaction]] = None) -> List[SettlementResultDTO]:
        """
        Dispatches transactions to registered handlers.

        Args:
            state: The current simulation state DTO.
            transactions: Optional list of transactions to process.
                          If provided, this list is used instead of state.transactions.
                          Useful when processing a combined list of drained and current transactions.

        Returns:
            List[SettlementResultDTO]: Results of executed transactions.
        """
        results: List[SettlementResultDTO] = []

        # 1. Build TransactionContext
        # Determine Public Manager from state if available
        public_manager = getattr(state, "public_manager", None)

        # Determine Bank and Central Bank from state
        bank = getattr(state, "bank", None)
        central_bank = getattr(state, "central_bank", None)

        # Determine Taxation System (Should be in state or we create/access it?)
        taxation_system = getattr(state, "taxation_system", None)
        if not taxation_system:
            if not hasattr(self, "taxation_system"):
                # Lazy init if missing? Or rely on config.
                from modules.government.taxation.system import TaxationSystem
                self.taxation_system = TaxationSystem(self.config_module)
            taxation_system = self.taxation_system

        context = TransactionContext(
            agents=state.agents,
            inactive_agents=getattr(state, "inactive_agents", {}),
            government=state.government,
            settlement_system=state.settlement_system,
            taxation_system=taxation_system,
            stock_market=state.stock_market,
            real_estate_units=state.real_estate_units,
            market_data=state.market_data,
            config_module=self.config_module,
            logger=state.logger,
            time=state.time,
            bank=bank,
            central_bank=central_bank,
            public_manager=public_manager,
            transaction_queue=[], # Initialize empty queue for side-effects
            shareholder_registry=state.shareholder_registry
        )

        default_handler = self._handlers.get("default")

        tx_list = transactions if transactions is not None else state.transactions

        for tx in tx_list:
            # 0. Skip Executed Transactions (TD-160: Atomic Inheritance)
            if hasattr(tx, "metadata") and tx.metadata and tx.metadata.get("executed", False):
                continue

            # 1. Special Routing: Public Manager (Seller)
            if (tx.seller_id == "PUBLIC_MANAGER" or tx.seller_id == -1) and self._public_manager_handler:
                buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
                if buyer:
                    success = self._public_manager_handler.handle(tx, buyer, None, context)
                    amount = tx.quantity * tx.price if success else 0.0
                    results.append(SettlementResultDTO(original_transaction=tx, success=success, amount_settled=amount))
                continue

            # 2. Standard Dispatch
            handler = self._handlers.get(tx.transaction_type)

            # Fallback
            if handler is None:
                 if tx.transaction_type in ["credit_creation", "credit_destruction"]:
                     continue # Symbolic, no-op

                 if default_handler:
                     handler = default_handler
                 else:
                     if tx.transaction_type == "housing":
                         pass
                     else:
                        state.logger.warning(f"No handler for tx type: {tx.transaction_type}")
                     continue

            # Resolve Agents
            buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
            seller = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)
            
            # Dispatch
            success = handler.handle(tx, buyer, seller, context)

            # Record Result
            amount = tx.quantity * tx.price if success else 0.0
            results.append(SettlementResultDTO(original_transaction=tx, success=success, amount_settled=amount))

            # Post-processing
            if success and tx.metadata and tx.metadata.get("triggers_effect"):
                state.effects_queue.append(tx.metadata)
                
        # Append queued transactions from context to state (e.g. credit creation from loans)
        if context.transaction_queue:
            state.transactions.extend(context.transaction_queue)

        return results
