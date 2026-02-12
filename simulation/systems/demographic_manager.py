from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import logging
import random
import math
from simulation.core_agents import Household
from simulation.utils.config_factory import create_config_dto
from simulation.dtos.config_dtos import HouseholdConfigDTO
from modules.system.api import DEFAULT_CURRENCY
from modules.simulation.api import AgentCoreConfigDTO, AgentStateDTO, ITalented
from modules.household.api import IHouseholdFactory

if TYPE_CHECKING:
    from simulation.dtos.strategy import ScenarioStrategy

logger = logging.getLogger(__name__)

class DemographicManager:
    """
    Phase 19: Demographic Manager
    - Handles lifecycle events: Aging, Birth, Death, Inheritance.
    - Implements evolutionary population dynamics.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DemographicManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_module: Any = None, strategy: Optional["ScenarioStrategy"] = None, household_factory: Optional[IHouseholdFactory] = None):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.config_module = config_module
        self.strategy = strategy
        self.logger = logging.getLogger("simulation.systems.demographic_manager")
        self.settlement_system: Optional[Any] = None # Injected via Initializer

        # Initialize Factory
        self.household_factory = household_factory
        # If no factory injected, we warn (since internal creation is complex without context)
        if not self.household_factory:
             self.logger.warning("DemographicManager initialized without a HouseholdFactory. Births may fail.")

        self.initialized = True
        self.logger.info("DemographicManager initialized.")

    def process_aging(self, agents: List[Household], current_tick: int, market_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Increments age for all households and runs internal lifecycle updates.
        Handles natural death (old age).
        """
        # Ticks per Year is defined in config (e.g., 100 ticks = 1 year)
        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100.0)

        for agent in agents:
            if not agent.is_active:
                continue

            # Phase 4 Lifecycle Update (Replaced CommerceSystem call)
            # Delegate internal lifecycle (aging, needs, taxes)
            agent.update_needs(current_tick, market_data)

            # Explicit aging removed as update_needs -> bio_component handles it.
            # However, we check death here.

            # Check Natural Death (Gompertz-Makeham law simplified)
            if agent.age > 80:
                death_prob = 0.05 + (agent.age - 80) * 0.01
                death_prob_per_tick = death_prob / ticks_per_year
                if random.random() < death_prob_per_tick:
                    self._execute_natural_death(agent, current_tick)

    def _execute_natural_death(self, agent: Household, current_tick: int):
        """
        Handles natural death event.
        Inheritance is handled later by Simulation engine or triggered here.
        Actually, Simulation._handle_agent_lifecycle handles liquidation.
        We just mark is_active = False and log cause.
        """
        agent.is_active = False
        self.logger.info(
            f"NATURAL_DEATH | Household {agent.id} died of old age at {agent.age:.1f}.",
            extra={"agent_id": agent.id, "age": agent.age, "tick": current_tick}
        )

    def process_births(
        self,
        simulation: Any,
        birth_requests: List[Household]
    ) -> List[Household]:
        """
        Executes birth requests.
        Creates new Household agents, inherits traits, sets up lineage.
        """
        new_children = []

        for parent in birth_requests:
            # Re-verify biological capability (sanity check)
            if not (self.config_module.REPRODUCTION_AGE_START <= parent.age <= self.config_module.REPRODUCTION_AGE_END):
                continue

            # Create Child
            child_id = simulation.next_agent_id
            simulation.next_agent_id += 1

            # Asset Transfer calculation
            parent_assets = 0
            if hasattr(parent, 'wallet'):
                parent_assets = parent.wallet.get_balance(DEFAULT_CURRENCY)
            elif hasattr(parent, 'assets') and isinstance(parent.assets, dict):
                parent_assets = int(parent.assets.get(DEFAULT_CURRENCY, 0))
            elif hasattr(parent, 'assets'):
                parent_assets = int(parent.assets)

            # TD-233: Calculate gift in pennies (10%)
            initial_gift_pennies = int(max(0, min(parent_assets * 0.1, parent_assets)))

            try:
                # Use Factory for creation
                child = self.household_factory.create_newborn(parent, simulation, child_id)

                # Register linkage and finalize
                parent.children_ids.append(child_id)
                new_children.append(child)

                # WO-124: Transfer Birth Gift via SettlementSystem
                if initial_gift_pennies > 0:

                    # Prefer injected settlement_system, fallback to simulation object for compatibility
                    settlement = self.settlement_system
                    if not settlement and hasattr(simulation, "settlement_system"):
                         settlement = simulation.settlement_system

                    if settlement:
                         settlement.transfer(parent, child, initial_gift_pennies, "BIRTH_GIFT")
                    else:
                         self.logger.error("BIRTH_ERROR | SettlementSystem not found. Cannot transfer birth gift.")

                self.logger.info(
                    f"BIRTH | Parent {parent.id} ({parent.age:.1f}y) -> Child {child.id}. "
                    f"Assets: {initial_gift_pennies}",
                    extra={"parent_id": parent.id, "child_id": child.id, "tick": simulation.time}
                )
            except Exception as e:
                # No asset rollback needed as transfer happens after success.
                self.logger.error(
                    f"BIRTH_FAILED | Failed to create child for parent {parent.id}. Error: {e}",
                    extra={"parent_id": parent.id, "error": str(e)}
                )
                continue

        return new_children

    def handle_inheritance(self, deceased_agent: Household, simulation: Any):
        """
        [DEPRECATED] This method is deprecated and should not be used.
        Use InheritanceManager via TransactionProcessor instead.
        Distribute assets to children with Zero-Sum integrity.
        """
        self.logger.warning(
            f"DEPRECATED_METHOD_CALL | DemographicManager.handle_inheritance called for {deceased_agent.id}. "
            "This logic is superseded by InheritanceManager and TransactionProcessor."
        )

        # Ensure SettlementSystem is available
        if not getattr(simulation, "settlement_system", None):
            raise RuntimeError("SettlementSystem not found. Cannot execute inheritance.")

        total_assets = 0.0
        if hasattr(deceased_agent, 'wallet'):
            total_assets = deceased_agent.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(deceased_agent, 'assets') and isinstance(deceased_agent.assets, dict):
            total_assets = deceased_agent.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(deceased_agent, 'assets'):
            total_assets = float(deceased_agent.assets)

        if total_assets <= 0:
            return

        # Calculate Tax
        # Assets are in pennies if they came from wallet
        total_assets_pennies = int(total_assets)
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.0)
        tax_amount_pennies = int(total_assets_pennies * tax_rate)
        net_estate_pennies = total_assets_pennies - tax_amount_pennies

        # Transfer Tax
        if tax_amount_pennies > 0:
            simulation.settlement_system.transfer(
                deceased_agent,
                simulation.government,
                tax_amount_pennies,
                "inheritance_tax",
                tick=simulation.time
            )

        # Find living heirs
        heirs = [simulation.agents[cid] for cid in deceased_agent.children_ids if cid in simulation.agents and simulation.agents[cid].is_active]

        if heirs:
            # FIX: Use integer arithmetic (cents) to prevent floating point rounding errors and leaks
            num_heirs = len(heirs)
            share_cents = net_estate_pennies // num_heirs
            remainder_cents = net_estate_pennies % num_heirs

            # Distribute shares
            for i, heir in enumerate(heirs):
                amount_cents = share_cents
                # Add remainder to the last heir to ensure sum equals net_estate
                if i == num_heirs - 1:
                    amount_cents += remainder_cents

                if amount_cents > 0:
                    simulation.settlement_system.transfer(
                        deceased_agent,
                        heir,
                        amount_cents,
                        "inheritance_distribution",
                        tick=simulation.time
                    )

                    self.logger.info(
                        f"INHERITANCE | Heir {heir.id} received {amount_cents} from {deceased_agent.id}.",
                        extra={"heir_id": heir.id, "deceased_id": deceased_agent.id, "amount": amount_cents}
                    )
        else:
            # No heirs: Escheatment to State
            simulation.settlement_system.transfer(
                deceased_agent,
                simulation.government,
                net_estate_pennies,
                "escheatment",
                tick=simulation.time
            )

        # No explicit `_sub_assets`: The transfers will naturally drain the `deceased_agent`'s balance to near zero (or exactly zero).
