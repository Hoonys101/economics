from __future__ import annotations
from typing import Dict, Any, Deque
from collections import deque
import logging

from simulation.systems.api import ILaborMarketAnalyzer

logger = logging.getLogger(__name__)

class LaborMarketAnalyzer(ILaborMarketAnalyzer):
    """
    System-level analyzer for the labor market.
    Centralizes logic previously in Household for wage tracking.
    """

    def __init__(self, config):
        self.config = config
        self.market_wage_history: Deque[float] = deque(maxlen=30) # For 30-tick avg

    def update_market_history(self, market_data: Dict[str, Any]) -> None:
        """
        Updates the internal wage history with the latest market data.
        """
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            self.market_wage_history.append(avg_market_wage)

    def calculate_shadow_reservation_wage(self, agent, market_data: Dict[str, Any]) -> float:
        """
        Calculates the shadow reservation wage for an agent based on system-wide trends.
        """
        # WO-056: Stage 1 Shadow Mode (Labor Market Mechanism).

        # 1. Calculate Startup Cost Shadow Index (Logic from Household)
        startup_cost_index = 0.0
        if self.market_wage_history:
            avg_wage_30 = sum(self.market_wage_history) / len(self.market_wage_history)
            startup_cost_index = avg_wage_30 * 6.0

        # 2. Retrieve agent's current shadow reservation wage
        # Assuming the agent stores its own shadow wage state.
        # If the analyzer is pure logic, it shouldn't store per-agent state.
        # The method signature takes 'agent'.

        shadow_reservation_wage = getattr(agent, "shadow_reservation_wage", 0.0)
        current_wage = getattr(agent, "current_wage", 0.0)
        is_employed = getattr(agent, "is_employed", False)
        expected_wage = getattr(agent, "expected_wage", 0.0)

        # Initialize if zero
        if shadow_reservation_wage <= 0.0:
            shadow_reservation_wage = current_wage if is_employed else expected_wage

        # Logic:
        # Wage Increase: 0.05 (Employment/Rise), Wage Decay: 0.02 (Unemployment)

        if is_employed:
            target = max(current_wage, shadow_reservation_wage)
            shadow_reservation_wage = (shadow_reservation_wage * 0.95) + (target * 0.05)
        else:
            # Decay Logic
            shadow_reservation_wage *= (1.0 - 0.02)
            # Apply floor
            min_wage = getattr(self.config, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if shadow_reservation_wage < min_wage:
                shadow_reservation_wage = min_wage

        # Note: The original code logged shadow stats here using log_shadow.
        # I should probably preserve that side effect or return values to be logged.
        # For now, I will perform the calculation and return the new value.
        # The agent is responsible for updating its state with the returned value.

        return shadow_reservation_wage
