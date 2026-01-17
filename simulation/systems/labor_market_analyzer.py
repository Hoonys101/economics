from __future__ import annotations
from typing import Dict, Any, Deque
from collections import deque
from simulation.systems.api import ILaborMarketAnalyzer
from simulation.config import SimulationConfig
from simulation.utils.shadow_logger import log_shadow

class LaborMarketAnalyzer(ILaborMarketAnalyzer):
    """
    노동 시장의 시스템 레벨 분석기.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.market_wage_history: Deque[float] = deque(maxlen=30)

    def update_market_history(self, market_data: Dict[str, Any]) -> None:
        """최신 시장 전체 임금 데이터로 내부 기록을 업데이트합니다."""
        avg_market_wage = 0.0
        if market_data and "labor" in market_data:
             avg_market_wage = market_data["labor"].get("avg_wage", 0.0)

        if avg_market_wage > 0:
            self.market_wage_history.append(avg_market_wage)

    def calculate_shadow_reservation_wage(self, agent: Any, market_data: Dict[str, Any]) -> float:
        """
        가계의 고정적인 유보 임금을 계산합니다.
        agent: Household object (typed Any to avoid circular import in runtime if not careful, but safely Household)
        """
        # Note: In the original code, this logic was inside Household._calculate_shadow_reservation_wage
        # But it used self.market_wage_history which was on the household.
        # Now the history is centralized here.

        # 2. Calculate Startup Cost Shadow Index (using centralized history)
        startup_cost_index = 0.0
        if self.market_wage_history:
            avg_wage_30 = sum(self.market_wage_history) / len(self.market_wage_history)
            startup_cost_index = avg_wage_30 * 6.0

        # 3. Calculate Shadow Reservation Wage (Sticky Logic)
        # We need to access agent's previous shadow wage.
        # It seems the agent still needs to store its own shadow_reservation_wage state.
        # The Analyzer calculates the *new* value based on the agent's state and market history.

        current_shadow = getattr(agent, "shadow_reservation_wage", 0.0)
        current_wage = getattr(agent, "current_wage", 0.0)
        expected_wage = getattr(agent, "expected_wage", 0.0)
        is_employed = getattr(agent, "is_employed", False)

        # Initialize if zero
        if current_shadow <= 0.0:
            current_shadow = current_wage if is_employed else expected_wage

        new_shadow = current_shadow

        if is_employed:
            target = max(current_wage, current_shadow)
            new_shadow = (current_shadow * 0.95) + (target * 0.05)
        else:
            # Decay Logic
            new_shadow *= (1.0 - 0.02)
            # Apply floor
            min_wage = getattr(self.config, "HOUSEHOLD_MIN_WAGE_DEMAND", 6.0)
            if new_shadow < min_wage:
                new_shadow = min_wage

        # Log (optional, keeping original behavior)
        # log_shadow is imported
        # log_shadow(
        #     tick=...,
        #     agent_id=agent.id,
        #     agent_type="Household",
        #     metric="shadow_wage",
        #     current_value=current_wage if is_employed else expected_wage,
        #     shadow_value=new_shadow,
        #     details=f"Employed={is_employed}, StartupIdx={startup_cost_index:.2f}"
        # )

        return new_shadow
