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
from simulation.dtos import DecisionContext, LeisureEffectDTO, LeisureType

# Import HouseholdAI and AIDrivenHouseholdDecisionEngine for mitosis
from simulation.ai.household_ai import HouseholdAI
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine

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


class Household(BaseAgent):
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

        # Initialize personality and desire weights
        self.personality = personality
        self.desire_weights: Dict[str, float] = self._initialize_desire_weights(
            personality
        )

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

        # Phase 4: Bankruptcy Penalty
        self.credit_frozen_until_tick: int = 0

        # Phase 5: Genealogy & Time Allocation
        self.parent_id: Optional[int] = None      # 부모 가구 ID
        self.last_fired_tick: int = -1  # 마지막으로 해고된 Tick (-1이면 없음)
        self.job_search_patience: int = 0 # 구직 활동 기간 (틱 단위)

        # --- Phase 19: Population Dynamics ---
        # Initialize age uniformly between 20 and 60 for initial population
        self.age: float = random.uniform(20.0, 60.0)

        # Education Level (0~5) based on Distribution
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
        self.children_ids: List[int] = []         # 자녀 가구 ID 목록
        self.generation: int = 0                  # 세대 (0=Original, 1=Child, ...)
        self.last_leisure_type: LeisureType = "IDLE"  # For visualization aggregation


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

        Returns:
            Dict[str, float]: 이번 틱에 소비한 아이템과 수량 맵.
        """
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["consumption"]}
        consumed_items: Dict[str, float] = {}

        # 1. 모든 인벤토리 품목에 대해 소비 가능 여부 확인
        for item_id, inventory_quantity in list(self.inventory.items()):
            if inventory_quantity <= 0:
                continue

            good_info = self.goods_info_map.get(item_id)
            if not good_info:
                continue

            utility_effects = good_info.get("utility_effects", {})
            if not utility_effects:
                continue

            should_consume = False
            for need_key, effect in utility_effects.items():
                current_need = self.needs.get(need_key, 0.0)
                
                # 소비 문턱값 설정
                threshold = self.config_module.NEED_MEDIUM_THRESHOLD
                if need_key == "survival":
                    threshold = self.config_module.SURVIVAL_NEED_CONSUMPTION_THRESHOLD
                
                if current_need > threshold:
                    should_consume = True
                    break
            
            if should_consume:
                is_durable = good_info.get("is_durable", False)
                # Fix Logic for Durables: Prevent fractional consumption ("Eating Fridges")
                if is_durable:
                    if inventory_quantity < 1.0:
                        continue  # 1.0개 모일 때까지 절대 소비(설치)하지 말고 대기
                    quantity_to_consume = 1.0 # 강제로 1개 단위로만 소비
                else:
                    quantity_to_consume = min(inventory_quantity, 1.0)
                
                if quantity_to_consume > 0:
                    self.consume(item_id, quantity_to_consume, current_time)
                    consumed_items[item_id] = consumed_items.get(item_id, 0.0) + quantity_to_consume
                    self.logger.debug(
                        f"HOUSEHOLD_CONSUMPTION | Household {self.id} consumed {quantity_to_consume:.2f} {item_id}. Remaining inventory: {self.inventory.get(item_id, 0.0):.2f}",
                        extra={**log_extra, "item_id": item_id, "quantity": quantity_to_consume}
                    )

        # 2. 욕구 업데이트 (자연적 증가/감소)
        self.update_needs(current_time, market_data)
        return consumed_items

    def _initialize_desire_weights(self, personality: Personality) -> Dict[str, float]:
        """
        주어진 특질에 따라 각 욕구의 성장 가중치를 초기화합니다.
        """
        if personality in [Personality.MISER, Personality.CONSERVATIVE]:
            return {"survival": 1.0, "asset": 1.5, "social": 0.5, "improvement": 0.5}
        elif personality in [Personality.STATUS_SEEKER, Personality.IMPULSIVE]:
            return {"survival": 1.0, "asset": 0.5, "social": 1.5, "improvement": 0.5}
        elif personality == Personality.GROWTH_ORIENTED:
            return {"survival": 1.0, "asset": 0.5, "social": 0.5, "improvement": 1.5}
        else:  # Default or unknown personality
            return {"survival": 1.0, "asset": 1.0, "social": 1.0, "improvement": 1.0}

    def calculate_social_status(self) -> None:
        """
        가계의 사회적 지위를 계산하고 업데이트합니다.
        사회적 지위는 가계의 현재 자산과 보유한 사치품의 가치를 기반으로 결정됩니다.
        결과 값은 `self.social_status`에 저장됩니다.
        """
        luxury_goods_value = 0.0
        for item_id, quantity in self.inventory.items():
            good_info = self.goods_info_map.get(item_id)
            if good_info and good_info.get("is_luxury", False):
                luxury_goods_value += quantity

        self.social_status = (
            self.assets * self.config_module.SOCIAL_STATUS_ASSET_WEIGHT
        ) + (luxury_goods_value * self.config_module.SOCIAL_STATUS_LUXURY_WEIGHT)

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
        주어진 여가 시간과 소비 아이템에 따라 여가 유형을 결정하고 효과를 계산합니다.

        Args:
            leisure_hours (float): 할당된 여가 시간.
            consumed_items (Dict[str, float]): 이번 틱에 소비된 아이템.

        Returns:
            LeisureEffectDTO: 계산된 여가 효과 데이터.
        """
        leisure_type: LeisureType = "SELF_DEV"  # Default

        # Determine Leisure Type
        has_children = len(self.children_ids) > 0
        has_education = consumed_items.get("education_service", 0.0) > 0
        has_luxury = (
            consumed_items.get("luxury_food", 0.0) > 0 or
            consumed_items.get("clothing", 0.0) > 0
        )

        if has_children and has_education:
            leisure_type = "PARENTING"
        elif has_luxury:
            leisure_type = "ENTERTAINMENT"
        else:
            leisure_type = "SELF_DEV"

        self.last_leisure_type = leisure_type

        # Apply Effects using Coefficients from Config
        coeffs = self.config_module.LEISURE_COEFFS.get(leisure_type, {})
        utility_per_hour = coeffs.get("utility_per_hour", 0.0)
        xp_gain_per_hour = coeffs.get("xp_gain_per_hour", 0.0)
        productivity_gain = coeffs.get("productivity_gain", 0.0)

        utility_gained = leisure_hours * utility_per_hour
        xp_gained = leisure_hours * xp_gain_per_hour
        prod_gained = leisure_hours * productivity_gain

        # Apply Self-Dev productivity gain immediately to self
        if leisure_type == "SELF_DEV" and prod_gained > 0:
            # Assuming 'productivity' skill or base talent modification
            # For simplicity, let's say it increases 'learning' skill if it exists, or just log for now
            # The spec says "本인 생산성 향상" (Productivity increase)
            # We can model this as labor_skill increase
            self.labor_skill += prod_gained
            self.logger.debug(
                f"LEISURE_SELF_DEV | Household {self.id} increased labor skill by {prod_gained:.4f}. New Skill: {self.labor_skill:.4f}",
                extra={"agent_id": self.id, "tags": ["LEISURE_EFFECT"]}
            )
        elif leisure_type == "ENTERTAINMENT" and utility_gained > 0:
            self.logger.debug(
                f"LEISURE_ENTERTAINMENT | Household {self.id} enjoyed entertainment. Utility: {utility_gained:.4f}",
                extra={"agent_id": self.id, "tags": ["LEISURE_EFFECT"]}
            )

        self.last_leisure_type = leisure_type

        return LeisureEffectDTO(
            leisure_type=leisure_type,
            leisure_hours=leisure_hours,
            utility_gained=utility_gained,
            xp_gained=xp_gained
        )

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
            "age": getattr(self, "age", 30.0),
            "education_level": getattr(self, "education_level", 0),
            "children_count": len(self.children_ids),
            "expected_wage": getattr(self, "expected_wage", 10.0),
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

    @override
    def make_decision(
        self,
        markets: Dict[str, "Market"],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
        government: Optional[Any] = None,
    ) -> Tuple[List["Order"], Tuple["Tactic", "Aggressiveness"]]:
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
        orders, chosen_tactic_tuple = self.decision_engine.make_decisions(context)

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
        Returns (BestSellerID, BestAskPrice)
        """
        market = markets.get(item_id)
        if not market:
            return None, 0.0
        
        # This requires Market to expose 'get_all_asks' with Seller Info
        # We assume order_book_market has get_all_asks(item_id) returning list of SellOrders
        # And SellOrder has agent_id.
        # But we need metadata (Quality, Awareness) which isn't in Order DTO yet?
        # WAIT. The Spec said "Firm places order, it stamps current Brand/Quality on it".
        # I didn't verify SellOrder metadata.
        # IF metadata is missing, we default to 0.5.
        
        asks = market.get_all_asks(item_id) # Should return List[Order]
        if not asks:
            return None, 0.0
            
        best_u = -float('inf')
        best_seller = None
        best_price = 0.0
        
        avg_sales = 10.0 # Default network effect base if unknown
        
        for ask in asks:
            price = ask.price
            seller_id = ask.agent_id
            
            # Phase 6: Read brand metadata from Order (Firm stamps it on SellOrder)
            brand_data = ask.brand_info or {}
            quality = brand_data.get("perceived_quality", 1.0)
            awareness = brand_data.get("brand_awareness", 0.0)
            
            loyalty = self.brand_loyalty.get(seller_id, 1.0)
            
            # Utility Function: U = (Quality * (1 + Awareness * Pref) * Loyalty) / Price
            # Beta (Brand Sensitivity) from Config
            beta = getattr(self.config_module, "BRAND_SENSITIVITY_BETA", 0.5)
            
            # Revised Formula: Q^alpha * (1+A)^beta / P
            # Note: Previous code used (1 + A * Pref). Spec says (1+A)^beta or similar.
            # Architect Prime Spec: U = (Q^alpha * (1+A)^beta) / P
            numerator = (quality ** self.quality_preference) * ((1.0 + awareness) ** beta)
            utility = (numerator * loyalty) / max(0.01, price)
            
            if utility > best_u:
                best_u = utility
                best_seller = seller_id
                best_price = price
        
        return best_seller, best_price

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

    def consume(self, item_id: str, quantity: float, current_time: int) -> None:
        log_extra = {
            "tick": current_time,
            "agent_id": self.id,
            "item_id": item_id,
            "quantity": quantity,
            "tags": ["household_consumption"],
        }
        self.logger.debug(
            f"CONSUME_METHOD_START | Household {self.id} attempting to consume: Item={item_id}, Qty={quantity:.1f}, Inventory={self.inventory.get(item_id, 0):.1f}",
            extra=log_extra,
        )
        good_info = self.goods_info_map.get(item_id, {})
        is_service = good_info.get("is_service", False)

        if is_service or self.inventory.get(item_id, 0) >= quantity:
            # Phase 15: Durable Asset Logic
            is_durable = good_info.get("is_durable", False)

            if is_durable and not is_service:
                # Durables must be consumed in integer units to function
                # Relaxed check for float precision (0.9 instead of 1.0)
                if quantity < 0.9:
                    self.logger.debug(
                        f"DURABLE_CONSUME_FAIL | Household {self.id} tried to consume partial {item_id}: {quantity:.2f}. Minimum 1.0 required.",
                        extra=log_extra
                    )
                    return # Do not consume inventory

                # If quantity valid for durable, reduce inventory
                self.inventory[item_id] -= quantity

                base_lifespan = good_info.get("base_lifespan", 50)
                # Use stored quality or default
                quality = self.inventory_quality.get(item_id, 1.0)

                # Create Asset (Round to nearest integer to handle 0.99 -> 1)
                num_assets = int(round(quantity))
                for _ in range(num_assets):
                    asset = {
                        "item_id": item_id,
                        "quality": quality,
                        "remaining_life": base_lifespan
                    }
                    self.durable_assets.append(asset)
                    self.logger.info(
                        f"DURABLE_ACQUIRED | Household {self.id} installed {item_id}. Quality: {quality:.2f}, Life: {base_lifespan}",
                         extra={**log_extra, "quality": quality}
                    )

            elif not is_service:
                # Standard Consumable
                self.logger.debug(
                    f"CONSUME_METHOD_INVENTORY_OK | Household {self.id} has enough {item_id}. Inventory BEFORE: {self.inventory.get(item_id, 0):.1f}. Survival Need BEFORE: {self.needs.get('survival', 0):.1f}",
                    extra={
                        **log_extra,
                        "inventory_before": self.inventory.get(item_id, 0),
                        "survival_need_before": self.needs.get("survival", 0),
                    },
                )
                self.inventory[item_id] -= quantity

            self.current_consumption += quantity


            if item_id == "food":
                self.current_food_consumption += quantity
                self.logger.debug(
                    f"CONSUME_METHOD_FOOD_UPDATE | Household {self.id} consumed food. Current food consumption: {self.current_food_consumption:.1f}. Inventory AFTER: {self.inventory.get(item_id, 0.0):.1f}. Survival Need AFTER: {self.needs.get('survival', 0):.1f}",
                    extra={
                        **log_extra,
                        "current_food_consumption": self.current_food_consumption,
                        "inventory_after": self.inventory.get(item_id, 0),
                        "survival_need_after": self.needs.get("survival", 0),
                    },
                )

            # Task #6: Gain Education XP
            if item_id == "education_service":
                self.education_xp += quantity * self.config_module.LEARNING_EFFICIENCY
                self.logger.debug(
                    f"EDUCATION | Household {self.id} gained XP. Total XP: {self.education_xp:.2f}",
                    extra={**log_extra, "education_xp": self.education_xp}
                )

            consumed_good = self.goods_info_map.get(item_id)
            # GEMINI_FIX: Check for "utility_effects" (used in config/decide_and_consume) OR "utility_per_need"
            utility_map = None
            if consumed_good:
                if "utility_effects" in consumed_good:
                    utility_map = consumed_good["utility_effects"]
                elif "utility_per_need" in consumed_good:
                    utility_map = consumed_good["utility_per_need"]

            if utility_map:
                for need_type, utility_value in utility_map.items():
                    # Ensure need_type is one of the new needs
                    if need_type in ["survival", "asset", "social", "improvement"]:
                        self.needs[need_type] = max(
                            0, self.needs.get(need_type, 0) - (utility_value * quantity)
                        )
                self.logger.debug(
                    f"CONSUME_METHOD_NEEDS_UPDATE | Household {self.id} consumed {quantity:.1f} of {item_id}. Needs after consumption: Survival={self.needs.get('survival', 0):.1f}, Asset={self.needs.get('asset', 0):.1f}, Social={self.needs.get('social', 0):.1f}, Improvement={self.needs.get('improvement', 0):.1f}",
                    extra={
                        **log_extra,
                        "survival_need": self.needs.get("survival", 0),
                        "asset_need": self.needs.get("asset", 0),
                        "social_need": self.needs.get("social", 0),
                        "improvement_need": self.needs.get("improvement", 0),
                    },

                )
            else:
                self.logger.debug(
                    f"CONSUME_METHOD_NO_UTILITY | Household {self.id} consumed {item_id} but no utility_per_need defined or needs not updated.",
                    extra=log_extra,
                )
        else:
            self.logger.debug(
                f"CONSUME_METHOD_INVENTORY_EMPTY | Household {self.id} tried to consume {item_id} but inventory is empty or insufficient. Inventory: {self.inventory.get(item_id, 0):.1f}, Quantity: {quantity:.1f}",
                extra=log_extra,
            )

    @override
    def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        log_extra = {
            "tick": current_tick,
            "agent_id": self.id,
            "tags": ["needs_update"],
        }
        self.logger.debug(
            f"HOUSEHOLD_NEEDS_UPDATE_START | Household {self.id} needs before update: {self.needs}. Survival Need: {self.needs.get('survival', 0):.2f}",
            extra={**log_extra, "needs_before": self.needs},
        )

        # Phase 15: Durable Asset Utility & Depreciation
        # Apply utility from owning durables BEFORE natural decay
        for asset in list(self.durable_assets):
            item_id = asset["item_id"]
            quality = asset["quality"]

            # Depreciation
            asset["remaining_life"] -= 1
            if asset["remaining_life"] <= 0:
                self.durable_assets.remove(asset)
                self.logger.info(
                    f"DURABLE_BROKEN | Household {self.id}'s {item_id} broke.",
                    extra={**log_extra, "item_id": item_id}
                )
                continue

            # Utility Application
            # Durable utility reduces 'quality' need or 'asset' need?
            # Config says: "utility_effects": {"quality": 10} for consumer_goods
            good_info = self.goods_info_map.get(item_id, {})
            utility_effects = good_info.get("utility_effects", {})

            for need_type, base_utility in utility_effects.items():
                # Utility = Base * Quality
                effective_utility = base_utility * quality
                # Satisfy need (reduce it)
                if need_type in self.needs:
                    self.needs[need_type] = max(0.0, self.needs[need_type] - effective_utility)

        # --- Personality-driven desire growth ---
        base_growth = self.config_module.BASE_DESIRE_GROWTH  # From config.py

        # Survival need grows for all
        self.needs["survival"] += base_growth

        # Other needs grow based on personality weights
        self.needs["asset"] += base_growth * self.desire_weights["asset"]
        self.needs["social"] += base_growth * self.desire_weights["social"]
        self.needs["improvement"] += base_growth * self.desire_weights["improvement"]
        self.needs["quality"] = self.needs.get("quality", 0.0) + (base_growth * self.desire_weights.get("quality", 1.0)) # WO-023

        # Cap all needs at MAX_DESIRE_VALUE
        for need_type in ["survival", "asset", "social", "improvement", "quality"]: # WO-023
            if need_type in self.needs:
                self.needs[need_type] = min(
                    self.config_module.MAX_DESIRE_VALUE, self.needs[need_type]
                )
        # --- End Personality-driven desire growth ---

        # Check for household death conditions
        if self.needs["survival"] >= self.config_module.SURVIVAL_NEED_DEATH_THRESHOLD:
            self.survival_need_high_turns += 1
        else:
            self.survival_need_high_turns = 0

        # WO-023-B: Human Capital Update
        self._update_skill()

        if (
            self.assets <= self.config_module.ASSETS_DEATH_THRESHOLD
            or self.survival_need_high_turns
            >= self.config_module.HOUSEHOLD_DEATH_TURNS_THRESHOLD
        ):
            self.is_active = False

            # Operation Forensics (WO-021)
            # Retrieve forensics data from market_data if available
            market_food_price = None
            job_vacancies = 0

            if market_data:
                 goods_market = market_data.get("goods_market", {})
                 market_food_price = goods_market.get("basic_food_current_sell_price")
                 job_vacancies = market_data.get("job_vacancies", 0)

            self.logger.warning(
                f"AGENT_DEATH | ID: {self.id}",
                extra={
                    "tick": current_tick,
                    "agent_id": self.id,
                    "cause": "starvation",
                    "cash_at_death": self.assets,
                    "food_inventory": self.inventory.get("basic_food", 0),
                    "market_food_price": market_food_price,
                    "last_labor_offer_tick": self.last_labor_offer_tick,
                    "job_vacancies_available": job_vacancies,
                    "survival_need": self.needs["survival"],
                    "tags": ["death", "autopsy"]
                }
            )

            self.logger.warning(
                f"HOUSEHOLD_INACTIVE | Household {self.id} became inactive. Assets: {self.assets:.2f}, Survival Need: {self.needs['survival']:.1f}, High Turns: {self.survival_need_high_turns}",
                extra={
                    **log_extra,
                    "assets": self.assets,
                    "survival_need": self.needs["survival"],
                    "high_turns": self.survival_need_high_turns,
                    "tags": ["death"],
                },
            )
        self.logger.debug(
            f"HOUSEHOLD_NEEDS_UPDATE_END | Household {self.id} needs after update: {self.needs}, is_active={self.is_active}. Survival Need: {self.needs.get('survival', 0):.2f}",
            extra={
                **log_extra,
                "needs_after": self.needs,
                "is_active_after": self.is_active,
            },
        )

    def _update_skill(self):
        """
        WO-023-B: Human Capital Growth Formula
        Labor Skill = 1.0 + ln(XP + 1) * Talent
        """
        import math
        # XP -> Skill Conversion
        # If XP is 0, log(1)=0 -> Skill=1.0 (Base)
        log_growth = math.log1p(self.education_xp)  # ln(x+1)
        
        # Talent Multiplier
        talent_factor = self.talent.base_learning_rate
        
        # New Skill Level
        new_skill = 1.0 + (log_growth * talent_factor)
        
        # Update
        old_skill = self.labor_skill
        self.labor_skill = new_skill
        
        # Optional: Log if significant change (e.g., > 1% increase) or periodically
        if new_skill > old_skill + 0.1:
            self.logger.debug(
                f"SKILL_UP | Household {self.id} skill improved: {old_skill:.2f} -> {new_skill:.2f} (XP: {self.education_xp:.1f})",
                 extra={"tags": ["education", "productivity"]}
            )

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float) -> "Household":
        """
        현재 가계 에이전트의 복제본을 생성합니다.
        """
        # Note: This is a shallow copy for most attributes.
        # Deep copy might be needed for mutable objects like decision_engine, skills, inventory, etc.
        # For now, assuming decision_engine, skills, inventory are re-initialized or handled separately
        # in the context where clone is called.
        cloned_household = Household(
            id=new_id,  # ID might need to be new if it's a new agent, or same if it's a snapshot
            talent=self.talent,  # Talent is immutable, can be shared
            goods_data=list(self.goods_info_map.values()),
            initial_assets=initial_assets_from_parent,  # Use current assets as initial for clone
            initial_needs=self.needs.copy(),  # Copy current needs
            decision_engine=self.decision_engine,  # Decision engine might need to be cloned too
            value_orientation=self.value_orientation,
            personality=self.personality,
            config_module=self.config_module,  # Pass config_module
            loan_market=self.decision_engine.loan_market,  # Pass loan_market if available
            risk_aversion=self.risk_aversion,  # Clone risk aversion
            logger=self.logger,
        )
        # Copy mutable attributes
        cloned_household.skills = self.skills.copy()
        cloned_household.inventory = self.inventory.copy()
        cloned_household.current_consumption = self.current_consumption
        cloned_household.employer_id = self.employer_id
        cloned_household.shares_owned = self.shares_owned.copy()
        cloned_household.is_employed = self.is_employed
        cloned_household.labor_skill = self.labor_skill
        cloned_household.survival_need_high_turns = self.survival_need_high_turns
        cloned_household.social_status = self.social_status
        cloned_household.perceived_avg_prices = self.perceived_avg_prices.copy()
        cloned_household.current_food_consumption = self.current_food_consumption
        cloned_household.credit_frozen_until_tick = self.credit_frozen_until_tick
        cloned_household.owned_properties = self.owned_properties.copy()
        cloned_household.residing_property_id = self.residing_property_id
        cloned_household.is_homeless = self.is_homeless

        return cloned_household

    def _create_new_decision_engine(self, new_id: int) -> AIDrivenHouseholdDecisionEngine:
        """
        새로운 DecisionEngine을 생성합니다 (Mitosis용).
        기존 clone()은 참조만 복사하므로, 완전히 독립적인 새 인스턴스를 생성해야 합니다.
        """
        # Access the shared AIDecisionEngine (central AI logic)
        shared_ai_engine = self.decision_engine.ai_engine.ai_decision_engine

        # Create new HouseholdAI
        new_ai_engine = HouseholdAI(
            agent_id=new_id,
            ai_decision_engine=shared_ai_engine,
            gamma=self.decision_engine.ai_engine.gamma,
            epsilon=self.decision_engine.ai_engine.action_selector.epsilon,
            base_alpha=self.decision_engine.ai_engine.base_alpha,
            learning_focus=self.decision_engine.ai_engine.learning_focus
        )

        # Create new DecisionEngine
        new_decision_engine = AIDrivenHouseholdDecisionEngine(
            ai_engine=new_ai_engine,
            config_module=self.config_module,
            logger=self.logger
        )
        return new_decision_engine
