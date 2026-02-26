from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from typing import override
import logging
from logging import Logger
from collections import deque, defaultdict
import random
import copy
import math

from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order, Skill, Talent
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)
from simulation.dtos import DecisionContext, FiscalContext, MacroFinancialContext, DecisionInputDTO, LeisureEffectDTO, ConsumptionResult

from modules.simulation.dtos.api import HouseholdConfigDTO
from simulation.portfolio import Portfolio
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine, IOrchestratorAgent, IInventoryHandler, ISensoryDataProvider, AgentSensorySnapshotDTO, InventorySlot, ItemDTO, InventorySlotDTO, AgentStateDTO

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent
from modules.finance.api import ICreditFrozen
from modules.common.financial.api import IFinancialAgent, IFinancialEntity
from modules.simulation.api import IEducated
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.wallet.wallet import Wallet
from modules.common.interfaces import IPropertyOwner, IInvestor
from modules.market.api import IHousingTransactionParticipant
import simulation

# Engines
from modules.household.engines.lifecycle import LifecycleEngine
from modules.household.engines.needs import NeedsEngine
from modules.household.engines.social import SocialEngine
from modules.household.engines.budget import BudgetEngine
from modules.household.engines.consumption_engine import ConsumptionEngine
from modules.household.engines.belief_engine import BeliefEngine
from modules.household.engines.crisis_engine import CrisisEngine
from modules.household.connectors.housing_connector import HousingConnector

# API & DTOs
from modules.household.api import (
    LifecycleInputDTO, NeedsInputDTO, SocialInputDTO, BudgetInputDTO, ConsumptionInputDTO,
    BeliefInputDTO, PanicSellingInputDTO,
    PrioritizedNeed, BudgetPlan, HousingActionDTO, CloningRequestDTO
)
from modules.household.dtos import (
    HouseholdStateDTO, EconContextDTO,
    BioStateDTO, EconStateDTO, SocialStateDTO,
    HouseholdSnapshotDTO, DurableAssetDTO
)
from simulation.dtos.persistence import HouseholdPersistenceDTO
from modules.market.api import IndustryDomain
from modules.analytics.dtos import AgentTickAnalyticsDTO
from modules.household.services import HouseholdSnapshotAssembler
from modules.household.mixins._state_access import HouseholdStateAccessMixin

