from __future__ import annotations
from typing import Dict, Any, List, Optional
from simulation.systems.api import IEventSystem, EventContext
from simulation.config import SimulationConfig

class EventSystem(IEventSystem):
    """예약되거나 트리거된 시뮬레이션 전반의 이벤트를 관리하는 시스템."""

    def __init__(self, config: SimulationConfig):
        self.config = config

    def execute_scheduled_events(self, time: int, context: EventContext) -> None:
        """현재 틱에 예약된 카오스 이벤트나 다른 시나리오를 실행합니다."""

        # Chaos Injection Events logic extracted from Simulation.run_tick

        if time == 200:
            # Inflation Shock
            # Log warning would ideally be done via a logger passed in, but the protocol doesn't specify one.
            # We assume the caller handles logging or we can use standard logging.
            # For now, we perform the logic.
            markets = context['markets']
            for market_name, market in markets.items():
                if hasattr(market, 'current_price'):
                    market.current_price *= 1.5
                if hasattr(market, 'avg_price'):
                    market.avg_price *= 1.5

        if time == 600:
            # Recession Shock
            households = context['households']
            for household in households:
                household.assets *= 0.5
