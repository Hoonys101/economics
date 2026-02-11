from __future__ import annotations
import logging
import math
from modules.firm.api import IProductionEngine, ProductionInputDTO, ProductionResultDTO

logger = logging.getLogger(__name__)

class ProductionEngine(IProductionEngine):
    """
    Stateless Engine for Production operations.
    Handles Cobb-Douglas production, automation decay, and R&D.
    Implements IProductionEngine.
    """

    def produce(
        self,
        input_dto: ProductionInputDTO
    ) -> ProductionResultDTO:
        """
        Executes production logic.
        Calculates production output based on labor, capital, and technology.
        Returns a DTO describing the result of the production cycle.
        """
        firm_snapshot = input_dto.firm_snapshot
        config = firm_snapshot.config
        production_state = firm_snapshot.production
        hr_state = firm_snapshot.hr

        try:
            # 1. Depreciation & Decay (Calculation, NO mutation)
            capital_depreciation_rate = config.capital_depreciation_rate
            capital_depreciation = production_state.capital_stock * capital_depreciation_rate
            effective_capital = max(production_state.capital_stock - capital_depreciation, 0.01)

            # Automation Decay
            # Original: state.automation_level *= 0.995
            # So decay is (1 - 0.995) = 0.005
            automation_decay_rate = 0.005 # Hardcoded in original logic
            automation_decay = production_state.automation_level * automation_decay_rate
            effective_automation = production_state.automation_level - automation_decay

            if effective_automation < 0.001:
                # If it drops below threshold, we lose the rest
                automation_decay += effective_automation
                effective_automation = 0.0

            # 2. Gather Inputs from HR State
            employees_data = hr_state.employees_data
            num_employees = len(employees_data)
            total_labor_skill = sum(emp.get("skill", 1.0) for emp in employees_data.values())
            avg_skill = total_labor_skill / num_employees if num_employees > 0 else 0.0

            # [EARLY EXIT]
            if total_labor_skill <= 0:
                return ProductionResultDTO(
                    success=True,
                    quantity_produced=0.0,
                    quality=0.0,
                    specialization=production_state.specialization,
                    capital_depreciation=capital_depreciation,
                    automation_decay=automation_decay
                )

            # 3. Production Parameters
            # Cobb-Douglas Parameters
            base_alpha = config.labor_alpha
            automation_reduction = config.automation_labor_reduction

            # Alpha Adjusted
            alpha_raw = base_alpha * (1.0 - (effective_automation * automation_reduction))
            alpha_adjusted = max(config.labor_elasticity_min, alpha_raw)
            beta_adjusted = 1.0 - alpha_adjusted

            # Technology Multiplier
            tfp = production_state.productivity_factor
            tfp *= input_dto.productivity_multiplier

            # Quality Calculation
            item_config = config.goods.get(production_state.specialization, {})
            quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
            # Use base_quality from state
            actual_quality = production_state.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

            produced_quantity = 0.0
            if total_labor_skill > 0 and effective_capital > 0:
                produced_quantity = tfp * (total_labor_skill ** alpha_adjusted) * (effective_capital ** beta_adjusted)

            actual_produced = 0.0
            consumed_inputs = {}

            production_cost = 0.0

            if produced_quantity > 0:
                # Input Constraints
                input_config = item_config.get("inputs", {})

                if input_config:
                    max_by_inputs = float('inf')
                    input_inventory = production_state.input_inventory

                    for mat, req_per_unit in input_config.items():
                        available = input_inventory.get(mat, 0.0)
                        if req_per_unit > 0:
                            max_by_inputs = min(max_by_inputs, available / req_per_unit)

                    actual_produced = min(produced_quantity, max_by_inputs)

                    # Calculate consumed inputs
                    for mat, req_per_unit in input_config.items():
                        consumed_inputs[mat] = actual_produced * req_per_unit
                else:
                    actual_produced = produced_quantity

            return ProductionResultDTO(
                success=True,
                quantity_produced=actual_produced,
                quality=actual_quality,
                specialization=production_state.specialization,
                inputs_consumed=consumed_inputs,
                production_cost=production_cost,
                capital_depreciation=capital_depreciation,
                automation_decay=automation_decay
            )

        except Exception as e:
            logger.error(f'PRODUCTION_ERROR | Firm {firm_snapshot.id}: {e}')
            return ProductionResultDTO(
                success=False,
                quantity_produced=0.0,
                quality=0.0,
                specialization=production_state.specialization,
                error_message=str(e)
            )
