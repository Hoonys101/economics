from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
import logging
from logging import Logger
from collections import deque, defaultdict
import random
from collections import deque

from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)
from simulation.core_markets import Market  # Import Market
from simulation.dtos import DecisionContext, LeisureEffectDTO, LeisureType, MacroFinancialContext
from simulation.portfolio import Portfolio

# Import HouseholdAI and AIDrivenHouseholdDecisionEngine for mitosis
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
# Phase 20: System 2
from simulation.ai.system2_planner import System2Planner
from simulation.ai.household_system2 import HouseholdSystem2Planner, HousingDecisionInputs
from simulation.components.consumption_behavior import ConsumptionBehavior
from simulation.components.psychology_component import PsychologyComponent
from simulation.components.leisure_manager import LeisureManager
from simulation.utils.shadow_logger import log_shadow
from simulation.components.demographics_component import DemographicsComponent
from simulation.components.economy_manager import EconomyManager
from simulation.components.labor_manager import LaborManager
from simulation.components.agent_lifecycle import AgentLifecycleComponent
from simulation.components.market_component import MarketComponent
from simulation.systems.api import LifecycleContext, MarketInteractionContext, LearningUpdateContext, ILearningAgent

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket

logger = logging.getLogger(__name__)


class Talent:
    """가계의 선천적 재능을 나타내는 클래스입니다.

    재능은 학습 속도와 특정 기술 도메인의 최대 역량치에 영향을 미칩니다.
    """

    base_learning_rate: float
    max_potential: Dict[str, float]
    related_domains: Dict[str, List[str]]

    def __init__(
        self,
        base_learning_rate: float,
        max_potential: Dict[str, float],
        related_domains: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Talent 클래스의 생성자입니다.

        Args:
            base_learning_rate (float): 재능의 기본 학습 속도입니다.
            max_potential (Dict[str, float]): 각 기술 도메인별 최대 잠재 역량치입니다.
            related_domains (Dict[str, List[str]], optional): 관련 도메인 맵입니다. 기본값은 None입니다.
        """
        self.base_learning_rate = base_learning_rate
        self.max_potential = max_potential
        self.related_domains = related_domains if related_domains is not None else {}


class Skill:
    """가계의 후천적 역량을 나타내는 클래스입니다.

    학습과 경험을 통해 증가하며, 특정 도메인에 대한 숙련도를 나타냅니다.
    """

    domain: str
    value: float
    observability: float

    def __init__(
        self, domain: str, value: float = 0.0, observability: float = 0.5
    ) -> None:
        """Skill 클래스의 생성자입니다.

        Args:
            domain (str): 기술이 속한 도메인.
            value (float): 기술의 현재 숙련도 값. 기본값은 0.0입니다.
            observability (float): 기술의 관찰 가능성. 기본값은 0.5입니다.
        """
        self.domain = domain
        self.value = value
        self.observability = observability


class Household(BaseAgent, ILearningAgent):
    """
    가계 주체. 소비와 노동 공급의 주체이며, 다양한 욕구를 가지고 의사결정을 수행합니다.
    경제 시뮬레이션 내에서 재화 소비, 노동 시장 참여, 자산 관리 등의 활동을 합니다.

    Attributes:
        id (int): 가계의 고유 ID.
        talent (Talent): 가계의 선천적 재능. 학습 속도와 기술 역량에 영향을 미칩니다.
        goods_info_map (Dict[str, Dict[str, Any]]): 시뮬레이션 내 모든 재화에 대한 정보 (ID: 정보 맵).
        initial_assets (float): 가계의 초기 자산.
        initial_needs (Dict[str, float]): 가계의 초기 욕구 수준 (예: 생존, 인정, 성장 등).
        decision_engine (BaseDecisionEngine): 가계의 의사결정 로직을 담당하는 엔진.
        value_orientation (str): 가계의 가치관 (예: "wealth_and_needs", "social_status").
        skills (Dict[str, Skill]): 가계가 보유한 기술 (도메인: Skill 객체 맵).
        inventory (Dict[str, float]): 가계가 보유한 재화 및 수량 (재화 ID: 수량 맵).
        current_consumption (float): 현재 턴의 총 소비량.
        employer_id (Optional[int]): 고용된 경우 고용 기업의 ID. 고용되지 않은 경우 None.
        shares_owned (Dict[int, float]): 보유한 기업 주식 수 (기업 ID: 주식 수 맵).
        is_employed (bool): 현재 고용 상태 여부.
        labor_skill (float): 노동 시장에서 가계의 노동 스킬 수준.
        survival_need_high_turns (int): 생존 욕구가 위험 수준으로 높은 상태로 지속된 턴 수.
        social_status (float): 가계의 사회적 지위. 자산과 사치품 소비에 기반하여 계산됩니다.
        perceived_avg_prices (Dict[str, float]): 가계가 인지하는 상품별 평균 가격 (재화 ID: 가격 맵).
        current_food_consumption (float): 현재 턴의 식량 소비량.
        aptitude (float): 잠재적 학습 능력 및 지능 (0.0 ~ 1.0, Gaussian Dist).
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
        """Household 클래스의 생성자입니다.

        Args:
            id (int): 가계의 고유 ID.
            talent (Talent): 가계의 선천적 재능.
            goods_data (List[Dict[str, Any]]): 시뮬레이션 내 모든 재화에 대한 정보.
            initial_assets (float): 가계의 초기 자산.
            initial_needs (Dict[str, float]): 가계의 초기 욕구 수준.
            decision_engine (BaseDecisionEngine): 가계의 의사결정 로직을 담당하는 엔진.
            value_orientation (str): 가계의 가치관.
            personality (Personality): 가계의 고유한 특질(성격).
            loan_market (Optional[LoanMarket]): 대출 시장 인스턴스. 기본값은 None.
            risk_aversion (float): 위험 회피 성향 (0.1 ~ 10.0). 기본값은 1.0.
            logger (Optional[Logger]): 로거 인스턴스. 기본값은 None.
        """
        super().__init__(
            id,
            initial_assets,
            initial_needs,
            decision_engine,
            value_orientation,
            name=f"Household_{id}",
            logger=logger,
        )
        self.credit_frozen_until_tick: int = 0  # Phase 4: Bankruptcy Penalty
        self.initial_assets_record = initial_assets # WO-Sociologist: Track starting point
        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized. Initial Needs: {self.needs}",
            extra={"tags": ["household_init"]},
        )
        self.risk_aversion = risk_aversion
        self.talent = talent
        self.skills: Dict[str, Skill] = {}
        self.goods_info_map: Dict[str, Dict[str, Any]] = {
            g["id"]: g for g in goods_data
        }

        # Initialize personality
        self.personality = personality

        # WO-054: Aptitude (Hidden Trait)
        # Gaussian: Mean 0.5, Std 0.15, Clamped 0.0-1.0
        raw_aptitude = random.gauss(0.5, 0.15)
        self.aptitude: float = max(0.0, min(1.0, raw_aptitude))

        # --- 3-Pillars Preferences (Value Orientation) ---
        # Value Orientation determines "What" (ROI weights), independent of Personality ("How fast" needs grow)
        mapping = getattr(config_module, "VALUE_ORIENTATION_MAPPING", {})
        prefs = mapping.get(
            value_orientation,
            {"preference_asset": 1.0, "preference_social": 1.0, "preference_growth": 1.0}
        )
        self.preference_asset = prefs["preference_asset"]
        self.preference_social = prefs["preference_social"]
        self.preference_growth = prefs["preference_growth"]

        self.config_module = config_module  # Store config_module

        self.current_food_consumption: float = 0.0
        self.current_consumption: float = 0.0
        self.employer_id: Optional[int] = None

        # Phase 22.5: Component Initialization (Architecture Detox)
        self.psychology = PsychologyComponent(self, personality, config_module)
        self.consumption = ConsumptionBehavior(self, config_module)
        self.leisure = LeisureManager(self, config_module)
        self.economy_manager = EconomyManager(self, config_module)
        self.labor_manager = LaborManager(self, config_module)
        self.lifecycle_component = AgentLifecycleComponent(self, config_module)
        self.market_component = MarketComponent(self, config_module)
        self.shares_owned: Dict[int, float] = {}
        self.is_employed: bool = False
        self.labor_skill: float = 1.0
        self.current_wage: float = 0.0
        self.survival_need_high_turns: int = 0
        self.social_status: float = 0.0
        self.perceived_avg_prices: Dict[str, float] = {}
        self.education_xp: float = 0.0  # Task #6: Education XP

        # Income Tracking (Reset every tick)
        self.labor_income_this_tick: float = 0.0
        self.capital_income_this_tick: float = 0.0

        # Phase 8: Inflation Psychology
        self.price_history: Dict[str, deque] = {}  # ItemID -> Deque[float]
        self.expected_inflation: Dict[str, float] = {} # ItemID -> Expected Inflation Rate

        # Phase 17-3B: Real Estate Attributes
        self.owned_properties: List[int] = []
        self.residing_property_id: Optional[int] = None
        self.is_homeless: bool = True


        # Initialize price history deques
        for item_id in self.goods_info_map.keys():
            self.price_history[item_id] = deque(maxlen=self.config_module.INFLATION_MEMORY_WINDOW)
            self.expected_inflation[item_id] = 0.0

        # Determine Adaptation Rate based on Personality
        # Removed MATERIALISTIC as it is not in Personality Enum
        if self.personality == Personality.STATUS_SEEKER: # Impulsive
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_IMPULSIVE
        elif self.personality == Personality.MISER: # Conservative
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_CONSERVATIVE
        else: # Normal
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_NORMAL

        # Operation Forensics (WO-021)
        self.last_labor_offer_tick: int = 0
        self.wage_modifier: float = 1.0  # Phase 21.6: Adaptive Wage Modifier (100%)

        # Phase 4: Bankruptcy Penalty
        self.credit_frozen_until_tick: int = 0

        # Phase 5: Genealogy & Time Allocation
        self.last_fired_tick: int = -1  # 마지막으로 해고된 Tick (-1이면 없음)
        self.job_search_patience: int = 0 # 구직 활동 기간 (틱 단위)

        # === DEMOGRAPHICS REFACTORING START ===

        # 1. DemographicsComponent 인스턴스화
        # If demographic data is not provided, generate it for a new agent.
        if initial_age is None:
            initial_age = random.uniform(20.0, 60.0)
        if gender is None:
            gender = random.choice(["M", "F"])
        if generation is None:
            generation = 0

        self.demographics = DemographicsComponent(
            owner=self,
            initial_age=initial_age,
            gender=gender,
            parent_id=parent_id,
            generation=generation,
            config_module=self.config_module
        )

        # === DEMOGRAPHICS REFACTORING END ===

        # Phase 20: The Matrix (Gender & Home Quality)
        self.home_quality_score: float = 1.0
        self.system2_planner = System2Planner(self, config_module)
        self.housing_planner = HouseholdSystem2Planner(self, config_module)
        self.housing_target_mode = "RENT"
        ticks_per_year = int(getattr(config_module, "TICKS_PER_YEAR", 100))
        self.housing_price_history = deque(maxlen=ticks_per_year)

        # Education Level (0~5)
        # WO-Sociologist: The Social Ladder (Asset-based Determination)
        wealth_thresholds = getattr(config_module, "EDUCATION_WEALTH_THRESHOLDS", None)
        if wealth_thresholds:
            # Deterministic, Wealth-Gated Education
            level = 0
            for lvl, threshold in sorted(wealth_thresholds.items()):
                if initial_assets >= threshold:
                    level = max(level, lvl)
            self.education_level = level
        else:
            # Legacy: Random Distribution
            dist = getattr(config_module, "EDUCATION_LEVEL_DISTRIBUTION", [1.0])
            self.education_level: int = random.choices(range(len(dist)), weights=dist)[0]

        # Expected Wage Calculation
        base_wage = getattr(config_module, "INITIAL_WAGE", 10.0)
        edu_mults = getattr(config_module, "EDUCATION_COST_MULTIPLIERS", {})
        self.expected_wage: float = base_wage * edu_mults.get(self.education_level, 1.0)

        self.time_budget: Dict[str, float] = {
            "labor": 0.0, "leisure": 0.0, "childcare": 0.0, "housework": 0.0
        }

        # --- Phase 17-3A: Real Estate ---
        self.owned_properties: List[int] = []  # IDs of owned RealEstateUnits
        self.residing_property_id: Optional[int] = None
        self.is_homeless: bool = False

        # Phase 17-3B: Personality Attributes (WO-029-D)
        # Initializes with 0.5 (Neutral) + small random noise for diversity
        self.ambition: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))

        # Phase 17-4: Vanity - Conformity (Biased Randomization)
        conformity_ranges = getattr(config_module, "CONFORMITY_RANGES", {})
        c_min, c_max = conformity_ranges.get(self.personality.name, conformity_ranges.get(None, (0.3, 0.7)))
        self.conformity: float = random.uniform(c_min, c_max)
        self.social_rank: float = 0.5  # Phase 17-4: Percentile Rank (0.0~1.0)

        # --- Phase 17-5: Leviathan (Political Opinion) ---
        self.approval_rating: int = 1 # 1: Approve, 0: Disapprove
        self.discontent: float = 0.0

        self.patience: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))
        self.optimism: float = max(0.0, min(1.0, 0.5 + random.uniform(-0.3, 0.3)))

        # --- Phase 14-1: Shareholder & Dividend Attributes ---
        self.portfolio: List[int] = []  # List of Firm IDs owned
        self.income_labor_cumulative: float = 0.0
        self.income_capital_cumulative: float = 0.0
        self.labor_income_this_tick: float = 0.0
        self.capital_income_this_tick: float = 0.0
        self.last_leisure_type: LeisureType = "IDLE"  # For visualization aggregation

        # Phase 22: Portfolio System (Option B: Wrapper)
        self.portfolio = Portfolio(self.id)


        self.decision_engine.loan_market = loan_market
        self.decision_engine.logger = self.logger  # Pass logger to decision engine
        
        # --- Phase 6: Brand Economy Traits ---
        # --- Phase 6: Brand Economy Traits ---
        # Initialize quality_preference based on Personality and Wealth
        mean_assets = self.config_module.INITIAL_HOUSEHOLD_ASSETS_MEAN
        is_wealthy = self.assets > mean_assets * 1.5
        is_poor = self.assets < mean_assets * 0.5
        

        if self.personality == Personality.STATUS_SEEKER or is_wealthy:
            # Snob: 0.7 ~ 1.0 (Uses config if available, else hardcoded)
            min_pref = getattr(self.config_module, "QUALITY_PREF_SNOB_MIN", 0.7)
            self.quality_preference = random.uniform(min_pref, 1.0)
        elif self.personality == Personality.MISER or is_poor:
            # Miser: 0.0 ~ 0.3
            max_pref = getattr(self.config_module, "QUALITY_PREF_MISER_MAX", 0.3)
            self.quality_preference = random.uniform(0.0, max_pref)
        else:
            # Average: 0.3 ~ 0.7
            min_snob = getattr(self.config_module, "QUALITY_PREF_SNOB_MIN", 0.7)
            max_miser = getattr(self.config_module, "QUALITY_PREF_MISER_MAX", 0.3)
            self.quality_preference = random.uniform(max_miser, min_snob) # 0.3 ~ 0.7
        self.brand_loyalty: Dict[int, float] = {}  # FirmID -> LoyaltyMultipler (Default 1.0)
        self.last_purchase_memory: Dict[str, int] = {} # ItemID -> FirmID
        
        # Phase 15: Materiality & Durables
        self.inventory_quality: Dict[str, float] = {}  # Weighted Average Quality
        self.durable_assets: List[Dict[str, Any]] = [] # [{'item_id': str, 'quality': float, 'remaining_life': int}]

        # --- Phase 8: Inflation Psychology ---
        self.price_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config_module.INFLATION_MEMORY_WINDOW)
        )
        self.expected_inflation: Dict[str, float] = defaultdict(float)
        
        # WO-056: Shadow Labor Market Attributes
        self.market_wage_history: deque[float] = deque(maxlen=30) # For 30-tick avg
        self.shadow_reservation_wage: float = 0.0 # Will be initialized based on current_wage or expected_wage

        # [Refactoring] Standardized Memory Structure
        # Used for storing generic agent history/state (e.g. past perceptions, triggers)
        self.memory: Dict[str, Any] = {}
        
        # Set Adaptation Rate (Lambda) based on Personality
        if self.personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_IMPULSIVE
        elif self.personality in [Personality.MISER, Personality.CONSERVATIVE]:
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_CONSERVATIVE
        else:
            self.adaptation_rate = self.config_module.ADAPTATION_RATE_NORMAL


    def quit(self) -> None:
        """현재 직장에서 퇴사합니다."""
        if self.is_employed:
            self.logger.info(f"Household {self.id} is quitting from Firm {self.employer_id}")
            self.is_employed = False
            self.employer_id = None
            self.current_wage = 0.0

    def decide_and_consume(self, current_time: int, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        가계가 현재 욕구 상태와 보유 재고를 바탕으로 재화를 소모합니다.
        """
        consumed_items = self.consumption.decide_and_consume(current_time, market_data)
        self.update_needs(current_time, market_data)
        return consumed_items

    def _initialize_desire_weights(self, personality: Personality):
        """
        Legacy wrapper for desire weights initialization.
        """
        pass # Handled by PsychologyComponent.__init__

    @property
    def desire_weights(self) -> Dict[str, float]:
        return self.psychology.desire_weights

    @property
    def income(self) -> float:
        """Facade property to get income from the LaborManager."""
        return self.labor_manager.get_income()

    def adjust_assets(self, delta: float) -> None:
        """
        Adjusts the household's assets by a given delta.

        Args:
            delta: The amount to add (positive) or subtract (negative) from assets.
        """
        self.assets += delta

    def modify_inventory(self, item_id: str, quantity: float) -> None:
        """
        Modifies the household's inventory for a given item.

        Args:
            item_id: The ID of the item to modify.
            quantity: The quantity to add (positive) or remove (negative).
        """
        if item_id not in self.inventory:
            self.inventory[item_id] = 0
        self.inventory[item_id] += quantity

    def add_education_xp(self, xp: float) -> None:
        """Adds education experience points."""
        self.education_xp += xp

    def add_durable_asset(self, asset: Dict[str, Any]) -> None:
        """Adds a durable asset to the household."""
        self.durable_assets.append(asset)

    def add_labor_income(self, income: float) -> None:
        """Adds labor income for the current tick."""
        self.labor_income_this_tick += income

    # --- Pass-through Properties ---
    @property
    def age(self) -> float:
        return self.demographics.age

    @property
    def gender(self) -> str:
        return self.demographics.gender

    @property
    def parent_id(self) -> Optional[int]:
        return self.demographics.parent_id

    @property
    def spouse_id(self) -> Optional[int]:
        return self.demographics.spouse_id

    @property
    def children_ids(self) -> List[int]:
        return self.demographics.children_ids

    @property
    def generation(self) -> int:
        return self.demographics.generation

    @property
    def children_count(self) -> int:
        return self.demographics.children_count

    def calculate_social_status(self) -> None:
        """
        사회적 지위 계산을 PsychologyComponent로 위임합니다.
        """
        self.psychology.calculate_social_status()

    @override
    def update_perceived_prices(self, market_data: Dict[str, Any]) -> None:
        """
        시장에서 인지된 상품 가격을 업데이트하고, 인플레이션을 예측하여 사재기(Hoarding) 심리를 형성합니다.
        (Phase 8: Adaptive Expectations)
        Args:
            market_data (Dict[str, Any]): 현재 시장 데이터를 포함하는 딕셔너리입니다.
        """
        goods_market = market_data.get("goods_market")
        if not goods_market:
            return

        for good in self.goods_info_map.values():
            item_id = good["id"]
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")

            if actual_price is not None and actual_price > 0:
                # --- Phase 8: Inflation Expectation Update ---
                history = self.price_history[item_id]
                if history:
                    last_price = history[-1]
                    if last_price > 0:
                        inflation_t = (actual_price - last_price) / last_price
                        
                        # Adaptive Expectation: pi_e(t+1) = pi_e(t) + lambda * (pi(t) - pi_e(t))
                        old_expect = self.expected_inflation[item_id]
                        new_expect = old_expect + self.adaptation_rate * (inflation_t - old_expect)
                        self.expected_inflation[item_id] = new_expect
                        
                        # Log significant expectation changes
                        if abs(new_expect) > 0.05: # > 5% inflation/deflation expectation
                             self.logger.debug(
                                f"INFLATION_EXPECTATION | Household {self.id} expects {new_expect:.1%} inflation for {item_id}",
                                extra={"tags": ["inflation_psychology"], "item_id": item_id, "inflation": new_expect}
                             )

                history.append(actual_price)
                # ---------------------------------------------

                old_perceived_price = self.perceived_avg_prices.get(
                    item_id, actual_price
                )
                new_perceived_price = (
                    self.config_module.PERCEIVED_PRICE_UPDATE_FACTOR * actual_price
                ) + (
                    (1 - self.config_module.PERCEIVED_PRICE_UPDATE_FACTOR)
                    * old_perceived_price
                )
                self.perceived_avg_prices[item_id] = new_perceived_price



    def apply_leisure_effect(
        self, leisure_hours: float, consumed_items: Dict[str, float]
    ) -> LeisureEffectDTO:
        """
        여가 효과 계산을 LeisureManager로 위임합니다.
        """
        return self.leisure.apply_leisure_effect(leisure_hours, consumed_items)

    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
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
            "social_rank": getattr(self, "social_rank", 0.0),
            "conformity": getattr(self, "conformity", 0.5),
            "approval_rating": getattr(self, "approval_rating", 1), # Phase 17-5
            "age": self.age,
            "education_level": getattr(self, "education_level", 0),
            "children_count": self.children_count,
            "expected_wage": getattr(self, "expected_wage", 10.0),
            "gender": self.gender,
            "home_quality_score": self.home_quality_score,
            "spouse_id": self.spouse_id,
            "aptitude": self.aptitude, # WO-054
        }
    # AI 상태 결정에 필요한 다른 데이터 추가 가능

    def get_pre_state_data(self) -> Dict[str, Any]:
        """
        AI 학습을 위한 이전 상태 데이터를 반환합니다.
        """
        return getattr(self, "pre_state_snapshot", self.get_agent_data())

    def update_political_opinion(self):
        """
        Phase 17-5: Update Political Opinion based on Discontent.
        Discontent = Survival Need / 100.0.
        Approval = 1 if Discontent < 0.4 else 0.
        """
        # Calculate Discontent
        survival_need = self.needs.get("survival", 0.0)
        self.discontent = min(1.0, survival_need / 100.0)

        # Determine Approval (Tolerance = 0.4)
        if self.discontent < 0.4:
            self.approval_rating = 1
        else:
            self.approval_rating = 0

    def _calculate_shadow_reservation_wage(self, market_data: Dict[str, Any], current_tick: int) -> None:
        """
        WO-056: Stage 1 Shadow Mode (Labor Market Mechanism).
        Calculates and logs the shadow reservation wage and startup cost index.
        """
        # 1. Update Market Wage History
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            self.market_wage_history.append(avg_market_wage)

        # 2. Calculate Startup Cost Shadow Index
        # Formula: Avg_Wage_last_30_ticks * 6
        startup_cost_index = 0.0
        if self.market_wage_history:
            avg_wage_30 = sum(self.market_wage_history) / len(self.market_wage_history)
            startup_cost_index = avg_wage_30 * 6.0

        # 3. Calculate Shadow Reservation Wage (Sticky Logic)
        # Initialize if zero (e.g. first run)
        if self.shadow_reservation_wage <= 0.0:
            self.shadow_reservation_wage = self.current_wage if self.is_employed else self.expected_wage

        # Logic:
        # Wage Increase Rate: 0.05 (if employed or market rising?)
        # Wage Decay Rate: 0.02 (if unemployed)
        # Spec says: "Wage Increase: 0.05 (Employment/Rise), Wage Decay: 0.02 (Unemployment)"

        if self.is_employed:
            target = max(self.current_wage, self.shadow_reservation_wage)
            self.shadow_reservation_wage = (self.shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            # Decay Logic: If unemployed, it decays.
            self.shadow_reservation_wage *= (1.0 - 0.02)
            # Apply floor (Survival minimum)
            min_wage = getattr(self.config_module, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if self.shadow_reservation_wage < min_wage:
                self.shadow_reservation_wage = min_wage

        # 4. Log
        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Household",
            metric="shadow_wage",
            current_value=self.current_wage if self.is_employed else self.expected_wage,
            shadow_value=self.shadow_reservation_wage,
            details=f"Employed={self.is_employed}, StartupIdx={startup_cost_index:.2f}"
        )

    def decide_housing(self, market_data: Dict[str, Any], current_time: int) -> None:
        """
        Executes System 2 Housing Logic.
        Triggered periodically or on critical events (e.g. homelessness).
        """
        # Trigger Condition: Homeless or Monthly Review (e.g., every 30 ticks)
        if not (self.is_homeless or current_time % 30 == 0):
            return

        # Prepare Inputs
        housing_market = market_data.get("housing_market", {})
        loan_market = market_data.get("loan_market", {})

        # Determine Market Price (Use avg rent / 0.01 / 12 proxy if price unavailable? No, usually separate)
        # Assuming engine injects 'housing_market' with 'avg_rent_price'
        # We need housing Sale Price. If missing, we estimate via Rent/Price Ratio or similar.
        # But let's check if 'avg_price' is available for 'housing' in goods_market?
        # Housing is usually separate.
        # Check 'housing' key in markets.

        market_rent = housing_market.get("avg_rent_price", 100.0)
        # Fallback estimation for sale price
        market_price = housing_market.get("avg_sale_price")
        if not market_price:
             market_price = market_rent * 12 * 20.0

        # Update Price History
        self.housing_price_history.append(market_price)

        risk_free_rate = loan_market.get("interest_rate", 0.05)

        # Calculate Price Growth Expectation (Adaptive)
        price_growth = 0.0
        if len(self.housing_price_history) >= 2:
            # Simple CAGR or linear growth from start of window to end
            start_price = self.housing_price_history[0]
            end_price = self.housing_price_history[-1]
            if start_price > 0:
                # Total growth over the window
                total_growth = (end_price - start_price) / start_price
                # Annualize? Window is roughly 1 year max.
                # If window is full (1 year), total_growth is annual growth.
                # If window is partial, we extrapolate?
                # Spec says "Rolling average of price change (Last 1 year)".
                # I'll treat total growth over the available history as the proxy for annual expectation if history is long enough,
                # or just use it as is.
                price_growth = total_growth

        ticks_per_year = getattr(self.config_module, "TICKS_PER_YEAR", 100)
        income = self.current_wage * ticks_per_year if self.is_employed else self.expected_wage * ticks_per_year

        inputs = HousingDecisionInputs(
            current_wealth=self.assets,
            annual_income=income,
            market_rent_monthly=market_rent,
            market_price=market_price,
            risk_free_rate=risk_free_rate,
            price_growth_expectation=price_growth
        )

        decision = self.housing_planner.decide(inputs)

        if decision != self.housing_target_mode:
            self.logger.info(
                f"HOUSING_DECISION_CHANGE | Household {self.id} switched housing mode: {self.housing_target_mode} -> {decision}",
                extra={"tick": current_time, "agent_id": self.id}
            )
            self.housing_target_mode = decision

    @override
    def make_decision(
        self,
        markets: Dict[str, "Market"],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
        government: Optional[Any] = None,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:
        # Phase 20: System 2 Housing Check
        self.decide_housing(market_data, current_time)

        self.calculate_social_status()

        log_extra = {
            "tick": current_time,
            "agent_id": self.id,
            "tags": ["household_action"],
        }
        self.logger.debug(
            f"HOUSEHOLD_DECISION_START | Household {self.id} before decision: Assets={self.assets:.2f}, is_employed={self.is_employed}, employer_id={self.employer_id}, Needs={self.needs}",
            extra={
                **log_extra,
                "assets_before": self.assets,
                "is_employed_before": self.is_employed,
                "employer_id_before": self.employer_id,
                "needs_before": self.needs,
            },
        )

        self.logger.debug(
            f"Calling decision_engine.make_decisions for Household {self.id}",
            extra=log_extra,
        )
        context = DecisionContext(
            household=self,
            markets=markets,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            government=government,
        )
        orders, chosen_tactic_tuple = self.decision_engine.make_decisions(context, macro_context)

        # WO-056: Shadow Mode Labor Logic
        self._calculate_shadow_reservation_wage(market_data, current_time)

        # WO-046: Execute System 2 Housing Decision
        if self.housing_target_mode == "BUY" and self.is_homeless:
            # Generate Buy Order if we don't own a home and decided to BUY
            # Strategy: Place order for "housing" generic market or specific units?
            # Housing Market expects item_id "unit_X". But we might not know which unit.
            # OrderBookMarket usually handles "housing" as a generic commodity if ID is just "housing"
            # OR we need to pick a unit.
            # Simulation.process_transactions handles "housing" generic orders?
            # Looking at engine.py, it expects item_id="unit_{id}".
            # So we must pick a unit or place a "Blind" buy order if supported.
            # Engine._process_transactions logic: if tx.transaction_type == "housing" -> _process_housing_transaction.
            # _process_housing_transaction parses "unit_{id}".
            # So we need a target unit.
            # Scan market for Sell Orders on housing?
            housing_market = markets.get("housing")
            if housing_market:
                # Find cheapest unit or random unit
                # HousingMarket is OrderBookMarket.
                # We need to scan asks. But asks are keyed by item_id.
                # We iterate all asks?
                target_unit_id = None
                best_price = float('inf')

                # Check for available units in market_data or query market directly
                # OrderBookMarket structure: sell_orders = {item_id: [Order...]}
                if hasattr(housing_market, "sell_orders"):
                    for item_id, sell_orders in housing_market.sell_orders.items():
                        if item_id.startswith("unit_") and sell_orders:
                            ask_price = sell_orders[0].price # Assuming sorted? OrderBookMarket usually sorts heaps.
                            # OrderBookMarket uses heapq for buy_orders (max heap) and sell_orders (min heap).
                            # So sell_orders[0] is lowest price.
                            if ask_price < best_price:
                                best_price = ask_price
                                target_unit_id = item_id

                if target_unit_id:
                     # Check affordability (assets + mortgage)
                     # Mortgage covers 80%. We need 20%.
                     down_payment = best_price * 0.2
                     if self.assets >= down_payment:
                         buy_order = Order(
                             agent_id=self.id,
                             item_id=target_unit_id,
                             price=best_price,
                             quantity=1.0,
                             market_id="housing",
                             order_type="BUY"
                         )
                         orders.append(buy_order)
                         self.logger.info(f"HOUSING_BUY | Household {self.id} decided to buy {target_unit_id} at {best_price}")

        # --- Phase 6: Targeted Order Refinement ---
        # The AI decides "What to buy", the Household Logic decides "From Whom".
        refined_orders = []
        for order in orders:
            if order.order_type == "BUY" and order.target_agent_id is None:
                # Select best seller
                best_seller_id, best_price = self.choose_best_seller(markets, order.item_id)
                if best_seller_id:
                    order.target_agent_id = best_seller_id
                    # Update price to seller's ask price if logic dictates, 
                    # but usually Order price is 'Max Willingness to Pay'.
                    # If we target, we usually agree to pay Ask Price if it's <= our Order Price.
                    # Or we just set target and let Market handle price check.
                    # The Spec says "Place BuyOrder with target_agent_id".
                    pass 
            refined_orders.append(order)
        orders = refined_orders
        # ------------------------------------------

        # Operation Forensics: Track last labor offer
        for order in orders:
            if order.order_type == "SELL" and (order.item_id == "labor" or order.market_id == "labor"):
                self.last_labor_offer_tick = current_time

        self.logger.debug(
            f"HOUSEHOLD_DECISION_END | Household {self.id} after decision: Assets={self.assets:.2f}, is_employed={self.is_employed}, employer_id={self.employer_id}, Needs={self.needs}, Decisions={len(orders)}",
            extra={
                **log_extra,
                "assets_after": self.assets,
                "is_employed_after": self.is_employed,
                "employer_id_after": self.employer_id,
                "needs_after": self.needs,
                "num_decisions": len(orders),
            },
        )
        return orders, chosen_tactic_tuple

    def choose_best_seller(self, markets: Dict[str, "Market"], item_id: str) -> Tuple[Optional[int], float]:
        """
        Phase 6: Utility-based Seller Selection.
        Delegates to MarketComponent.
        """
        context: MarketInteractionContext = {"markets": markets}
        return self.market_component.choose_best_seller(item_id, context)

    def execute_tactic(
        self,
        tactic: Tactic,
        aggressiveness: Aggressiveness,
        markets: Dict[str, "Market"],
        current_time: int,
    ) -> List["Order"]:
        """
        AI가 결정한 전술과 적극성에 따라 실제 행동을 실행하고 주문을 생성한다.
        이 메서드는 SimulationEngine에서 호출된다.
        """
        log_extra = {
            "tick": current_time,
            "agent_id": self.id,
            "tactic": tactic.name,
            "aggressiveness": aggressiveness.name,
            "tags": ["household_execute_tactic"],
        }
        self.logger.debug(
            f"HOUSEHOLD_EXECUTE_TACTIC | Household {self.id} executing tactic {tactic.name} with aggressiveness {aggressiveness.name}",
            extra=log_extra,
        )

        # 현재는 decision_engine의 _execute_tactic을 직접 호출하여 위임
        # 향후 Household 클래스 내에서 직접 처리하는 로직으로 변경될 수 있음
        orders = self.decision_engine._execute_tactic(
            tactic, aggressiveness, self, markets, current_time
        )
        return orders

    def get_desired_wage(self) -> float:
        """가계가 희망하는 최저 임금을 반환합니다."""
        if self.assets < self.config_module.HOUSEHOLD_LOW_ASSET_THRESHOLD:
            return self.config_module.HOUSEHOLD_LOW_ASSET_WAGE
        return self.config_module.HOUSEHOLD_DEFAULT_WAGE

    def consume(
        self, item_id: str, quantity: float, current_time: int
    ) -> "ConsumptionResult":
        """Delegates consumption to the EconomyManager."""
        return self.economy_manager.consume(item_id, quantity, current_time)

    @override
    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        """
        Delegates the household's tick-level updates to AgentLifecycleComponent.
        """
        context: LifecycleContext = {
            "household": self,
            "market_data": market_data if market_data else {},
            "time": current_tick
        }
        self.lifecycle_component.run_tick(context)

    def _update_skill(self):
        """Delegates skill updates to the LaborManager."""
        self.labor_manager.update_skills()

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Household":
        """
        현재 가계 에이전트의 복제본을 생성합니다 (Mitosis용).
        """
        # === DEMOGRAPHICS REFACTORING START ===

        # 1. 자손의 인구통계 정보 생성 위임
        offspring_demo_data = self.demographics.create_offspring_demographics(new_id, current_tick)

        # 2. 새로운 Household 생성
        cloned_household = Household(
            id=new_id,
            talent=self.talent,
            goods_data=[g for g in self.goods_info_map.values()],
            initial_assets=initial_assets_from_parent,
            initial_needs=self.needs.copy(),
            decision_engine=self._create_new_decision_engine(new_id),
            value_orientation=self.value_orientation,
            personality=self.personality,
            config_module=self.config_module,
            loan_market=self.decision_engine.loan_market,
            risk_aversion=self.risk_aversion,
            logger=self.logger,
            **offspring_demo_data
        )

        # === DEMOGRAPHICS REFACTORING END ===

        # Attribute Sync
        cloned_household.skills = {k: Skill(v.domain, v.value, v.observability) for k, v in self.skills.items()}
        cloned_household.inventory = self.inventory.copy()
        cloned_household.labor_skill = self.labor_skill
        
        # Aptitude Inheritance (WO-054)
        # Regression toward the mean?
        # Child Aptitude = 0.6*Parent + 0.4*Random
        raw_aptitude = (self.aptitude * 0.6) + (random.gauss(0.5, 0.15) * 0.4)
        cloned_household.aptitude = max(0.0, min(1.0, raw_aptitude))

        return cloned_household

    def _create_new_decision_engine(self, new_id: int) -> AIDrivenHouseholdDecisionEngine:
        """
        새로운 DecisionEngine을 생성합니다.
        """
        from simulation.ai.household_ai import HouseholdAI
        from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine
        
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
        """다른 Household의 demographics 컴포넌트에 위임"""
        return self.demographics.get_generational_similarity(self.talent.base_learning_rate, other.talent.base_learning_rate)

    def apply_child_inheritance(self, child: "Household"):
        """
        Phase 19: 자녀에게 기술 및 특성을 물려줍니다.
        """
        # 1. Skill Inheritance (20% of parent's value)
        for domain, skill in self.skills.items():
            child.skills[domain] = Skill(
                domain=domain,
                value=skill.value * 0.2,
                observability=skill.observability
            )
        
        # 2. Update expected wage based on inherited education if applicable
        child.education_level = min(self.education_level, 1) # Reset but maybe give a head start
        child.expected_wage = self.expected_wage * 0.8 # Legacy expectations

    def update_learning(self, context: LearningUpdateContext) -> None:
        """
        ILearningAgent implementation.
        Updates the internal AI engine with the new state and reward.
        """
        # Inject Leisure Utility if present in context (it might be passed as part of next_agent_data by CommerceSystem? No, it's separate)
        # Actually in Simulation.run_tick, we were injecting it into agent_data manually.
        # Ideally, context should carry it or we put it in next_agent_data.
        # The spec says: context has reward, next_agent_data, next_market_data.

        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]

        self.decision_engine.ai_engine.update_learning_v2(
            reward=reward,
            next_agent_data=next_agent_data,
            next_market_data=next_market_data,
        )
