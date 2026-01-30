from typing import Any
import math

from modules.government.api import IMonetaryPolicyManager
from modules.government.dtos import MonetaryPolicyDTO, MacroEconomicSnapshotDTO
from simulation.dtos.api import MarketSnapshotDTO

class MonetaryPolicyManager(IMonetaryPolicyManager):
    """
    Manages monetary policy using a Taylor Rule.
    Stateless calculation based on MacroEconomicSnapshotDTO.
    """

    def __init__(self, config_module: Any):
        self.inflation_target = getattr(config_module, "CB_INFLATION_TARGET", 0.02)
        self.alpha = getattr(config_module, "CB_TAYLOR_ALPHA", 1.5)
        self.beta = getattr(config_module, "CB_TAYLOR_BETA", 0.5)
        self.neutral_rate = getattr(config_module, "CB_NEUTRAL_RATE", 0.02)

    def determine_monetary_stance(self, market_snapshot: MacroEconomicSnapshotDTO) -> MonetaryPolicyDTO:
        """
        Calculates the target interest rate based on the Taylor Rule:
        i_t = max(0, r* + pi_t + alpha * (pi_t - pi*) + beta * (log Y_t - log Y*))

        Where:
        - r*: Neutral real rate
        - pi_t: Current inflation rate
        - pi*: Inflation target
        - Y_t: Current GDP
        - Y*: Potential GDP
        """

        inflation_rate = market_snapshot.inflation_rate if market_snapshot.inflation_rate is not None else 0.0
        current_gdp = market_snapshot.nominal_gdp if market_snapshot.nominal_gdp is not None else 0.0
        potential_gdp = market_snapshot.potential_gdp if market_snapshot.potential_gdp is not None else 0.0

        # Calculate Output Gap (log approximation)
        output_gap = 0.0
        if current_gdp > 0 and potential_gdp > 0:
            try:
                output_gap = math.log(current_gdp) - math.log(potential_gdp)
            except ValueError:
                output_gap = 0.0

        # Taylor Rule Calculation
        # i_t = r* + pi_t + alpha * (pi_t - pi*) + beta * output_gap

        taylor_rate = (
            self.neutral_rate +
            inflation_rate +
            self.alpha * (inflation_rate - self.inflation_target) +
            self.beta * output_gap
        )

        # Zero Lower Bound
        target_rate = max(0.0, taylor_rate)

        return MonetaryPolicyDTO(
            target_interest_rate=target_rate,
            inflation_target=self.inflation_target,
            unemployment_target=0.0 # Not used in simple Taylor Rule
        )
