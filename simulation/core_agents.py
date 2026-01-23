from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
import logging
from logging import Logger
from collections import deque, defaultdict
import random

from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order, Skill, Talent
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)
from simulation.core_markets import Market
from simulation.dtos import DecisionContext, LeisureEffectDTO, LeisureType, MacroFinancialContext
from simulation.portfolio import Portfolio

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent

# New Components
from modules.household.bio_component import BioComponent
from modules.household.econ_component import EconComponent
from modules.household.social_component import SocialComponent
from modules.household.dtos import HouseholdStateDTO, CloningRequestDTO, EconContextDTO

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class Household(BaseAgent, ILearningAgent):
    """
    Household Agent (Facade).
    Delegates Bio/Econ/Social logic to specialized components.
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
        config_module: Any,
        loan_market: Optional[LoanMarket] = None,
        risk_aversion: float = 1.0,
        logger: Optional[Logger] = None,
        # Demographics
        initial_age: Optional[float] = None,
        gender: Optional[str] = None,
        parent_id: Optional[int] = None,
        generation: Optional[int] = None,
    ) -> None:
        self.id = id # Initialize ID early for components
        # --- Core Attributes ---
        self.talent = talent
        self.config_module = config_module
        self.risk_aversion = risk_aversion
        self.personality = personality
        self.goods_info_map: Dict[str, Dict[str, Any]] = {
            g["id"]: g for g in goods_data
        }

        # --- Value Orientation (3 Pillars) ---
        mapping = getattr(config_module, "VALUE_ORIENTATION_MAPPING", {})
        prefs = mapping.get(
            value_orientation,
            {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        )
        self.preference_asset = prefs["preference_asset"]
        self.preference_social = prefs["preference_social"]
        self.preference_growth = prefs["preference_growth"]

        # Initialize Logger early for components
        self.logger = logger if logger else logging.getLogger(f"Household_{id}")

        # --- Initialize Components ---
        self.bio_component = BioComponent(
            self, config_module, initial_age, gender, parent_id, generation
        )
        self.econ_component = EconComponent(self, config_module)
        self.social_component = SocialComponent(self, config_module, personality, initial_assets)

        # --- Legacy & Compatibility Attributes ---
        # Some attributes are kept on Facade if they are deeply intertwined or purely transient
        self.initial_assets_record = initial_assets
        self.credit_frozen_until_tick: int = 0

        # WO-054: Aptitude (Hidden Trait) - Kept on Facade as it's intrinsic
        raw_aptitude = random.gauss(0.5, 0.15)
        self.aptitude: float = max(0.0, min(1.0, raw_aptitude))

        # Initialize Econ Component Initial State
        self.econ_component._assets = initial_assets
        # Skills & Inventory are managed by Econ Component primarily, but accessed via Facade
        # Currently BaseAgent has self.inventory. We should sync or delegate.
        # EconComponent has its own _inventory. BaseAgent's inventory is initialized empty.
        # We will use EconComponent's inventory as the source of truth,
        # but BaseAgent.inventory might be accessed by legacy code.
        # Strategy: Override inventory property on Household to delegate to EconComponent.

        # Skills
        self.skills: Dict[str, Skill] = {}

        # Setup Decision Engine
        decision_engine.loan_market = loan_market
        decision_engine.logger = self.logger

        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized (Refactored).",
            extra={"tags": ["household_init"]}
        )

        super().__init__(
            id,
            initial_assets,
            initial_needs,
            decision_engine,
            value_orientation,
            name=f"Household_{id}",
            logger=logger,
        )

        # --- Core Attributes ---
        self.talent = talent
        self.config_module = config_module
        self.risk_aversion = risk_aversion
        self.personality = personality
        self.goods_info_map: Dict[str, Dict[str, Any]] = {
            g["id"]: g for g in goods_data
        }

        # --- Value Orientation (3 Pillars) ---
        mapping = getattr(config_module, "VALUE_ORIENTATION_MAPPING", {})
        prefs = mapping.get(
            value_orientation,
            {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        )
        self.preference_asset = prefs["preference_asset"]
        self.preference_social = prefs["preference_social"]
        self.preference_growth = prefs["preference_growth"]

        # --- Initialize Components ---
        self.bio_component = BioComponent(
            self, config_module, initial_age, gender, parent_id, generation
        )
        self.econ_component = EconComponent(self, config_module)
        self.social_component = SocialComponent(self, config_module, personality, initial_assets)
        
        # --- Legacy & Compatibility Attributes ---
        # Some attributes are kept on Facade if they are deeply intertwined or purely transient
        self.initial_assets_record = initial_assets
        self.credit_frozen_until_tick: int = 0

        # Phase 23: Inflation Expectation & Price Memory
        # Moved to EconComponent (WO-092)

        # WO-054: Aptitude (Hidden Trait) - Kept on Facade as it's intrinsic
        raw_aptitude = random.gauss(0.5, 0.15)
        self.aptitude: float = max(0.0, min(1.0, raw_aptitude))
        
        # Initialize Econ Component Initial State
        self.econ_component._assets = initial_assets
        # Skills & Inventory are managed by Econ Component primarily, but accessed via Facade
        # Currently BaseAgent has self.inventory. We should sync or delegate.
        # EconComponent has its own _inventory. BaseAgent's inventory is initialized empty.
        # We will use EconComponent's inventory as the source of truth,
        # but BaseAgent.inventory might be accessed by legacy code.
        # Strategy: Override inventory property on Household to delegate to EconComponent.
        
        # Skills
        self.skills: Dict[str, Skill] = {}
        
        # Setup Decision Engine
        self.decision_engine.loan_market = loan_market
        self.decision_engine.logger = self.logger

        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized (Refactored).",
            extra={"tags": ["household_init"]}
        )

    # --- Property Delegation: BioComponent ---
    @property
    def age(self) -> float:
        return self.bio_component.age

    @age.setter
    def age(self, value: float) -> None:
        self.bio_component.demographics.age = value

    @property
    def gender(self) -> str:
        return self.bio_component.gender

    @gender.setter
    def gender(self, value: str) -> None:
        self.bio_component.demographics.gender = value

    @property
    def parent_id(self) -> Optional[int]:
        return self.bio_component.parent_id

    @parent_id.setter
    def parent_id(self, value: Optional[int]) -> None:
        self.bio_component.demographics.parent_id = value

    @property
    def generation(self) -> int:
        return self.bio_component.generation

    @generation.setter
    def generation(self, value: int) -> None:
        self.bio_component.demographics.generation = value

    @property
    def spouse_id(self) -> Optional[int]:
        return self.bio_component.spouse_id

    @spouse_id.setter
    def spouse_id(self, value: Optional[int]) -> None:
        self.bio_component.demographics.spouse_id = value

    @property
    def children_ids(self) -> List[int]:
        return self.bio_component.children_ids

    @property
    def children_count(self) -> int:
        return self.bio_component.children_count

    # --- Property Delegation: EconComponent ---
    @property
    def assets(self) -> float:
        return self.econ_component.assets

    def _add_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to EconComponent."""
        self.econ_component._add_assets(amount)

    def _sub_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to EconComponent."""
        self.econ_component._sub_assets(amount)

    @property
    def inventory(self) -> Dict[str, float]:
        return self.econ_component.inventory

    @inventory.setter
    def inventory(self, value: Dict[str, float]) -> None:
        self.econ_component.inventory = value

    @property
    def inventory_quality(self) -> Dict[str, float]:
        return self.econ_component.inventory_quality

    @inventory_quality.setter
    def inventory_quality(self, value: Dict[str, float]) -> None:
        self.econ_component.inventory_quality = value

    @property
    def is_employed(self) -> bool:
        return self.econ_component.is_employed

    @is_employed.setter
    def is_employed(self, value: bool) -> None:
        self.econ_component.is_employed = value

    @property
    def employer_id(self) -> Optional[int]:
        return self.econ_component.employer_id

    @employer_id.setter
    def employer_id(self, value: Optional[int]) -> None:
        self.econ_component.employer_id = value

    @property
    def current_wage(self) -> float:
        return self.econ_component.current_wage

    @current_wage.setter
    def current_wage(self, value: float) -> None:
        self.econ_component.current_wage = value

    @property
    def wage_modifier(self) -> float:
        return self.econ_component.wage_modifier

    @wage_modifier.setter
    def wage_modifier(self, value: float) -> None:
        self.econ_component.wage_modifier = value

    @property
    def labor_skill(self) -> float:
        return self.econ_component.labor_skill

    @labor_skill.setter
    def labor_skill(self, value: float) -> None:
        self.econ_component.labor_skill = value

    @property
    def education_xp(self) -> float:
        return self.econ_component.education_xp

    @education_xp.setter
    def education_xp(self, value: float) -> None:
        self.econ_component.education_xp = value

    @property
    def education_level(self) -> int:
        return self.econ_component.education_level

    @education_level.setter
    def education_level(self, value: int) -> None:
        self.econ_component.education_level = value

    @property
    def expected_wage(self) -> float:
        return self.econ_component.expected_wage

    @expected_wage.setter
    def expected_wage(self, value: float) -> None:
        self.econ_component.expected_wage = value

    @property
    def portfolio(self) -> Portfolio:
        return self.econ_component.portfolio

    @portfolio.setter
    def portfolio(self, value: Portfolio) -> None:
        self.econ_component.portfolio = value

    @property
    def shares_owned(self) -> Dict[int, float]:
        # Legacy compat: Map portfolio holdings to shares_owned dict
        return self.econ_component.portfolio.to_legacy_dict()

    @shares_owned.setter
    def shares_owned(self, value: Dict[int, float]) -> None:
        self.econ_component.portfolio.sync_from_legacy(value)

    @property
    def income(self) -> float:
        return self.econ_component.labor_manager.get_income()

    @property
    def labor_manager(self) -> Any:
        return self.econ_component.labor_manager

    @property
    def economy_manager(self) -> Any:
        return self.econ_component.economy_manager

    @property
    def labor_income_this_tick(self) -> float:
        return self.econ_component.labor_income_this_tick

    @labor_income_this_tick.setter
    def labor_income_this_tick(self, value: float) -> None:
        self.econ_component.labor_income_this_tick = value

    @property
    def capital_income_this_tick(self) -> float:
        return self.econ_component.capital_income_this_tick

    @capital_income_this_tick.setter
    def capital_income_this_tick(self, value: float) -> None:
        self.econ_component.capital_income_this_tick = value

    @property
    def durable_assets(self) -> List[Dict[str, Any]]:
        return self.econ_component.durable_assets

    @durable_assets.setter
    def durable_assets(self, value: List[Dict[str, Any]]) -> None:
        self.econ_component.durable_assets = value

    @property
    def owned_properties(self) -> List[int]:
        return self.econ_component.owned_properties

    @owned_properties.setter
    def owned_properties(self, value: List[int]) -> None:
        self.econ_component.owned_properties = value

    @property
    def residing_property_id(self) -> Optional[int]:
        return self.econ_component.residing_property_id

    @residing_property_id.setter
    def residing_property_id(self, value: Optional[int]) -> None:
        self.econ_component.residing_property_id = value

    @property
    def is_homeless(self) -> bool:
        return self.econ_component.is_homeless

    @is_homeless.setter
    def is_homeless(self, value: bool) -> None:
        self.econ_component.is_homeless = value

    @property
    def housing_target_mode(self) -> str:
        return self.econ_component.housing_target_mode

    @housing_target_mode.setter
    def housing_target_mode(self, value: str) -> None:
        self.econ_component.housing_target_mode = value

    @property
    def housing_price_history(self) -> deque:
        return self.econ_component.housing_price_history

    @housing_price_history.setter
    def housing_price_history(self, value: deque) -> None:
        self.econ_component.housing_price_history = value

    @property
    def last_labor_offer_tick(self) -> int:
        return self.econ_component.last_labor_offer_tick

    @last_labor_offer_tick.setter
    def last_labor_offer_tick(self, value: int) -> None:
        self.econ_component.last_labor_offer_tick = value

    @property
    def last_fired_tick(self) -> int:
        return self.econ_component.last_fired_tick

    @last_fired_tick.setter
    def last_fired_tick(self, value: int) -> None:
        self.econ_component.last_fired_tick = value

    @property
    def job_search_patience(self) -> int:
        return self.econ_component.job_search_patience

    @job_search_patience.setter
    def job_search_patience(self, value: int) -> None:
        self.econ_component.job_search_patience = value

    @property
    def market_wage_history(self) -> deque:
        return self.econ_component.market_wage_history

    @market_wage_history.setter
    def market_wage_history(self, value: deque) -> None:
        self.econ_component.market_wage_history = value

    @property
    def shadow_reservation_wage(self) -> float:
        return self.econ_component.shadow_reservation_wage

    @shadow_reservation_wage.setter
    def shadow_reservation_wage(self, value: float) -> None:
        self.econ_component.shadow_reservation_wage = value

    @property
    def current_consumption(self) -> float:
        return self.econ_component.current_consumption

    @current_consumption.setter
    def current_consumption(self, value: float) -> None:
        self.econ_component.current_consumption = value

    @property
    def current_food_consumption(self) -> float:
        return self.econ_component.current_food_consumption

    @current_food_consumption.setter
    def current_food_consumption(self, value: float) -> None:
        self.econ_component.current_food_consumption = value

    @property
    def expected_inflation(self) -> Dict[str, float]:
        return self.econ_component.expected_inflation

    @expected_inflation.setter
    def expected_inflation(self, value: Dict[str, float]) -> None:
        self.econ_component.expected_inflation = value

    @property
    def perceived_avg_prices(self) -> Dict[str, float]:
        return self.econ_component.perceived_avg_prices

    @perceived_avg_prices.setter
    def perceived_avg_prices(self, value: Dict[str, float]) -> None:
        self.econ_component.perceived_avg_prices = value

    @property
    def price_history(self) -> defaultdict[str, deque]:
        return self.econ_component.price_history

    @price_history.setter
    def price_history(self, value: defaultdict[str, deque]) -> None:
        self.econ_component.price_history = value

    @property
    def adaptation_rate(self) -> float:
        return self.econ_component.adaptation_rate

    @adaptation_rate.setter
    def adaptation_rate(self, value: float) -> None:
        self.econ_component.adaptation_rate = value

    @property
    def social_status(self) -> float:
        return self.social_component.social_status

    @social_status.setter
    def social_status(self, value: float) -> None:
        self.social_component.social_status = value

    # --- Property Delegation: SocialComponent ---
    @property
    def approval_rating(self) -> int:
        return self.social_component.approval_rating

    @approval_rating.setter
    def approval_rating(self, value: int) -> None:
        self.social_component.approval_rating = value

    @property
    def discontent(self) -> float:
        return self.social_component.discontent

    @discontent.setter
    def discontent(self, value: float) -> None:
        self.social_component.discontent = value

    @property
    def conformity(self) -> float:
        return self.social_component.conformity

    @conformity.setter
    def conformity(self, value: float) -> None:
        self.social_component.conformity = value

    @property
    def social_rank(self) -> float:
        return self.social_component.social_rank

    @social_rank.setter
    def social_rank(self, value: float) -> None:
        self.social_component.social_rank = value

    @property
    def quality_preference(self) -> float:
        return self.social_component.quality_preference

    @quality_preference.setter
    def quality_preference(self, value: float) -> None:
        self.social_component.quality_preference = value

    @property
    def brand_loyalty(self) -> Dict[int, float]:
        return self.social_component.brand_loyalty

    @brand_loyalty.setter
    def brand_loyalty(self, value: Dict[int, float]) -> None:
        self.social_component.brand_loyalty = value

    @property
    def last_purchase_memory(self) -> Dict[str, int]:
        return self.social_component.last_purchase_memory

    @last_purchase_memory.setter
    def last_purchase_memory(self, value: Dict[str, int]) -> None:
        self.social_component.last_purchase_memory = value

    @property
    def patience(self) -> float:
        return self.social_component.patience

    @patience.setter
    def patience(self, value: float) -> None:
        self.social_component.patience = value

    @property
    def optimism(self) -> float:
        return self.social_component.optimism

    @optimism.setter
    def optimism(self, value: float) -> None:
        self.social_component.optimism = value

    @property
    def ambition(self) -> float:
        return self.social_component.ambition

    @ambition.setter
    def ambition(self, value: float) -> None:
        self.social_component.ambition = value

    @property
    def last_leisure_type(self) -> LeisureType:
        return self.social_component.last_leisure_type

    @last_leisure_type.setter
    def last_leisure_type(self, value: LeisureType) -> None:
        self.social_component.last_leisure_type = value

    @property
    def home_quality_score(self) -> float:
        return self.econ_component.home_quality_score

    @home_quality_score.setter
    def home_quality_score(self, value: float) -> None:
        self.econ_component.home_quality_score = value

    @property
    def psychology(self) -> PsychologyComponent:
        return self.social_component.psychology

    @property
    def desire_weights(self) -> Dict[str, float]:
        return self.social_component.psychology.desire_weights

    # --- Methods ---

    def create_state_dto(self) -> HouseholdStateDTO:
        """Creates a comprehensive DTO of the household's current state."""
        return HouseholdStateDTO(
            id=self.id,
            assets=self.assets,
            inventory=self.inventory.copy(),
            needs=self.needs.copy(),
            preference_asset=self.preference_asset,
            preference_social=self.preference_social,
            preference_growth=self.preference_growth,
            personality=self.personality,
            durable_assets=self.durable_assets, # Should we copy?
            expected_inflation=self.expected_inflation.copy(), # From Facade (transient)
            is_employed=self.is_employed,
            current_wage=self.current_wage,
            wage_modifier=self.wage_modifier,
            is_homeless=self.is_homeless,
            residing_property_id=self.residing_property_id,
            owned_properties=list(self.owned_properties),
            portfolio_holdings=self.portfolio.holdings, # Direct reference to Share objects (dataclasses)
            risk_aversion=self.risk_aversion,
            agent_data=self.get_agent_data(),
            conformity=self.conformity,
            social_rank=self.social_rank,
            approval_rating=self.approval_rating,
            # WO-108: Parity Fields
            perceived_fair_price=self.perceived_avg_prices.copy(),
            sentiment_index=self.optimism
        )

    @override
    def make_decision(
        self,
        markets: Dict[str, "Market"],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
        government: Optional[Any] = None,
        macro_context: Optional[MacroFinancialContext] = None,
        stress_scenario_config: Optional["StressScenarioConfig"] = None,
    ) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:

        # 0. Update Social Status (Before Decision)
        self.social_component.calculate_social_status()

        # 1. Prepare DTOs
        state_dto = self.create_state_dto()

        # Context for Decision Engine (Pure Logic)
        context = DecisionContext(
            household=self, # COMPATIBILITY RESTORED: Required for RuleBasedHouseholdDecisionEngine
            markets=markets,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            government=government,
            stress_scenario_config=stress_scenario_config
        )
        # Hack: DecisionContext currently expects 'household' but we want to use 'state' in new engine.
        # We need to modify DecisionContext to accept 'state' or monkey-patch it here if we can't change DTO yet.
        # But per plan, we ARE changing DTO. So we will set `context.state = state_dto`.
        context.state = state_dto # Dynamically attach DTO

        # 2. Call Decision Engine
        orders, chosen_tactic_tuple = self.decision_engine.make_decisions(context, macro_context)

        # 3. Orchestrate/Refine Orders via EconComponent
        econ_context = EconContextDTO(markets, market_data, current_time)
        refined_orders = self.econ_component.orchestrate_economic_decisions(econ_context, orders, stress_scenario_config)

        return refined_orders, chosen_tactic_tuple

    def adjust_assets(self, delta: float) -> None:
        self.econ_component.adjust_assets(delta)

    def modify_inventory(self, item_id: str, quantity: float) -> None:
        if item_id not in self.inventory:
            self.inventory[item_id] = 0
        self.inventory[item_id] += quantity

    def quit(self) -> None:
        if self.is_employed:
            self.logger.info(f"Household {self.id} is quitting from Firm {self.employer_id}")
            self.is_employed = False
            self.employer_id = None
            self.current_wage = 0.0

    def decide_and_consume(self, current_time: int, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        consumed_items = self.econ_component.consumption.decide_and_consume(current_time, market_data)
        self.update_needs(current_time, market_data)
        return consumed_items

    def consume(self, item_id: str, quantity: float, current_time: int) -> "ConsumptionResult":
        return self.econ_component.consume(item_id, quantity, current_time)

    @override
    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """Delegates lifecycle updates to BioComponent."""
        context: LifecycleContext = {
            "household": self, # Some lifecycle logic might still need 'self' to access properties
            "market_data": market_data if market_data else {},
            "time": current_tick
        }
        self.bio_component.run_lifecycle(context)

    def calculate_social_status(self) -> None:
        self.social_component.calculate_social_status()

    def update_political_opinion(self):
        self.social_component.update_political_opinion()

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        return self.social_component.apply_leisure_effect(leisure_hours, consumed_items)

    # --- Inflation & Price Logic (Transient/Facade specific) ---
    @override
    def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional["StressScenarioConfig"] = None) -> None:
        self.econ_component.update_perceived_prices(market_data, stress_scenario_config)

    # --- Learning & Cloning ---
    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Household":
        request = CloningRequestDTO(new_id, initial_assets_from_parent, current_tick)
        return self.bio_component.clone(request)

    def _create_new_decision_engine(self, new_id: int) -> AIDrivenHouseholdDecisionEngine:
        # Helper for BioComponent.clone
        shared_ai_engine = self.decision_engine.ai_engine.ai_decision_engine
        new_ai_engine = HouseholdAI(
            agent_id=str(new_id),
            ai_decision_engine=shared_ai_engine,
            gamma=self.decision_engine.ai_engine.gamma,
            epsilon=self.decision_engine.ai_engine.action_selector.epsilon,
            base_alpha=self.decision_engine.ai_engine.base_alpha,
            learning_focus=self.decision_engine.ai_engine.learning_focus
        )
        return AIDrivenHouseholdDecisionEngine(
            ai_engine=new_ai_engine,
            config_module=self.config_module,
            logger=self.logger
        )

    def get_generational_similarity(self, other: "Household") -> float:
        return self.bio_component.get_generational_similarity(other)

    def update_learning(self, context: LearningUpdateContext) -> None:
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]

        self.decision_engine.ai_engine.update_learning_v2(
            reward=reward,
            next_agent_data=next_agent_data,
            next_market_data=next_market_data,
        )

    def get_agent_data(self) -> Dict[str, Any]:
        return {
            "assets": self.assets,
            "needs": self.needs.copy(),
            "is_active": self.is_active,
            "is_employed": self.is_employed,
            "current_wage": self.current_wage,
            "employer_id": self.employer_id,
            "social_status": self.social_status,
            "credit_frozen_until_tick": self.credit_frozen_until_tick,
            "is_homeless": self.is_homeless,
            "owned_properties_count": len(self.owned_properties),
            "residing_property_id": self.residing_property_id,
            "social_rank": self.social_rank,
            "conformity": self.conformity,
            "approval_rating": self.approval_rating,
            "age": self.age,
            "education_level": self.education_level,
            "children_count": self.children_count,
            "expected_wage": self.expected_wage,
            "gender": self.gender,
            "home_quality_score": self.home_quality_score,
            "spouse_id": self.spouse_id,
            "aptitude": self.aptitude,
        }

    # Pass-through Methods for Legacy Components accessing 'self'
    def add_education_xp(self, xp: float) -> None:
        self.econ_component.education_xp += xp

    def add_durable_asset(self, asset: Dict[str, Any]) -> None:
        self.econ_component.durable_assets.append(asset)

    def add_labor_income(self, income: float) -> None:
        self.econ_component.labor_income_this_tick += income

    def apply_child_inheritance(self, child: "Household"):
        """
        Phase 19: Legacy logic
        """
        # Skill Inheritance
        for domain, skill in self.skills.items():
            child.skills[domain] = Skill(
                domain=domain,
                value=skill.value * 0.2,
                observability=skill.observability
            )
        # Wage inheritance
        child.education_level = min(self.education_level, 1)
        child.expected_wage = self.expected_wage * 0.8

    def get_desired_wage(self) -> float:
        """Calculate desired wage based on assets."""
        if self.assets < self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD:
            return self.config_module.HOUSEHOLD_LOW_ASSET_WAGE
        return self.config_module.HOUSEHOLD_DEFAULT_WAGE

    def _update_skill(self) -> None:
        """Delegate skill update to LaborManager."""
        self.econ_component.labor_manager.update_skills()
