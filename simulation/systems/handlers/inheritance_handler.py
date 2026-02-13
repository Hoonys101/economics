from typing import Any, List, Tuple
import logging
from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction
from modules.system.api import DEFAULT_CURRENCY
from modules.finance.api import IFinancialAgent

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
        if not deceased_agent:
            context.logger.error("INHERITANCE_FAIL | Deceased agent (buyer) is None.")
            return False

        heir_ids = tx.metadata.get("heir_ids", []) if tx.metadata else []

        # Assets are in pennies (integer)
        assets_val = 0
        if isinstance(deceased_agent, IFinancialAgent):
            assets_val = deceased_agent.get_balance(DEFAULT_CURRENCY)
        else:
            # Fallback
            assets_raw = getattr(deceased_agent, 'assets', 0)
            if isinstance(assets_raw, dict):
                 assets_val = int(assets_raw.get(DEFAULT_CURRENCY, 0))
            else:
                 try:
                     assets_val = int(float(assets_raw))
                 except (ValueError, TypeError):
                     assets_val = 0

        if assets_val <= 0:
            context.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no assets ({assets_val}).")
            return True

        # Resolve Valid Heirs
        valid_heirs = []
        agents = context.agents

        for h_id in heir_ids:
            heir = agents.get(h_id)
            # Also check inactive_agents if heirs are temporarily inactive? No, heirs should be active.
            if heir:
                valid_heirs.append(heir)
            else:
                context.logger.warning(f"INHERITANCE_WARN | Heir {h_id} not found in active agents.")

        count = len(valid_heirs)
        credits: List[Tuple[Any, int, str]] = []

        if count > 0:
            # Distribute to Heirs
            base_amount = assets_val // count
            distributed_sum = 0

            # Distribute to all but last
            for i in range(count - 1):
                heir = valid_heirs[i]
                if base_amount > 0:
                    credits.append((heir, base_amount, "inheritance_distribution"))
                    distributed_sum += base_amount

            # Last valid heir gets remainder
            last_heir = valid_heirs[-1]
            remaining_amount = assets_val - distributed_sum
            if remaining_amount > 0:
                credits.append((last_heir, remaining_amount, "inheritance_distribution_final"))

            context.logger.info(f"INHERITANCE_PLAN | Distributing {assets_val} to {count} heirs.")

        else:
            # Fallback: Escheatment (No Valid Heirs)
            context.logger.warning(f"INHERITANCE_FALLBACK | Agent {deceased_agent.id} has no VALID heirs (ids: {heir_ids}). Escheating {assets_val} to Government.")
            gov = context.government
            if gov:
                credits.append((gov, assets_val, "escheatment_fallback"))
            else:
                context.logger.critical("INHERITANCE_CRITICAL | Government not found for fallback escheatment! Assets LEAKED.")
                return False

        # Atomic Settlement
        if credits:
            success = context.settlement_system.settle_atomic(deceased_agent, credits, context.time)

            if success:
                 context.logger.info(f"INHERITANCE_SUCCESS | Distributed {assets_val} from {deceased_agent.id}.")
            else:
                 context.logger.error(f"INHERITANCE_FAIL | Atomic settlement failed for {deceased_agent.id}.")

            return success

        return True
