from __future__ import annotations
from typing import Any, Dict
from modules.analysis.api import VerificationConfigDTO, StormReportDTO
from simulation.dtos.api import MarketSnapshotDTO

class StormVerifier:
    def __init__(self, config: VerificationConfigDTO, simulation: Any):
        self._config = config
        self._simulation = simulation
        self._metrics = {
            "zlb_hit": False,
            "deficit_spending": False,
            "starvation_ticks": 0,
            "total_population_ticks": 0,
            "peak_debt_to_gdp": 0.0
        }

    def update(self, current_tick: int, market_snapshot: MarketSnapshotDTO):
        # 1. ZLB Check (Monetary Policy)
        # Access Central Bank base_rate
        if self._simulation.central_bank:
             if self._simulation.central_bank.base_rate < 0.001:
                 self._metrics["zlb_hit"] = True

        # 2. Deficit Spending Check (Fiscal Policy)
        # Access Government spending/revenue
        if self._simulation.government:
            spending = self._simulation.government.expenditure_this_tick
            revenue = self._simulation.government.revenue_this_tick
            # Only trigger if significant spending happens (avoid trivial 0 > 0 cases)
            if spending > revenue and spending > 1.0:
                self._metrics["deficit_spending"] = True

            # 3. Debt-to-GDP Check
            debt = self._simulation.government.total_debt
            gdp = market_snapshot.gdp
            if gdp > 0:
                debt_to_gdp = debt / gdp
                if debt_to_gdp > self._metrics["peak_debt_to_gdp"]:
                    self._metrics["peak_debt_to_gdp"] = debt_to_gdp

        # 4. Starvation Rate Check
        # TD-118: Access inventory as dictionary
        starving_count = 0
        all_households = self._simulation.households
        active_households = [h for h in all_households if h.is_active]

        # Hardcoded threshold from draft context "config.STARVATION_THRESHOLD"
        # I'll read from simulation config or default to 1.0
        starvation_threshold = 1.0
        if hasattr(self._simulation.config_module, "STARVATION_THRESHOLD"):
             starvation_threshold = self._simulation.config_module.STARVATION_THRESHOLD

        for hh in active_households:
            # TD-118 compliance
            food_inventory = hh.inventory.get("basic_food", 0.0)
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

        return StormReportDTO(
            zlb_hit=self._metrics["zlb_hit"],
            deficit_spending_triggered=self._metrics["deficit_spending"],
            starvation_rate=final_starvation_rate,
            peak_debt_to_gdp=self._metrics["peak_debt_to_gdp"],
            volatility_metrics={"TBD": 0.0},
            success=success
        )
