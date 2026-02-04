from typing import Any, Dict, List, Tuple, Optional
import math
import logging
from modules.system.api import DEFAULT_CURRENCY

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
        Phase 20 Step 3: Includes Housing Costs (Rent/Mortgage)
        """
        # Optimization: Run only every X ticks
        if current_tick - self.last_calc_tick < self.calc_interval and self.cached_projection:
            return self.cached_projection

        self.last_calc_tick = current_tick

        # 1. Gather Inputs
        current_wealth = 0.0
        if hasattr(self.agent, 'wallet'):
            current_wealth = self.agent.wallet.get_balance(DEFAULT_CURRENCY)
        elif hasattr(self.agent, 'assets') and isinstance(self.agent.assets, dict):
            current_wealth = self.agent.assets.get(DEFAULT_CURRENCY, 0.0)
        elif hasattr(self.agent, 'assets'):
            current_wealth = float(self.agent.assets)

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

        # C. Housing Costs Integration (Rent/Mortgage)
        housing_costs = 0.0

        # Scenario 1: Homeowner with Mortgage
        # We check actual daily interest burden from Bank via injected debt_data
        debt_data_map = market_data.get("debt_data", {})
        my_debt = debt_data_map.get(self.agent.id, {})
        daily_interest = my_debt.get("daily_interest_burden", 0.0)

        # Scenario 2: Renter (or Homeless)
        # If I don't own the home I live in, or I am homeless -> I pay rent (or should pay rent)
        # Note: If homeless, cost is 0 financially but huge utility penalty.
        # But System 2 tracks financial solvency. Homeless people might eventually rent.
        # However, strictly:
        # If agent.residing_property_id is NOT in agent.owned_properties -> Renter.
        # If agent.is_homeless -> Potential Renter (Assumed to pay rent to survive or 0)
        # Spec says: "If agent.is_homeless or no resident property: deduct avg_rent_price"

        is_homeowner = False
        if self.agent.residing_property_id is not None:
            if self.agent.residing_property_id in self.agent.owned_properties:
                is_homeowner = True

        if is_homeowner:
            housing_costs = daily_interest # Mortgage Interest
        else:
            # Renter or Homeless
            housing_market = market_data.get("housing_market", {})
            avg_rent = housing_market.get("avg_rent_price", 100.0)
            housing_costs = avg_rent

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
