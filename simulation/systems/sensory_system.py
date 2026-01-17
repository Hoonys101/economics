from __future__ import annotations
from typing import Dict, Any, List, Optional, Deque
from collections import deque
from simulation.systems.api import ISensorySystem, SensoryContext
from simulation.config import SimulationConfig
from simulation.dtos import GovernmentStateDTO

class SensorySystem(ISensorySystem):
    """
    원시 데이터를 정부 AI와 같은 에이전트의 의사결정을 위해 평활화되거나 집계된 지표로
    처리하는 시스템.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.inflation_buffer: Deque[float] = deque(maxlen=10)
        self.unemployment_buffer: Deque[float] = deque(maxlen=10)
        self.gdp_growth_buffer: Deque[float] = deque(maxlen=10)
        self.wage_buffer: Deque[float] = deque(maxlen=10)
        self.approval_buffer: Deque[float] = deque(maxlen=10)
        self.last_avg_price_for_sma: float = 10.0
        self.last_gdp_for_sma: float = 0.0

    def generate_government_sensory_dto(self, context: SensoryContext) -> GovernmentStateDTO:
        """주요 지표의 SMA를 계산하고 DTO로 패키징합니다."""
        tracker = context['tracker']
        government = context['government']
        time = context['time']

        # Collect Raw Data
        latest_indicators = tracker.get_latest_indicators()

        # Inflation (Price Change)
        current_price = latest_indicators.get("avg_goods_price", 10.0)
        last_price = self.last_avg_price_for_sma
        inflation_rate = (current_price - last_price) / last_price if last_price > 0 else 0.0
        self.last_avg_price_for_sma = current_price

        # Unemployment
        unemployment_rate = latest_indicators.get("unemployment_rate", 0.0)

        # GDP Growth
        current_gdp = latest_indicators.get("total_production", 0.0)
        last_gdp = self.last_gdp_for_sma
        gdp_growth = (current_gdp - last_gdp) / last_gdp if last_gdp > 0 else 0.0
        self.last_gdp_for_sma = current_gdp

        # Wage
        avg_wage = latest_indicators.get("avg_wage", 0.0)

        # Approval
        approval = government.approval_rating

        # Append to Buffers
        self.inflation_buffer.append(inflation_rate)
        self.unemployment_buffer.append(unemployment_rate)
        self.gdp_growth_buffer.append(gdp_growth)
        self.wage_buffer.append(avg_wage)
        self.approval_buffer.append(approval)

        # Calculate SMA
        def calculate_sma(buffer: Deque[float]) -> float:
            return sum(buffer) / len(buffer) if buffer else 0.0

        sensory_dto = GovernmentStateDTO(
            tick=time,
            inflation_sma=calculate_sma(self.inflation_buffer),
            unemployment_sma=calculate_sma(self.unemployment_buffer),
            gdp_growth_sma=calculate_sma(self.gdp_growth_buffer),
            wage_sma=calculate_sma(self.wage_buffer),
            approval_sma=calculate_sma(self.approval_buffer),
            current_gdp=current_gdp
        )

        return sensory_dto
