from typing import Any, List, Tuple
import math
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

logger = logging.getLogger(__name__)

class InheritanceHandler(ITransactionHandler):
    """
    Handles 'inheritance_distribution' transactions.
    Distributes deceased agent's assets to heirs using Zero-Sum integer math logic.
    Enforces atomic settlement.
    """

    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the inheritance distribution.
        Buyer: Deceased Agent (Estate)
        Seller: Not used (None) or could be considered heirs implicitly.
        """
        # "buyer" is the Deceased Agent (Estate) holding the assets.
        deceased_agent = buyer

        heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []

        # Round total cash to 2 decimals to prevent floating point dust propagation.
        # Any residual dust (< 0.01) remains on the deceased agent (effectively burnt or ignored).
        total_cash = round(deceased_agent.assets, 2)

        if total_cash <= 0 or not heir_ids:
            context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no assets ({total_cash}) or heirs.")
            return True # Nothing to distribute, technically a success (no-op)

        count = len(heir_ids)
        # Calculate amount per heir, avoiding float precision issues (floor to cent)
        base_amount = math.floor((total_cash / count) * 100) / 100.0

        credits: List[Tuple[Any, float, str]] = []
        distributed_sum = 0.0

        agents = context.agents # SimulationState has agents dict

        # Distribute to all but the last heir
        for i in range(count - 1):
            h_id = heir_ids[i]
            heir = agents.get(h_id)
            if heir:
                credits.append((heir, base_amount, "inheritance_distribution"))
                distributed_sum += base_amount

        # Last heir gets the remainder to ensure zero-sum of the rounded total
        last_heir_id = heir_ids[-1]
        last_heir = agents.get(last_heir_id)
        if last_heir:
            remaining_amount = round(total_cash - distributed_sum, 2)
            # Ensure we don't transfer negative amounts or dust if something went wrong
            if remaining_amount > 0:
                credits.append((last_heir, remaining_amount, "inheritance_distribution_final"))

        # Atomic Settlement
        if credits:
            success = context.settlement_system.settle_atomic(deceased_agent, credits, context.time)

            if success:
                 context.logger.info(f"INHERITANCE_SUCCESS | Distributed {total_cash} from {deceased_agent.id} to {count} heirs.")
            else:
                 context.logger.error(f"INHERITANCE_FAIL | Atomic settlement failed for {deceased_agent.id}.")

            return success

        return True
