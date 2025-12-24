from __future__ import annotations
from typing import List, Dict, Any, Optional, override, Tuple, TYPE_CHECKING
import logging
from logging import Logger

from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.models import Order
from simulation.ai.api import (
    Personality,
    Tactic,
    Aggressiveness,
)  # Personality, Tactic, Aggressiveness Enum 임포트
from simulation.core_markets import Market  # Import Market
from simulation.dtos import DecisionContext

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
        self.logger.debug(
            f"HOUSEHOLD_INIT | Household {self.id} initialized. Initial Needs: {self.needs}",
            extra={"tags": ["household_init"]},
        )
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

        # Initialize new desires based on the personality-driven model

        # Remove old needs that are replaced by the new model
        # self.needs.setdefault("labor_need", 0.0) # Replaced by 'asset' or 'survival' indirectly
        # self.needs["wealth_need"] = initial_needs.get("wealth_need", 0.0) # Replaced by 'asset'
        # self.needs["imitation_need"] = initial_needs.get("imitation_need", 0.0) # Replaced by 'social'
        # self.needs["child_rearing_need"] = initial_needs.get("child_rearing_need", 0.0) # Not directly mapped to new model yet

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

        self.config_module = config_module  # Store config_module
        self.decision_engine.loan_market = loan_market
        self.decision_engine.logger = self.logger  # Pass logger to decision engine

    def quit(self) -> None:
        """현재 직장에서 퇴사합니다."""
        if self.is_employed:
            self.logger.info(f"Household {self.id} is quitting from Firm {self.employer_id}")
            self.is_employed = False
            self.employer_id = None
            self.current_wage = 0.0

    def decide_and_consume(self, current_time: int) -> None:
        """가계가 현재 욕구 상태와 보유 재고를 바탕으로 재화를 소모합니다."""
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["consumption"]}

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
                # 기본적으로 1.0 단위를 소모 (재고가 적으면 재정량만큼)
                quantity_to_consume = min(inventory_quantity, 1.0) 
                
                if quantity_to_consume > 0:
                    self.consume(item_id, quantity_to_consume, current_time)
                    self.logger.info(
                        f"HOUSEHOLD_CONSUMPTION | Household {self.id} consumed {quantity_to_consume:.2f} {item_id}. Remaining inventory: {self.inventory.get(item_id, 0.0):.2f}",
                        extra={**log_extra, "item_id": item_id, "quantity": quantity_to_consume}
                    )

        # 2. 욕구 업데이트 (자연적 증가/감소)
        self.update_needs(current_time)

    def _initialize_desire_weights(self, personality: Personality) -> Dict[str, float]:
        """
        주어진 특질에 따라 각 욕구의 성장 가중치를 초기화합니다.
        """
        if personality == Personality.MISER:
            return {"survival": 1.0, "asset": 1.5, "social": 0.5, "improvement": 0.5}
        elif personality == Personality.STATUS_SEEKER:
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

    def update_perceived_prices(self, market_data: Dict[str, Any]) -> None:
        """
        시장에서 인지된 상품 가격을 업데이트합니다.
        실제 시장 가격과 기존 인지 가격을 기반으로 가계의 인지 가격을 조정합니다.

        Args:
            market_data (Dict[str, Any]): 현재 시장 데이터를 포함하는 딕셔너리입니다.
                                         'goods_market' 키를 통해 상품 시장 정보에 접근합니다.
        """
        goods_market = market_data.get("goods_market")
        if not goods_market:
            return

        for good in self.goods_info_map.values():
            item_id = good["id"]
            actual_price = goods_market.get(f"{item_id}_avg_traded_price")

            if actual_price is not None and actual_price > 0:
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
        }
    # AI 상태 결정에 필요한 다른 데이터 추가 가능

    def get_pre_state_data(self) -> Dict[str, Any]:
        """
        AI 학습을 위한 이전 상태 데이터를 반환합니다.
        """
        return getattr(self, "pre_state_snapshot", self.get_agent_data())

    @override
    def make_decision(
        self,
        markets: Dict[str, "Market"],
        goods_data: List[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
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
        )
        orders, chosen_tactic_tuple = self.decision_engine.make_decisions(context)

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
    #                 * 0.5
    #             )  # 최대 50%까지 감소
    #
    #     # 최소 임금 보장
    #     return max(desired_wage, self.config_module.LABOR_MARKET_MIN_WAGE)

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
        if self.inventory.get(item_id, 0) >= quantity:
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
                    f"CONSUME_METHOD_FOOD_UPDATE | Household {self.id} consumed food. Current food consumption: {self.current_food_consumption:.1f}. Inventory AFTER: {self.inventory.get(item_id, 0):.1f}. Survival Need AFTER: {self.needs.get('survival', 0):.1f}",
                    extra={
                        **log_extra,
                        "current_food_consumption": self.current_food_consumption,
                        "inventory_after": self.inventory.get(item_id, 0),
                        "survival_need_after": self.needs.get("survival", 0),
                    },
                )

            consumed_good = self.goods_info_map.get(item_id)
            if consumed_good and "utility_per_need" in consumed_good:
                for need_type, utility_value in consumed_good[
                    "utility_per_need"
                ].items():
                    # Ensure need_type is one of the new needs
                    if need_type in ["survival", "asset", "social", "improvement"]:
                        self.needs[need_type] = max(
                            0, self.needs.get(need_type, 0) - (utility_value * quantity)
                        )
                self.logger.info(
                    f"CONSUME_METHOD_NEEDS_UPDATE | Household {self.id} consumed {quantity:.1f} of {item_id}. Needs after consumption: Survival={self.needs['survival']:.1f}, Asset={self.needs['asset']:.1f}, Social={self.needs['social']:.1f}, Improvement={self.needs['improvement']:.1f}",
                    extra={
                        **log_extra,
                        "survival_need": self.needs["survival"],
                        "asset_need": self.needs["asset"],
                        "social_need": self.needs["social"],
                        "improvement_need": self.needs["improvement"],
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
    def update_needs(self, current_tick: int):
        log_extra = {
            "tick": current_tick,
            "agent_id": self.id,
            "tags": ["needs_update"],
        }
        self.logger.debug(
            f"HOUSEHOLD_NEEDS_UPDATE_START | Household {self.id} needs before update: {self.needs}. Survival Need: {self.needs.get('survival', 0):.2f}",
            extra={**log_extra, "needs_before": self.needs},
        )

        # --- Personality-driven desire growth ---
        base_growth = self.config_module.BASE_DESIRE_GROWTH  # From config.py

        # Survival need grows for all
        self.needs["survival"] += base_growth

        # Other needs grow based on personality weights
        self.needs["asset"] += base_growth * self.desire_weights["asset"]
        self.needs["social"] += base_growth * self.desire_weights["social"]
        self.needs["improvement"] += base_growth * self.desire_weights["improvement"]

        # Cap all needs at MAX_DESIRE_VALUE
        for need_type in ["survival", "asset", "social", "improvement"]:
            self.needs[need_type] = min(
                self.config_module.MAX_DESIRE_VALUE, self.needs[need_type]
            )
        # --- End Personality-driven desire growth ---

        # --- Old needs logic (to be removed or re-evaluated) ---
        # The following needs are now managed by the new personality-driven system
        # or are derived from other needs. They should be removed or integrated.
        # For now, I will comment them out to avoid conflicts.
        # self.needs["labor_need"] += ...
        # self.needs["recognition_need"] += ...
        # self.needs["growth_need"] += ...
        # self.needs["liquidity_need"] += ...
        # self.needs["wealth_need"] += ...
        # self.needs["imitation_need"] += ...
        # self.needs["child_rearing_need"] += ...
        # --- End Old needs logic ---

        # Check for household death conditions
        if self.needs["survival"] >= self.config_module.SURVIVAL_NEED_DEATH_THRESHOLD:
            self.survival_need_high_turns += 1
        else:
            self.survival_need_high_turns = 0

        if (
            self.assets <= self.config_module.ASSETS_DEATH_THRESHOLD
            or self.survival_need_high_turns
            >= self.config_module.HOUSEHOLD_DEATH_TURNS_THRESHOLD
        ):
            self.is_active = False
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

        return cloned_household
