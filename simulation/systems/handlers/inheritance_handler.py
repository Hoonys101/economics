from typing import Any, List, Tuple
import math
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY

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

        # SSoT: Use total_pennies directly (Strict Schema Enforced)
        # This ensures we only distribute what was calculated by the Manager, preventing leaks from shared wallets.
        assets_val = int(tx.total_pennies)

        if assets_val <= 0:
            context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no distributable assets ({assets_val}).")
            return True

        if not heir_ids:
            # If no heirs but we have dust/cash, handled elsewhere or we skip
            # InheritanceManager should handle escheatment if no heirs.
             context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no heirs.")
             return True

        count = len(heir_ids)
        # Calculate amount per heir (integer division)
        base_amount = assets_val // count

        credits: List[Tuple[Any, int, str]] = []
        distributed_sum = 0

        agents = context.agents # SimulationState has agents dict

        # Distribute to all but the last heir
        for i in range(count - 1):
            h_id = heir_ids[i]
            heir = agents.get(h_id)
            if heir:
                credits.append((heir, base_amount, "inheritance_distribution"))
                distributed_sum += base_amount

        # Last heir gets the remainder to ensure zero-sum
        last_heir_id = heir_ids[-1]
        last_heir = agents.get(last_heir_id)
        if last_heir:
            remaining_amount = assets_val - distributed_sum
            # Ensure we don't transfer negative amounts
            if remaining_amount > 0:
                credits.append((last_heir, remaining_amount, "inheritance_distribution_final"))

        # Atomic Settlement
        if credits:
            success = context.settlement_system.settle_atomic(deceased_agent, credits, context.time)

            if success:
                 context.logger.info(f"INHERITANCE_SUCCESS | Distributed {assets_val} from {deceased_agent.id} to {count} heirs.")
            else:
                 context.logger.error(f"INHERITANCE_FAIL | Atomic settlement failed for {deceased_agent.id}.")

            return success

        return True

    def rollback(self, tx: Transaction, context: TransactionContext) -> bool:
        """
        Reverses inheritance distribution.
        Heirs pay back the Estate.
        """
        deceased_agent_id = tx.buyer_id
        estate_agent = context.agents.get(deceased_agent_id) or context.inactive_agents.get(deceased_agent_id)

        if not estate_agent:
             return False

        heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []
        if not heir_ids:
             return True

        # Reconstruct amounts (assuming consistent state or using total_pennies from tx if accurate)
        # Note: handle() uses current wallet balance. If we assume rollback happens immediately,
        # we can't easily know exactly what was distributed unless we stored it in tx.metadata['distribution'].
        # However, we can try to reverse using total_pennies if that was populated correctly.
        # But handle() calculates assets_val dynamically and doesn't update tx.total_pennies necessarily?
        # Let's assume for now that we can't perfectly rollback without detailed logs,
        # so we log warning and fail safe, OR we assume total_pennies in tx is the amount.

        amount = tx.total_pennies
        if amount <= 0:
             return True

        count = len(heir_ids)
        base_amount = amount // count
        distributed_sum = 0

        # Reverse transfers
        success_all = True

        for i, h_id in enumerate(heir_ids):
             heir = context.agents.get(h_id)
             if not heir: continue

             repay_amount = base_amount
             if i == count - 1:
                 repay_amount = amount - distributed_sum

             distributed_sum += base_amount

             if repay_amount > 0:
                 if not context.settlement_system.transfer(heir, estate_agent, repay_amount, f"rollback_inheritance:{tx.id}"):
                      success_all = False

        return success_all
