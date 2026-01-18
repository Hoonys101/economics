from __future__ import annotations
from typing import Dict, Any, TYPE_CHECKING
import logging

from simulation.systems.api import IAgentLifecycleComponent, LifecycleContext

if TYPE_CHECKING:
    from simulation.core_agents import Household

logger = logging.getLogger(__name__)

class AgentLifecycleComponent(IAgentLifecycleComponent):
    """
    Orchestrates the tick lifecycle for an agent (Work, Consume, Tax, Psychology).
    Extracts logic previously in Household.update_needs.
    """

    def __init__(self, owner: 'Household', config):
        self.owner = owner
        self.config = config

    def run_tick(self, context: LifecycleContext) -> None:
        """
        Orchestrates the household's tick-level updates in a specific order:
        1. Work to earn income.
        2. Consume goods to satisfy needs.
        3. Pay taxes.
        4. Update psychological needs.
        """
        household = context["household"]
        market_data = context["market_data"]
        time = context["time"]

        # Ensure household is the owner (sanity check)
        if household is not self.owner:
             logger.warning(f"LifecycleComponent running for {household.id} but owned by {self.owner.id}")

        # 1. Work (via LaborManager)
        # Assuming a fixed 8 hours of work per tick if employed
        work_hours = 8.0 if household.is_employed else 0.0
        # Household delegates to labor_manager
        if hasattr(household, 'labor_manager'):
            household.labor_manager.work(work_hours)

        # 2. Consume (via ConsumptionBehavior / EconomyManager)
        # The existing decide_and_consume delegates to consumption.decide_and_consume
        # then calls update_needs.
        # But here we ARE in the replacement for update_needs.
        # The CommerceSystem calls household.consume() directly or
        # calls household.decide_and_consume().
        # In the new architecture, CommerceSystem handles the "Decide and Consume" phase.
        # However, AgentLifecycleComponent.run_tick is supposed to replace `update_needs`.
        # `update_needs` in the old code called `decide_and_consume` which called `update_needs`... wait.
        # No. `decide_and_consume` called `consumption.decide_and_consume` THEN `update_needs`.
        # `update_needs` itself did: Work -> decide_and_consume -> Pay Taxes -> Psychology.
        # Use recursion if decide_and_consume called update_needs?
        # Let's check existing Household.decide_and_consume:
        # def decide_and_consume(self, current_time, market_data):
        #     consumed_items = self.consumption.decide_and_consume(current_time, market_data)
        #     self.update_needs(current_time, market_data)  <-- Recursion?!
        #     return consumed_items

        # And Household.update_needs:
        # def update_needs(self, current_tick, market_data):
        #     self.labor_manager.work(...)
        #     self.decide_and_consume(...) <-- Recursion?!
        #     self.economy_manager.pay_taxes()
        #     self.psychology.update_needs(...)

        # This looks like infinite recursion in the old code!
        # Unless one of them checks something?
        # Actually, `decide_and_consume` in `Household` called `self.consumption.decide_and_consume`
        # and THEN `self.update_needs`.
        # AND `update_needs` called `self.decide_and_consume`.
        # This DEFINITELY looks like a bug or I misread the file.
        # Let's re-read `Household` file content in memory.

        # From previous `read_file` of `simulation/core_agents.py`:
        # def decide_and_consume(self, current_time: int, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        #     consumed_items = self.consumption.decide_and_consume(current_time, market_data)
        #     self.update_needs(current_time, market_data)
        #     return consumed_items
        #
        # def update_needs(self, current_tick: int, market_data: Optional[Dict[str, Any]] = None):
        #     ...
        #     self.labor_manager.work(work_hours)
        #     self.decide_and_consume(current_tick, market_data)
        #     ...

        # Yes, it IS mutual recursion. This causes `RecursionError` if run.
        # Maybe `update_needs` is abstract in BaseAgent and overridden here?
        # Maybe `decide_and_consume` is NOT called by `update_needs` in reality?
        # Wait, the code I read says:
        #     self.decide_and_consume(current_tick, market_data)
        # inside `update_needs`.
        # If `decide_and_consume` calls `update_needs`, then it's a loop.

        # Perhaps the intention was `decide_and_consume` acts as the entry point?
        # Or `update_needs` acts as the entry point?
        # In `Simulation.run_tick`:
        # household.update_needs(self.time, consumption_market_data)
        # So `update_needs` is the entry point.
        # Then `update_needs` calls `decide_and_consume`.
        # Then `decide_and_consume` calls `update_needs`.
        # Loop.

        # The refactoring MUST fix this.
        # The spec says:
        # CommerceSystem calls `household.update_needs()` (which delegates to Lifecycle).
        # And CommerceSystem ALSO does `execute_consumption_and_leisure`.
        # In `CommerceSystem.execute_consumption_and_leisure`:
        # 1. household.consume() / vectorized buy
        # 2. household.apply_leisure_effect()
        # 3. household.update_needs()

        # So `update_needs` (LifecycleComponent) should NOT call `consume` or `decide_and_consume` anymore if CommerceSystem handled it.
        # The responsibility of Consumption is moved to CommerceSystem.
        # LifecycleComponent should just handle:
        # 1. Work
        # 2. Taxes
        # 3. Psychology

        # So I will remove consumption call from here.

        # 3. Pay Taxes (via EconomyManager)
        if hasattr(household, 'economy_manager'):
            household.economy_manager.pay_taxes()

        # 4. Update Psychological Needs (via PsychologyComponent)
        if hasattr(household, 'psychology'):
            household.psychology.update_needs(time, market_data)
