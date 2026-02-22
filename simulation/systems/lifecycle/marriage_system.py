from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional, Dict, Any, Tuple
import logging
import random

from modules.finance.api import ISettlementSystem, IFinancialAgent
from modules.common.interfaces import IPropertyOwner
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

if TYPE_CHECKING:
    from simulation.dtos.api import SimulationState
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class MarriageSystem:
    """
    Manages the marriage market and household mergers.
    Implements the "Asset Merger & Dependent Spouse" model.
    """

    def __init__(self, settlement_system: ISettlementSystem, logger: logging.Logger):
        self.settlement_system = settlement_system
        self.logger = logger
        # Configurable params
        self.marriage_min_age = 18.0
        self.marriage_max_age = 60.0
        self.marriage_chance = 0.05 # 5% chance per tick for eligible singles to marry

    def execute(self, state: SimulationState) -> List[Transaction]:
        """
        Identifies eligible singles, matches them, and executes mergers.
        Returns any financial transactions generated (e.g. dowry/transfer).
        """
        # 0. Build Real Estate Map for efficient lookup
        # We assume state.real_estate_units contains all units
        real_estate_map = {u.id: u for u in state.real_estate_units}

        # 1. Identify Eligible Singles
        singles_m: List[Household] = []
        singles_f: List[Household] = []

        for agent in state.households:
            if not agent.is_active:
                continue
            if agent.spouse_id is not None:
                continue

            # Age check
            if not (self.marriage_min_age <= agent.age <= self.marriage_max_age):
                continue

            if agent.gender == "M":
                singles_m.append(agent)
            elif agent.gender == "F":
                singles_f.append(agent)
            else:
                # Random assignment for non-binary to simplify matching for now
                if random.random() < 0.5:
                    singles_m.append(agent)
                else:
                    singles_f.append(agent)

        # 2. Matchmaking (Shuffle and zip)
        random.shuffle(singles_m)
        random.shuffle(singles_f)

        matches: List[Tuple[Household, Household]] = []
        limit = min(len(singles_m), len(singles_f))

        # Simple random matching with probability
        for i in range(limit):
            if random.random() < self.marriage_chance:
                matches.append((singles_m[i], singles_f[i]))

        transactions: List[Transaction] = []

        # 3. Execute Mergers
        for male, female in matches:
            # Decide Head (Primary) and Spouse (Secondary)
            # Logic: Higher wealth becomes Head. Tie-breaker: Male (arbitrary convention for consistent tie-breaking).
            m_wealth = male.total_wealth
            f_wealth = female.total_wealth

            if m_wealth >= f_wealth:
                head = male
                spouse = female
            else:
                head = female
                spouse = male

            # Execute
            txs = self._execute_merger(head, spouse, state.time, real_estate_map)
            transactions.extend(txs)

            self.logger.info(
                f"MARRIAGE_EVENT | {head.id} married {spouse.id}. "
                f"Head: {head.id}, Spouse: {spouse.id} (Inactive). "
                f"Merged Wealth: {head.total_wealth}",
                extra={"tags": ["marriage", "lifecycle"]}
            )

        return transactions

    def _execute_merger(self, head: Household, spouse: Household, tick: int, real_estate_map: Dict[int, Any]) -> List[Transaction]:
        transactions = []

        # 1. Asset Transfer (Cash)
        # Using SettlementSystem for auditability
        spouse_balance = spouse.balance_pennies
        if spouse_balance > 0:
            tx = self.settlement_system.transfer(
                debit_agent=spouse,
                credit_agent=head,
                amount=spouse_balance,
                memo="MARRIAGE_MERGER",
                tick=tick,
                currency=DEFAULT_CURRENCY
            )
            # We don't append to transactions list because SettlementSystem records it in the ledger.
            # LifecycleManager returns transactions for deferred execution/logging if needed.
            # But usually SettlementSystem executes immediately.
            pass

        # 2. Portfolio Merger
        # Merge spouse's portfolio into head's
        head.portfolio.merge(spouse.portfolio)
        spouse.portfolio.holdings.clear()

        # 3. Inventory Transfer
        # Copy spouse's inventory to head
        for item, qty in spouse.inventory.items():
            head.add_item(item, qty)
        spouse.clear_inventory()

        # 4. Property Transfer
        # Iterate spouse's owned properties
        # We must use list() because we will modify the list during iteration if we call remove_property
        # But here we are transferring.
        spouse_props = list(spouse.owned_properties)
        for prop_id in spouse_props:
            # Update Unit Owner (Global State)
            if prop_id in real_estate_map:
                unit = real_estate_map[prop_id]
                unit.owner_id = head.id

            # Update Agent Lists (Local State)
            head.add_property(prop_id)
            spouse.remove_property(prop_id)

        # 5. Children Transfer
        for child_id in spouse.children_ids:
            head.add_child(child_id)
        # We don't strictly need to clear spouse.children_ids, but for correctness:
        # spouse.children_ids.clear() # BioStateDTO field, better not to mutate directly if private, but lists are ref.
        # Household doesn't expose clear_children.
        # It's fine to leave them on the inactive agent record.

        # 6. State Update
        head.spouse_id = spouse.id
        spouse.spouse_id = head.id

        # Mark Spouse as Inactive
        spouse.is_active = False

        # Move Spouse to Head's residence
        # If spouse was renting, they effectively leave.
        # If head is homeless, spouse becomes homeless (unless they brought a house, which we just transferred).
        # If head has a home, spouse moves in.
        spouse.residing_property_id = head.residing_property_id
        spouse.is_homeless = head.is_homeless

        return transactions
