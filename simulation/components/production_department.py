from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import math

if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

class ProductionDepartment:
    """Handles the production logic for a firm."""

    def __init__(self, firm: Firm, config_module: any):
        self.firm = firm
        self.config_module = config_module

    def set_automation_level(self, level: float) -> None:
        """Set the automation level of the firm."""
        self.firm.automation_level = max(0.0, min(1.0, level))

    def produce(self, current_time: int, technology_manager: any = None) -> float:
        """
        Cobb-Douglas 생산 함수를 사용한 생산 로직.
        Phase 21: Modified Cobb-Douglas with Automation.
        """
        try:
            # [EARLY EXIT]
            if len(self.firm.hr.employees) == 0:
                return 0.0

            log_extra = {"tick": current_time, "agent_id": self.firm.id, "tags": ["production"]}

            # 1. 감가상각 처리
            depreciation_rate = getattr(self.config_module, "CAPITAL_DEPRECIATION_RATE", 0.05)
            self.firm.capital_stock *= (1.0 - depreciation_rate)

            # Phase 21: Automation Decay
            self.firm.automation_level *= 0.995 # Slow decay (0.5% per tick)
            if self.firm.automation_level < 0.001: self.firm.automation_level = 0.0

            # 2. 노동 및 자본 투입량 계산
            # SoC Refactor: Get total labor skill from HR
            total_labor_skill = self.firm.hr.get_total_labor_skill()

            # 3. Cobb-Douglas Parameters
            base_alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
            automation_reduction = getattr(self.config_module, "AUTOMATION_LABOR_REDUCTION", 0.5)

            # Phase 21: Adjusted Alpha
            # alpha_adjusted = base_alpha * (1 - automation_level * 0.5)
            # If Automation = 1.0, Alpha = 0.7 * 0.5 = 0.35 (Capital dependent)
            alpha_raw = base_alpha * (1.0 - (self.firm.automation_level * automation_reduction))
            alpha_adjusted = max(getattr(self.config_module, "LABOR_ELASTICITY_MIN", 0.3), alpha_raw)
            beta_adjusted = 1.0 - alpha_adjusted

            # Effective Labor & Capital
            capital = max(self.firm.capital_stock, 0.01)

            # Technology Multiplier (WO-053)
            tech_multiplier = 1.0

            tfp = self.firm.productivity_factor * tech_multiplier  # Total Factor Productivity

            if technology_manager:
                tech_multiplier = technology_manager.get_productivity_multiplier(self.firm.id, self.firm.sector)
                tfp *= tech_multiplier

            # Phase 15: Quality Calculation
            avg_skill = self.firm.hr.get_avg_skill()

            item_config = self.config_module.GOODS.get(self.firm.specialization, {})
            quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
            actual_quality = self.firm.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

            produced_quantity = 0.0
            if total_labor_skill > 0 and capital > 0:
                produced_quantity = tfp * (total_labor_skill ** alpha_adjusted) * (capital ** beta_adjusted)

            actual_produced = 0.0
            if produced_quantity > 0:
                # WO-030: Input Constraints Logic
                input_config = self.config_module.GOODS.get(self.firm.specialization, {}).get("inputs", {})

                if input_config:
                    max_by_inputs = float('inf')
                    for mat, req_per_unit in input_config.items():
                        available = self.firm.input_inventory.get(mat, 0.0)
                        if req_per_unit > 0:
                            max_by_inputs = min(max_by_inputs, available / req_per_unit)

                    # Constrain production
                    actual_produced = min(produced_quantity, max_by_inputs)

                    # Deduct used inputs
                    for mat, req_per_unit in input_config.items():
                        amount_to_deduct = actual_produced * req_per_unit
                        self.firm.input_inventory[mat] = max(0.0, self.firm.input_inventory.get(mat, 0.0) - amount_to_deduct)
                else:
                    actual_produced = produced_quantity

                if actual_produced > 0:
                    self.firm.add_inventory(self.firm.specialization, actual_produced, actual_quality)

            return actual_produced

        except Exception as e:
            import traceback
            logger.error(f'FIRM_CRASH_PREVENTED | Firm {self.firm.id}: {e}')
            logger.debug(traceback.format_exc())
            return 0.0
