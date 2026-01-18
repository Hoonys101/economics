from __future__ import annotations
from typing import Dict, List, Any
import logging

from simulation.systems.api import IEventSystem, EventContext

logger = logging.getLogger(__name__)

class EventSystem(IEventSystem):
    """
    Manages scheduled chaos events and scenarios.
    Extracts logic previously in Simulation.run_tick (Chaos Injection Events).
    """

    def __init__(self, config):
        self.config = config

    def execute_scheduled_events(self, time: int, context: EventContext) -> None:
        """
        Executes events scheduled for specific ticks.
        """
        # ===== Chaos Injection Events =====
        if time == 200:
            logger.warning("🔥 CHAOS: Inflation Shock at Tick 200!")
            markets = context["markets"]
            for market_name, market in markets.items():
                if hasattr(market, 'current_price'):
                    market.current_price *= 1.5
                if hasattr(market, 'avg_price'):
                    market.avg_price *= 1.5

        if time == 600:
            logger.warning("🔥 CHAOS: Recession Shock at Tick 600!")
            households = context["households"]
            for household in households:
                household.assets *= 0.5
                # Tech Note WO-057: Asset shock was deemed sufficient.
                # If further impact is needed, household.monthly_income could also be reduced by 50%.
