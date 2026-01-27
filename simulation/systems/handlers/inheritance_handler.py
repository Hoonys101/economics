from typing import Any, List, Optional
import math
import logging
from simulation.systems.api import ISpecializedTransactionHandler
from simulation.models import Transaction
from simulation.dtos.api import SimulationState

logger = logging.getLogger(__name__)

class InheritanceHandler(ISpecializedTransactionHandler):
    """
    Handles 'inheritance_distribution' transactions.
    Distributes deceased agent's assets to heirs using Zero-Sum integer math logic.
    """

    def __init__(self, settlement_system: Any, logger: Optional[logging.Logger] = None):
        self.settlement = settlement_system
        self.logger = logger if logger else logging.getLogger(__name__)

    def handle(self, transaction: Transaction, buyer: Any, seller: Any, state: SimulationState) -> bool:
        """
        Executes the inheritance distribution.
        Buyer: Deceased Agent (Estate)
        Seller: Not used (None) or could be considered heirs implicitly.
        """
        # "buyer" is the Deceased Agent (Estate) holding the assets.
        deceased_agent = buyer

        heir_ids = transaction.metadata.get("heir_ids", []) if transaction.metadata else []
        total_cash = deceased_agent.assets

        if total_cash <= 0 or not heir_ids:
            self.logger.info(f"INHERITANCE_SKIP | Agent {deceased_agent.id} has no assets ({total_cash}) or heirs.")
            return True # Nothing to distribute, technically a success (no-op)

        count = len(heir_ids)
        # Calculate amount per heir, avoiding float precision issues (floor to cent)
        base_amount = math.floor((total_cash / count) * 100) / 100.0

        distributed_sum = 0.0
        all_success = True

        agents = state.agents # SimulationState has agents dict

        # Distribute to all but the last heir
        for i in range(count - 1):
            h_id = heir_ids[i]
            heir = agents.get(h_id)
            if heir:
                if self.settlement.transfer(deceased_agent, heir, base_amount, "inheritance_distribution"):
                    distributed_sum += base_amount
                else:
                    all_success = False
                    self.logger.error(f"INHERITANCE_FAIL | Failed to transfer {base_amount} to heir {h_id}")

        # Last heir gets the remainder to ensure zero-sum
        last_heir_id = heir_ids[-1]
        last_heir = agents.get(last_heir_id)
        if last_heir:
            remaining_amount = total_cash - distributed_sum
            # Ensure we don't transfer negative amounts or dust if something went wrong
            if remaining_amount > 0:
                if not self.settlement.transfer(deceased_agent, last_heir, remaining_amount, "inheritance_distribution_final"):
                    all_success = False
                    self.logger.error(f"INHERITANCE_FAIL | Failed to transfer remainder {remaining_amount} to last heir {last_heir_id}")
            elif remaining_amount < 0:
                 self.logger.critical(f"INHERITANCE_ERROR | Remainder negative! Distributed: {distributed_sum}, Total: {total_cash}")
                 all_success = False

        if all_success:
             self.logger.info(f"INHERITANCE_SUCCESS | Distributed {total_cash} from {deceased_agent.id} to {count} heirs.")

        return all_success
