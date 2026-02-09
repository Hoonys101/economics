from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Optional
import logging
import math
import random
from simulation.components.state.firm_state_models import ProductionState, HRState
from modules.inventory.api import IInventoryHandler

if TYPE_CHECKING:
    from simulation.dtos.config_dtos import FirmConfigDTO

logger = logging.getLogger(__name__)

class ProductionEngine:
    """
    Stateless Engine for Production operations.
    Handles Cobb-Douglas production, automation decay, and R&D.
    """

    def produce(
        self,
        state: ProductionState,
        inventory_handler: IInventoryHandler,
        hr_state: HRState,
        config: FirmConfigDTO,
        current_time: int,
        firm_id: int,
        technology_manager: Optional[Any] = None
    ) -> float:
        """
        Executes production logic.
        Updates state (capital stock, automation, input inventory) and adds output to inventory_handler.
        """
        try:
            # [EARLY EXIT]
            if len(hr_state.employees) == 0:
                # Logging skipped for brevity, or can be injected
                return 0.0

            # 1. Depreciation & Decay
            depreciation_rate = config.capital_depreciation_rate
            state.capital_stock *= (1.0 - depreciation_rate)

            # Automation Decay
            state.automation_level *= 0.995
            if state.automation_level < 0.001: state.automation_level = 0.0

            # 2. Labor & Capital Inputs
            total_labor_skill = sum(emp.labor_skill or 0.0 for emp in hr_state.employees)

            # Cobb-Douglas Parameters
            base_alpha = config.labor_alpha
            automation_reduction = config.automation_labor_reduction

            # Alpha Adjusted
            alpha_raw = base_alpha * (1.0 - (state.automation_level * automation_reduction))
            alpha_adjusted = max(config.labor_elasticity_min, alpha_raw)
            beta_adjusted = 1.0 - alpha_adjusted

            # Effective Inputs
            capital = max(state.capital_stock, 0.01)

            # Technology Multiplier
            tfp = state.productivity_factor
            if technology_manager:
                tfp *= technology_manager.get_productivity_multiplier(firm_id)

            # Quality Calculation
            avg_skill = total_labor_skill / len(hr_state.employees) if hr_state.employees else 0.0
            item_config = config.goods.get(state.specialization, {})
            quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
            actual_quality = state.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

            produced_quantity = 0.0
            if total_labor_skill > 0 and capital > 0:
                produced_quantity = tfp * (total_labor_skill ** alpha_adjusted) * (capital ** beta_adjusted)

            actual_produced = 0.0
            if produced_quantity > 0:
                # Input Constraints
                input_config = config.goods.get(state.specialization, {}).get("inputs", {})

                if input_config:
                    max_by_inputs = float('inf')
                    for mat, req_per_unit in input_config.items():
                        available = state.input_inventory.get(mat, 0.0)
                        if req_per_unit > 0:
                            max_by_inputs = min(max_by_inputs, available / req_per_unit)

                    actual_produced = min(produced_quantity, max_by_inputs)

                    # Deduct used inputs
                    for mat, req_per_unit in input_config.items():
                        amount_to_deduct = actual_produced * req_per_unit
                        state.input_inventory[mat] = max(0.0, state.input_inventory.get(mat, 0.0) - amount_to_deduct)
                else:
                    actual_produced = produced_quantity

                if actual_produced > 0:
                    inventory_handler.add_item(state.specialization, actual_produced, quality=actual_quality)

            return actual_produced

        except Exception as e:
            logger.error(f'PRODUCTION_ERROR | Firm {firm_id}: {e}')
            return 0.0

    def invest_in_automation(
        self,
        state: ProductionState,
        amount: float,
        cost_per_pct: float
    ) -> float:
        """
        Updates automation level based on investment.
        Payment is handled by Finance (Orchestrator).
        Returns the gained automation level.
        """
        if cost_per_pct > 0:
            gained_a = (amount / cost_per_pct) / 100.0
            state.automation_level = max(0.0, min(1.0, state.automation_level + gained_a))
            return gained_a
        return 0.0

    def invest_in_capex(
        self,
        state: ProductionState,
        amount: float,
        capital_to_output_ratio: float
    ) -> float:
        """
        Updates capital stock.
        """
        efficiency = 1.0 / capital_to_output_ratio
        added_capital = amount * efficiency
        state.capital_stock += added_capital
        return added_capital

    def execute_rd_outcome(
        self,
        state: ProductionState,
        hr_state: HRState,
        revenue: float,
        budget: float,
        current_time: int
    ) -> bool:
        """
        Executes probabilistic R&D outcome.
        Updates state.base_quality and productivity_factor.
        """
        state.research_history["total_spent"] += budget

        denominator = max(revenue * 0.2, 100.0)
        base_chance = min(1.0, budget / denominator)

        avg_skill = 1.0
        if hr_state.employees:
            avg_skill = sum(emp.labor_skill or 0.0 for emp in hr_state.employees) / len(hr_state.employees)

        success_chance = base_chance * avg_skill

        if random.random() < success_chance:
            state.research_history["success_count"] += 1
            state.research_history["last_success_tick"] = current_time
            state.base_quality += 0.05
            state.productivity_factor *= 1.05
            return True
        return False
