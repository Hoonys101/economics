from __future__ import annotations
from typing import TypedDict, Dict

class VerificationConfigDTO(TypedDict):
    """Configuration for the verification component."""
    max_starvation_rate: float
    max_debt_to_gdp: float
    # TBD: Define volatility reduction target

class StormReportDTO(TypedDict):
    """The final report summarizing the stress test results."""
    zlb_hit: bool
    deficit_spending_triggered: bool
    starvation_rate: float
    peak_debt_to_gdp: float
    volatility_metrics: Dict[str, float]
    success: bool
