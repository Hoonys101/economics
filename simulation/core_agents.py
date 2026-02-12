from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
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

from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.portfolio import Portfolio
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine, IOrchestratorAgent, IInventoryHandler, ISensoryDataProvider, AgentSensorySnapshotDTO, InventorySlot, ItemDTO, InventorySlotDTO, AgentStateDTO

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent
from modules.finance.api import IFinancialAgent, ICreditFrozen
from modules.simulation.api import IEducated
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.wallet.wallet import Wallet
from modules.common.interfaces import IPropertyOwner, IInvestor
import simulation

# Engines
from modules.household.engines.lifecycle import LifecycleEngine
from modules.household.engines.needs import NeedsEngine
from modules.household.engines.social import SocialEngine
from modules.household.engines.budget import BudgetEngine
from modules.household.engines.consumption_engine import ConsumptionEngine

# API & DTOs
from modules.household.api import (
    LifecycleInputDTO, NeedsInputDTO, SocialInputDTO, BudgetInputDTO, ConsumptionInputDTO,
    PrioritizedNeed, BudgetPlan, HousingActionDTO, CloningRequestDTO
)
from modules.household.dtos import (
    HouseholdStateDTO, EconContextDTO,
    BioStateDTO, EconStateDTO, SocialStateDTO,
    HouseholdSnapshotDTO
)
from modules.analytics.dtos import AgentTickAnalyticsDTO
from modules.household.services import HouseholdSnapshotAssembler
from modules.household.mixins._state_access import HouseholdStateAccessMixin

# Protocols
from modules.hr.api import IEmployeeDataProvider

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class HouseholdStateContainer:
    """Helper to expose Household state components."""
    def __init__(self, agent: "Household"):
        self._agent = agent

    @property
    def econ_state(self) -> EconStateDTO:
        return self._agent._econ_state

    @property
    def bio_state(self) -> BioStateDTO:
        return self._agent._bio_state

    @property
    def social_state(self) -> SocialStateDTO:
        return self._agent._social_state

