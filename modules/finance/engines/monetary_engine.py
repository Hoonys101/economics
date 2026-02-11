from typing import Any
import logging
from modules.finance.engines.api import (
    IMonetaryEngine,
    MonetaryStateDTO,
    MarketSnapshotDTO,
    MonetaryDecisionDTO
)

logger = logging.getLogger(__name__)

class MonetaryEngine(IMonetaryEngine):
    """
    Stateless engine that calculates monetary policy (interest rates).
    Implements Taylor Rule.
    """

    def __init__(self, config_module: Any = None):
        self.config = config_module
        self.alpha = getattr(config_module, "CB_TAYLOR_ALPHA", 1.5)
        self.beta = getattr(config_module, "CB_TAYLOR_BETA", 0.5)

    def calculate_rate(
        self,
        state: MonetaryStateDTO,
        market: MarketSnapshotDTO
    ) -> MonetaryDecisionDTO:

        current_gdp = market["current_gdp"]
        potential_gdp = state["potential_gdp"]
        inflation_rate = market["inflation_rate_annual"]
        inflation_target = state["inflation_target"]
        current_base_rate = state["current_base_rate"]

        # 1. Calculate Output Gap
        output_gap = 0.0
        if potential_gdp > 0:
            output_gap = (current_gdp - potential_gdp) / potential_gdp

        # 2. Taylor Rule
        # r* (Neutral Rate) assumed 2%
        neutral_rate = 0.02

        # i = r* + pi + alpha(pi - pi*) + beta(y)
        taylor_rate = neutral_rate + inflation_rate + \
                      self.alpha * (inflation_rate - inflation_target) + \
                      self.beta * output_gap

        # 3. Apply Strategy Overrides (WO-136)
        if state.get("override_target_rate") is not None:
             taylor_rate = state["override_target_rate"]

        if state.get("rate_multiplier") is not None:
             taylor_rate *= state["rate_multiplier"]

        # 4. ZLB (Zero Lower Bound)
        target_rate = max(0.0, taylor_rate)

        # 5. Smoothing
        max_change = 0.0025
        delta = target_rate - current_base_rate

        if abs(delta) > max_change:
            target_rate = current_base_rate + (max_change * (1.0 if delta > 0 else -1.0))

        return MonetaryDecisionDTO(
            new_base_rate=target_rate
        )
