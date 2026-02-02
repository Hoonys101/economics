from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING, List, Optional
import logging

from simulation.systems.api import SystemInterface, ITransactionHandler, TransactionContext

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

    def execute(self, state: SimulationState, transactions: Optional[List[Transaction]] = None) -> None:
        """
        Dispatches transactions to registered handlers.

        Args:
            state: The current simulation state DTO.
            transactions: Optional list of transactions to process.
                          If provided, this list is used instead of state.transactions.
                          Useful when processing a combined list of drained and current transactions.
        """
        # 1. Build TransactionContext
        # Note: public_manager and bank/central_bank must be in state or accessible.
        # SimulationState usually has bank, central_bank. public_manager might be in state.

        # Determine Public Manager from state if available
        public_manager = getattr(state, "public_manager", None)

        # Determine Bank and Central Bank from state
        bank = getattr(state, "bank", None)
        central_bank = getattr(state, "central_bank", None)

        # Determine Taxation System (Should be in state or we create/access it?)
        # Legacy TP created it in __init__. But Spec says "taxation_system: 'TaxationSystem'" in context.
        # Ideally state has it. If not, we might need to rely on it being passed or created.
        # SimulationState doesn't explicitly list taxation_system in my read earlier.
        # But TransactionProcessor had self.taxation_system.
        # If I want to pass it to context, I should probably maintain it here or assume state has it.
        # Spec says: "The settlement and taxation systems are now part of the context and will be instantiated at a higher level (e.g., in Simulation)."
        # So I should expect state to have it? Or I can attach my own if state doesn't have it?
        # SimulationState definition in `simulation/dtos/api.py` was not read fully but `world_state.py` didn't explicitly have it as public attribute in `__init__`.
        # However, `TransactionProcessor` used to own `TaxationSystem`.
        # I'll instantiate `TaxationSystem` in `__init__` if needed, or check if I should attach it.
        # Wait, if `TransactionProcessor` is the one creating context, it can pass its own `taxation_system`.
        # The Spec example: "taxation_system=state.taxation_system, # Assumes this is created alongside".
        # If state doesn't have it, I'll use `self.taxation_system`.

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
            transaction_queue=[] # Initialize empty queue for side-effects
        )

        default_handler = self._handlers.get("default")

        tx_list = transactions if transactions is not None else state.transactions

        for tx in tx_list:
            # 1. Special Routing: Public Manager (Seller)
            # Check if seller is PUBLIC_MANAGER (String ID check or object check handled by logic)
            if (tx.seller_id == "PUBLIC_MANAGER" or tx.seller_id == -1) and self._public_manager_handler:
                # Handler expects (tx, buyer, seller, context).
                # PublicManagerHandler needs buyer. We resolve it here.
                buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
                # Seller is None/Placeholder for PM
                if buyer:
                    self._public_manager_handler.handle(tx, buyer, None, context)
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
                     # Warn only if it's not a known ignored type
                     # Housing pass in legacy?
                     if tx.transaction_type == "housing":
                         # Maybe HousingHandler is registered?
                         pass
                     else:
                        state.logger.warning(f"No handler for tx type: {tx.transaction_type}")
                     continue

            # Resolve Agents
            # Note: seller might be None (e.g. for some system txs, though usually -1 or ID used)
            # Handlers should handle None seller if appropriate (e.g. HousingHandler).
            buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
            seller = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)
            
            # Special case for Government/Bank ID resolution if needed
            # But handlers usually check IDs or context.government.
            
            # Dispatch
            success = handler.handle(tx, buyer, seller, context)

            # Post-processing
            if success and tx.metadata and tx.metadata.get("triggers_effect"):
                state.effects_queue.append(tx.metadata)
                
        # Append queued transactions from context to state (e.g. credit creation from loans)
        if context.transaction_queue:
            # We assume state.transactions is the list we can append to?
            # Or state.inter_tick_queue?
            # HousingHandler appended to `state.transactions` (current tick log).
            # So we extend state.transactions.
            # But iterating and appending might be dangerous if loop continues?
            # We are outside the loop now.
            state.transactions.extend(context.transaction_queue)
