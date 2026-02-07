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

        # Round total cash to 2 decimals to prevent floating point dust propagation.
        assets_val = 0.0
        if hasattr(deceased_agent, 'wallet'):
            assets_val = deceased_agent.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(deceased_agent, 'assets') and isinstance(deceased_agent.assets, dict):
            assets_val = deceased_agent.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(deceased_agent, 'assets'):
            assets_val = float(deceased_agent.assets)

        # TD-233: Use floor to ensure we don't distribute non-existent rounded-up cents
        total_cash = math.floor(assets_val * 100) / 100.0
        dust = assets_val - total_cash

        if total_cash <= 0 and dust <= 1e-9:
            context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no assets ({assets_val}).")
            return True

        if not heir_ids:
            # If no heirs but we have dust/cash, handled elsewhere or we skip
            # InheritanceManager should handle escheatment if no heirs.
             context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no heirs.")
             return True

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

        # TD-233: Sweep fractional dust to Government to ensure Zero Leak (Agent balance -> 0.0)
        if dust > 1e-9 and context.government:
             credits.append((context.government, dust, "inheritance_dust_sweep"))

        # Atomic Settlement
        if credits:
            success = context.settlement_system.settle_atomic(deceased_agent, credits, context.time)

            if success:
                 context.logger.info(f"INHERITANCE_SUCCESS | Distributed {total_cash} from {deceased_agent.id} to {count} heirs. Swept {dust:.4f} dust.")
            else:
                 context.logger.error(f"INHERITANCE_FAIL | Atomic settlement failed for {deceased_agent.id}.")

            return success

        return True
