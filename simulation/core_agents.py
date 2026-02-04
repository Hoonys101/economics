from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
import logging
from logging import Logger
from collections import deque, defaultdict
import random
import copy

from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order, Skill, Talent
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)
from simulation.dtos import DecisionContext, FiscalContext, MacroFinancialContext, DecisionInputDTO

from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.portfolio import Portfolio

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode
from modules.finance.wallet.wallet import Wallet
import simulation

# New Components
from modules.household.bio_component import BioComponent
from modules.household.econ_component import EconComponent
from modules.household.social_component import SocialComponent
from modules.household.consumption_manager import ConsumptionManager
from modules.household.decision_unit import DecisionUnit
from modules.household.political_component import PoliticalComponent
from modules.household.dtos import (
    HouseholdStateDTO, CloningRequestDTO, EconContextDTO,
    BioStateDTO, EconStateDTO, SocialStateDTO,
    HouseholdSnapshotDTO
)
from modules.household.services import HouseholdSnapshotAssembler
from modules.household.api import (
    OrchestrationContextDTO
)

# Mixins
from modules.household.mixins._properties import HouseholdPropertiesMixin
from modules.household.mixins._financials import HouseholdFinancialsMixin
from modules.household.mixins._lifecycle import HouseholdLifecycleMixin
from modules.household.mixins._reproduction import HouseholdReproductionMixin
from modules.household.mixins._state_access import HouseholdStateAccessMixin

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class Household(
    HouseholdPropertiesMixin,
    HouseholdFinancialsMixin,
    HouseholdLifecycleMixin,
    HouseholdReproductionMixin,
    HouseholdStateAccessMixin,
    BaseAgent,
    ILearningAgent
):
    """
    Household Agent (Facade).
    Delegates Bio/Econ/Social logic to specialized stateless components.
    State is held in internal DTOs.
    """

    def __init__(
        self,
        id: int,
        talent: Talent,
        goods_data: List[Dict[str, Any]],
        initial_assets: float,
        initial_needs: Dict[str, float],
        decision_engine: BaseDecisionEngine,
        value_orientation: str,
        personality: Personality,
        config_dto: HouseholdConfigDTO,
        loan_market: Optional[LoanMarket] = None,
        risk_aversion: float = 1.0,
        logger: Optional[Logger] = None,
        # Demographics
        initial_age: Optional[float] = None,
        gender: Optional[str] = None,
        parent_id: Optional[int] = None,
        generation: Optional[int] = None,
        initial_assets_record: Optional[float] = None,  # WO-124: Explicit record of intended assets
        **kwargs,
    ) -> None:
        self.config = config_dto

        # --- Value Orientation (3 Pillars) ---
        mapping = self.config.value_orientation_mapping
        prefs = mapping.get(
            value_orientation,
            {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        )
        self.preference_asset = prefs["preference_asset"]
        self.preference_social = prefs["preference_social"]
        self.preference_growth = prefs["preference_growth"]

        # Initialize Logger early
        self.logger = logger if logger else logging.getLogger(f"Household_{id}")

        # --- Initialize Components (Stateless) ---
        self.bio_component = BioComponent()
        self.econ_component = EconComponent()
        self.social_component = SocialComponent()
        self.consumption_manager = ConsumptionManager()
        self.decision_unit = DecisionUnit()
        self.political_component = PoliticalComponent(personality)

        # --- Initialize Internal State DTOs ---

        # Bio State
        self._bio_state = BioStateDTO(
            id=id,
            age=initial_age if initial_age is not None else random.uniform(*self.config.initial_household_age_range),
            gender=gender if gender is not None else random.choice(["M", "F"]),
            generation=generation if generation is not None else 0,
            is_active=True,
            needs=initial_needs.copy(),
            parent_id=parent_id
        )

        # Econ State
        price_memory_len = int(self.config.price_memory_length)
        wage_memory_len = int(self.config.wage_memory_length)
        ticks_per_year = int(self.config.ticks_per_year)

        # Initial Perceived Prices
        perceived_prices = {}
        for g in goods_data:
             perceived_prices[g["id"]] = g.get("initial_price", 10.0)

        # Adaptation Rate
        adaptation_rate = self.config.adaptation_rate_normal
        if personality == Personality.IMPULSIVE:
             adaptation_rate = self.config.adaptation_rate_impulsive
        elif personality == Personality.CONSERVATIVE:
             adaptation_rate = self.config.adaptation_rate_conservative

        # WO-054: Aptitude
        raw_aptitude = random.gauss(*self.config.initial_aptitude_distribution)
        aptitude = max(0.0, min(1.0, raw_aptitude))

        initial_assets_dict = {DEFAULT_CURRENCY: float(initial_assets)}

        self._econ_state = EconStateDTO(
            wallet=Wallet(id, initial_assets_dict),
            inventory={},
            inventory_quality={},
            durable_assets=[],
            portfolio=Portfolio(id),
            is_employed=False,
            employer_id=None,
            current_wage=0.0,
            wage_modifier=1.0,
            labor_skill=1.0,
            education_xp=0.0,
            education_level=0,
            expected_wage=10.0,
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
            shadow_reservation_wage=0.0,
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
            labor_income_this_tick=0.0,
            capital_income_this_tick=0.0,
            initial_assets_record=initial_assets_record if initial_assets_record is not None else initial_assets
        )

        # Social State
        # Conformity
        conformity_ranges = self.config.conformity_ranges
        c_min, c_max = conformity_ranges.get(personality.name, conformity_ranges.get(None, (0.3, 0.7)))
        conformity = random.uniform(c_min, c_max)

        # Quality Preference
        mean_assets = self.config.initial_household_assets_mean
        is_wealthy = initial_assets > mean_assets * 1.5
        is_poor = initial_assets < mean_assets * 0.5

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

        # Initialize Desire Weights in SocialState
        if personality in [Personality.MISER, Personality.CONSERVATIVE]:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 1.5, "social": 0.5, "improvement": 0.5, "quality": 1.0}
        elif personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 0.5, "social": 1.5, "improvement": 0.5, "quality": 1.0}
        elif personality == Personality.GROWTH_ORIENTED:
            self._social_state.desire_weights = {"survival": 1.0, "asset": 0.5, "social": 0.5, "improvement": 1.5, "quality": 1.0}
        else:
             self._social_state.desire_weights = {"survival": 1.0, "asset": 1.0, "social": 1.0, "improvement": 1.0, "quality": 1.0}

        self.goods_info_map = {g["id"]: g for g in goods_data}
        self.risk_aversion = risk_aversion

        # WO-167: Grace Protocol (Distress Mode)
        self.distress_tick_counter: int = 0

        # Setup Decision Engine
        decision_engine.loan_market = loan_market
        decision_engine.logger = self.logger

        super().__init__(
            id,
            initial_assets,
            initial_needs,
            decision_engine,
            value_orientation,
            name=f"Household_{id}",
            logger=logger,
            **kwargs,
        )

        # Ensure BaseAgent uses the same wallet as EconStateDTO
        self._wallet = self._econ_state.wallet

        # WO-123: Memory Logging - Record Birth
        if self.memory_v2:
            from modules.memory.V2.dtos import MemoryRecordDTO
            record = MemoryRecordDTO(
                tick=0,
                agent_id=self.id,
                event_type="BIRTH",
                data={"initial_assets": initial_assets}
            )
            self.memory_v2.add_record(record)

        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized (Decomposed).",
            extra={"tags": ["household_init"]}
        )

    @override
    def make_decision(
        self,
        input_dto: DecisionInputDTO
    ) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:

        # Unpack input_dto
        # markets = input_dto.markets # Removed TD-194
        goods_data = input_dto.goods_data
        market_data = input_dto.market_data
        current_time = input_dto.current_time
        fiscal_context = input_dto.fiscal_context
        macro_context = input_dto.macro_context
        stress_scenario_config = input_dto.stress_scenario_config
        market_snapshot = input_dto.market_snapshot
        government_policy = input_dto.government_policy
        agent_registry = input_dto.agent_registry or {}

        # 0. Update Social Status (Before Decision)
        self._social_state = self.social_component.calculate_social_status(
            self._social_state,
            self._econ_state.assets,
            self._econ_state.inventory,
            self.config
        )

        # WO-103: Purity Guard - Update Wage Dynamics
        self._econ_state = self.econ_component.update_wage_dynamics(
            self._econ_state, self.config, self._econ_state.is_employed
        )

        # 1. Prepare DTOs
        # [TD-194] Use Snapshot DTO
        snapshot_dto = self.create_snapshot_dto()
        
        # WO-103: Purity Guard - Prepare Config DTO
        # self.config is already the DTO.
        config_dto = self.config

        # Backward compatibility for legacy DecisionEngine if it expects HouseholdStateDTO
        # We can construct it from snapshot if needed, or pass snapshot if engine is updated.
        # Ideally engines should be updated, but for now we might need to pass legacy DTO to context
        # if DecisionContext expects it.
        legacy_state_dto = self.create_state_dto()

        context = DecisionContext(
            state=legacy_state_dto,
            config=config_dto,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            stress_scenario_config=stress_scenario_config,
            market_snapshot=market_snapshot,
            government_policy=government_policy,
            agent_registry=agent_registry or {}
        )

        # 2. Run Decision Engine (Logic moved from DecisionUnit.make_decision)
        decision_output = self.decision_engine.make_decisions(context, macro_context)

        # Handle both DTO and legacy Tuple
        if hasattr(decision_output, "orders"):
            initial_orders = decision_output.orders
            chosen_tactic_tuple = decision_output.metadata
        else:
            initial_orders, chosen_tactic_tuple = decision_output

        # 3. Construct Orchestration DTOs (ACL)

        # Use valid snapshot from input
        orchestration_context = OrchestrationContextDTO(
            market_snapshot=market_snapshot,
            current_time=current_time,
            stress_scenario_config=stress_scenario_config,
            config=self.config,
            household_state=snapshot_dto,
            housing_system=input_dto.housing_system
        )

        # 4. Delegate to DecisionUnit (Stateless)
        self._econ_state, refined_orders = self.decision_unit.orchestrate_economic_decisions(
            state=self._econ_state,
            context=orchestration_context,
            initial_orders=initial_orders
        )

        return refined_orders, chosen_tactic_tuple
