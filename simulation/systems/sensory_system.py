"""
Implements the SensorySystem which processes raw economic indicators into smoothed data for the government.
"""
from collections import deque
from typing import Any, Deque, List, Optional
from simulation.systems.api import ISensorySystem, SensoryContext
from simulation.dtos import GovernmentStateDTO

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
        active_households = [h for h in households if h._bio_state.is_active]
        if active_households:
             # Calculate Gini
             if inequality_tracker:
                 # Ensure we use default currency assets
                 # Household assets structure might vary based on Phase 33
                 # Assuming _econ_state.assets is Dict or float.
                 # InequalityTracker expects list of floats.

                 # Helper to extract asset value safely
                 def get_asset_val(h):
                     if hasattr(h._econ_state, 'wallet'):
                         return h._econ_state.wallet.get_total_value() # Assuming this exists or similar
                     if isinstance(h._econ_state.assets, dict):
                         # Just use default currency for Gini or sum?
                         # Usually Wealth = Sum of all assets in base currency
                         # For now, let's assume default currency is enough or assets is float
                         # But wait, InequalityTracker.calculate_wealth_distribution accesses h._econ_state.assets directly
                         # If assets is a dict, InequalityTracker might fail if it doesn't handle it.
                         # Let's check InequalityTracker again? No, let's trust it handles it or we handle it here.
                         from modules.system.api import DEFAULT_CURRENCY
                         return h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0)
                     return float(h._econ_state.assets)

                 # However, InequalityTracker.calculate_gini_coefficient takes List[float].
                 # We should pass floats.

                 # Actually, let's look at how InequalityTracker uses assets.
                 # "sorted(households, key=lambda h: h._econ_state.assets)"
                 # If assets is dict, this fails.
                 # This implies InequalityTracker might be broken for Phase 33 if assets is dict.
                 # BUT, for this task, I will extract float.

                 assets_list = []
                 for h in active_households:
                     val = 0.0
                     if isinstance(h._econ_state.assets, dict):
                         from modules.system.api import DEFAULT_CURRENCY
                         val = h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0)
                     else:
                         val = float(h._econ_state.assets)
                     assets_list.append(val)

                 gini_index = inequality_tracker.calculate_gini_coefficient(assets_list)

                 # Use same values for sorting
                 # Sort by assets
                 # Zip assets and households
                 combined = list(zip(active_households, assets_list))
                 combined.sort(key=lambda x: x[1]) # Sort by asset value

                 sorted_hh = [x[0] for x in combined]
             else:
                 # Fallback sorting if no tracker (though we need logic)
                 # Replicate extraction logic
                 def get_val(h):
                     if isinstance(h._econ_state.assets, dict):
                         from modules.system.api import DEFAULT_CURRENCY
                         return h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0)
                     return float(h._econ_state.assets)
                 sorted_hh = sorted(active_households, key=get_val)

             n = len(sorted_hh)

             # Low Asset: Bottom 50%
             n_low = int(n * 0.5)
             low_hh = sorted_hh[:n_low]
             if low_hh:
                 approval_low_asset = sum(h._social_state.approval_rating for h in low_hh) / len(low_hh)

             # High Asset: Top 20%
             n_high = int(n * 0.2)
             high_hh = sorted_hh[-n_high:] if n_high > 0 else []
             if high_hh:
                 approval_high_asset = sum(h._social_state.approval_rating for h in high_hh) / len(high_hh)

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
