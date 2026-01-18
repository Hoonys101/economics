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
        household = context["household"]
        market_data = context["market_data"]
        time = context["time"]

        # 1. Work (via LaborManager)
        # Assuming a fixed 8 hours of work per tick if employed
        work_hours = 8.0 if household.is_employed else 0.0
        household.labor_manager.work(work_hours)

        # 2. Consume (via EconomyManager/CommerceSystem)
        # Note: In the new architecture, Consumption is largely handled by CommerceSystem
        # BEFORE this component is called in the `update_needs` chain.
        # However, `decide_and_consume` logic might still reside in Household for legacy support.
        # Ideally, this step is skipped here if CommerceSystem did it.
        # But `Household.update_needs` currently calls `decide_and_consume`.
        # We will keep it here for now, but in `Household` refactor,
        # `update_needs` will delegate to this.

        # household.decide_and_consume(time, market_data)
        # -> This is redundant if CommerceSystem already executed consumption.
        # -> BUT CommerceSystem calls `household.update_needs` AFTER `decide_consumption_batch`.
        # -> So we should probably NOT consume again here if it was done via vector.
        # -> However, `decide_and_consume` delegates to `consumption.decide_and_consume`.
        # -> If CommerceSystem handled it, we should ensure `consumption.decide_and_consume`
        #    doesn't double dip or we assume CommerceSystem *replaced* that call.

        # For Safety: We assume CommerceSystem handled the PRIMARY consumption.
        # We only handle "needs update" based on that consumption?
        # Actually, `household.update_needs` in `Simulation` is called inside `CommerceSystem`.
        # So we are inside the call stack of CommerceSystem.

        # 3. Pay Taxes (via EconomyManager)
        household.economy_manager.pay_taxes()

        # 4. Update Psychological Needs (via PsychologyComponent)
        household.psychology.update_needs(time, market_data)
