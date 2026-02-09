"""
Implements the SensorySystem which processes raw economic indicators into smoothed data for the government.
"""
from collections import deque
from typing import Any, Deque, List, Optional
from simulation.systems.api import ISensorySystem, SensoryContext
from simulation.dtos import GovernmentStateDTO
from modules.simulation.api import ISensoryDataProvider, AgentSensorySnapshotDTO

class SensorySystem(ISensorySystem):
    """
    Processes raw economic data into SMA buffers and produces Sensory DTOs.
    Owning the state of buffers.
    """

    def __init__(self, config: Any):
        self.config = config

        # State Ownership
        self.inflation_buffer: Deque[float] = deque(maxlen=10)
        self.unemployment_buffer: Deque[float] = deque(maxlen=10)
        self.gdp_growth_buffer: Deque[float] = deque(maxlen=10)
        self.wage_buffer: Deque[float] = deque(maxlen=10)
        self.approval_buffer: Deque[float] = deque(maxlen=10)

        self.last_avg_price_for_sma: float = 10.0
        self.last_gdp_for_sma: float = 0.0

    def generate_government_sensory_dto(self, context: SensoryContext) -> GovernmentStateDTO:
        """
        Calculates indicators, updates buffers, and returns the DTO.
        """
        tracker = context["tracker"]
        government = context["government"]
        time = context["time"]

        latest_indicators = tracker.get_latest_indicators()

        # 1. Inflation (Price Change)
        current_price = latest_indicators.get("avg_goods_price", 10.0)
        last_price = self.last_avg_price_for_sma
        inflation_rate = (current_price - last_price) / last_price if last_price > 0 else 0.0
        self.last_avg_price_for_sma = current_price

        # 2. Unemployment
        unemployment_rate = latest_indicators.get("unemployment_rate", 0.0)

        # 3. GDP Growth
        current_gdp = latest_indicators.get("total_production", 0.0)
        last_gdp = self.last_gdp_for_sma
        gdp_growth = (current_gdp - last_gdp) / last_gdp if last_gdp > 0 else 0.0
        self.last_gdp_for_sma = current_gdp

        # 4. Wage
        avg_wage = latest_indicators.get("avg_wage", 0.0)

        # 5. Approval
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

        # WO-057-A: Robust Sensing for AdaptiveGovBrain
        gini_index = 0.0
        approval_low_asset = 0.5
        approval_high_asset = 0.5

        inequality_tracker = context.get("inequality_tracker")
        households = context.get("households", [])

        # Only process if we have households
        # Use ISensoryDataProvider protocol
        active_snapshots: List[tuple[Any, AgentSensorySnapshotDTO]] = []

        for h in households:
            # We assume households implement ISensoryDataProvider as per Protocol Purity
            # But we can check or try/except for robustness during migration if needed
            # For this task, we assume strict compliance or fallback
            if isinstance(h, ISensoryDataProvider):
                snapshot = h.get_sensory_snapshot()
                if snapshot['is_active']:
                    active_snapshots.append((h, snapshot))
            else:
                # Fallback for legacy agents not yet migrated (should not happen if all are migrated)
                pass

        if active_snapshots:
             assets_list = [snap['total_wealth'] for _, snap in active_snapshots]

             if inequality_tracker:
                 gini_index = inequality_tracker.calculate_gini_coefficient(assets_list)

             # Sort by assets
             combined = sorted(active_snapshots, key=lambda x: x[1]['total_wealth'])

             # Extract approval ratings from sorted list
             n = len(combined)

             # Low Asset: Bottom 50%
             n_low = int(n * 0.5)
             low_group = combined[:n_low]
             if low_group:
                 approval_low_asset = sum(snap['approval_rating'] for _, snap in low_group) / len(low_group)

             # High Asset: Top 20%
             n_high = int(n * 0.2)
             high_group = combined[-n_high:] if n_high > 0 else []
             if high_group:
                 approval_high_asset = sum(snap['approval_rating'] for _, snap in high_group) / len(high_group)

        return GovernmentStateDTO(
            tick=time,
            inflation_sma=calculate_sma(self.inflation_buffer),
            unemployment_sma=calculate_sma(self.unemployment_buffer),
            gdp_growth_sma=calculate_sma(self.gdp_growth_buffer),
            wage_sma=calculate_sma(self.wage_buffer),
            approval_sma=calculate_sma(self.approval_buffer),
            current_gdp=current_gdp,
            gini_index=gini_index,
            approval_low_asset=approval_low_asset,
            approval_high_asset=approval_high_asset
        )
