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
        Returns:
            {
                "npv_wealth": float,
                "bankruptcy_tick": Optional[int],
                "survival_prob": float
            }
        """
        # Optimization: Run only every X ticks
        if current_tick - self.last_calc_tick < self.calc_interval and self.cached_projection:
            return self.cached_projection

        self.last_calc_tick = current_tick

        # 1. Gather Inputs
        current_wealth = self.agent.assets
        expected_wage = getattr(self.agent, "expected_wage", 10.0)

        # Estimate Cost of Living (Survival)
        # Use simple heuristic: Price of basic_food * consumption
        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_current_sell_price", 5.0)
        daily_consumption = getattr(self.config, "HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK", 2.0)
        daily_survival_cost = food_price * daily_consumption

        # Net Cash Flow Projection (Simple Linear)
        # Step 2: Socio-Tech Dynamics Integration

        # A. Determine Work Hours Capability
        # Retrieve time allocation from AI
        # We need a hypothetical scenario: "If I have a child..."
        # But project_future usually projects "Current Status Quo" into future.
        # However, if the agent *has* a child, the constraints apply NOW.
        # So we use current agent attributes.

        # Fetch data for time allocation
        agent_data = self.agent.get_agent_data()

        # Mock/Retrieve Spouse/Children data for the projection
        # Ideally self.agent has access to these.
        # For Step 1 simplicity, we check self.agent.children_ids
        children_data = [{"age": 1} for _ in self.agent.children_ids] # Assume infants if any, or check real ages if possible
        # Or better: check actual children ages from agent.children_ids?
        # Agent doesn't store ages of children directly in list, only IDs.
        # But let's assume for projection if we have children count > 0, we pay the tax?
        # Step 2 requirement: "System 2 Integration: ... deduct childcare time cost"

        # Let's perform a lightweight call to decide_time_allocation
        # We need the HouseholdAI instance.
        household_ai = getattr(self.agent.decision_engine, "ai_engine", None)

        time_obligations = 0.0

        if household_ai and hasattr(household_ai, "decide_time_allocation"):
             # We need to construct spouse_data dummy if spouse exists
             spouse_data = {"id": self.agent.spouse_id} if self.agent.spouse_id else None

             # Fetch real children data if possible, else heuristic
             # Since we can't easily fetch other agents (children) here without engine ref,
             # we rely on agent_data["children_count"].
             # If children_count > 0, assume at least one is infant for worst-case projection?
             # Or assume status quo.
             # Refined approach: Agent should store 'has_infant' boolean updated daily?
             # For now, let's create a dummy list if count > 0 to trigger the logic.
             c_count = len(self.agent.children_ids)
             # Heuristic: If I have children, assume 1 is infant for stress testing the projection
             # Or only if I *really* have one.
             # Given System 2 is "Slow/Planner", it should be accurate.
             # But without Engine access to Child Agent, we can't know age.
             # Compromise: We add 'has_infant' to Household state in core_agents later?
             # Or we simply assume: "If I am planning to reproduce, I WILL have an infant."
             # But this method projects CURRENT state.
             # If I currently have an infant, my income is LOW.
             # So daily_income should reflect CURRENT constraints.

             # Actually, let's just use the result from decision_engine if it cached it?
             # Or call it.
             dummy_children = [{"age": 1}] if c_count > 0 else []

             alloc = household_ai.decide_time_allocation(
                 agent_data, spouse_data, dummy_children, self.config
             )
             time_obligations = alloc["total_obligated"]

        # B. Calculate Effective Work Hours
        # Max Work = 24 - Sleep(8) - Personal(2) - Obligations
        # Let's say Max Physiological Work = 14.
        available_work_hours = max(0.0, 14.0 - time_obligations)

        # Cap at standard 8 hours for wage projection (or use available if less)
        projected_work_hours = min(8.0, available_work_hours)

        # C. Expenses (Formula/Appliance)
        # If we used Formula logic (Lactation Lock released), we must pay for it.
        # How do we know if we used Formula?
        # decide_time_allocation doesn't return cost.
        # But we know if tech_level > 0 and we are Female and shared childcare, we used it.
        # Simply: Add a fixed "Child Rearing Cost" if children > 0.
        extra_expenses = 0.0
        tech_level = getattr(self.config, "FORMULA_TECH_LEVEL", 0.0)
        if len(self.agent.children_ids) > 0:
            # Formula Cost?
             if tech_level > 0.5: # Assuming usage
                 extra_expenses += 5.0 # Cost of Formula per tick

        daily_income = expected_wage * projected_work_hours
        daily_net_flow = daily_income - daily_survival_cost - extra_expenses

        # 2. Simulation Loop
        npv_wealth = 0.0
        bankruptcy_tick = None
        simulated_wealth = current_wealth

        for t in range(1, self.horizon + 1):
            # Apply Discount
            discount_factor = self.discount_rate ** t

            # Update Wealth
            simulated_wealth += daily_net_flow

            # Check Bankruptcy
            if simulated_wealth < 0 and bankruptcy_tick is None:
                bankruptcy_tick = current_tick + t

            # Add to NPV (Utility of Wealth?)
            # Ideally NPV is sum of discounted cash flows, but here we track discounted wealth utility?
            # Or just Sum of DCF.
            # Let's use Sum of Discounted Net Cash Flow + Initial Wealth
            npv_wealth += daily_net_flow * discount_factor

        final_npv = current_wealth + npv_wealth

        # 3. Survival Probability (Heuristic)
        survival_prob = 1.0
        if bankruptcy_tick:
            # If bankrupt within horizon, prob drops
            ticks_until_broke = bankruptcy_tick - current_tick
            survival_prob = min(1.0, ticks_until_broke / self.horizon)

        result = {
            "npv_wealth": final_npv,
            "bankruptcy_tick": bankruptcy_tick,
            "survival_prob": survival_prob
        }

        self.cached_projection = result
        return result
