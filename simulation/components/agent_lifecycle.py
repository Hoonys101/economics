"""
Implements the AgentLifecycleComponent which manages the daily routine of a Household agent.
"""
from typing import Any, Dict, Protocol
from simulation.systems.api import IAgentLifecycleComponent, LifecycleContext

class AgentLifecycleComponent(IAgentLifecycleComponent):
    """
    Manages the 'run_tick' logic for a Household: Work -> Consume -> Tax -> Psychology.
    """

    def __init__(self, owner: Any, config: Any):
        self.owner = owner # Household
        self.config = config

    def run_tick(self, context: LifecycleContext) -> None:
        """
        Orchestrates the household's tick-level updates.
        """
        state = context["state"]
        market_data = context["market_data"]
        time = context["time"]

        # 1. Work (via LaborManager)
        # Assuming a fixed 8 hours of work per tick if employed
        work_hours = 8.0 if state.is_employed else 0.0
        self.owner.labor_manager.work(work_hours)

        # 2. Consume (via EconomyManager/CommerceSystem)
        # Consumption is now handled by CommerceSystem before calling update_needs.
        # We deliberately skip calling household.decide_and_consume here to avoid
        # double consumption (Architecture Ambiguity Fix).
        # The logic flow is: CommerceSystem -> execute consumption -> household.update_needs -> Lifecycle.run_tick

        # 3. Pay Taxes (via EconomyManager)
        self.owner.economy_manager.pay_taxes()

        # 4. Update Psychological Needs (via PsychologyComponent)
        self.owner.psychology.update_needs(time, market_data)