# Protocols
from modules.hr.api import IEmployeeDataProvider
from simulation.dtos.household_state_container import HouseholdStateContainer
from modules.government.political.api import IVoter, VoteRecordDTO

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class Household(
    ILearningAgent,
    IEmployeeDataProvider,
    IEducated,
    IHousingTransactionParticipant,
    IFinancialEntity,
    IOrchestratorAgent,
    ICreditFrozen,
    IInventoryHandler,
    ISensoryDataProvider,
    IInvestor,
    HouseholdStateAccessMixin,
    IVoter
):
    """
    Household Agent (Orchestrator).
    Delegates Bio/Econ/Social logic to specialized stateless Engines.
    State is held in internal DTOs.
    """

    def __init__(
        self,
        core_config: AgentCoreConfigDTO,
        engine: IDecisionEngine,
        talent: Talent,
        goods_data: List[Dict[str, Any]],
        personality: Personality,
        config_dto: HouseholdConfigDTO,
        loan_market: Optional[LoanMarket] = None,
        risk_aversion: float = 1.0,
        # Demographics
        initial_age: Optional[float] = None,
        gender: Optional[str] = None,
        parent_id: Optional[int] = None,
        generation: Optional[int] = None,
        initial_assets_record: Optional[int] = None,  # MIGRATION: int pennies
        demographic_manager: Optional[Any] = None,
        major: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.config = config_dto
        self.logger = core_config.logger
        self.demographic_manager = demographic_manager
        self.last_labor_allocation = 0.0

        # --- Initialize Engines (Stateless) ---
        self.lifecycle_engine = LifecycleEngine()
        self.needs_engine = NeedsEngine()
        self.social_engine = SocialEngine()
        self.budget_engine = BudgetEngine()
        self.consumption_engine = ConsumptionEngine()
        self.belief_engine = BeliefEngine()
        self.crisis_engine = CrisisEngine()
        self.housing_connector = HousingConnector()

        # --- Initialize Internal State DTOs ---

        # 1. Bio State
        age_range = getattr(self.config, 'initial_household_age_range', (20, 60))
        if not age_range: age_range = (20, 60)

        # Initialize sex from gender for biological alignment (Wave 4)
        initial_gender = gender if gender is not None else random.choice(["M", "F"])

        self._bio_state = BioStateDTO(
            id=core_config.id,
            age=initial_age if initial_age is not None else random.uniform(*age_range),
            gender=initial_gender,
            generation=generation if generation is not None else 0,
            is_active=True,
            needs=core_config.initial_needs.copy(),
            parent_id=parent_id,
            sex=initial_gender # Birth biological sex aligns with gender
        )

        # 2. Econ State
        price_memory_len = int(self.config.price_memory_length)
        wage_memory_len = int(self.config.wage_memory_length)
        ticks_per_year = int(self.config.ticks_per_year)

        perceived_prices = {}
        for g in goods_data:
             perceived_prices[g["id"]] = g.get("initial_price", 1000)

        adaptation_rate = self.config.adaptation_rate_normal
        if personality == Personality.IMPULSIVE:
             adaptation_rate = self.config.adaptation_rate_impulsive
        elif personality == Personality.CONSERVATIVE:
             adaptation_rate = self.config.adaptation_rate_conservative

        raw_aptitude = random.gauss(*self.config.initial_aptitude_distribution)
        aptitude = max(0.0, min(1.0, raw_aptitude))

        temp_wallet = Wallet(core_config.id, {})

        self._econ_state = EconStateDTO(
            wallet=temp_wallet,
            inventory={},
            inventory_quality={},
            durable_assets=[],
            portfolio=Portfolio(core_config.id),
            is_employed=False,
            employer_id=None,
            current_wage_pennies=0,
            wage_modifier=1.0,
            labor_skill=1.0,
            education_xp=0.0,
            education_level=0,
            market_insight=0.5, # Phase 4.1: Dynamic Cognitive Filter
            major=major, # Phase 4.1: Major-Matching
            expected_wage_pennies=1000, # Default 10.00
            talent=talent,
            skills={},
            aptitude=aptitude,
            owned_properties=[],
            residing_property_id=None,
            is_homeless=True,
            home_quality_score=1.0,
            housing_target_mode="RENT",
            housing_price_history=deque(maxlen=ticks_per_year),
            market_wage_history=deque(maxlen=wage_memory_len),
            shadow_reservation_wage_pennies=0,
            last_labor_offer_tick=0,
            last_fired_tick=-1,
            job_search_patience=0,
            employment_start_tick=-1,
            current_consumption=0.0,
            current_food_consumption=0.0,
            expected_inflation=defaultdict(float),
            perceived_avg_prices=perceived_prices,
            price_history=defaultdict(lambda: deque(maxlen=price_memory_len)),
            price_memory_length=price_memory_len,
            adaptation_rate=adaptation_rate,
            labor_income_this_tick_pennies=0,
            capital_income_this_tick_pennies=0,
            consumption_expenditure_this_tick_pennies=0,
            food_expenditure_this_tick_pennies=0,
            initial_assets_record_pennies=initial_assets_record if initial_assets_record is not None else 0
        )

        self._core_config = core_config
        self.decision_engine = engine
        self.id = core_config.id
        self.name = core_config.name
        self.logger = core_config.logger
        self.memory_v2 = core_config.memory_interface
        self.value_orientation = core_config.value_orientation
        self.needs = core_config.initial_needs.copy() # Legacy accessor support

        self._credit_frozen_until_tick = 0
        self._pre_state_data: Dict[str, Any] = {}
        self._wallet = self._econ_state.wallet

        # Value Orientation
        mapping = self.config.value_orientation_mapping
        prefs = mapping.get(
            self.value_orientation,
            {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        )
        self.preference_asset = prefs["preference_asset"]
        self.preference_social = prefs["preference_social"]
        self.preference_growth = prefs["preference_growth"]

        # 3. Social State
        conformity_ranges = self.config.conformity_ranges
        c_min, c_max = conformity_ranges.get(personality.name, conformity_ranges.get(None, (0.3, 0.7)))
        conformity = random.uniform(c_min, c_max)

        # Scale mean assets for check? Config is now in pennies.
        mean_assets_pennies = self.config.initial_household_assets_mean
        effective_initial_assets = initial_assets_record if initial_assets_record is not None else 0

        is_wealthy = effective_initial_assets > mean_assets_pennies * 1.5
        is_poor = effective_initial_assets < mean_assets_pennies * 0.5

        if personality == Personality.STATUS_SEEKER or is_wealthy:
            min_pref = self.config.quality_pref_snob_min
            q_pref = random.uniform(min_pref, 1.0)
        elif personality == Personality.MISER or is_poor:
            max_pref = self.config.quality_pref_miser_max
            q_pref = random.uniform(0.0, max_pref)
        else:
            min_snob = self.config.quality_pref_snob_min
            max_miser = self.config.quality_pref_miser_max
            q_pref = random.uniform(max_miser, min_snob)

        self._social_state = SocialStateDTO(
            personality=personality,
            social_status=0.0,
            discontent=0.0,
            approval_rating=1,
            conformity=conformity,
            social_rank=0.5,
            quality_preference=q_pref,
            brand_loyalty={},
            last_purchase_memory={},
            patience=max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3))),
            optimism=max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3))),
            ambition=max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3))),
            last_leisure_type="IDLE",
            demand_elasticity=getattr(self.config, 'elasticity_mapping', {}).get(
                personality.name,
                getattr(self.config, 'elasticity_mapping', {}).get("DEFAULT", 1.0)
            )
        )

        if personality in [Personality.MISER, Personality.CONSERVATIVE]:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 1.5, "social": 0.5, "improvement": 0.5, "quality": 1.0}
        elif personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 0.5, "social": 1.5, "improvement": 0.5, "quality": 1.0}
        elif personality == Personality.GROWTH_ORIENTED:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 0.5, "social": 0.5, "improvement": 1.5, "quality": 1.0}
        else:
             self._social_state.desire_weights = {"survival": 1.0, "asset": 1.0, "social": 1.0, "improvement": 1.0, "quality": 1.0}

        # Initialize Political State
        vision_map = {
            Personality.GROWTH_ORIENTED: 0.9,
            Personality.STATUS_SEEKER: 0.8,
            Personality.MISER: 0.4,
            Personality.CONSERVATIVE: 0.3,
            Personality.IMPULSIVE: 0.5
        }
        base_v = vision_map.get(personality, 0.5)
        self._social_state.economic_vision = max(0.0, min(1.0, base_v + random.uniform(-0.15, 0.15)))
        self._social_state.trust_score = 0.5

        self.goods_info_map = {g["id"]: g for g in goods_data}
        self.goods_data = goods_data
        self.risk_aversion = risk_aversion

        # WO-167: Grace Protocol
        self.distress_tick_counter: int = 0

        self.decision_engine.loan_market = loan_market
        self.decision_engine.logger = self.logger

        if self.memory_v2:
            from modules.memory.V2.dtos import MemoryRecordDTO
            record = MemoryRecordDTO(
                tick=0,
                agent_id=self.id,
                event_type="BIRTH",
                data={"initial_assets": initial_assets_record if initial_assets_record is not None else 0}
            )
            self.memory_v2.add_record(record)

        # Internal buffers for Orchestrator flow
        self._prioritized_needs: List[PrioritizedNeed] = []
        self._cloning_requests: List[CloningRequestDTO] = []

        self._state_container = HouseholdStateContainer(self)

        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized (Engine-based).",
            extra={"tags": ["household_init"]}
        )

    @property
    def state(self) -> HouseholdStateContainer:
        return self._state_container

    # --- IOrchestratorAgent Implementation ---

    def get_core_config(self) -> AgentCoreConfigDTO:
        return self._core_config

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        return {
            "is_active": self.is_active,
            "approval_rating": self._social_state.approval_rating,
            "total_wealth": self._econ_state.wallet.get_balance(DEFAULT_CURRENCY)
        }

    def get_current_state(self) -> AgentStateDTO:
        main_items = [
            ItemDTO(name=k, quantity=v, quality=self.get_quality(k, InventorySlot.MAIN))
            for k, v in self._econ_state.inventory.items()
        ]

        inventories = {
            InventorySlot.MAIN.name: InventorySlotDTO(items=main_items)
        }

        return AgentStateDTO(
            assets=self._econ_state.wallet.get_all_balances(),
            is_active=self.is_active,
            inventories=inventories,
            inventory=None
        )

    def load_state(self, state: AgentStateDTO) -> None:
        if state.assets and any(v > 0 for v in state.assets.values()):
             self.logger.warning(f"Agent {self.id}: load_state called with assets, but direct loading is disabled for integrity. Assets ignored: {state.assets}")

        self._econ_state.inventory.clear()
        self._econ_state.inventory_quality.clear()
        self.is_active = state.is_active

        # Restore from inventories
        if state.inventories:
            main_slot = state.inventories.get(InventorySlot.MAIN.name)
            if main_slot:
                for item in main_slot.items:
                    self._econ_state.inventory[item.name] = item.quantity
                    self._econ_state.inventory_quality[item.name] = item.quality

        # Fallback for legacy
        elif state.inventory:
            self._econ_state.inventory.update(state.inventory)

    @property
    def is_active(self) -> bool:
        return self._bio_state.is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._bio_state.is_active = value

    @property
    def gender(self) -> str:
        return self._bio_state.gender

    @property
    def parent_id(self) -> Optional[int]:
        return self._bio_state.parent_id

    @property
    def generation(self) -> int:
        return self._bio_state.generation

    @property
    def age(self) -> float:
        return self._bio_state.age

    @age.setter
    def age(self, value: float) -> None:
        self._bio_state.age = value

    @property
    def sex(self) -> str:
        """Biological sex (M/F). Used for reproduction and matching (Wave 4)."""
        return self._bio_state.sex

    @property
    def health_status(self) -> float:
        """Normalized health (0.0 to 1.0). (Wave 4)"""
        return self._bio_state.health_status

    @health_status.setter
    def health_status(self, value: float) -> None:
        self._bio_state.health_status = value

    @property
    def has_disease(self) -> bool:
        """Infection status requiring medical utility. (Wave 4)"""
        return self._bio_state.has_disease

    @has_disease.setter
    def has_disease(self, value: bool) -> None:
        self._bio_state.has_disease = value

    @property
    def spouse_id(self) -> Optional[int]:
        return self._bio_state.spouse_id

    @spouse_id.setter
    def spouse_id(self, value: Optional[int]) -> None:
        self._bio_state.spouse_id = value

    @property
    def children_ids(self) -> List[int]:
        return self._bio_state.children_ids

    def add_child(self, child_id: int) -> None:
        """Adds a child to the household's bio state."""
        if child_id not in self._bio_state.children_ids:
            self._bio_state.children_ids.append(child_id)

    @property
    def social_status(self) -> float:
        return self._social_state.social_status

    @social_status.setter
    def social_status(self, value: float) -> None:
        self._social_state.social_status = value

    @property
    def social_rank(self) -> float:
        return self._social_state.social_rank

    @social_rank.setter
    def social_rank(self, value: float) -> None:
        self._social_state.social_rank = value

    @property
    def conformity(self) -> float:
        return self._social_state.conformity

    @conformity.setter
    def conformity(self, value: float) -> None:
        self._social_state.conformity = value

    @property
    def is_employed(self) -> bool:
        return self._econ_state.is_employed

    @is_employed.setter
    def is_employed(self, value: bool) -> None:
        self._econ_state.is_employed = value

    @property
    def employer_id(self) -> Optional[int]:
        return self._econ_state.employer_id

    @employer_id.setter
    def employer_id(self, value: Optional[int]) -> None:
        self._econ_state.employer_id = value

    @property
    def labor_skill(self) -> float:
        return self._econ_state.labor_skill

    @labor_skill.setter
    def labor_skill(self, value: float) -> None:
        self._econ_state.labor_skill = value

    @property
    def inventory(self) -> Dict[str, float]:
        return self._econ_state.inventory

    @property
    def portfolio(self) -> Portfolio:
        return self._econ_state.portfolio

    @property
    def talent(self) -> Talent:
        return self._econ_state.talent

    @property
    def labor_income_this_tick(self) -> int:
        return self._econ_state.labor_income_this_tick_pennies

    @labor_income_this_tick.setter
    def labor_income_this_tick(self, value: int) -> None:
        self._econ_state.labor_income_this_tick_pennies = value

    @property
    def capital_income_this_tick(self) -> int:
        return self._econ_state.capital_income_this_tick_pennies

    @capital_income_this_tick.setter
    def capital_income_this_tick(self, value: int) -> None:
        self._econ_state.capital_income_this_tick_pennies = value

    @property
    def employment_start_tick(self) -> int:
        return self._econ_state.employment_start_tick

    @employment_start_tick.setter
    def employment_start_tick(self, value: int) -> None:
        self._econ_state.employment_start_tick = value

    def quit(self) -> None:
        """
        Executes the resignation process for the employee.
        Sets is_employed to False and clears employer_id.
        """
        self.is_employed = False
        self.employer_id = None

    @property
    def tick_analytics(self) -> AgentTickAnalyticsDTO:
        return AgentTickAnalyticsDTO(
            run_id=0,
            time=0,
            agent_id=self.id,
            labor_income_this_tick=self._econ_state.labor_income_this_tick_pennies,
            capital_income_this_tick=self._econ_state.capital_income_this_tick_pennies,
            consumption_this_tick=self._econ_state.consumption_expenditure_this_tick_pennies,
            utility_this_tick=None,
            savings_rate_this_tick=None
        )

    @property
    def personality(self) -> Personality:
        return self._social_state.personality

    @property
    def education_xp(self) -> float:
        return self._econ_state.education_xp

    @education_xp.setter
    def education_xp(self, value: float) -> None:
        self._econ_state.education_xp = value

    @property
    def education_level(self) -> int:
        return self._econ_state.education_level

    @education_level.setter
    def education_level(self, value: int) -> None:
        self._econ_state.education_level = value

    @property
    def expected_wage(self) -> int:
        return self._econ_state.expected_wage_pennies

    @expected_wage.setter
    def expected_wage(self, value: int) -> None:
        self._econ_state.expected_wage_pennies = value

    # --- Lifecycle & Needs Management ---

    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """
        Orchestrates Lifecycle, Needs, and Social Engines.
        Called by LifecycleManager.
        """
        if not self.is_active:
            return

        # Phase 4.1: Natural Decay of Insight
        current_insight = self._econ_state.market_insight
        decay_rate = getattr(self.config, "insight_decay_rate", 0.001)
        self._econ_state.market_insight = max(0.0, current_insight - decay_rate)

        # 1. Lifecycle Engine (Aging & Reproduction Check)
        lifecycle_input = LifecycleInputDTO(
            bio_state=self._bio_state,
            econ_state=self._econ_state,
            config=self.config,
            current_tick=current_tick
        )
        lifecycle_output = self.lifecycle_engine.process_tick(lifecycle_input)
        self._bio_state = lifecycle_output.bio_state
        self._cloning_requests = lifecycle_output.cloning_requests # Buffer requests

        # Death Handling (Push Model)
        if lifecycle_output.death_occurred:
            if self.demographic_manager:
                self.demographic_manager.register_death(self, cause="NATURAL")
                # Clear labor hours on death
                self.demographic_manager.update_labor_hours(self.gender, -self.last_labor_allocation)
            self.last_labor_allocation = 0.0
            self.is_active = False

        # 2. Needs Engine (Needs Decay & Prioritization)
        needs_input = NeedsInputDTO(
            bio_state=self._bio_state,
            econ_state=self._econ_state,
            social_state=self._social_state,
            config=self.config,
            current_tick=current_tick,
            goods_data=self.goods_info_map,
            market_data=market_data
        )
        needs_output = self.needs_engine.evaluate_needs(needs_input)
        self._bio_state = needs_output.bio_state
        self._prioritized_needs = needs_output.prioritized_needs # Buffer for Budgeting

        # 3. Social Engine (Status & Political)
        social_input = SocialInputDTO(
            social_state=self._social_state,
            econ_state=self._econ_state,
            bio_state=self._bio_state,
            all_items=self.get_all_items(),
            config=self.config,
            current_tick=current_tick,
            market_data=market_data
        )
        social_output = self.social_engine.update_status(social_input)
        self._social_state = social_output.social_state

        # Note: Work logic (EconComponent.work) was previously here.
        # It didn't modify state significantly except fatigue/income tracking.
        # If needed, it should be in NeedsEngine (Fatigue) or ConsumptionEngine (Work execution).
        # We rely on Market Execution for Income.

    # --- Decision Making ---

    @override
    def make_decision(
        self,
        input_dto: DecisionInputDTO
    ) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:

        market_snapshot = input_dto.market_snapshot
        current_time = input_dto.current_time
        macro_context = input_dto.macro_context

        # 1. AI Decision (Abstract Plan)
        # Prepare Context
        snapshot_dto = self.create_snapshot_dto()
        
        # Legacy compatibility state (if engines still need it)
        legacy_state_dto = self.create_state_dto()

        context = DecisionContext(
            state=legacy_state_dto,
            config=self.config,
            goods_data=input_dto.goods_data,
            market_data=input_dto.market_data,
            current_time=current_time,
            stress_scenario_config=input_dto.stress_scenario_config,
            market_snapshot=market_snapshot,
            government_policy=input_dto.government_policy,
            agent_registry=input_dto.agent_registry or {},
            market_context=input_dto.market_context
        )

        decision_output = self.decision_engine.make_decisions(context, macro_context)

        if hasattr(decision_output, "orders"):
            initial_orders = decision_output.orders
            chosen_tactic_tuple = decision_output.metadata
        else:
            initial_orders, chosen_tactic_tuple = decision_output

        # 2. Budget Engine (Planning)
        budget_input = BudgetInputDTO(
            econ_state=self._econ_state,
            prioritized_needs=self._prioritized_needs, # Populated by update_needs
            abstract_plan=initial_orders,
            market_snapshot=market_snapshot,
            config=self.config,
            current_tick=current_time,
            agent_id=self.id # Wave 4.3: Identity Pass-through
        )
        budget_output = self.budget_engine.allocate_budget(budget_input)

        self._econ_state = budget_output.econ_state
        budget_plan = budget_output.budget_plan
        housing_action = budget_output.housing_action

        # Execute Housing Action (Side Effect)
        if housing_action and input_dto.housing_system:
            # Dispatch to Housing System
            self._execute_housing_action(housing_action, input_dto.housing_system)

        # 3. Consumption Engine (Execution)
        consumption_input = ConsumptionInputDTO(
            econ_state=self._econ_state,
            bio_state=self._bio_state,
            budget_plan=budget_plan,
            market_snapshot=market_snapshot,
            config=self.config,
            current_tick=current_time,
            stress_scenario_config=input_dto.stress_scenario_config
        )
        consumption_output = self.consumption_engine.generate_orders(consumption_input)

        self._econ_state = consumption_output.econ_state
        self._bio_state = consumption_output.bio_state # Updated needs after consumption
        if consumption_output.social_state:
             self._social_state = consumption_output.social_state

        refined_orders = consumption_output.orders

        # Wave 4.3: Health Shock Labor Penalty
        # If agent is sick, they cannot work (Lost Labor).
        # We filter out any generated labor SELL orders.
        if self._bio_state.has_disease:
            refined_orders = [o for o in refined_orders if not (o.side == "SELL" and o.item_id == "labor")]
            # Also notify Demographics/Labor system if needed, or rely on delta below.

        # Labor Hour Tracking (Push Model)
        current_labor_hours = 0.0
        for order in refined_orders:
            if order.side == "SELL" and order.item_id == "labor":
                current_labor_hours += order.quantity

        delta = current_labor_hours - self.last_labor_allocation
        if delta != 0:
            if self.demographic_manager:
                self.demographic_manager.update_labor_hours(self.gender, delta)
            self.last_labor_allocation = current_labor_hours

        return refined_orders, chosen_tactic_tuple

    def _execute_housing_action(self, action: HousingActionDTO, housing_system: Any):
        """Helper to execute housing actions via connector."""
        self.housing_connector.execute_action(action, housing_system, self.id)

    # --- Other Interface Implementations ---

    # IPropertyOwner Implementation
    @property
    def owned_properties(self) -> List[int]:
        return self._econ_state.owned_properties

    def add_property(self, property_id: int) -> None:
        if property_id not in self._econ_state.owned_properties:
            self._econ_state.owned_properties.append(property_id)

    def remove_property(self, property_id: int) -> None:
        if property_id in self._econ_state.owned_properties:
            self._econ_state.owned_properties.remove(property_id)

    @property
    def residing_property_id(self) -> Optional[int]:
        return self._econ_state.residing_property_id

    @residing_property_id.setter
    def residing_property_id(self, value: Optional[int]) -> None:
        self._econ_state.residing_property_id = value

    @property
    def is_homeless(self) -> bool:
        return self._econ_state.is_homeless

    @is_homeless.setter
    def is_homeless(self, value: bool) -> None:
        self._econ_state.is_homeless = value

    @property
    def home_quality_score(self) -> float:
        return self._econ_state.home_quality_score

    @home_quality_score.setter
    def home_quality_score(self, value: float) -> None:
        self._econ_state.home_quality_score = value

    # IHousingTransactionParticipant Implementation
    @property
    def current_wage(self) -> int:
        return self._econ_state.current_wage_pennies

    @current_wage.setter
    def current_wage(self, value: int) -> None:
        self._econ_state.current_wage_pennies = value

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value

    @property
    @override
    def assets(self) -> int:
        return self._econ_state.wallet.get_balance(DEFAULT_CURRENCY)

    @property
    def balance_pennies(self) -> int:
        return self._econ_state.wallet.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.add(amount_pennies, currency=currency, memo="Deposit")

    @override
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.subtract(amount_pennies, currency=currency, memo="Withdraw")

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.add(amount, currency=currency, memo="Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.subtract(amount, currency=currency, memo="Withdraw")
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        return self.get_balance(DEFAULT_CURRENCY)

    @override
    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self._econ_state.wallet.get_balance(currency)

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> int:
        """Returns liquid assets in pennies (int)."""
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        """Returns total debt in pennies (int)."""
        # Household doesn't traditionally have debt in the same way Firms do here,
        # but we provide the method for protocol compliance.
        return 0

    @override
    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        return self._econ_state.wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        """
        Returns the total wealth in default currency estimation.
        TD-270: Standardized multi-currency summation.
        """
        balances = self._econ_state.wallet.get_all_balances()
        total = 0
        # For now, we assume 1:1 exchange rate as per spec draft for simple conversion.
        for amount in balances.values():
            total += amount
        return total

    @override
    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        return self._econ_state.wallet.get_all_balances()

    @override
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if slot != InventorySlot.MAIN: return False
        if quantity < 0: return False
        current = self._econ_state.inventory.get(item_id, 0.0)
        self._econ_state.inventory[item_id] = current + quantity
        
        existing_quality = self._econ_state.inventory_quality.get(item_id, 1.0)
        total_qty = current + quantity
        if total_qty > 0:
            new_avg_quality = ((current * existing_quality) + (quantity * quality)) / total_qty
            self._econ_state.inventory_quality[item_id] = new_avg_quality
        return True

    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if slot != InventorySlot.MAIN: return False
        if quantity < 0: return False
        current = self._econ_state.inventory.get(item_id, 0.0)
        if current < quantity: return False
        self._econ_state.inventory[item_id] = current - quantity
        if self._econ_state.inventory[item_id] <= 1e-9:
            del self._econ_state.inventory[item_id]
        return True

    @override
    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot != InventorySlot.MAIN: return 0.0
        return self._econ_state.inventory.get(item_id, 0.0)

    @override
    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot != InventorySlot.MAIN: return 0.0
        return self._econ_state.inventory_quality.get(item_id, 1.0)

    @override
    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        if slot != InventorySlot.MAIN: return {}
        return self._econ_state.inventory.copy()

    @override
    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        if slot != InventorySlot.MAIN: return
        self._econ_state.inventory.clear()
        self._econ_state.inventory_quality.clear()

    @override
    def get_agent_data(self) -> Dict[str, Any]:
        return {
            "assets": self._econ_state.wallet.get_all_balances(),
            "needs": self._bio_state.needs.copy(),
            "inventory": self._econ_state.inventory.copy(),
            "is_active": self.is_active,
            "is_employed": self._econ_state.is_employed,
            "labor_skill": self._econ_state.labor_skill,
            "current_wage": self._econ_state.current_wage_pennies,
            "social_status": self._social_state.social_status,
            "gender": self.gender,
            "age": self.age,
            "home_quality_score": self._econ_state.home_quality_score,
            "children_count": len(self.children_ids),
            "education_level": self._econ_state.education_level,
            "education_xp": self._econ_state.education_xp,
            "market_insight": self._econ_state.market_insight,
            "major": self._econ_state.major,
            "aptitude": self._econ_state.aptitude
        }

    def get_pre_state_data(self) -> Dict[str, Any]:
        return self._pre_state_data

    def update_pre_state_data(self):
        self._pre_state_data = self.get_agent_data()

    def update_learning(self, context: LearningUpdateContext) -> None:
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]
        if hasattr(self.decision_engine, 'ai_engine'):
             insight_gain = self.decision_engine.ai_engine.update_learning_v2(
                reward=reward,
                next_agent_data=next_agent_data,
                next_market_data=next_market_data,
            )
             # Phase 4.1: Active Learning (Insight Gain from Surprise)
             # Map TD-Error (insight_gain) to market_insight increase
             multiplier = getattr(self.config, "insight_learning_multiplier", 5.0)
             gain = insight_gain * multiplier
             current_insight = self._econ_state.market_insight
             self._econ_state.market_insight = min(1.0, current_insight + gain)

    # --- Helpers ---

    def create_snapshot_dto(self) -> HouseholdSnapshotDTO:
        return HouseholdSnapshotDTO(
            id=self.id,
            bio_state=self._bio_state.copy(),
            econ_state=self._econ_state.copy(),
            social_state=self._social_state.copy(),
            major=self._econ_state.major
        )

    def create_state_dto(self) -> HouseholdStateDTO:
        """Legacy DTO creation."""
        # Convert DurableAssetDTOs to dicts for legacy compatibility
        durable_assets_legacy = []
        for d in self._econ_state.durable_assets:
            durable_assets_legacy.append({
                'item_id': d.item_id,
                'quality': d.quality,
                'remaining_life': d.remaining_life
            })

        # Map fields manually or use partial data
        return HouseholdStateDTO(
            id=self.id,
            assets=self._econ_state.wallet.get_all_balances(),
            inventory=self._econ_state.inventory.copy(),
            needs=self._bio_state.needs.copy(),
            preference_asset=self.preference_asset,
            preference_social=self.preference_social,
            preference_growth=self.preference_growth,
            personality=self._social_state.personality,
            durable_assets=durable_assets_legacy,
            expected_inflation=self._econ_state.expected_inflation,
            is_employed=self._econ_state.is_employed,
            current_wage_pennies=self._econ_state.current_wage_pennies,
            wage_modifier=self._econ_state.wage_modifier,
            is_homeless=self._econ_state.is_homeless,
            residing_property_id=self._econ_state.residing_property_id,
            owned_properties=self._econ_state.owned_properties,
            portfolio_holdings=self._econ_state.portfolio.to_legacy_dict(),
            risk_aversion=self.risk_aversion,
            agent_data=self.get_agent_data(),
            market_insight=self._econ_state.market_insight,
            major=self._econ_state.major,
            perceived_prices=self._econ_state.perceived_avg_prices,
            conformity=self._social_state.conformity,
            social_rank=self._social_state.social_rank,
            approval_rating=self._social_state.approval_rating,
            optimism=self._social_state.optimism,
            ambition=self._social_state.ambition,
            talent_score=self._econ_state.talent.base_learning_rate,
            shadow_reservation_wage_pennies=self._econ_state.shadow_reservation_wage_pennies
        )


    def initialize_demographics(
        self,
        age: float,
        gender: str,
        parent_id: Optional[int],
        generation: int,
        spouse_id: Optional[int] = None
    ) -> None:
        """
        Explicitly initializes demographic state.
        Used by DemographicManager during agent creation.
        """
        self._bio_state.age = age
        self._bio_state.gender = gender
        self._bio_state.parent_id = parent_id
        self._bio_state.generation = generation
        self._bio_state.spouse_id = spouse_id

    def initialize_personality(self, personality: Personality, desire_weights: Dict[str, float]) -> None:
        """
        Explicitly initializes personality and desire weights.
        Used by DemographicManager and AITrainingManager (during brain inheritance).
        """
        self._social_state.personality = personality
        self._social_state.desire_weights = desire_weights

    # Legacy Mixin Methods Stubs/Implementations

    def add_education_xp(self, xp: float) -> None:
        self._econ_state.education_xp += xp
        # Delegate skill calculation to LifecycleEngine (Logic Placement Refactor)
        talent_factor = self._econ_state.talent.base_learning_rate
        new_skill = self.lifecycle_engine.calculate_new_skill_level(
            self._econ_state.education_xp, talent_factor
        )
        self._econ_state.labor_skill = new_skill

    def add_durable_asset(self, asset: Dict[str, Any]) -> None:
        # Convert dictionary to DurableAssetDTO for internal storage
        dto = DurableAssetDTO(
            item_id=asset['item_id'],
            quality=asset['quality'],
            remaining_life=asset['remaining_life']
        )
        self._econ_state.durable_assets.append(dto)

    def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional[StressScenarioConfig] = None, current_tick: int = 0) -> None:
        """
        Delegates to BeliefEngine for updating price beliefs.
        """
        input_dto = BeliefInputDTO(
            current_tick=current_tick,
            perceived_prices=self._econ_state.perceived_avg_prices,
            expected_inflation=self._econ_state.expected_inflation,
            price_history=self._econ_state.price_history,
            adaptation_rate=self._econ_state.adaptation_rate,
            goods_info_map=self.goods_info_map,
            config=self.config,
            market_data=market_data,
            stress_scenario_config=stress_scenario_config
        )

        result = self.belief_engine.update_beliefs(input_dto)

        # Update state with results
        self._econ_state.perceived_avg_prices = result.new_perceived_prices
        self._econ_state.expected_inflation = result.new_expected_inflation
        # price_history is updated in-place by the engine via the DTO reference

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        # Delegate to ConsumptionEngine
        new_social, new_econ, result_dto = self.consumption_engine.apply_leisure_effect(
            leisure_hours,
            consumed_items,
            self._social_state,
            self._econ_state,
            self._bio_state,
            self.config
        )
        self._social_state = new_social
        self._econ_state = new_econ
        return result_dto

    def consume(self, item_id: str, amount: float, current_tick: int) -> None:
        """
        Consumes an item from inventory and updates consumption stats.
        Restored legacy method used by CommerceSystem.
        """
        if amount <= 0: return

        # Remove from inventory
        available = self.get_quantity(item_id)
        to_remove = min(available, amount)

        if to_remove > 0:
            self.remove_item(item_id, to_remove)

            # Check if this item is a durable asset and remove it if so
            # This logic is imperfect as 'consume' implies using up, but for durables it might mean 'using'
            # However, if 'consume' removes it, we should probably check durable assets too.
            # But durable assets are separate list. remove_item handles inventory dict.
            # If consumption removes from inventory, it doesn't touch durable_assets list unless explicit.
            # Durable assets are usually added to list upon purchase and stay there until decay.
            # 'Consume' here likely means 'eat' or 'use up single use'.
            # So we don't touch durable assets list here.

            # Update Econ State
            # Note: We track quantity here. Utility is calculated elsewhere or implied.
            self._econ_state.current_consumption += to_remove
            if item_id == "basic_food" or item_id == "luxury_food":
                 self._econ_state.current_food_consumption += to_remove

            # Phase 4.1: Service Boosting (Education)
            if item_id == "education_service":
                # Boost insight by constant per unit consumed
                boost = getattr(self.config, "education_boost_amount", 0.05)
                current_insight = self._econ_state.market_insight
                self._econ_state.market_insight = min(1.0, current_insight + boost * to_remove)

            # Wave 4.3: Health Recovery (Medical)
            if item_id == "medical_service":
                self._bio_state.has_disease = False
                self._bio_state.health_status = 1.0
                self.logger.info(f"HEALTH_CURED | Agent {self.id} cured of disease via medical service.")

    def record_consumption(self, amount: float, is_food: bool = False) -> None:
        """Records consumption statistics (called by Registry/Handlers)."""
        self._econ_state.current_consumption += amount
        if is_food:
            self._econ_state.current_food_consumption += amount

    def add_labor_income(self, amount: int) -> None:
        """Adds to labor income tracker (called by Handlers)."""
        self._econ_state.labor_income_this_tick_pennies += amount

    def add_consumption_expenditure(self, amount: int, item_id: Optional[str] = None) -> None:
        """
        Adds to consumption expenditure tracker (called by Handlers).
        Implements IConsumptionTracker.
        """
        self._econ_state.consumption_expenditure_this_tick_pennies += amount

        # Simple heuristic for food identification or use goods data
        is_food = False
        if item_id:
             if "food" in item_id.lower():
                 is_food = True
             elif item_id in self.goods_info_map and self.goods_info_map[item_id].get("type") == "food":
                 is_food = True

        if is_food:
            self._econ_state.food_expenditure_this_tick_pennies += amount

    def trigger_emergency_liquidation(self) -> List[Order]:
        """
        WO-167: Trigger panic selling/liquidation for distress.
        Used by LifecycleManager.
        """
        input_dto = PanicSellingInputDTO(
            owner_id=self.id,
            portfolio_holdings=self._econ_state.portfolio.holdings,
            inventory=self._econ_state.inventory,
            market_data=None # Not strictly needed for market sell orders in current implementation
        )

        result = self.crisis_engine.evaluate_distress(input_dto)
        return result.orders

    def reset_tick_state(self) -> None:
        """
        Resets tick-level financial accumulators to zero.
        Adheres to the "Late-Reset Principle".
        """
        self._econ_state.labor_income_this_tick_pennies = 0
        self._econ_state.capital_income_this_tick_pennies = 0
        self._econ_state.consumption_expenditure_this_tick_pennies = 0
        self._econ_state.food_expenditure_this_tick_pennies = 0
        self._econ_state.current_consumption = 0.0
        self._econ_state.current_food_consumption = 0.0
        self.logger.debug(
            f"TICK_RESET | Agent {self.id} tick state has been reset.",
            extra={"agent_id": self.id, "tags": ["lifecycle", "reset"]}
        )

    # --- IVoter Implementation ---
    def cast_vote(self, current_tick: int, government_state: Any) -> VoteRecordDTO:
        # 1. Calculate Utility Gap / Approval
        # We use approval_rating from SocialState which tracks satisfaction
        approval_value = self._social_state.approval_rating

        # 2. Identify Grievance
        primary_grievance = "NONE"
        if approval_value < 0.4:
            # Check financial stress
            liquid_assets = self.get_liquid_assets()
            if liquid_assets < 1000: # Poverty line in pennies
                 primary_grievance = "POVERTY"
            # Check Tax (if gov state available)
            elif hasattr(government_state, 'income_tax_rate') and government_state.income_tax_rate > 0.2:
                 primary_grievance = "HIGH_TAX"
            # Check Inflation (heuristic)
            elif self._econ_state.expected_inflation.get("CPI", 0.0) > 0.05:
                 primary_grievance = "INFLATION"

        # 3. Calculate Weight (Plutocracy Factor)
        # Base 1.0. Multiplied by Social Status (0-1 approx) and Wealth (log).
        wealth_factor = math.log(max(1.0, self.get_liquid_assets() + 1.0), 10)
        weight = 1.0 * (1.0 + self._social_state.social_status) * wealth_factor

        return VoteRecordDTO(
            agent_id=self.id,
            tick=current_tick,
            approval_value=approval_value,
            primary_grievance=primary_grievance,
            political_weight=weight
        )

    def get_persistence_dto(self) -> HouseholdPersistenceDTO:
        snapshot = self.create_snapshot_dto()
        return HouseholdPersistenceDTO(
            snapshot=snapshot,
            distress_tick_counter=self.distress_tick_counter,
            credit_frozen_until_tick=self.credit_frozen_until_tick
        )

    def restore_from_persistence_dto(self, dto: HouseholdPersistenceDTO):
        """Restores state from a persistence DTO."""
        self.distress_tick_counter = dto.distress_tick_counter
        self.credit_frozen_until_tick = dto.credit_frozen_until_tick

        self._bio_state = dto.snapshot.bio_state
        self._econ_state = dto.snapshot.econ_state
        self._social_state = dto.snapshot.social_state
