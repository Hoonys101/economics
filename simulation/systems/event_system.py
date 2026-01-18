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

    def execute_scheduled_events(self, time: int, context: EventContext) -> None:
        """
        Checks the current time and executes hardcoded events if they match.
        """
        markets = context["markets"]
        households = context["households"]

        # 1. Inflation Shock at Tick 200
        if time == 200:
            logger.warning("🔥 CHAOS: Inflation Shock at Tick 200!")
            for market in markets.values():
                if hasattr(market, 'current_price'):
                    market.current_price *= 1.5
                if hasattr(market, 'avg_price'):
                    market.avg_price *= 1.5

        # 2. Recession Shock at Tick 600
        if time == 600:
            logger.warning("🔥 CHAOS: Recession Shock at Tick 600!")
            for household in households:
                household.assets *= 0.5
                # Note: logic to reduce monthly_income could be added here if needed
