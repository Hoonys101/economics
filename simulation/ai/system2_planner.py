from typing import Any, Dict, List, Tuple, Optional
import math
import logging

logger = logging.getLogger(__name__)

class System2Planner:
    """
    The 'System 2' Planner (Slow, Deliberative).
    Projects future states to guide System 1 (Impulsive/Fast) constraints.
    """

    def __init__(self, agent: Any, config_module: Any):
        self.agent = agent
        self.config = config_module

        # Hyperparameters
        self.horizon = getattr(self.config, "SYSTEM2_HORIZON", 100)
        self.discount_rate = getattr(self.config, "SYSTEM2_DISCOUNT_RATE", 0.98)
        self.calc_interval = getattr(self.config, "SYSTEM2_TICKS_PER_CALC", 10)

        # State
        self.last_calc_tick = -999
        self.cached_projection: Dict[str, Any] = {}

    def project_future(self, current_tick: int, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Projects future wealth and survival probability.
        Jules: Update this to include Housing Costs (Rent/Mortgage) as per WO-036.
        """
        # Optimization: Run only every X ticks
        if current_tick - self.last_calc_tick < self.calc_interval and self.cached_projection:
            return self.cached_projection

        self.last_calc_tick = current_tick

        # 1. Gather Inputs
        current_wealth = self.agent.assets
        expected_wage = getattr(self.agent, "expected_wage", 10.0)

        # Survival Cost
        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        daily_consumption = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        daily_survival_cost = food_price * daily_consumption

        # A. Determine Work Hours (Existing)
        agent_data = self.agent.get_agent_data()
        household_ai = getattr(self.agent.decision_engine, "ai_engine", None)
        time_obligations = 0.0

        if household_ai and hasattr(household_ai, "decide_time_allocation"):
            spouse_data = {"id": self.agent.spouse_id} if self.agent.spouse_id else None
            c_count = len(self.agent.children_ids)
            dummy_children = [{"age": 1}] if c_count > 0 else []
            alloc = household_ai.decide_time_allocation(agent_data, spouse_data, dummy_children, self.config)
            time_obligations = alloc["total_obligated"]

        available_work_hours = max(0.0, 14.0 - time_obligations)
        projected_work_hours = min(8.0, available_work_hours)

        # TODO: C. Housing Costs Integration (Rent/Mortgage) - See WO-036
        housing_costs = 0.0

        # D. Expenses (Formula)
        extra_expenses = 0.0
        tech_level = getattr(self.config, "FORMULA_TECH_LEVEL", 0.0)
        if len(self.agent.children_ids) > 0:
            if tech_level > 0.5: 
                extra_expenses += 5.0

        daily_income = expected_wage * projected_work_hours
        daily_net_flow = daily_income - daily_survival_cost - extra_expenses - housing_costs

        # 2. Simulation Loop
        npv_wealth = 0.0
        bankruptcy_tick = None
        simulated_wealth = current_wealth

        for t in range(1, self.horizon + 1):
            discount_factor = self.discount_rate ** t
            simulated_wealth += daily_net_flow
            if simulated_wealth < 0 and bankruptcy_tick is None:
                bankruptcy_tick = current_tick + t
            npv_wealth += daily_net_flow * discount_factor

        final_npv = current_wealth + npv_wealth

        result = {
            "npv_wealth": final_npv,
            "bankruptcy_tick": bankruptcy_tick,
            "survival_prob": 1.0 # Heuristic calculation here
        }
        self.cached_projection = result
        return result
