from typing import Dict, Any, Tuple, Optional
import math
import logging

class System2Planner:
    """
    Phase 20: System 2 Planner (The Internal World Model)

    Implements a forward-looking cognitive engine that projects future wealth
    and survival probabilities to modulate System 1 (Reactive) behavior.
    """

    def __init__(self, config_module: Any, logger: Optional[logging.Logger] = None):
        self.config = config_module
        self.logger = logger or logging.getLogger(__name__)

    def project_future(self, agent_data: Dict[str, Any], market_data: Dict[str, Any]) -> Tuple[float, int]:
        """
        Projects future financial state based on current trends.

        Args:
            agent_data: Dictionary containing 'assets', 'expected_wage', 'needs', etc.
            market_data: Dictionary containing market averages (e.g., 'goods_market').

        Returns:
            Tuple[float, int]: (NPV_Wealth, Estimated_Bankruptcy_Tick)
            - NPV_Wealth: Net Present Value of projected assets at SYSTEM2_HORIZON.
            - Estimated_Bankruptcy_Tick: The tick offset when bankruptcy occurs (0 to HORIZON, or -1 if safe).
        """

        # 1. Extract State
        current_assets = agent_data.get("assets", 0.0)
        expected_wage = agent_data.get("expected_wage", 10.0)

        # 2. Determine Survival Cost (Food Price)
        # Fallback to config default if market data is missing
        goods_market = market_data.get("goods_market", {})
        food_price = goods_market.get("basic_food_avg_traded_price", 0.0)

        if food_price <= 0.0:
            food_price = self.config.GOODS_INITIAL_PRICE.get("basic_food", 5.0)

        survival_threshold = self.config.HOUSEHOLD_FOOD_CONSUMPTION_PER_TICK # e.g. 2.0

        # 3. Calculate Daily Net CashFlow
        # CashFlow = (Wage * WorkHours) - (FoodPrice * Quantity)
        # Assumption: Full employment (8 hours/day as per spec, but verify work hours logic)
        # Spec says: Daily_Net_CashFlow = (Expected_Wage * 8) - (Average_Price * Survival_Threshold)
        # Note: 8 hours assumption might need to be dynamic later, but spec is explicit.
        daily_income = expected_wage * 8.0
        daily_expense = food_price * survival_threshold
        daily_net_cashflow = daily_income - daily_expense

        # 4. Forward Projection
        horizon = self.config.SYSTEM2_HORIZON
        discount_rate = self.config.SYSTEM2_DISCOUNT_RATE

        projected_wealth = current_assets
        bankruptcy_tick = -1
        npv_sum = 0.0

        for t in range(1, horizon + 1):
            # Future Wealth(t) = Current + (Flow * t)
            # (Linear projection)
            projected_wealth += daily_net_cashflow

            # Check Bankruptcy
            if projected_wealth < 0 and bankruptcy_tick == -1:
                bankruptcy_tick = t

            # NPV Calculation
            # Spec says: NPV_Wealth = Sum over t [ Future_Wealth(t) * (SYSTEM2_DISCOUNT_RATE ^ t) ]
            # Note: This sums the discounted *wealth state* at each tick, not the cashflow.
            # Interpreting strictly as per spec.
            discount_factor = math.pow(discount_rate, t)
            npv_sum += projected_wealth * discount_factor

        return npv_sum, bankruptcy_tick
