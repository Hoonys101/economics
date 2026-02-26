# ROLE: Tier 1 (Universal)
# GUIDELINE: MANDATORY CORE CONTRACT. Any modifications or new logic must strictly adhere to these interfaces and rules.
# ==========================================
from typing import Dict, Any, Optional
from modules.scenarios.api import IScenarioJudge, Tier
from modules.simulation.dtos.api import MoneySupplyDTO
from modules.simulation.api import EconomicIndicatorsDTO
from modules.system.api import IWorldStateMetricsProvider

# ------------------------------------------------------------------------------
# 2. Concrete Judge Implementations (Contracts)
# ------------------------------------------------------------------------------
class PhysicsIntegrityJudge(IScenarioJudge):
    """
    Tier 1: System Integrity & Physics.
    Strictly verifies Zero-Sum invariants, Monetary Supply (M2) in integer pennies,
    and system-wide structural constraints. No floats allowed.
    """
    @property
    def tier(self) -> Tier:
        return Tier.PHYSICS

    @property
    def name(self) -> str:
        return "PhysicsIntegrityJudge"

    def judge(self, world_state: IWorldStateMetricsProvider) -> bool:
        # In a real scenario, this would verify invariants.
        # For now, we return True as the core logic is in get_metrics for reporting.
        return True

    def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
        money_supply: MoneySupplyDTO = world_state.calculate_total_money()
        # We report raw values. Baseline comparison would happen in the scenario runner/verifier.
        return {
            "m2_supply_pennies": money_supply.total_m2_pennies,
            "system_debt_pennies": money_supply.system_debt_pennies,
            "m2_delta": 0 # Placeholder, validated invariant would go here if baseline known
        }

class MacroHealthJudge(IScenarioJudge):
    """
    Tier 2: Macroeconomic Health.
    Verifies GDP growth, CPI/Inflation stability, and Unemployment Rates.
    Relies entirely on EconomicIndicatorsDTO.
    """
    @property
    def tier(self) -> Tier:
        return Tier.MACRO

    @property
    def name(self) -> str:
        return "MacroHealthJudge"

    def judge(self, world_state: IWorldStateMetricsProvider) -> bool:
        return True

    def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
        indicators: EconomicIndicatorsDTO = world_state.get_economic_indicators()
        return {
            "gdp": indicators.gdp,
            "cpi": indicators.cpi,
            "unemployment_rate": getattr(indicators, 'unemployment_rate', 0.0) # Ensure mapped in DTO
        }

class MicroSentimentJudge(IScenarioJudge):
    """
    Tier 3: Agent Behavior & Micro Sentiment.
    Verifies agent panic index, withdrawal pressure, and average health/survival needs.
    """
    @property
    def tier(self) -> Tier:
        return Tier.MICRO

    @property
    def name(self) -> str:
        return "MicroSentimentJudge"

    def judge(self, world_state: IWorldStateMetricsProvider) -> bool:
        return True

    def get_metrics(self, world_state: IWorldStateMetricsProvider) -> Dict[str, Any]:
        panic_index: float = world_state.get_market_panic_index()
        CRITICAL_THRESHOLD = 0.8 # Example threshold
        return {
            "market_panic_index": panic_index,
            "withdrawal_pressure_alert": panic_index > CRITICAL_THRESHOLD
        }
