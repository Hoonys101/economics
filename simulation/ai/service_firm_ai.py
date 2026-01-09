import logging
from typing import Any, Dict, Tuple, TYPE_CHECKING, Optional

from simulation.ai.firm_ai import FirmAI
from simulation.ai.enums import Personality

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class ServiceFirmAI(FirmAI):
    """
    서비스 기업용 AI 엔진 (Phase 17-1).
    재고 기반 상태 대신 가동률(Utilization Rate) 기반 상태를 사용.
    """

    def _get_common_state(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple:
        """
        Override standard state with Utilization-based metric.
        """
        # 1. Utilization Level instead of Inventory Level
        # We need capacity and sales from the agent.
        # agent_data comes from firm.get_agent_data().
        # We need to ensure ServiceFirm adds 'capacity_this_tick' and 'sales_volume_this_tick' to agent_data.
        # Standard Firm adds 'sales_volume_this_tick' (actually we added it in engine logic implicitly? No, Firm tracks it).
        # Let's check Firm.get_agent_data in firms.py.
        # It currently does NOT return sales_volume_this_tick. It returns revenue_this_turn.
        # I need to modify Firm or ServiceFirm to include this in get_agent_data.
        # But wait, I can access the agent instance directly if I really need to, but _get_common_state signature is fixed.
        # Actually FirmAI is attached to the agent.
        # agent_data is passed from outside.

        # Let's rely on the passed agent_data. I must update ServiceFirm.get_agent_data override.

        capacity = agent_data.get("capacity_this_tick", 1.0) # Avoid div by 0
        sales = agent_data.get("sales_volume_this_tick", 0.0)

        utilization = sales / capacity if capacity > 0 else 0.0

        # Discretize Utilization
        # 0.0 - 0.5 (Under) -> 0
        # 0.5 - 0.9 (Healthy) -> 1
        # 0.9 - 1.0 (Over) -> 2
        util_idx = 0
        if utilization < 0.5:
            util_idx = 0
        elif utilization < 0.9:
            util_idx = 1
        else:
            util_idx = 2

        # 2. Cash Level (Same as FirmAI)
        cash = agent_data.get("assets", 0)
        cash_idx = self._discretize(cash, [100, 500, 1000, 5000, 10000])

        # 3. Debt Ratio (Same as FirmAI)
        debt_info = market_data.get("debt_data", {}).get(self.agent_id, {"total_principal": 0.0, "daily_interest_burden": 0.0})
        total_debt = debt_info.get("total_principal", 0.0)
        interest_burden = debt_info.get("daily_interest_burden", 0.0)
        debt_ratio = total_debt / cash if cash > 0 else 0.0
        debt_idx = self._discretize(debt_ratio, [0.1, 0.3, 0.5, 0.8])

        # 4. Interest Burden (Same as FirmAI)
        burden_ratio = interest_burden / (cash * 0.01 + 1e-9)
        burden_idx = self._discretize(burden_ratio, [0.1, 0.2, 0.5])

        return (util_idx, cash_idx, debt_idx, burden_idx)

    def calculate_reward(self, firm_agent: "Firm", prev_state: Dict, current_state: Dict) -> float:
        """
        Add Waste Penalty to standard reward.
        """
        # Get base reward (Profit/Brand/etc based on personality)
        base_reward = super().calculate_reward(firm_agent, prev_state, current_state)

        # Calculate Waste Penalty
        # Need waste_this_tick and unit_cost.
        # These should be accessible from firm_agent if it's passed.
        # Yes, firm_agent is passed.

        if hasattr(firm_agent, "waste_this_tick") and hasattr(firm_agent, "capacity_this_tick"):
            waste = firm_agent.waste_this_tick
            capacity = firm_agent.capacity_this_tick
            expenses = firm_agent.expenses_this_tick # Tracked in Firm

            unit_cost = expenses / capacity if capacity > 0 else 0.0
            penalty_factor = getattr(firm_agent.config_module, "SERVICE_WASTE_PENALTY_FACTOR", 0.5)

            penalty = waste * unit_cost * penalty_factor

            total_reward = base_reward - penalty

            logger.debug(
                f"SERVICE_REWARD | Firm {firm_agent.id} | Base: {base_reward:.2f}, Penalty: {penalty:.2f} (Waste: {waste:.1f})",
                extra={"agent_id": firm_agent.id, "tags": ["ai_reward", "service"]}
            )
            return total_reward

        return base_reward
