from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
from simulation.systems.api import IAgentLifecycleComponent, LifecycleContext
from simulation.config import SimulationConfig

if TYPE_CHECKING:
    from simulation.core_agents import Household

class AgentLifecycleComponent(IAgentLifecycleComponent):
    """
    에이전트의 틱당 생명주기를 조율하는 컴포넌트.
    Household.update_needs 메서드를 대체합니다.
    """

    def __init__(self, owner: Household, config: SimulationConfig):
        self.owner = owner
        self.config = config

    def work(self) -> None:
        """
        노동을 수행합니다 (Simulation orchestration에서 직접 호출).
        """
        work_hours = 8.0 if self.owner.is_employed else 0.0
        self.owner.labor_manager.work(work_hours)

    def run_tick(self, context: LifecycleContext) -> None:
        """
        에이전트의 틱(일하기, 소비하기, 세금내기, 심리상태 업데이트)을 조율합니다.

        NOTE: 'Work' is now handled separately by `work()` method called by Simulation
        orchestration to ensure correct order (Work -> Consume -> Cleanup).
        This method now handles 'Cleanup' (Tax, Psych).
        """
        household = self.owner
        time = context['time']
        market_data = context['market_data']

        # 0. Labor Market Logic (Shadow Wage Update)
        # Using dependency injected analyzer
        if 'labor_market_analyzer' in context:
            analyzer = context['labor_market_analyzer']
            new_shadow_wage = analyzer.calculate_shadow_reservation_wage(household, market_data)
            household.shadow_reservation_wage = new_shadow_wage

        # 1. Pay Taxes
        household.economy_manager.pay_taxes()

        # 2. Update Psychological Needs
        household.psychology.update_needs(time, market_data)
