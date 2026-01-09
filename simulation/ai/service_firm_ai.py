from typing import Any, Dict, Tuple, TYPE_CHECKING
import logging

from .firm_ai import FirmAI
from .enums import Personality

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class ServiceFirmAI(FirmAI):
    """
    서비스 기업 전용 AI (Phase 17-1).
    - Inventory Level 대신 Utilization Rate(가동률) 사용.
    - Reward 계산 시 Waste Penalty 적용.
    """

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Common state features for Service Firm.
        Differences:
        - Channel 0: Inventory Level -> Utilization Rate
        """
        # 1. Utilization Rate (Sales / Capacity)
        capacity = agent_data.get("capacity_this_tick", 0.0)
        sales = agent_data.get("sales_this_tick", 0.0)

        utilization = 0.0
        if capacity > 0:
            utilization = sales / capacity

        # Discretize Utilization
        # 0.0 - 0.5: Low (Under-utilized)
        # 0.5 - 0.9: Good
        # 0.9 - 1.0: High (Over-utilized / Efficient)
        # > 1.0: Oversold (Should not happen if blocked by inventory logic, but logically possible if demand > supply)
        util_idx = self._discretize(utilization, [0.5, 0.9, 1.0])

        # 2. Cash Level (Same as parent)
        cash = agent_data.get("assets", 0)
        cash_idx = self._discretize(cash, [100, 500, 1000, 5000, 10000])

        # 3. Debt Ratio (Same as parent)
        debt_info = market_data.get("debt_data", {}).get(self.agent_id, {"total_principal": 0.0, "daily_interest_burden": 0.0})
        total_debt = debt_info.get("total_principal", 0.0)
        debt_ratio = total_debt / cash if cash > 0 else 0.0
        debt_idx = self._discretize(debt_ratio, [0.1, 0.3, 0.5, 0.8])

        # 4. Interest Burden (Same as parent)
        interest_burden = debt_info.get("daily_interest_burden", 0.0)
        burden_ratio = interest_burden / (cash * 0.01 + 1e-9)
        burden_idx = self._discretize(burden_ratio, [0.1, 0.2, 0.5])

        return (util_idx, cash_idx, debt_idx, burden_idx)

    def calculate_reward(self, firm_agent: "Firm", prev_state: Dict, current_state: Dict) -> float:
        """
        Calculate Reward with Waste Penalty.
        Reward = NetProfit - (Waste * UnitCost * PenaltyFactor)
        """
        # 1. Base Reward (Profit/Brand/etc via Parent Logic OR Reimplemented?)
        # Spec says: "Override calculate_reward ... Add Penalty: Waste Penalty."
        # It implies adding to the base metric (Net Profit).

        # Calculate Net Profit (Asset Delta)
        current_assets = current_state.get("assets", 0.0)
        prev_assets = prev_state.get("assets", 0.0)
        net_profit = current_assets - prev_assets

        # 2. Calculate Waste Penalty
        # Get from firm_agent directly or current_state (if we added it to get_agent_data)
        # We added waste_this_tick to get_agent_data in ServiceFirm.
        waste = current_state.get("waste_this_tick", 0.0)
        capacity = current_state.get("capacity_this_tick", 0.0)
        expenses = current_state.get("expenses_this_tick", 0.0)

        # Unit Cost = Expenses / Capacity
        # Note: expenses_this_tick includes wages, maintenance, etc.
        unit_cost = 0.0
        if capacity > 0:
            unit_cost = expenses / capacity
        elif expenses > 0:
            unit_cost = expenses # Fallback if capacity 0 but expenses exist

        penalty_factor = getattr(firm_agent.config_module, "SERVICE_WASTE_PENALTY_FACTOR", 0.5)
        waste_penalty = waste * unit_cost * penalty_factor

        # 3. Final Reward
        reward = net_profit - waste_penalty

        # Log for debugging
        if waste_penalty > 0:
            logger.debug(
                f"SERVICE_REWARD | Firm {firm_agent.id} | Profit: {net_profit:.2f}, Waste: {waste:.1f}, Penalty: {waste_penalty:.2f}, Final: {reward:.2f}",
                extra={"agent_id": firm_agent.id}
            )

        return reward
