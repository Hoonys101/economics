from __future__ import annotations
from typing import List, Dict, Any, Optional
import logging
import random
from simulation.core_agents import Household

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

    def __init__(self, config_module: Any = None):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.config_module = config_module
        self.logger = logging.getLogger("simulation.systems.demographic_manager")
        self.settlement_system: Optional[Any] = None # Injected via Initializer
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

            # Asset Transfer (e.g. 10% of parent assets as startup gift?)
            # Or just cost of birth (hospital fee)?
            # Phase 19 Spec doesn't specify asset transfer amount,
            # but usually children start with 0 or small amount.
            # Let's assume standard INITIAL_ASSETS or small portion from parent.
            # "Initial 자산은 부모 자산의 일부 이전"
            initial_gift = max(0.0, min(parent.assets * 0.1, parent.assets))

            # WO-124: Removed direct asset modification. Transfer happens via SettlementSystem after creation.

            try:
                # Create Instance
                # We need to clone parent's structure but reset state
                # Assuming Household.__init__ takes similar args.
                # We need to access simulation.goods_data etc.
                # Ideally Simulation passes factory or we use parent's references.

                # 1. Talent Inheritance & Mutation
                child_talent = self._inherit_talent(parent.talent)

                # 2. Brain (HouseholdAI) - Inherit weights/policy
                # This requires creating a new decision engine.
                # We can use parent.clone() logic but customized.

                # Create Decision Engine (similar to parent's type)
                # We need simulation.ai_trainer to get engine
                # Accessing simulation.ai_trainer...
                ai_trainer = simulation.ai_trainer

                # Value Orientation Inheritance (with mutation?)
                value_orientation = parent.value_orientation # Strict inheritance for now

                # Get base engine
                base_ai_engine = ai_trainer.get_engine(value_orientation)

                # Create HouseholdAI wrapper
                from simulation.ai.household_ai import HouseholdAI
                from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine

                # Inherit Personality (with mutation)
                child_personality = self._inherit_personality(parent.personality)

                new_ai = HouseholdAI(
                    agent_id=str(child_id),
                    ai_decision_engine=base_ai_engine,
                    # Inherit parameters maybe?
                )

                # Create Decision Engine
                # WO-110: Allow selecting engine type for newborns (AIDriven vs RuleBased)
                newborn_engine_type = getattr(self.config_module, "NEWBORN_ENGINE_TYPE", "AIDriven")

                if newborn_engine_type == "RuleBased":
                    from simulation.decisions.rule_based_household_engine import RuleBasedHouseholdDecisionEngine
                    new_decision_engine = RuleBasedHouseholdDecisionEngine(
                        config_module=self.config_module,
                        logger=simulation.logger
                    )
                else:
                    new_decision_engine = AIDrivenHouseholdDecisionEngine(
                        ai_engine=new_ai,
                        config_module=self.config_module,
                        logger=simulation.logger
                    )
                    new_decision_engine.loan_market = simulation.markets.get("loan_market")

                # Load initial needs from config
                initial_needs_for_newborn = getattr(self.config_module, "NEWBORN_INITIAL_NEEDS", {})
                if not initial_needs_for_newborn:
                    self.logger.warning("NEWBORN_INITIAL_NEEDS not found in config. Newborns may be inactive.")

                # WO-124: Instantiate with 0 assets. Gift is transferred via SettlementSystem.
                child = Household(
                    id=child_id,
                    talent=child_talent,
                    goods_data=simulation.goods_data,
                    initial_assets=0.0,
                    initial_needs=initial_needs_for_newborn.copy(),
                    decision_engine=new_decision_engine,
                    value_orientation=value_orientation,
                    personality=child_personality,
                    config_module=self.config_module,
                    loan_market=simulation.markets.get("loan_market"),
                    risk_aversion=parent.risk_aversion, # Inherit risk aversion
                    logger=simulation.logger
                )

                # Initialize Phase 19 Attributes
                child.initialize_demographics(
                    age=0.0,
                    gender=child.gender, # Kept from init
                    parent_id=parent.id,
                    generation=parent.generation + 1
                )
                child.education_level = 0 # Start at 0
                child.expected_wage = self._calculate_expected_wage(child.education_level)

                # Brain Weight Inheritance
                if hasattr(simulation, "ai_training_manager"):
                    simulation.ai_training_manager.inherit_brain(parent, child)
                else:
                    # Fallback if manager not found (e.g. mocked simulation)
                    self.logger.warning("AITrainingManager not found for brain inheritance.")

                # Register linkage and finalize
                parent.children_ids.append(child_id)
                new_children.append(child)

                # WO-124: Transfer Birth Gift via SettlementSystem
                if initial_gift > 0:
                    # Prefer injected settlement_system, fallback to simulation object for compatibility
                    settlement = self.settlement_system or getattr(simulation, "settlement_system", None)

                    if settlement:
                         settlement.transfer(parent, child, initial_gift, "BIRTH_GIFT")
                    else:
                         self.logger.error("BIRTH_ERROR | SettlementSystem not found. Cannot transfer birth gift.")

                self.logger.info(
                    f"BIRTH | Parent {parent.id} ({parent.age:.1f}y) -> Child {child.id}. "
                    f"Assets: {initial_gift:.2f}",
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

    def _inherit_talent(self, parent_talent: Any) -> Any:
        """
        Inherit talent with mutation.
        """
        # Assuming Talent class has base_learning_rate etc.
        # Deep copy
        from simulation.core_agents import Talent
        import copy

        new_talent = copy.deepcopy(parent_talent)

        # Mutation
        mutation_range = 0.1
        new_talent.base_learning_rate *= random.uniform(1.0 - mutation_range, 1.0 + mutation_range)

        return new_talent

    def _inherit_personality(self, parent_personality: Any) -> Any:
        """
        Inherit personality with potential mutation.
        """
        # Mutation Probability
        if random.random() < getattr(self.config_module, "MITOSIS_MUTATION_PROBABILITY", 0.1):
            from simulation.ai.enums import Personality
            available = list(Personality)
            return random.choice(available)
        return parent_personality

    def _calculate_expected_wage(self, education_level: int) -> float:
        base_wage = getattr(self.config_module, "INITIAL_WAGE", 10.0)
        multipliers = getattr(self.config_module, "EDUCATION_COST_MULTIPLIERS", {})
        mult = multipliers.get(education_level, 1.0)
        return base_wage * mult

    def handle_inheritance(self, deceased_agent: Household, simulation: Any):
        """
        Distribute assets to children.
        """
        if not deceased_agent.children_ids:
            # No heirs -> State (Tax)
            return # Already handled by existing liquidation logic (Government collection)

        # Find living heirs
        heirs = [simulation.agents[cid] for cid in deceased_agent.children_ids if cid in simulation.agents and simulation.agents[cid].is_active]

        if not heirs:
            return # No living heirs

        # Distribute Assets
        # Existing logic in engine._handle_agent_lifecycle wipes assets via tax?
        # We need to intercept or modify engine to call this BEFORE wiping.
        # But per instructions: "HouseholdAI handles decision, DemographicManager handles execution".
        # Inheritance logic might need to run before standard liquidation.

        amount = deceased_agent.assets
        if amount <= 0: return

        # Tax
        tax_rate = getattr(self.config_module, "INHERITANCE_TAX_RATE", 0.0)
        tax = amount * tax_rate
        net_amount = amount - tax

        # Send Tax
        simulation.government.collect_tax(tax, "inheritance_tax", deceased_agent.id, simulation.time)

        # Distribute
        share = net_amount / len(heirs)
        for heir in heirs:
            heir._add_assets(share)
            self.logger.info(
                f"INHERITANCE | Heir {heir.id} received {share:.2f} from {deceased_agent.id}.",
                extra={"heir_id": heir.id, "deceased_id": deceased_agent.id}
            )

        # Clear deceased assets so engine doesn't double count or tax again
        deceased_agent._sub_assets(deceased_agent.assets)
