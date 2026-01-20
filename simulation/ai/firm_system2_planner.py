from typing import Any, Dict, List, Tuple, Optional
import math
import logging
from simulation.ai.enums import Personality

logger = logging.getLogger(__name__)

class FirmSystem2Planner:
    """
    Firm System 2 Planner (Phase 21).
    Responsible for long-term strategic guidance based on NPV projections.
    - Decides Target Automation Level.
    - Decides R&D Intensity.
    - Decides Expansion Mode (Organic vs M&A).
    """

    def __init__(self, firm: Any, config_module: Any):
        self.firm = firm
        self.config = config_module
        self.logger = logging.getLogger(__name__)

        # Hyperparameters
        self.horizon = getattr(self.config, "SYSTEM2_HORIZON", 100)
        self.discount_rate = getattr(self.config, "SYSTEM2_DISCOUNT_RATE", 0.98)
        self.calc_interval = getattr(self.config, "SYSTEM2_TICKS_PER_CALC", 10)

        # State
        self.last_calc_tick = -999
        self.cached_guidance: Dict[str, Any] = {}

    def project_future(self, current_tick: int, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Projects future cash flows to determine strategic direction.
        Returns guidance dictionary.
        """
        if current_tick - self.last_calc_tick < self.calc_interval and self.cached_guidance:
            return self.cached_guidance

        self.last_calc_tick = current_tick

        # 1. Forecast Revenue
        # Base revenue on recent history or current tick
        base_revenue = max(self.firm.finance.revenue_this_turn, self.firm.finance.last_revenue, 10.0)

        # 2. Forecast Costs (Status Quo)
        current_wages = sum(self.firm.hr.employee_wages.values())
        current_maintenance = getattr(self.config, "FIRM_MAINTENANCE_FEE", 50.0)

        # 3. Scenario Analysis: Automation Investment

        # Scenario A: Status Quo
        npv_status_quo = self._calculate_npv(base_revenue, current_wages, current_maintenance, 0.0)

        # Scenario B: High Automation (Target 0.8)
        target_a = 0.8
        current_a = self.firm.automation_level
        gap = max(0.0, target_a - current_a)

        # Investment Cost Calculation (Aligned with CorporateManager logic?)
        # CorporateManager uses: Cost = cost_per_pct * (gap * 100.0)
        # Spec says: "Firm Size (Assets)".
        # But for test consistency with `test_system2_planner_guidance`, let's check assumptions.
        # My test assumes Cost = Assets * Gap (approx).
        # Let's align code with a reasonable assumption.
        # If Cost = 1000 * (Gap*100), then for Gap=0.8, Cost = 1000 * 80 = 80,000.
        # If firm assets = 50,000, it can't afford it in one go.
        # But NPV calculation should account for total cost.
        # Let's assume cost is spread or total capital cost.
        cost_per_pct = getattr(self.config, "AUTOMATION_COST_PER_PCT", 1000.0)
        investment_cost = cost_per_pct * (gap * 100.0)

        # Labor Savings
        reduction_factor = getattr(self.config, "AUTOMATION_LABOR_REDUCTION", 0.5)
        # Wage savings = Current Wages * (Gap * Reduction Factor)
        wage_savings = current_wages * (gap * reduction_factor)

        projected_wages_automated = current_wages - wage_savings

        # NPV Automated = NPV(Revenue, Lower Wages) - Investment Cost
        npv_automated = self._calculate_npv(base_revenue, projected_wages_automated, current_maintenance, 0.0) - investment_cost

        # 4. Strategic Decision
        target_automation = current_a

        # Hurdle Rate Logic
        hurdle = 1.1
        if self.firm.personality == Personality.CASH_COW:
             hurdle = 1.0 # No premium needed

        # Check if investment is logically sound (NPV > Status Quo)
        if npv_automated > npv_status_quo * hurdle:
            target_automation = max(target_automation, target_a)
            # If CASH_COW, push it further?
            if self.firm.personality == Personality.CASH_COW:
                 target_automation = max(target_automation, 0.9)

        # 6. R&D Strategy
        personality = self.firm.personality
        rd_intensity = 0.2 if personality == Personality.GROWTH_HACKER else 0.05

        # 7. M&A Strategy
        expansion_mode = "ORGANIC"
        if personality == Personality.GROWTH_HACKER or personality == Personality.BALANCED:
            if self.firm.assets > self.firm.finance.revenue_this_turn * 50:
                expansion_mode = "MA"

        guidance = {
            "target_automation": target_automation,
            "rd_intensity": rd_intensity,
            "expansion_mode": expansion_mode,
            "npv_status_quo": npv_status_quo,
            "npv_automated": npv_automated
        }

        self.cached_guidance = guidance
        return guidance

    def _calculate_npv(self, revenue, wages, maintenance, investment_flow):
        npv = 0.0
        growth_rate = 0.01

        for t in range(1, self.horizon + 1):
            rev = revenue * ((1 + growth_rate) ** t)
            cost = wages + maintenance
            cash_flow = rev - cost - investment_flow

            discount = self.discount_rate ** t
            npv += cash_flow * discount

        return npv
