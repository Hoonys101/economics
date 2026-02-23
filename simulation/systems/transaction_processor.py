from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING, List, Optional, Iterable
import logging

from simulation.systems.api import (
    SystemInterface,
    ITransactionHandler,
    TransactionContext,
)
from simulation.dtos.settlement_dtos import SettlementResultDTO
from modules.finance.utils.currency_math import round_to_pennies
from modules.system.constants import ID_PUBLIC_MANAGER

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

    def _handle_public_manager(self, tx: Transaction, context: TransactionContext) -> Optional[SettlementResultDTO]:
        """
        Handles transactions where the seller is the Public Manager.
        Returns a SettlementResultDTO if handled, or None if not applicable.
        """
        # 1. Check if it is a PM transaction
        is_pm_seller = (
            tx.seller_id == ID_PUBLIC_MANAGER
            or tx.seller_id == "PUBLIC_MANAGER"
            or tx.seller_id == -1
        )
        is_systemic = tx.transaction_type in [
            "inheritance_distribution",
            "escheatment",
        ]

        if is_pm_seller and not is_systemic and self._public_manager_handler:
            buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(
                tx.buyer_id
            )
            if buyer:
                try:
                    success = self._public_manager_handler.handle(
                        tx, buyer, None, context
                    )

                    amount = 0.0
                    if success:
                        if getattr(tx, 'total_pennies', 0) > 0:
                            amount = tx.total_pennies
                        else:
                            amount = round_to_pennies(tx.quantity * tx.price * 100)

                    return SettlementResultDTO(
                        original_transaction=tx,
                        success=success,
                        amount_settled=amount,
                    )
                except Exception as e:
                    context.logger.error(f"Public Manager Handler Failed for {tx.item_id}: {e}", exc_info=True)
                    return SettlementResultDTO(
                        original_transaction=tx,
                        success=False,
                        amount_settled=0.0
                    )
        return None

    def execute(
        self,
        state: SimulationState,
        transactions: Optional[Iterable[Transaction]] = None,
    ) -> List[SettlementResultDTO]:
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
            government=state.primary_government,
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
            transaction_queue=[],  # Initialize empty queue for side-effects
            shareholder_registry=state.shareholder_registry,
        )

        default_handler = self._handlers.get("default")

        tx_list = transactions if transactions is not None else state.transactions

        for tx in tx_list:
            # 0. Skip Executed Transactions (TD-160: Atomic Inheritance)
            if (
                hasattr(tx, "metadata")
                and tx.metadata
                and tx.metadata.get("executed", False)
            ):
                continue

            # 1. Special Routing: Public Manager (Seller)
            pm_result = self._handle_public_manager(tx, context)
            if pm_result:
                results.append(pm_result)
                continue

            # 2. Standard Dispatch
            handler = self._handlers.get(tx.transaction_type)

            # Fallback
            if handler is None:
                if tx.transaction_type in ["credit_creation", "credit_destruction"]:
                    continue  # Symbolic, no-op

                if default_handler:
                    handler = default_handler
                else:
                    if tx.transaction_type == "housing":
                        pass
                    else:
                        state.logger.warning(
                            f"No handler for tx type: {tx.transaction_type}"
                        )
                    continue

            # Resolve Agents
            # Note: We resolve them outside try-except because if this fails,
            # something is structurally wrong with the simulation state (missing agent).
            # However, for robustness, we could wrap this too. But usually we want to crash early on corrupted state.
            buyer = context.agents.get(tx.buyer_id)
            is_buyer_inactive = False
            if not buyer:
                buyer = context.inactive_agents.get(tx.buyer_id)
                if buyer: is_buyer_inactive = True

            seller = context.agents.get(tx.seller_id)
            is_seller_inactive = False
            if not seller:
                seller = context.inactive_agents.get(tx.seller_id)
                if seller: is_seller_inactive = True

            # Inactive Agent Guard
            # Skip transaction if an agent is inactive, unless it's a special type (Escheatment/Liquidation)
            allowed_inactive_types = ["escheatment", "liquidation", "asset_buyout", "asset_transfer", "education_spending"]
            if (is_buyer_inactive or is_seller_inactive) and tx.transaction_type not in allowed_inactive_types:
                state.logger.warning(
                    f"Transaction Skipped: Inactive Agent involved. "
                    f"Buyer: {tx.buyer_id} (Inactive={is_buyer_inactive}), "
                    f"Seller: {tx.seller_id} (Inactive={is_seller_inactive}) "
                    f"for Transaction: {tx.transaction_type}"
                )
                results.append(
                    SettlementResultDTO(
                        original_transaction=tx, success=False, amount_settled=0.0
                    )
                )
                continue

            # Agent Existential Guard
            if buyer is None or seller is None:
                state.logger.error(
                    f"Transaction Failed: Missing Agent. Buyer: {tx.buyer_id}, Seller: {tx.seller_id} "
                    f"for Transaction: {tx.transaction_type}"
                )
                results.append(
                    SettlementResultDTO(
                        original_transaction=tx, success=False, amount_settled=0.0
                    )
                )
                continue

            try:
                # Dispatch
                success = handler.handle(tx, buyer, seller, context)

                # Record Result
                amount = 0.0
                if success:
                    # TD-MKT-FLOAT-MATCH: total_pennies is the SSoT for settlement
                    if getattr(tx, 'total_pennies', 0) > 0:
                        amount = tx.total_pennies
                    else:
                        amount = round_to_pennies(tx.quantity * tx.price * 100)

                results.append(
                    SettlementResultDTO(
                        original_transaction=tx, success=success, amount_settled=amount
                    )
                )

                # Post-processing
                if success and tx.metadata and tx.metadata.get("triggers_effect"):
                    state.effects_queue.append(tx.metadata)

            except Exception as e:
                # Catch-all for handler failures to prevent crashing the entire tick
                state.logger.error(f"Transaction Handler Failed for {tx.transaction_type} (ID: {getattr(tx, 'id', 'unknown')}): {e}", exc_info=True)
                results.append(
                    SettlementResultDTO(
                        original_transaction=tx, success=False, amount_settled=0.0
                    )
                )

        # Append queued transactions from context to state (e.g. credit creation from loans)
        if context.transaction_queue:
            state.transactions.extend(context.transaction_queue)

        return results
