from typing import List, Dict, Any, Optional
import logging
from logging import Logger

from simulation.base_agent import BaseAgent
from simulation.decisions.household_decision_engine import HouseholdDecisionEngine # HouseholdDecisionEngine 임포트
import config # config.py를 파일 상단에서 임포트
from simulation.models import Transaction
from simulation.ai_model import AIDecisionEngine # AIDecisionEngine 임포트
from simulation.loan_market import LoanMarket # LoanMarket 임포트

logger = logging.getLogger(__name__)

class Talent:
    """가계의 선천적 재능을 나타내는 클래스입니다.

    재능은 학습 속도와 특정 기술 도메인의 최대 역량치에 영향을 미칩니다.
    """
    base_learning_rate: float
    max_potential: Dict[str, float]
    related_domains: Dict[str, List[str]]

    def __init__(self, base_learning_rate: float, max_potential: Dict[str, float], related_domains: Optional[Dict[str, List[str]]] = None) -> None:
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

    def __init__(self, domain: str, value: float = 0.0, observability: float = 0.5) -> None:
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
        decision_engine (HouseholdDecisionEngine): 가계의 의사결정 로직을 담당하는 엔진.
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
    def __init__(self, id: int, talent: Talent, goods_data: List[Dict[str, Any]], initial_assets: float, initial_needs: Dict[str, float], decision_engine: HouseholdDecisionEngine, value_orientation: str, loan_market: Optional[LoanMarket] = None, ai_engine: Optional[AIDecisionEngine] = None, logger: Optional[Logger] = None):
        """Household 클래스의 생성자입니다.

        Args:
            id (int): 가계의 고유 ID.
            talent (Talent): 가계의 선천적 재능.
            goods_data (List[Dict[str, Any]]): 시뮬레이션 내 모든 재화에 대한 정보.
            initial_assets (float): 가계의 초기 자산.
            initial_needs (Dict[str, float]): 가계의 초기 욕구 수준.
            decision_engine (HouseholdDecisionEngine): 가계의 의사결정 로직을 담당하는 엔진.
            value_orientation (str): 가계의 가치관.
            loan_market (Optional[LoanMarket]): 대출 시장 인스턴스. 기본값은 None.
            ai_engine (Optional[AIDecisionEngine]): AI 의사결정 엔진 인스턴스. 기본값은 None.
            logger (Optional[Logger]): 로거 인스턴스. 기본값은 None.
        """
        super().__init__(id, initial_assets, initial_needs, decision_engine, value_orientation, name=f"Household_{id}", logger=logger)
        self.talent = talent
        self.skills: Dict[str, Skill] = {}
        self.goods_info_map: Dict[str, Dict[str, Any]] = {g['id']: g for g in goods_data}
        self.needs.setdefault("labor_need", 0.0)
        self.needs["wealth_need"] = initial_needs.get("wealth_need", 0.0)
        self.needs["imitation_need"] = initial_needs.get("imitation_need", 0.0)
        self.needs["child_rearing_need"] = initial_needs.get("child_rearing_need", 0.0)
        self.current_food_consumption: float = 0.0
        self.current_consumption: float = 0.0
        self.employer_id: Optional[int] = None
        self.shares_owned: Dict[int, float] = {}
        self.is_employed: bool = False
        self.labor_skill: float = 1.0
        self.survival_need_high_turns: int = 0
        self.social_status: float = 0.0
        self.perceived_avg_prices: Dict[str, float] = {}

        self.decision_engine.loan_market = loan_market

    def calculate_social_status(self) -> None:
        """
        가계의 사회적 지위를 계산하고 업데이트합니다.
        사회적 지위는 가계의 현재 자산과 보유한 사치품의 가치를 기반으로 결정됩니다.
        결과 값은 `self.social_status`에 저장됩니다.
        """
        luxury_goods_value = 0.0
        for item_id, quantity in self.inventory.items():
            good_info = self.goods_info_map.get(item_id)
            if good_info and good_info.get('is_luxury', False):
                luxury_goods_value += quantity
        
        self.social_status = (self.assets * config.SOCIAL_STATUS_ASSET_WEIGHT) + \
                             (luxury_goods_value * config.SOCIAL_STATUS_LUXURY_WEIGHT)

    def update_perceived_prices(self, market_data: Dict[str, Any]) -> None:
        """
        시장에서 인지된 상품 가격을 업데이트합니다.
        실제 시장 가격과 기존 인지 가격을 기반으로 가계의 인지 가격을 조정합니다.

        Args:
            market_data (Dict[str, Any]): 현재 시장 데이터를 포함하는 딕셔너리입니다.
                                         'goods_market' 키를 통해 상품 시장 정보에 접근합니다.
        """
        goods_market = market_data.get('goods_market')
        if not goods_market:
            return

        for good in self.goods_info_map.values():
            item_id = good['id']
            actual_price = goods_market.get(f'{item_id}_avg_traded_price')

            if actual_price is not None and actual_price > 0:
                old_perceived_price = self.perceived_avg_prices.get(item_id, actual_price)
                new_perceived_price = (config.PERCEIVED_PRICE_UPDATE_FACTOR * actual_price) + \
                                      ((1 - config.PERCEIVED_PRICE_UPDATE_FACTOR) * old_perceived_price)
                self.perceived_avg_prices[item_id] = new_perceived_price


    def make_decision(self, market_data: Dict[str, Any], current_time: int) -> List[Transaction]:
        self.calculate_social_status()
        
        log_extra = {'tick': current_time, 'agent_id': self.id, 'tags': ['household_action']}
        self.logger.debug(f"HOUSEHOLD_DECISION_START | Household {self.id} before decision: Assets={self.assets:.2f}, is_employed={self.is_employed}, employer_id={self.employer_id}, Needs={self.needs}", extra={**log_extra, 'assets_before': self.assets, 'is_employed_before': self.is_employed, 'employer_id_before': self.employer_id, 'needs_before': self.needs})

        self.logger.debug(f"Calling decision_engine.make_decisions for Household {self.id}", extra=log_extra)
        decisions = self.decision_engine.make_decisions(self, current_time, market_data)
        self.logger.debug(f"HOUSEHOLD_DECISION_END | Household {self.id} after decision: Assets={self.assets:.2f}, is_employed={self.is_employed}, employer_id={self.employer_id}, Needs={self.needs}, Decisions={len(decisions)}", extra={**log_extra, 'assets_after': self.assets, 'is_employed_after': self.is_employed, 'employer_id_after': self.employer_id, 'needs_after': self.needs, 'num_decisions': len(decisions)})
        return decisions

    def consume(self, item_id: str, quantity: float, current_time: int) -> None:
        log_extra = {'tick': current_time, 'agent_id': self.id, 'item_id': item_id, 'quantity': quantity}
        self.logger.debug(f"Attempting to consume: Item={item_id}, Qty={quantity:.1f}, Inventory={self.inventory.get(item_id, 0):.1f}", extra=log_extra)
        if self.inventory.get(item_id, 0) >= quantity:
            self.logger.debug(f"Consuming {quantity:.1f} of {item_id}. Inventory BEFORE: {self.inventory.get(item_id, 0):.1f}. Survival Need BEFORE: {self.needs.get('survival_need', 0):.1f}", extra={**log_extra, 'inventory_before': self.inventory.get(item_id, 0), 'survival_need_before': self.needs.get('survival_need', 0)})
            self.inventory[item_id] -= quantity
            self.current_consumption += quantity 
            
            if item_id == 'food':
                self.current_food_consumption += quantity
                self.logger.debug(f"Consumed {quantity:.1f} of food. Current food consumption: {self.current_food_consumption:.1f}. Inventory AFTER: {self.inventory.get(item_id, 0):.1f}. Survival Need AFTER: {self.needs.get('survival_need', 0):.1f}", extra={**log_extra, 'current_food_consumption': self.current_food_consumption, 'inventory_after': self.inventory.get(item_id, 0), 'survival_need_after': self.needs.get('survival_need', 0)})

            consumed_good = self.goods_info_map.get(item_id)
            if consumed_good and 'utility_per_need' in consumed_good:
                for need_type, utility_value in consumed_good['utility_per_need'].items():
                    self.needs[need_type] = max(0, self.needs.get(need_type, 0) - (utility_value * quantity))
                self.logger.info(f"Consumed {quantity:.1f} of {item_id}. Needs after consumption: Survival={self.needs['survival_need']:.1f}, Recognition={self.needs['recognition_need']:.1f}, Growth={self.needs['growth_need']:.1f}, Liquidity={self.needs['liquidity_need']:.1f}, Imitation={self.needs['imitation_need']:.1f}", extra={**log_extra, 'survival_need': self.needs['survival_need'], 'recognition_need': self.needs['recognition_need'], 'growth_need': self.needs['growth_need'], 'liquidity_need': self.needs['liquidity_need'], 'imitation_need': self.needs['imitation_need']})

    def update_needs(self, current_time: int) -> None:
        log_extra = {'tick': current_time, 'agent_id': self.id, 'tags': ['needs_update']}
        self.logger.debug(f"HOUSEHOLD_NEEDS_UPDATE_START | Household {self.id} needs before update: Survival={self.needs["survival_need"]:.1f}, Labor={self.needs["labor_need"]:.1f}, Assets={self.assets:.2f}, is_employed={self.is_employed}", extra={**log_extra, 'needs_before': self.needs, 'assets_before': self.assets, 'is_employed_before': self.is_employed})
        
        self.needs["survival_need"] += config.SURVIVAL_NEED_INCREASE_RATE
        self.needs["survival_need"] = min(100.0, self.needs["survival_need"])

        if self.needs["survival_need"] > config.NEED_MEDIUM_THRESHOLD:
            self.needs["labor_need"] += (self.needs["survival_need"] - config.NEED_MEDIUM_THRESHOLD) * config.SURVIVAL_TO_LABOR_NEED_FACTOR
            self.needs["labor_need"] = min(100.0, self.needs["labor_need"])

        self.needs["recognition_need"] += config.RECOGNITION_NEED_INCREASE_RATE
        if self.needs["survival_need"] < config.NEED_MEDIUM_THRESHOLD:
            pass
        elif self.needs["survival_need"] < config.NEED_HIGH_THRESHOLD:
            self.needs["recognition_need"] += config.RECOGNITION_NEED_INCREASE_RATE * 0.5
        else:
            self.needs["recognition_need"] = max(0, self.needs["recognition_need"] - config.RECOGNITION_NEED_INCREASE_RATE * 0.1)
        self.needs["recognition_need"] = min(100.0, self.needs["recognition_need"])

        if self.needs["survival_need"] < config.NEED_MEDIUM_THRESHOLD and self.needs["recognition_need"] < config.NEED_MEDIUM_THRESHOLD:
            self.needs["growth_need"] += config.GROWTH_NEED_INCREASE_RATE
        elif self.needs["survival_need"] < config.NEED_HIGH_THRESHOLD or self.needs["recognition_need"] < config.NEED_HIGH_THRESHOLD:
            self.needs["growth_need"] += config.GROWTH_NEED_INCREASE_RATE * 0.5
        else:
            self.needs["growth_need"] = max(0, self.needs["growth_need"] - config.GROWTH_NEED_INCREASE_RATE * 0.1)
        self.needs["growth_need"] = min(100.0, self.needs["growth_need"])

        self.needs["liquidity_need"] += config.LIQUIDITY_NEED_INCREASE_RATE
        self.needs["liquidity_need"] = min(100.0, self.needs["liquidity_need"])

        if (self.needs["survival_need"] < config.NEED_MEDIUM_THRESHOLD or 
            self.needs["recognition_need"] < config.NEED_MEDIUM_THRESHOLD or 
            self.needs["growth_need"] < config.NEED_MEDIUM_THRESHOLD):
            pass
        else:
            self.needs["wealth_need"] += config.WEALTH_NEED_INCREASE_RATE
        self.needs["wealth_need"] = min(100.0, self.needs["wealth_need"])

        self.needs["imitation_need"] += config.IMITATION_NEED_INCREASE_RATE * (1 + self.needs["recognition_need"] / 100.0)
        self.needs["imitation_need"] = min(100.0, self.needs["imitation_need"])
        self.logger.debug(f"Imitation Need updated to: {self.needs['imitation_need']:.2f}", extra={**log_extra, 'imitation_need': self.needs['imitation_need']})

        if (self.needs["survival_need"] < config.NEED_MEDIUM_THRESHOLD and 
            self.needs["recognition_need"] < config.NEED_MEDIUM_THRESHOLD and 
            self.needs["growth_need"] < config.NEED_MEDIUM_THRESHOLD and 
            self.needs["wealth_need"] < config.NEED_MEDIUM_THRESHOLD):
            self.needs["child_rearing_need"] += config.CHILD_REARING_NEED_INCREASE_RATE
        self.needs["child_rearing_need"] = min(100.0, self.needs["child_rearing_need"])

        if self.needs["survival_need"] >= config.SURVIVAL_NEED_DEATH_THRESHOLD:
            self.survival_need_high_turns += 1
        else:
            self.survival_need_high_turns = 0

        if (self.assets <= config.ASSETS_DEATH_THRESHOLD or 
            self.survival_need_high_turns >= config.HOUSEHOLD_DEATH_TURNS_THRESHOLD):
            self.is_active = False
            self.logger.warning(f"HOUSEHOLD_INACTIVE | Household {self.id} became inactive. Assets: {self.assets:.2f}, Survival Need: {self.needs['survival_need']:.1f}, High Turns: {self.survival_need_high_turns}", extra={**log_extra, 'assets': self.assets, 'survival_need': self.needs['survival_need'], 'high_turns': self.survival_need_high_turns, 'tags': ['death']})
        self.logger.debug(f"HOUSEHOLD_NEEDS_UPDATE_END | Household {self.id} needs after update: Survival={self.needs["survival_need"]:.1f}, Labor={self.needs["labor_need"]:.1f}, Assets={self.assets:.2f}, is_employed={self.is_employed}, is_active={self.is_active}", extra={**log_extra, 'needs_after': self.needs, 'assets_after': self.assets, 'is_employed_after': self.is_employed, 'is_active_after': self.is_active})
