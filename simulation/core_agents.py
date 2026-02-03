from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
import logging
from logging import Logger
from collections import deque, defaultdict
import random
import copy

from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order, StockOrder, Skill, Talent
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)
from simulation.core_markets import Market
from simulation.interfaces.market_interface import IMarket
from simulation.dtos import DecisionContext, FiscalContext, LeisureEffectDTO, LeisureType, MacroFinancialContext, ConsumptionResult, DecisionInputDTO
from simulation.dtos.config_dtos import HouseholdConfigDTO
from simulation.portfolio import Portfolio
from modules.finance.api import IPortfolioHandler, IHeirProvider, PortfolioDTO, PortfolioAsset

from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent
import simulation

# New Components
from modules.household.bio_component import BioComponent
from modules.household.econ_component import EconComponent
from modules.household.social_component import SocialComponent
from modules.household.consumption_manager import ConsumptionManager
from modules.household.decision_unit import DecisionUnit
from modules.household.dtos import (
    HouseholdStateDTO, CloningRequestDTO, EconContextDTO,
    BioStateDTO, EconStateDTO, SocialStateDTO
)
from modules.household.api import (
    HousingMarketUnitDTO, HousingMarketSnapshotDTO,
    LoanMarketSnapshotDTO, LaborMarketSnapshotDTO,
    MarketSnapshotDTO, OrchestrationContextDTO
)

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class Household(BaseAgent, ILearningAgent):
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

        # --- Initialize Internal State DTOs ---

        # Bio State
        self._bio_state = BioStateDTO(
            id=id,
            age=initial_age if initial_age is not None else random.uniform(20.0, 60.0),
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
        raw_aptitude = random.gauss(0.5, 0.15)
        aptitude = max(0.0, min(1.0, raw_aptitude))

        self._econ_state = EconStateDTO(
            assets=initial_assets,
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

    # --- Property Overrides (BaseAgent & Compatibility) ---

    @property
    @override
    def assets(self) -> float:
        return self._econ_state.assets

    @assets.setter
    def assets(self, value: float) -> None:
        self._econ_state.assets = value
        self._assets = value

    @property
    @override
    def inventory(self) -> Dict[str, float]:
        return self._econ_state.inventory

    @inventory.setter
    def inventory(self, value: Dict[str, float]) -> None:
        self._econ_state.inventory = value

    @property
    def inventory_quality(self) -> Dict[str, float]:
        return self._econ_state.inventory_quality

    @inventory_quality.setter
    def inventory_quality(self, value: Dict[str, float]) -> None:
        self._econ_state.inventory_quality = value

    @property
    @override
    def needs(self) -> Dict[str, float]:
        return self._bio_state.needs

    @needs.setter
    def needs(self, value: Dict[str, float]) -> None:
        self._bio_state.needs = value

    @property
    def is_active(self) -> bool:
        return self._bio_state.is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._bio_state.is_active = value

    @property
    def age(self) -> float:
        return self._bio_state.age

    @age.setter
    def age(self, value: float) -> None:
        self._bio_state.age = value

    @property
    def children_ids(self) -> List[int]:
        return self._bio_state.children_ids

    @children_ids.setter
    def children_ids(self, value: List[int]) -> None:
        self._bio_state.children_ids = value

    @property
    def is_homeless(self) -> bool:
        return self._econ_state.is_homeless

    @is_homeless.setter
    def is_homeless(self, value: bool) -> None:
        self._econ_state.is_homeless = value

    @property
    def residing_property_id(self) -> Optional[int]:
        return self._econ_state.residing_property_id

    @residing_property_id.setter
    def residing_property_id(self, value: Optional[int]) -> None:
        self._econ_state.residing_property_id = value

    @property
    def owned_properties(self) -> List[int]:
        return self._econ_state.owned_properties

    @owned_properties.setter
    def owned_properties(self, value: List[int]) -> None:
        self._econ_state.owned_properties = value

    @property
    def current_wage(self) -> float:
        return self._econ_state.current_wage

    @current_wage.setter
    def current_wage(self, value: float) -> None:
        self._econ_state.current_wage = value

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
    def skills(self) -> Dict[str, "Skill"]:
        """[TD-162] Backward compat: Exposes _econ_state.skills."""
        return self._econ_state.skills

    @skills.setter
    def skills(self, value: Dict[str, "Skill"]) -> None:
        self._econ_state.skills = value

    @property
    def portfolio(self) -> "Portfolio":
        """[TD-162] Backward compat: Exposes _econ_state.portfolio."""
        return self._econ_state.portfolio

    @portfolio.setter
    def portfolio(self, value: "Portfolio") -> None:
        self._econ_state.portfolio = value

    @override
    def _add_assets(self, amount: float) -> None:
        self._econ_state.assets += amount
        self._assets = self._econ_state.assets

    @override
    def _sub_assets(self, amount: float) -> None:
        self._econ_state.assets -= amount
        self._assets = self._econ_state.assets

    @property
    def gender(self) -> str:
        """Exposes gender from bio_state."""
        return self._bio_state.gender

    @property
    def home_quality_score(self) -> float:
        """Exposes home_quality_score from econ_state."""
        return self._econ_state.home_quality_score

    # --- Methods ---

    def create_state_dto(self) -> HouseholdStateDTO:
        """Creates a comprehensive DTO of the household's current state (Adapter)."""
        return HouseholdStateDTO(
            id=self.id,
            assets=self._econ_state.assets,
            inventory=self._econ_state.inventory.copy(),
            needs=self._bio_state.needs.copy(),
            preference_asset=self.preference_asset,
            preference_social=self.preference_social,
            preference_growth=self.preference_growth,
            personality=self._social_state.personality,
            durable_assets=[d.copy() for d in self._econ_state.durable_assets],
            expected_inflation=self._econ_state.expected_inflation.copy(),
            is_employed=self._econ_state.is_employed,
            current_wage=self._econ_state.current_wage,
            wage_modifier=self._econ_state.wage_modifier,
            is_homeless=self._econ_state.is_homeless,
            residing_property_id=self._econ_state.residing_property_id,
            owned_properties=list(self._econ_state.owned_properties),
            portfolio_holdings={k: copy.copy(v) for k, v in self._econ_state.portfolio.holdings.items()},
            risk_aversion=self.risk_aversion,
            agent_data=self.get_agent_data(),
            conformity=self._social_state.conformity,
            social_rank=self._social_state.social_rank,
            approval_rating=self._social_state.approval_rating,
            optimism=self._social_state.optimism,
            ambition=self._social_state.ambition,
            perceived_fair_price=self._econ_state.perceived_avg_prices.copy(),
            sentiment_index=self._social_state.optimism,
            perceived_prices=self._econ_state.perceived_avg_prices.copy(),
            demand_elasticity=getattr(self._social_state, 'demand_elasticity', 1.0)
        )

    def get_agent_data(self) -> Dict[str, Any]:
        """Adapter for AI learning data."""
        return {
            "assets": self._econ_state.assets,
            "needs": self._bio_state.needs.copy(),
            "is_active": self._bio_state.is_active,
            "is_employed": self._econ_state.is_employed,
            "current_wage": self._econ_state.current_wage,
            "employer_id": self._econ_state.employer_id,
            "social_status": self._social_state.social_status,
            "credit_frozen_until_tick": self._econ_state.credit_frozen_until_tick,
            "is_homeless": self._econ_state.is_homeless,
            "owned_properties_count": len(self._econ_state.owned_properties),
            "residing_property_id": self._econ_state.residing_property_id,
            "social_rank": self._social_state.social_rank,
            "conformity": self._social_state.conformity,
            "approval_rating": self._social_state.approval_rating,
            "age": self._bio_state.age,
            "education_level": self._econ_state.education_level,
            "children_count": len(self._bio_state.children_ids),
            "expected_wage": self._econ_state.expected_wage,
            "gender": self._bio_state.gender,
            "home_quality_score": self._econ_state.home_quality_score,
            "spouse_id": self._bio_state.spouse_id,
            "aptitude": self._econ_state.aptitude,
        }

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
        state_dto = self.create_state_dto()
        
        # WO-103: Purity Guard - Prepare Config DTO
        # self.config is already the DTO.
        config_dto = self.config

        context = DecisionContext(
            state=state_dto,
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
            household_state=state_dto,
            housing_system=input_dto.housing_system
        )

        # 4. Delegate to DecisionUnit (Stateless)
        self._econ_state, refined_orders = self.decision_unit.orchestrate_economic_decisions(
            state=self._econ_state,
            context=orchestration_context,
            initial_orders=initial_orders
        )

        return refined_orders, chosen_tactic_tuple

    def adjust_assets(self, delta: float) -> None:
        self._econ_state.assets += delta

    def modify_inventory(self, item_id: str, quantity: float) -> None:
        if item_id not in self._econ_state.inventory:
            self._econ_state.inventory[item_id] = 0
        self._econ_state.inventory[item_id] += quantity

    def quit(self) -> None:
        if self._econ_state.is_employed:
            self.logger.info(f"Household {self.id} is quitting from Firm {self._econ_state.employer_id}")
            self._econ_state.is_employed = False
            self._econ_state.employer_id = None
            self._econ_state.current_wage = 0.0

    def consume(self, item_id: str, quantity: float, current_time: int) -> "ConsumptionResult":
        # Delegate to ConsumptionManager
        self._econ_state, new_needs, result = self.consumption_manager.consume(
            self._econ_state,
            self._bio_state.needs,
            item_id,
            quantity,
            current_time,
            self.goods_info_map.get(item_id, {}),
            self.config
        )
        self._bio_state.needs = new_needs
        return result

    def trigger_emergency_liquidation(self) -> List[Any]:
        """
        WO-167: Generates emergency sell orders for all inventory items and stocks.
        Returns mixed list of Order and StockOrder.
        """
        orders = []

        # 1. Liquidate Inventory
        for good, qty in self._econ_state.inventory.items():
            if qty <= 0:
                continue

            price = self._econ_state.perceived_avg_prices.get(good, 10.0)
            liquidation_price = price * 0.8

            order = Order(
                agent_id=self.id,
                side="SELL",
                item_id=good,
                quantity=qty,
                price_limit=liquidation_price,
                market_id=good
            )
            orders.append(order)

        # 2. Liquidate Stocks
        for firm_id, holding in self._econ_state.portfolio.holdings.items():
            shares = holding.quantity
            if shares <= 0:
                continue

            # Heuristic price for stock: we don't have access to stock market price here easily
            # without checking markets. We'll use a very low price to ensure sale (market order effectively)
            # or rely on the market to match.
            # Ideally we check market data if passed, but here we assume desperation.
            # We will use 1.0 or 0.1 as a "market sell" signal if the market supports it,
            # but OrderBookMarket matches based on price.
            # If we set price too low, we might crash the market.
            # Let's try to be somewhat reasonable: 10.0 (default fallback) * 0.8 = 8.0
            price = 8.0

            order = Order(
                agent_id=self.id,
                side="SELL",
                item_id=f"stock_{firm_id}",
                quantity=shares,
                price_limit=price,
                market_id="stock_market"
            )
            orders.append(order)

        if orders:
            self.logger.warning(
                f"GRACE_PROTOCOL | Household {self.id} triggering emergency liquidation. Generated {len(orders)} orders.",
                extra={"agent_id": self.id, "tags": ["grace_protocol", "liquidation"]}
            )

        return orders

    @override
    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """
        Updates agent needs and lifecycle (Bio, Social, Econ-Work).
        Replaces legacy AgentLifecycleComponent.
        """
        if not self._bio_state.is_active:
            return

        # 1. Work (Econ)
        if self._econ_state.is_employed:
            self._econ_state, labor_res = self.econ_component.work(
                self._econ_state, 8.0, self.config
            )
            # We could log labor_res if needed

        # 2. Update Psychology/Social (Needs & Death Check)
        self._social_state, new_needs, new_durable_assets, is_active = self.social_component.update_psychology(
            self._social_state,
            self._bio_state.needs,
            self._econ_state.assets,
            self._econ_state.durable_assets,
            self.goods_info_map,
            self.config,
            current_tick,
            market_data
        )
        self._bio_state.needs = new_needs
        self._econ_state.durable_assets = new_durable_assets

        # WO-167: Grace Protocol - Override death if in distress grace period
        if not is_active and 0 < self.distress_tick_counter <= 5:
            is_active = True
            self.logger.info(
                f"GRACE_PROTOCOL_SAVE | Household {self.id} saved from death. Distress tick {self.distress_tick_counter}",
                extra={"agent_id": self.id, "tags": ["grace_protocol", "survival"]}
            )

        self._bio_state.is_active = is_active

        # 3. Update Political Opinion
        self._social_state = self.social_component.update_political_opinion(
            self._social_state, self._bio_state.needs.get("survival", 0.0)
        )

        # 4. Aging (Bio) - Also checks natural death
        self._bio_state = self.bio_component.age_one_tick(
            self._bio_state, self.config, current_tick
        )

        # 5. Skill Updates
        self._econ_state = self.econ_component.update_skills(self._econ_state, self.config)

    def apply_leisure_effect(self, leisure_hours: float, consumed_items: Dict[str, float]) -> LeisureEffectDTO:
        self._social_state, self._econ_state.labor_skill, result = self.social_component.apply_leisure_effect(
            self._social_state,
            self._econ_state.labor_skill,
            len(self._bio_state.children_ids),
            leisure_hours,
            consumed_items,
            self.config
        )
        return result

    @override
    def update_perceived_prices(self, market_data: Dict[str, Any], stress_scenario_config: Optional["StressScenarioConfig"] = None) -> None:
        self._econ_state = self.econ_component.update_perceived_prices(
            self._econ_state, market_data, self.goods_info_map, stress_scenario_config, self.config
        )

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Household":
        """
        Clones the household. Orchestrates Bio and Econ cloning logic.
        """
        # 1. Bio Cloning (Demographics)
        offspring_demo = self.bio_component.create_offspring_demographics(
            self._bio_state, new_id, current_tick, self.config
        )

        # 2. Econ Cloning (Inheritance)
        # We need parent skills.
        econ_inheritance = self.econ_component.prepare_clone_state(
            self._econ_state, self._econ_state.skills, self.config
        )

        # 3. Create Decision Engine
        new_decision_engine = self._create_new_decision_engine(new_id)

        # 4. Instantiate New Household
        # Combine args
        cloned_household = Household(
            id=new_id,
            talent=self._econ_state.talent, # Copied reference
            goods_data=[g for g in self.goods_info_map.values()],
            initial_assets=initial_assets_from_parent,
            initial_needs=self._bio_state.needs.copy(), # Inherit current needs or reset? Usually reset.
            # BioComponent.create_offspring_demographics didn't return initial needs.
            # We'll use copy of parent needs as per original logic.

            decision_engine=new_decision_engine,
            value_orientation=self.value_orientation,
            personality=self._social_state.personality, # Inherit personality
            config_dto=self.config,
            loan_market=self.decision_engine.loan_market,
            risk_aversion=self.risk_aversion,
            logger=None,

            # Demographics from Bio
            initial_age=offspring_demo["initial_age"],
            gender=offspring_demo["gender"],
            parent_id=offspring_demo["parent_id"],
            generation=offspring_demo["generation"]
        )

        # 5. Apply Econ Inheritance
        cloned_household._econ_state.skills = econ_inheritance["skills"]
        cloned_household._econ_state.education_level = econ_inheritance["education_level"]
        cloned_household._econ_state.expected_wage = econ_inheritance["expected_wage"]
        cloned_household._econ_state.labor_skill = econ_inheritance["labor_skill"]
        if "aptitude" in econ_inheritance:
             cloned_household._econ_state.aptitude = econ_inheritance["aptitude"]

        return cloned_household

    def _create_new_decision_engine(self, new_id: int) -> AIDrivenHouseholdDecisionEngine:
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
            config_module=self.config,
            logger=self.logger
        )

    def get_generational_similarity(self, other: "Household") -> float:
        talent_diff = abs(self._econ_state.talent.base_learning_rate - other._econ_state.talent.base_learning_rate)
        similarity = max(0.0, 1.0 - talent_diff)
        return similarity

    def update_learning(self, context: LearningUpdateContext) -> None:
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]

        self.decision_engine.ai_engine.update_learning_v2(
            reward=reward,
            next_agent_data=next_agent_data,
            next_market_data=next_market_data,
        )

    # Legacy method support
    def add_education_xp(self, xp: float) -> None:
        self._econ_state.education_xp += xp

    def add_durable_asset(self, asset: Dict[str, Any]) -> None:
        self._econ_state.durable_assets.append(asset)

    def add_labor_income(self, income: float) -> None:
        self._econ_state.labor_income_this_tick += income

    def get_desired_wage(self) -> float:
        if self._econ_state.assets < self.config.household_low_asset_threshold:
            return self.config.household_low_asset_wage
        return self.config.household_default_wage

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

    def record_consumption(self, quantity: float, is_food: bool = False) -> None:
        """
        Updates consumption counters.
        Used by Registry during transaction processing.
        """
        self._econ_state.current_consumption += quantity
        if is_food:
            self._econ_state.current_food_consumption += quantity

    def reset_consumption_counters(self) -> None:
        """
        Resets consumption counters for the new tick.
        Used by TickScheduler.
        """
        self._econ_state.current_consumption = 0.0
        self._econ_state.current_food_consumption = 0.0
        self._econ_state.labor_income_this_tick = 0.0
        self._econ_state.capital_income_this_tick = 0.0

    @override
    def _add_assets(self, amount: float) -> None:
        self._econ_state.assets += amount
        self._assets = self._econ_state.assets # Sync legacy property

    @override
    def _sub_assets(self, amount: float) -> None:
        self._econ_state.assets -= amount
        self._assets = self._econ_state.assets # Sync legacy property

    @override
    def adjust_assets(self, delta: float) -> None:
        """
        Adjusts assets by delta (positive or negative).
        Delegates to _add_assets or _sub_assets to ensure validation and hooks run.
        """
        if delta >= 0:
            self._add_assets(delta)
        else:
            self._sub_assets(abs(delta))

    # --- IPortfolioHandler Implementation ---

    def get_portfolio(self) -> PortfolioDTO:
        assets = []
        for firm_id, share in self._econ_state.portfolio.holdings.items():
            assets.append(PortfolioAsset(
                asset_type="stock",
                asset_id=str(firm_id),
                quantity=share.quantity
            ))
        return PortfolioDTO(assets=assets)

    def receive_portfolio(self, portfolio: PortfolioDTO) -> None:
        for asset in portfolio.assets:
            if asset.asset_type == "stock":
                try:
                    firm_id = int(asset.asset_id)
                    # TD-160: Inherited assets are integrated.
                    # We use 0.0 acquisition price as default for inheritance if not specified.
                    self._econ_state.portfolio.add(firm_id, asset.quantity, 0.0)
                except ValueError:
                    self.logger.error(f"Invalid firm_id in portfolio receive: {asset.asset_id}")
            else:
                self.logger.warning(f"Household received unhandled asset type: {asset.asset_type} (ID: {asset.asset_id})")

    def clear_portfolio(self) -> None:
        self._econ_state.portfolio.holdings.clear()

    # --- IHeirProvider Implementation ---

    def get_heir(self) -> Optional[int]:
        """
        Returns the ID of the designated heir (Spouse -> Oldest Child -> None).
        """
        if self._bio_state.spouse_id is not None:
            return self._bio_state.spouse_id
        if self._bio_state.children_ids:
            return self._bio_state.children_ids[0]
        return None
