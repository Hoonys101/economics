import logging
import random
from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING

from .api import BaseAIEngine, Intention, Tactic, Aggressiveness
from .q_table_manager import QTableManager
from simulation.schemas import HouseholdActionVector

if TYPE_CHECKING:
    from simulation.ai_model import AIDecisionEngine

logger = logging.getLogger(__name__)


class HouseholdAI(BaseAIEngine):
    """
    가계 에이전트를 위한 AI 엔진.
    Architecture V2: Multi-Channel Aggressiveness Output
    """

    # Discrete Aggressiveness Levels for Q-Learning
    AGGRESSIVENESS_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]

    def __init__(
        self,
        agent_id: str,
        ai_decision_engine: "AIDecisionEngine",
        gamma: float = 0.9,
        epsilon: float = 0.1,
        base_alpha: float = 0.1,
        learning_focus: float = 0.5,
    ):
        super().__init__(agent_id, gamma, epsilon, base_alpha, learning_focus)
        self.ai_decision_engine: AIDecisionEngine | None = None
        self.set_ai_decision_engine(ai_decision_engine)
        
        # New Q-Table Managers
        # One Q-Table per Consumption Category (e.g., 'basic_food', 'luxury')
        self.q_consumption: Dict[str, QTableManager] = {} 
        self.q_work = QTableManager()
        self.q_investment = QTableManager()  # 주식 투자 적극성 Q-테이블

        # State Tracking
        self.last_consumption_states: Dict[str, Tuple] = {}
        self.last_consumption_action_idxs: Dict[str, int] = {}
        self.last_work_state: Optional[Tuple] = None
        self.last_work_action_idx: Optional[int] = None
        self.last_investment_state: Optional[Tuple] = None
        self.last_investment_action_idx: Optional[int] = None

    def set_ai_decision_engine(self, engine: "AIDecisionEngine"):
        self.ai_decision_engine = engine

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state: Assets, General Needs, Debt Ratio, Interest Burden
        """
        # 1. Asset Level
        assets = agent_data.get("assets", 0)
        asset_bins = [100.0, 500.0, 2000.0, 10000.0]
        asset_idx = self._discretize(assets, asset_bins)
        
        # 2. Avg Need Level
        needs = agent_data.get("needs", {})
        avg_need = sum(needs.values()) / max(len(needs), 1)
        need_idx = self._discretize(avg_need, [20, 50, 80])

        # 3. Debt Metrics (from market_data injection)
        debt_info = market_data.get("debt_data", {}).get(self.agent_id, {"total_principal": 0.0, "daily_interest_burden": 0.0})
        total_debt = debt_info.get("total_principal", 0.0)
        interest_burden = debt_info.get("daily_interest_burden", 0.0)

        debt_ratio = total_debt / assets if assets > 0 else 0.0
        debt_idx = self._discretize(debt_ratio, [0.1, 0.3, 0.5, 0.8])
        
        # 4. Interest Burden Ratio (vs Asset or Income Proxy)
        # Using asset as income proxy since income is volatile
        burden_ratio = interest_burden / (assets * 0.01 + 1e-9) # Assume 1% daily return as baseline
        burden_idx = self._discretize(burden_ratio, [0.1, 0.2, 0.5])

        return (asset_idx, need_idx, debt_idx, burden_idx)

    def decide_action_vector(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
        goods_list: List[str] # List of item_ids to decide consumption for
    ) -> HouseholdActionVector:
        """
        Decide aggressiveness for consumption (per item) and work.
        """
        state = self._get_common_state(agent_data, market_data)
        
        # 1. Consumption Aggressiveness
        consumption_aggressiveness = {}
        self.last_consumption_states = {}
        self.last_consumption_action_idxs = {}

        # Task #6: Maslow Gating (Action Masking)
        needs = agent_data.get("needs", {})
        survival_need = needs.get("survival", 0.0)
        # Use config if available via ai_decision_engine, else fallback
        config_module = getattr(self.ai_decision_engine, "config_module", None)
        survival_threshold = getattr(config_module, "MASLOW_SURVIVAL_THRESHOLD", 50.0)
        is_starving = survival_need > survival_threshold

        for item_id in goods_list:
            if item_id not in self.q_consumption:



                self.q_consumption[item_id] = QTableManager()
            
            item_state = state 
            self.last_consumption_states[item_id] = item_state
            
            actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
            action_idx = self.action_selector.choose_action(
                self.q_consumption[item_id], item_state, actions
            )
            self.last_consumption_action_idxs[item_id] = action_idx
            agg = self.AGGRESSIVENESS_LEVELS[action_idx]

            # Apply Gating if Starving
            if is_starving and config_module:
                good_info = config_module.GOODS.get(item_id, {})
                utility_effects = good_info.get("utility_effects", {})
                if utility_effects.get("survival", 0) <= 0:
                    agg = 0.0  # Force passive if no survival benefit

            consumption_aggressiveness[item_id] = agg





        # 2. Work Aggressiveness
        self.last_work_state = state
        work_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
        work_action_idx = self.action_selector.choose_action(
            self.q_work, state, work_actions
        )
        self.last_work_action_idx = work_action_idx
        work_agg = self.AGGRESSIVENESS_LEVELS[work_action_idx]

        # 3. Investment Aggressiveness
        # 자산이 충분할 때만 투자 고려
        assets = agent_data.get("assets", 0)
        if assets >= 500.0 and not is_starving:  # 최소 투자 자산 및 배고프지 않을 때
            self.last_investment_state = state
            inv_actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))
            inv_action_idx = self.action_selector.choose_action(
                self.q_investment, state, inv_actions
            )
            self.last_investment_action_idx = inv_action_idx
            investment_agg = self.AGGRESSIVENESS_LEVELS[inv_action_idx]
        else:
            self.last_investment_state = None
            self.last_investment_action_idx = None
            investment_agg = 0.0

        return HouseholdActionVector(
            consumption_aggressiveness=consumption_aggressiveness,
            work_aggressiveness=work_agg,
            learning_aggressiveness=0.0,
            investment_aggressiveness=investment_agg
        )


    def decide_reproduction(
        self,
        agent_data: Dict[str, Any],
        market_data: Dict[str, Any],
        current_time: int
    ) -> bool:
        """
        Phase 19: Evolutionary Reproduction Decision
        Revised by WO-048 (Adaptive Breeding)
        """
        # 0. Config Access
        config_module = getattr(self.ai_decision_engine, "config_module", None)
        if not config_module:
            return False

        # 1. Biological Constraint
        age = agent_data.get("age", 0.0)
        start_age = getattr(config_module, "REPRODUCTION_AGE_START", 20)
        end_age = getattr(config_module, "REPRODUCTION_AGE_END", 45)

        if not (start_age <= age <= end_age):
            return False

        # Step 1: Technology Check
        tech_enabled = getattr(config_module, "TECH_CONTRACEPTION_ENABLED", True)
        if not tech_enabled:
            fertility_rate = getattr(config_module, "BIOLOGICAL_FERTILITY_RATE", 0.15)
            return random.random() < fertility_rate

        # Step 2: System 2 NPV Calculation (Modern Era)
        # Parameters
        child_monthly_cost = getattr(config_module, "CHILD_MONTHLY_COST", 500.0)
        opp_cost_factor = getattr(config_module, "OPPORTUNITY_COST_FACTOR", 0.5)
        raising_years = getattr(config_module, "RAISING_YEARS", 20)
        child_emotional_value_base = getattr(config_module, "CHILD_EMOTIONAL_VALUE_BASE", 200000.0)
        old_age_support_rate = getattr(config_module, "OLD_AGE_SUPPORT_RATE", 0.1)
        support_years = getattr(config_module, "SUPPORT_YEARS", 20)

        # Proxies
        current_wage = agent_data.get("current_wage", 0.0)
        monthly_income = current_wage * 8.0 * 20.0

        # Cost Calculation
        c_direct = child_monthly_cost * 12 * raising_years
        c_opp = (monthly_income * opp_cost_factor) * 12 * raising_years
        total_cost = c_direct + c_opp

        # Benefit Calculation
        current_children = agent_data.get("children_count", 0)
        u_emotional = child_emotional_value_base / (current_children + 1)

        expected_child_income = monthly_income
        u_support = expected_child_income * old_age_support_rate * 12 * support_years
        total_benefit = u_emotional + u_support

        # NPV
        npv = total_benefit - total_cost

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"WO-048 Reproduction NPV: Agent={self.agent_id} "
                f"Wage={current_wage:.2f} Income={monthly_income:.2f} "
                f"Cost={total_cost:.1f}(Direct={c_direct:.1f}, Opp={c_opp:.1f}) "
                f"Benefit={total_benefit:.1f}(Emo={u_emotional:.1f}, Sup={u_support:.1f}) "
                f"NPV={npv:.2f}"
            )

        return npv > 0

    def update_learning_v2(
        self,
        reward: float,
        next_agent_data: Dict[str, Any],
        next_market_data: Dict[str, Any],
    ) -> None:
        """
        Update Household Q-Tables.
        """
        next_state = self._get_common_state(next_agent_data, next_market_data)
        actions = list(range(len(self.AGGRESSIVENESS_LEVELS)))

        # Update Consumption Q-Tables
        for item_id, q_manager in self.q_consumption.items():
            last_state = self.last_consumption_states.get(item_id)
            last_action = self.last_consumption_action_idxs.get(item_id)
            
            if last_state is not None and last_action is not None:
                q_manager.update_q_table(
                    last_state,
                    last_action,
                    reward,
                    next_state,
                    actions,
                    self.base_alpha,
                    self.gamma
                )

        # Update Work Q-Table
        if self.last_work_state is not None and self.last_work_action_idx is not None:
            self.q_work.update_q_table(
                self.last_work_state,
                self.last_work_action_idx,
                reward,
                next_state,
                actions,
                self.base_alpha,
                self.gamma
            )

        # Update Investment Q-Table
        if self.last_investment_state is not None and self.last_investment_action_idx is not None:
            self.q_investment.update_q_table(
                self.last_investment_state,
                self.last_investment_action_idx,
                reward,
                next_state,
                actions,
                self.base_alpha,
                self.gamma
            )

    # Legacy Methods
    def _get_strategic_state(self, a, m): pass
    def _get_tactical_state(self, i, a, m): pass
    def _get_strategic_actions(self): pass
    def _get_tactical_actions(self, i): pass
    def _calculate_reward(self, pre_state_data, post_state_data, agent_data, market_data):
        """
        가계 보상: Wealth 증분 + 욕구 해소 만족도.
        """
        # 1. Wealth Delta
        wealth_reward = super()._calculate_reward(pre_state_data, post_state_data, agent_data, market_data)
        
        # 2. Need Satisfaction (욕구 감소량)
        pre_needs = pre_state_data.get("needs", {})
        post_needs = post_state_data.get("needs", {})
        
        need_reduction = sum(pre_needs.values()) - sum(post_needs.values())
        
        # 가중치 적용 (config에서 가져오거나 기본값 사용)
        # 팁: 가계의 경우 욕구 해소가 자산 증식보다 더 강력한 동기일 수 있음.
        asset_weight = 1.0
        growth_weight = 5.0 # 욕구 해소에 더 높은 가중치
        
        # 3. Leisure Utility (Phase 5)
        # agent_data is injected with 'leisure_utility' in engine.py
        leisure_utility = agent_data.get("leisure_utility", 0.0)

        # Use config LEISURE_WEIGHT if available, else default 0.3
        leisure_weight = 0.3
        if self.ai_decision_engine and getattr(self.ai_decision_engine, "config_module", None):
            leisure_weight = getattr(self.ai_decision_engine.config_module, "LEISURE_WEIGHT", 0.3)

        total_reward = (
            (wealth_reward * asset_weight) +
            (need_reduction * growth_weight) +
            (leisure_utility * leisure_weight)
        )
        
        # --- Phase 17-4: Vanity Reward (Relative Deprivation) ---
        if self.ai_decision_engine and getattr(self.ai_decision_engine, "config_module", None):
            config = self.ai_decision_engine.config_module
            if getattr(config, "ENABLE_VANITY_SYSTEM", False):
                # Calculate Social Component
                my_rank = agent_data.get("social_rank", 0.5)

                # Reference Group is Top X% (e.g. 0.20 means Top 20%)
                # Percentile Threshold = 1.0 - 0.20 = 0.80
                ref_percentile_threshold = 1.0 - getattr(config, "REFERENCE_GROUP_PERCENTILE", 0.20)

                # Relative Deprivation: Gap from the reference group threshold
                # If my_rank (0.5) < ref (0.8), component is -0.3
                social_component = my_rank - ref_percentile_threshold

                # Conformity Weight
                conformity = agent_data.get("conformity", 0.5) # Fallback 0.5
                vanity_weight = getattr(config, "VANITY_WEIGHT", 1.0)

                vanity_effect = conformity * social_component * vanity_weight
                total_reward += (vanity_effect * 100.0)

        return total_reward
    def decide_time_allocation(
        self,
        agent_data: Dict[str, Any],
        spouse_data: Optional[Dict[str, Any]] = None,
        children_data: List[Dict[str, Any]] = [],
        config_module: Any = None
    ) -> Dict[str, float]:
        """
        Phase 20 Step 2: Socio-Tech Time Demand Model

        Calculates required hours for Housework and Childcare, applying constraints.
        Returns 'time_budget' dictionary.
        """
        if not config_module:
            # Fallback if config not passed (shouldn't happen in proper integration)
            config_module = getattr(self.ai_decision_engine, "config_module", None)

        # 1. Base Housework Demand
        # Range 4-6 hours (randomized or fixed base?) Spec says 4-6h.
        # Config has HOUSEWORK_BASE_HOURS = 6.0
        base_housework = getattr(config_module, "HOUSEWORK_BASE_HOURS", 6.0)

        # Tech Effect: Appliances
        # Logic: If 'appliances' in inventory/installed, reduce housework.
        # Check agent_data for 'home_quality_score' or 'durable_assets'?
        # agent_data is simplified dictionary. We might need to inspect actual agent object if not in data.
        # Ideally agent_data should have 'has_appliances' flag or count.
        # Or we check 'home_quality_score' > 1.0 implies appliances?
        # Let's assume agent_data has 'owned_durables' or similar, OR we check utility efficiency.
        # "Home Quality & Appliances: Appliances reduce housework directly."
        # If agent_data doesn't have inventory, we rely on a simplified flag injected by Engine or Agent.get_agent_data().
        # Let's assume get_agent_data needs update OR we infer from home_quality.

        # Assumption: home_quality_score reflects appliances.
        # Base=1.0. With Appliances=1.5 (due to config utility).
        # We can use home_quality_score to discount housework?
        # Spec says "Appliances directly reduce time".
        # Let's assume a reduction factor if home_quality_score > 1.2

        home_quality = agent_data.get("home_quality_score", 1.0)
        housework_modifier = 1.0
        if home_quality > 1.2:
            housework_modifier = 0.5 # 50% reduction!

        required_housework = base_housework * housework_modifier

        # 2. Childcare Demand (The "Mommy Tax")
        childcare_hours = 0.0
        # Check for children aged 0-2
        has_infant = False
        for child in children_data:
            if child.get("age", 5) <= 2:
                has_infant = True
                break # Only count once per day? Or per child? Spec: "0~2세 자녀 존재 시 +8시간" (Binary condition effectively)

        if has_infant:
            childcare_hours = 8.0

        # 3. Lactation Lock & Sharing Logic
        # Who pays this time cost?
        # Inputs
        gender = agent_data.get("gender", "M")
        tech_level = getattr(config_module, "FORMULA_TECH_LEVEL", 0.0)

        # Determine Share
        my_share_housework = required_housework
        my_share_childcare = childcare_hours

        if spouse_data:
            # Shared Household
            # Default: Split Housework 50/50? Or Traditional?
            # Spec says "Variable sharing". Let's assume 50/50 for Housework if not specified.
            my_share_housework = required_housework * 0.5

            # Childcare Sharing
            if has_infant:
                if tech_level < 0.5: # No Formula
                    # Strong Lactation Lock
                    # If Female: Take 100% of childcare (8h)
                    # If Male: Take 0%
                    if gender == "F":
                        my_share_childcare = childcare_hours
                    else:
                        my_share_childcare = 0.0
                else:
                    # Formula Available -> Shared
                    # 50/50 Split
                    my_share_childcare = childcare_hours * 0.5
        else:
            # Single Parent / Single Household
            # Takes full burden
            pass

        # 4. Construct Budget
        # Total Hours = 24.0
        # Obligatory = Sleep(8?) + Personal(2?) -> usually modeled as 'leisure' min constraint?
        # Here we just output the Demands. The 'Labor' availability is calculated by subtraction in System 2 or Decision Engine.

        return {
            "housework": my_share_housework,
            "childcare": my_share_childcare,
            "total_obligated": my_share_housework + my_share_childcare
        }
