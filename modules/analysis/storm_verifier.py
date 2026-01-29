from __future__ import annotations
from typing import Any, Dict, List
import statistics
from modules.analysis.api import VerificationConfigDTO, StormReportDTO
from modules.simulation.api import MarketSnapshotDTO, ISimulationState

class StormVerifier:
    def __init__(self, config: VerificationConfigDTO, simulation: ISimulationState):
        self._config = config
        self._simulation = simulation
        self._metrics = {
            "zlb_hit": False,
            "deficit_spending": False,
            "starvation_ticks": 0,
            "total_population_ticks": 0,
            "peak_debt_to_gdp": 0.0
        }
        self._gdp_history: List[float] = []
        self._cpi_history: List[float] = []

    def update(self, current_tick: int, market_snapshot: MarketSnapshotDTO):
        # Store history
        self._gdp_history.append(market_snapshot.get("gdp", 0.0))
        self._cpi_history.append(market_snapshot.get("cpi", 0.0))

        # 1. ZLB Check (Monetary Policy)
        # Access Central Bank base_rate via Protocol
        # Strict config access without defaults
        zlb_threshold = self._config["zlb_threshold"]
        if self._simulation.central_bank:
             if self._simulation.central_bank.base_rate < zlb_threshold:
                 self._metrics["zlb_hit"] = True

        # 2. Deficit Spending Check (Fiscal Policy)
        # Access Government spending/revenue via Protocol
        deficit_threshold = self._config["deficit_spending_threshold"]
        if self._simulation.government:
            spending = self._simulation.government.expenditure_this_tick
            revenue = self._simulation.government.revenue_this_tick
            # Only trigger if significant spending happens (avoid trivial 0 > 0 cases)
            if spending > revenue and spending > deficit_threshold:
                self._metrics["deficit_spending"] = True

            # 3. Debt-to-GDP Check
            debt = self._simulation.government.total_debt
            gdp = market_snapshot["gdp"]
            if gdp > 0:
                debt_to_gdp = debt / gdp
                if debt_to_gdp > self._metrics["peak_debt_to_gdp"]:
                    self._metrics["peak_debt_to_gdp"] = debt_to_gdp

        # 4. Starvation Rate Check
        # TD-118: Access inventory as dictionary
        starving_count = 0
        all_households = self._simulation.households
        active_households = [h for h in all_households if h.is_active]

        # Load starvation threshold from config via Protocol without default
        starvation_threshold = self._simulation.config_module.STARVATION_THRESHOLD

        basic_food_key = self._config["basic_food_key"]

        for hh in active_households:
            # TD-118 compliance: inventory is Dict[str, float] via IHousehold protocol
            food_inventory = hh.inventory.get(basic_food_key, 0.0)
            if food_inventory < starvation_threshold:
                starving_count += 1

        self._metrics["starvation_ticks"] += starving_count
        self._metrics["total_population_ticks"] += len(active_households)

    def generate_report(self) -> StormReportDTO:
        final_starvation_rate = 0.0
        if self._metrics["total_population_ticks"] > 0:
            final_starvation_rate = self._metrics["starvation_ticks"] / self._metrics["total_population_ticks"]

        success = (
            final_starvation_rate < self._config["max_starvation_rate"] and
            self._metrics["peak_debt_to_gdp"] < self._config["max_debt_to_gdp"]
        )

        # Volatility Metrics
        gdp_stdev = 0.0
        if len(self._gdp_history) > 1:
            gdp_stdev = statistics.stdev(self._gdp_history)

        cpi_rolling_mean = 0.0
        if self._cpi_history:
            # Calculate simple average for now as the "rolling mean" summary
            cpi_rolling_mean = statistics.mean(self._cpi_history)

        return StormReportDTO(
            zlb_hit=self._metrics["zlb_hit"],
            deficit_spending_triggered=self._metrics["deficit_spending"],
            starvation_rate=final_starvation_rate,
            peak_debt_to_gdp=self._metrics["peak_debt_to_gdp"],
            volatility_metrics={
                "gdp_stdev": gdp_stdev,
                "cpi_rolling_mean": cpi_rolling_mean
            },
            success=success
        )
