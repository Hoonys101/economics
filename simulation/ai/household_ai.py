import logging
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from .api import BaseAIEngine, Intention, Tactic

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

logger = logging.getLogger(__name__)

class HouseholdAI(BaseAIEngine):
    """
    가계 에이전트를 위한 AI 엔진.
    BaseAIEngine을 상속받아 가계에 특화된 상태, 행동, 보상 함수를 정의한다.
    """
    def __init__(self, agent_id: str, gamma: float = 0.9, epsilon: float = 0.1, base_alpha: float = 0.1, learning_focus: float = 0.5):
        super().__init__(agent_id, gamma, epsilon, base_alpha, learning_focus)
        # AIDecisionEngine 인스턴스를 저장할 속성 초기화
        self.ai_decision_engine: AIDecisionEngine | None = None
        self.last_chosen_tactic: Tactic | None = None
        self.chosen_intention: Intention | None = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        """
        AIDecisionEngine 인스턴스를 외부에서 주입받아 설정합니다.
        이 메서드는 순환 참조 문제를 해결하기 위해 사용됩니다.
        """
        self.ai_decision_engine = engine



    def _discretize(self, value: float, bins: List[float]) -> int:
        """주어진 값을 구간(bin)에 따라 이산화하여 인덱스를 반환한다."""
        for i, b in enumerate(bins):
            if value <= b:
                return i
        return len(bins)

    def _get_strategic_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        가계의 거시적 상태를 정의한다.
        자산과 각 욕구 수준을 5단계로 이산화하여 상태를 표현한다.
        """
        # 자산 수준 (예: 5단계로 구분)
        # TODO: 이 구간 값들은 시뮬레이션의 스케일에 맞춰 동적으로 조정하거나, 통계 기반으로 설정해야 함
        asset_bins = [100, 500, 2000, 10000] 
        discretized_assets = self._discretize(agent_data.get('assets', 0), asset_bins)

        # 욕구 수준 (예: 5단계로 구분)
        need_bins = [10, 30, 60, 100]
        discretized_survival = self._discretize(agent_data.get('needs', {}).get('survival', 0), need_bins)
        discretized_social = self._discretize(agent_data.get('needs', {}).get('social', 0), need_bins)
        discretized_growth = self._discretize(agent_data.get('needs', {}).get('growth', 0), need_bins)

        return (discretized_assets, discretized_survival, discretized_social, discretized_growth)

    def _get_tactical_state(self, intention: Intention, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        선택된 Intention에 따른 가계의 세부 상태를 정의한다.
        각 Intention에 맞는 시장 데이터와 에이전트 데이터를 바탕으로 상태를 이산화한다.
        """
        assets = agent_data.get('assets', 0)
            
        if intention in [Intention.SATISFY_SURVIVAL_NEED, Intention.SATISFY_SOCIAL_NEED]:
            # 소비 관련 전술 상태는 가용 자산과 시장의 평균 상품 가격을 기반으로 한다.
            # HouseholdDecisionEngine에서 상세한 상품별 가격 비교를 수행하므로,
            # AI는 전반적인 구매력에 집중한다.
            avg_goods_price = market_data.get('avg_goods_price', 10.0) # engine.py에서 계산된 평균 가격 사용
            affordability = assets / avg_goods_price if avg_goods_price > 0 else 0
            return (self._discretize(affordability, [1, 2, 5, 10]),)

        elif intention == Intention.INCREASE_ASSETS:
            # 노동 시장 상황 (평균 임금, 실업률)
            # TODO: 'labor_market'에서 실제 데이터를 받아와야 함
            avg_wage = market_data.get('labor', {}).get('avg_wage', 100)
            unemployment_rate = market_data.get('labor', {}).get('unemployment_rate', 0.1)
            
            discretized_wage = self._discretize(avg_wage, [50, 100, 200, 400])
            discretized_unemployment = self._discretize(unemployment_rate, [0.05, 0.1, 0.2, 0.4])
            return (discretized_wage, discretized_unemployment)

        elif intention == Intention.IMPROVE_SKILLS:
            # 교육 투자 여력 (가용 자산 / 교육 비용)
            # 교육 서비스 가격은 goods_market_data에서 가져오도록 변경
            education_cost = market_data.get('goods_market', {}).get('education_service_current_sell_price', 500)
            affordability = assets / education_cost if education_cost > 0 else 0
            return (self._discretize(affordability, [0.5, 1, 1.5, 2.0]),)

        return tuple()

    def _get_strategic_actions(self) -> List[Intention]:
        """
        가계가 선택할 수 있는 Intention 목록.
        """
        return [
            Intention.DO_NOTHING,
            Intention.SATISFY_SURVIVAL_NEED,
            Intention.SATISFY_SOCIAL_NEED,
            Intention.INCREASE_ASSETS,
            Intention.IMPROVE_SKILLS,
        ]

    def _get_tactical_actions(self, intention: Intention) -> List[Tactic]:
        """
        주어진 Intention에 대해 가계가 선택할 수 있는 Tactic 목록.
        """
        if intention in [Intention.SATISFY_SURVIVAL_NEED, Intention.SATISFY_SOCIAL_NEED]:
            return [Tactic.EVALUATE_CONSUMPTION_OPTIONS]
        elif intention == Intention.INCREASE_ASSETS:
            return [Tactic.PARTICIPATE_LABOR_MARKET, Tactic.INVEST_IN_STOCKS]
        elif intention == Intention.IMPROVE_SKILLS:
            return [Tactic.TAKE_EDUCATION]
        return []

    def _calculate_reward(self, pre_state_data: Dict[str, Any], post_state_data: Dict[str, Any], agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """
        가계 행동의 결과로 얻어지는 보상을 계산한다.
        자산 변화, 각 욕구의 감소량에 가중치를 적용하여 보상을 계산한다.
        생존에 실패(자산 0 이하)할 경우 큰 페널티를 부과한다.
        """
        # 보상 가중치
        reward_weights = {
            'expenditure_cost': 0.5,        # 지출 비용 (음의 보상)
            'survival_need_reduction': 5.0, # 생존 욕구 감소 (가장 중요)
            'social_need_reduction': 2.0,   # 사회적 욕구 감소
            'growth_need_reduction': 1.5,   # 성장 욕구 감소
            'bankruptcy_penalty': -1000.0   # 파산 페널티
        }

        # 파산 여부 확인
        if post_state_data.get('assets', 0) <= 0:
            return reward_weights['bankruptcy_penalty']

        # 1. 지출 비용 계산 (음의 보상)
        # 자산 감소가 지출을 의미한다고 가정. 자산 증가분은 지출로 보지 않음.
        expenditure_cost = pre_state_data.get('assets', 0) - post_state_data.get('assets', 0)
        if expenditure_cost < 0: # 자산이 증가했다면 지출은 0
            expenditure_cost = 0
        
        reward = -(expenditure_cost * reward_weights['expenditure_cost'])

        # 2. 욕구 감소 보상 (효용 증가)
        pre_needs = pre_state_data.get('needs', {})
        post_needs = post_state_data.get('needs', {})

        survival_reduction = pre_needs.get('survival', 0) - post_needs.get('survival', 0)
        social_reduction = pre_needs.get('social', 0) - post_needs.get('social', 0)
        growth_reduction = pre_needs.get('growth', 0) - post_needs.get('growth', 0)

        reward += survival_reduction * reward_weights['survival_need_reduction']
        reward += social_reduction * reward_weights['social_need_reduction']
        reward += growth_reduction * reward_weights['growth_need_reduction']
        
        # Integrate predicted reward from AIDecisionEngine
        if self.ai_decision_engine:
            logger.debug(f"HOUSEHOLD_AI_REWARD | AIDecisionEngine present: {self.ai_decision_engine is not None}, is_trained: {self.ai_decision_engine.is_trained}", extra={'tags': ['ai_debug', 'reward_calc']})
            if self.ai_decision_engine.is_trained:
                predicted_reward = self.ai_decision_engine.get_predicted_reward(agent_data, market_data)
                # TODO: Refine how predicted_reward is integrated (e.g., weighting, thresholding)
                reward += predicted_reward * 0.05 # Add a small portion as a bonus
            else:
                logger.debug("HOUSEHOLD_AI_REWARD | AIDecisionEngine not trained, skipping predicted reward integration.", extra={'tags': ['ai_debug', 'reward_calc']})
        else:
            logger.debug("HOUSEHOLD_AI_REWARD | AIDecisionEngine is None, skipping predicted reward integration.", extra={'tags': ['ai_debug', 'reward_calc']})
        
        return reward
