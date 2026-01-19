"""
Implements the EventSystem which handles scheduled chaos events.
"""
from typing import Dict, Any, List
import logging
from simulation.systems.api import IEventSystem, EventContext

logger = logging.getLogger(__name__)

class EventSystem(IEventSystem):
    """
    Manages scheduled events like Inflation Shock and Recession Shock.
    """

    def __init__(self, config: Any):
        self.config = config

    def execute_scheduled_events(self, time: int, context: EventContext, config: "StressScenarioConfig") -> None:
        """
        Executes stress scenario triggers based on the provided configuration.
        """
        if not config or not config.is_active or time != config.start_tick:
            return

        logger.warning(f"🔥 STRESS_TEST: Activating '{config.scenario_name}' at Tick {time}!")
        households = context["households"]
        firms = context["firms"]

        # Scenario 1: Hyperinflation (Demand-Pull Shock)
        if config.scenario_name == 'hyperinflation' and config.demand_shock_cash_injection > 0:
            for h in households:
                h.assets *= (1 + config.demand_shock_cash_injection)
            logger.info(f"  -> Injected {config.demand_shock_cash_injection:.0%} cash into all households.")

        # Scenario 2: Deflationary Spiral (Asset Shock)
        if config.scenario_name == 'deflation' and config.asset_shock_reduction > 0:
            for agent in households + firms:
                agent.assets *= (1 - config.asset_shock_reduction)
            logger.info(f"  -> Reduced all agent assets by {config.asset_shock_reduction:.0%}.")

        # Scenario 3: Supply Shock (Productivity Collapse)
        if config.scenario_name == 'supply_shock' and config.exogenous_productivity_shock:
            for firm in firms:
                # Check if firm type is in the shock dictionary
                if firm.type in config.exogenous_productivity_shock:
                    shock_multiplier = config.exogenous_productivity_shock[firm.type]
                    firm.productivity_factor *= shock_multiplier
                    logger.info(f"  -> Applied productivity shock ({shock_multiplier}) to Firm {firm.id} (Type: {firm.type}).")