class Household(
    ILearningAgent,
    IEmployeeDataProvider,
    IEducated,
    IFinancialAgent,
    IOrchestratorAgent,
    ICreditFrozen,
    IInventoryHandler,
    ISensoryDataProvider,
    IPropertyOwner,
    IInvestor,
    HouseholdStateAccessMixin
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
        **kwargs,
    ) -> None:
        self.config = config_dto
        self.logger = core_config.logger

        # --- Initialize Engines (Stateless) ---
        self.lifecycle_engine = LifecycleEngine()
        self.needs_engine = NeedsEngine()
        self.social_engine = SocialEngine()
        self.budget_engine = BudgetEngine()
        self.consumption_engine = ConsumptionEngine()

        # --- Initialize Internal State DTOs ---

        # 1. Bio State
        self._bio_state = BioStateDTO(
            id=core_config.id,
            age=initial_age if initial_age is not None else random.uniform(*self.config.initial_household_age_range),
            gender=gender if gender is not None else random.choice(["M", "F"]),
            generation=generation if generation is not None else 0,
            is_active=True,
            needs=core_config.initial_needs.copy(),
            parent_id=parent_id
        )

        # 2. Econ State
        price_memory_len = int(self.config.price_memory_length)
        wage_memory_len = int(self.config.wage_memory_length)
        ticks_per_year = int(self.config.ticks_per_year)

        perceived_prices = {}
        for g in goods_data:
             perceived_prices[g["id"]] = g.get("initial_price", 10.0)

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

        # Scale mean assets for check? Assuming config mean is in dollars, convert to pennies for check?
        # Or assume config is updated? Config is usually external.
        # Let's assume config remains float dollars for inputs, we convert to pennies.
        mean_assets_pennies = int(self.config.initial_household_assets_mean * 100)
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
    def spouse_id(self) -> Optional[int]:
        return self._bio_state.spouse_id

    @spouse_id.setter
    def spouse_id(self, value: Optional[int]) -> None:
        self._bio_state.spouse_id = value

    @property
    def children_ids(self) -> List[int]:
        return self._bio_state.children_ids

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
    def tick_analytics(self) -> AgentTickAnalyticsDTO:
        return AgentTickAnalyticsDTO(
            run_id=0,
            time=0,
            agent_id=self.id,
            labor_income_this_tick=self._econ_state.labor_income_this_tick_pennies,
            capital_income_this_tick=self._econ_state.capital_income_this_tick_pennies,
            consumption_this_tick=self._econ_state.current_consumption,
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
            current_tick=current_time
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

        return refined_orders, chosen_tactic_tuple

    def _execute_housing_action(self, action: HousingActionDTO, housing_system: Any):
        """Helper to execute housing actions via system."""
        # Convert back to dict expected by system if needed, or update system to accept DTO
        # Existing HousingSystem likely expects specific method calls.
        if action.action_type == "INITIATE_PURCHASE":
            if hasattr(housing_system, 'initiate_purchase'):
                # Assuming initiate_purchase takes a dict similar to HousingPurchaseDecisionDTO
                # logic in HousingPlanner returns HousingPurchaseDecisionDTO (TypedDict).
                # housing_system.initiate_purchase expects HousingPurchaseDecisionDTO.
                decision_dict = {
                    "decision_type": "INITIATE_PURCHASE",
                    "target_property_id": int(action.property_id),
                    "offer_price": int(action.offer_price), # Ensure int pennies
                    "down_payment_amount": int(action.down_payment_amount) # Ensure int pennies
                }
                housing_system.initiate_purchase(decision_dict, buyer_id=self.id)

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

    @override
    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        raise NotImplementedError("Direct deposit is deprecated. Use SettlementSystem.transfer.")

    @override
    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        raise NotImplementedError("Direct withdraw is deprecated. Use SettlementSystem.transfer.")

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.add(amount, currency=currency, memo="Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._econ_state.wallet.subtract(amount, currency=currency, memo="Withdraw")

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        return self._econ_state.wallet.get_balance(currency)

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
            "children_count": len(self.children_ids)
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
             self.decision_engine.ai_engine.update_learning_v2(
                reward=reward,
                next_agent_data=next_agent_data,
                next_market_data=next_market_data,
            )

    # --- Helpers ---

    def create_snapshot_dto(self) -> HouseholdSnapshotDTO:
        return HouseholdSnapshotDTO(
            id=self.id,
            bio_state=self._bio_state.copy(),
            econ_state=self._econ_state.copy(),
            social_state=self._social_state.copy()
        )

    def create_state_dto(self) -> HouseholdStateDTO:
        """Legacy DTO creation."""
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
            durable_assets=self._econ_state.durable_assets,
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
            perceived_prices=self._econ_state.perceived_avg_prices,
            conformity=self._social_state.conformity,
            social_rank=self._social_state.social_rank,
            approval_rating=self._social_state.approval_rating,
            optimism=self._social_state.optimism,
            ambition=self._social_state.ambition
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
        self._econ_state.durable_assets.append(asset)

    def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional[StressScenarioConfig] = None) -> None:
        # Legacy EconComponent.update_perceived_prices logic.
        # Ideally should be in BudgetEngine or similar.
        # Implementing here for now to avoid breakage.
        goods_market = market_data.get("goods_market")
        if not goods_market: return

        adaptive_rate = self._econ_state.adaptation_rate
        if stress_scenario_config and stress_scenario_config.is_active:
            if stress_scenario_config.scenario_name == 'hyperinflation':
                if hasattr(stress_scenario_config, "inflation_expectation_multiplier"):
                     adaptive_rate *= stress_scenario_config.inflation_expectation_multiplier

        for item_id, good in self.goods_info_map.items():
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")
            if actual_price is not None and actual_price > 0:
                history = self._econ_state.price_history[item_id]
                if history:
                    last_price = history[-1]
                    if last_price > 0:
                        inflation_t = (actual_price - last_price) / last_price
                        old_expect = self._econ_state.expected_inflation.get(item_id, 0.0)
                        new_expect = old_expect + adaptive_rate * (inflation_t - old_expect)
                        self._econ_state.expected_inflation[item_id] = new_expect

                history.append(actual_price)

                old_perceived_price = self._econ_state.perceived_avg_prices.get(item_id, actual_price)
                update_factor = self.config.perceived_price_update_factor
                new_perceived_price = (update_factor * actual_price) + ((1 - update_factor) * old_perceived_price)
                self._econ_state.perceived_avg_prices[item_id] = new_perceived_price

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

            # Update Econ State
            # Note: We track quantity here. Utility is calculated elsewhere or implied.
            self._econ_state.current_consumption += to_remove
            if item_id == "basic_food" or item_id == "luxury_food":
                 self._econ_state.current_food_consumption += to_remove

    def record_consumption(self, amount: float, is_food: bool = False) -> None:
        """Records consumption statistics (called by Registry/Handlers)."""
        self._econ_state.current_consumption += amount
        if is_food:
            self._econ_state.current_food_consumption += amount

    def add_labor_income(self, amount: int) -> None:
        """Adds to labor income tracker (called by Handlers)."""
        self._econ_state.labor_income_this_tick_pennies += amount

    def trigger_emergency_liquidation(self) -> List[Order]:
        """
        WO-167: Trigger panic selling/liquidation for distress.
        Used by LifecycleManager.
        """
        # Logic similar to ConsumptionEngine Panic Selling, but triggered externally.
        orders = []
        # Sell stocks
        for firm_id, share in self._econ_state.portfolio.holdings.items():
             if share.quantity > 0:
                 stock_order = Order(
                     agent_id=self._econ_state.portfolio.owner_id,
                     side="SELL",
                     item_id=f"stock_{firm_id}",
                     quantity=share.quantity,
                     price_limit=0.0,
                     market_id="stock_market"
                 )
                 orders.append(stock_order)
        # Sell Inventory?
        for item_id, qty in self._econ_state.inventory.items():
            if qty > 0:
                # Assuming can sell goods
                pass
        return orders

    def reset_tick_state(self) -> None:
        """
        Resets tick-level financial accumulators to zero.
        Adheres to the "Late-Reset Principle".
        """
        self._econ_state.labor_income_this_tick_pennies = 0
        self._econ_state.capital_income_this_tick_pennies = 0
        self._econ_state.current_consumption = 0.0
        self._econ_state.current_food_consumption = 0.0
        self.logger.debug(
            f"TICK_RESET | Agent {self.id} tick state has been reset.",
            extra={"agent_id": self.id, "tags": ["lifecycle", "reset"]}
        )
