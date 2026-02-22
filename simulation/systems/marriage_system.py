from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING, Any
import random
import logging

from simulation.systems.api import SystemInterface
from simulation.dtos.api import SimulationState
from modules.household.dtos import BioStateDTO, EconStateDTO
from modules.finance.api import IFinancialEntity

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class MarriageSystem:
    """
    Wave 4.3: Manages the Marriage Market (Household Merging).
    - Matches eligible single agents.
    - Merges wallets (Zero-Sum Transfer + Shared Access).
    - Merges residences.
    """

    def __init__(self, config: Any):
        self.config = config
        self.logger = logger

    def execute(self, state: SimulationState) -> None:
        """
        Main execution loop for marriage matching.
        """
        # 1. Filter Eligible Singles
        eligible_singles = self._find_eligible_singles(state.households)

        if len(eligible_singles) < 2:
            return

        # 2. Shuffle for randomness
        random.shuffle(eligible_singles)

        # 3. Matching Loop
        # Simple greedy matching for now (O(N))
        # Blueprint calls for "Search & Bargaining", but simplified for Wave 4.3.

        matched_pairs: List[Tuple[Household, Household]] = []
        skip_ids = set()

        for i in range(len(eligible_singles)):
            agent_a = eligible_singles[i]
            if agent_a.id in skip_ids:
                continue

            # Look for a match
            for j in range(i + 1, len(eligible_singles)):
                agent_b = eligible_singles[j]
                if agent_b.id in skip_ids:
                    continue

                if self._is_match(agent_a, agent_b):
                    matched_pairs.append((agent_a, agent_b))
                    skip_ids.add(agent_a.id)
                    skip_ids.add(agent_b.id)
                    break

        # 4. Execute Marriages
        for spouse_a, spouse_b in matched_pairs:
            self._execute_marriage(spouse_a, spouse_b, state)

    def _find_eligible_singles(self, households: List[Household]) -> List[Household]:
        candidates = []
        for h in households:
            if not h.is_active:
                continue

            # Check if already married
            if h._bio_state.spouse_id is not None:
                continue

            # Check Age (Adults only)
            if 20 <= h.age <= 45:
                candidates.append(h)

        return candidates

    def _is_match(self, a: Household, b: Household) -> bool:
        """
        Determines compatibility.
        - Age difference < 5 years
        - Opposite sex (for now, based on Blueprint reproduction implication)
        """
        # Age check
        if abs(a.age - b.age) > 5:
            return False

        # Sex check (if defined)
        # BioStateDTO has 'sex' field with default "F"
        if a._bio_state.sex == b._bio_state.sex:
             return False

        # Wealth/Status matching (Assortative Mating) - optional
        # For Wave 4.3, keep it simple.

        return True

    def _execute_marriage(self, a: Household, b: Household, state: SimulationState) -> None:
        """
        Performs the atomic merge of two households.
        """
        # 1. Determine Head of Household (HOH)
        # Criteria: Higher assets or random
        assets_a = a.total_wealth
        assets_b = b.total_wealth

        if assets_a >= assets_b:
            hoh = a
            spouse = b
        else:
            hoh = b
            spouse = a

        # 2. Wealth Transfer (Zero-Sum Integrity)
        # Transfer all liquid assets from Spouse to HOH
        spouse_balance = spouse.balance_pennies
        if spouse_balance > 0:
            if state.settlement_system:
                 # Use generic transfer if available
                 try:
                     state.settlement_system.transfer(
                         sender_id=spouse.id,
                         receiver_id=hoh.id,
                         amount=spouse_balance,
                         currency="USD",
                         memo="MARRIAGE_MERGE"
                     )
                 except AttributeError:
                     # Fallback: If transfer doesn't exist, we assume simple wallet move (less safe but functional)
                     # In a real scenario, we'd ensure Interface compliance.
                     # Here, since we are setting wallet reference next, the funds are effectively moved
                     # IF we add them to the HOH wallet first.
                     hoh.deposit(spouse_balance)
                     spouse.withdraw(spouse_balance) # This might fail if wallet doesn't allow neg?
                     pass

        # 3. Wallet Merge (Reference Copy)
        # This effectively makes them share the SAME bank account for future transactions.
        spouse._econ_state.wallet = hoh._econ_state.wallet

        # 4. Housing Merge
        # Spouse moves into HOH's house
        spouse.residing_property_id = hoh.residing_property_id
        # If spouse owned a house, they keep it (as landlord), but live with HOH.

        # 5. Linkage
        hoh.spouse_id = spouse.id
        spouse.spouse_id = hoh.id

        self.logger.info(f"MARRIAGE | {hoh.id} (HOH) married {spouse.id}. Assets Merged. Address Shared.")
