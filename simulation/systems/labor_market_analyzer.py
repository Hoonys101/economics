"""
Implements the LaborMarketAnalyzer which tracks market-wide wage history.
"""
from collections import deque
from typing import Any, Dict, Deque
from simulation.systems.api import ILaborMarketAnalyzer

class LaborMarketAnalyzer(ILaborMarketAnalyzer):
    """
    Analyzes labor market trends and calculates shadow reservation wages.
    """

    def __init__(self, config: Any):
        self.config = config
        self.market_wage_history: Deque[float] = deque(maxlen=30)

    def update_market_history(self, market_data: Dict[str, Any]) -> None:
        """
        Updates the internal wage history with the latest market average.
        """
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            self.market_wage_history.append(avg_market_wage)

    def calculate_shadow_reservation_wage(self, agent: Any, market_data: Dict[str, Any]) -> float:
        """
        Calculates the shadow reservation wage for an agent based on their status and market history.
        """
        # Note: agent is typed Any to avoid circular import, expected to be Household.

        # 1. Startup Cost Index
        startup_cost_index = 0.0
        if self.market_wage_history:
            avg_wage_30 = sum(self.market_wage_history) / len(self.market_wage_history)
            startup_cost_index = avg_wage_30 * 6.0

        # 2. Sticky Logic
        current_shadow = getattr(agent, "shadow_reservation_wage", 0.0)

        # Initialize if zero
        if current_shadow <= 0.0:
            current_shadow = agent.current_wage if agent.is_employed else agent.expected_wage

        if agent.is_employed:
            target = max(agent.current_wage, current_shadow)
            # Wage Increase Rate: 0.05
            new_shadow = (current_shadow * 0.95) + (target * 0.05)
        else:
            # Wage Decay Rate: 0.02
            new_shadow = current_shadow * (1.0 - 0.02)

            # Apply Floor
            min_wage = getattr(self.config, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if new_shadow < min_wage:
                new_shadow = min_wage

        return new_shadow
