from __future__ import annotations
import logging
import math
from typing import Dict, Any, Optional, List

from modules.firm.api import (
    IProductionEngine, ProductionInputDTO, ProductionResultDTO,
    ProductionContextDTO, ProductionIntentDTO, ProcurementIntentDTO,
    IProductionDepartment, AgentID
)
from modules.system.api import MarketSnapshotDTO
from simulation.models import Order

logger = logging.getLogger(__name__)

class ProductionEngine(IProductionEngine, IProductionDepartment):
    """
    Stateless Engine for Production operations.
    Handles Cobb-Douglas production, automation decay, and R&D.
    Implements IProductionEngine and IProductionDepartment.
    """

    def decide_production(self, context: ProductionContextDTO) -> ProductionIntentDTO:
        """
        Pure function: ProductionContextDTO -> ProductionIntentDTO.
        Decides production quantity and calculates consumption/depreciation.
        """
        # 1. Depreciation & Decay (Calculation, NO mutation)
        # MIGRATION: Integer Math for Capital Depreciation (pennies)
        # Formula: floor(capital_stock * rate_basis_points / 10000)
        rate_bp = int(context.capital_depreciation_rate * 10000)
        capital_depreciation_val = (context.capital_stock * rate_bp) // 10000

        # effective_capital must be at least 0.
        effective_capital = max(context.capital_stock - capital_depreciation_val, 0)

        # Automation Decay (Float is acceptable for non-monetary abstract value)
        automation_decay_rate = 0.005
        automation_decay = context.automation_level * automation_decay_rate
        effective_automation = context.automation_level - automation_decay

        if effective_automation < 0.001:
            automation_decay += effective_automation
            effective_automation = 0.0

        avg_skill = context.employees_avg_skill
        total_labor_skill = avg_skill * context.current_workforce_count

        # [EARLY EXIT]
        if total_labor_skill <= 0:
            return ProductionIntentDTO(
                target_production_quantity=0.0,
                materials_to_use={},
                estimated_cost_pennies=0,
                capital_depreciation=int(capital_depreciation_val),
                automation_decay=automation_decay,
                quality=0.0
            )

        # 3. Production Parameters
        base_alpha = context.labor_alpha
        automation_reduction = context.automation_labor_reduction

        # Alpha Adjusted
        alpha_raw = base_alpha * (1.0 - (effective_automation * automation_reduction))
        alpha_adjusted = max(context.labor_elasticity_min, alpha_raw)
        beta_adjusted = 1.0 - alpha_adjusted

        # Technology Multiplier
        tfp = context.production_efficiency
        tfp *= context.technology_level # productivity_multiplier passed in context.technology_level? No, technology_level is base?
        # In build_context, I will map input_dto.productivity_multiplier * firm.productivity_factor to technology_level.

        # Quality Calculation
        quality_sensitivity = context.quality_sensitivity
        actual_quality = context.base_quality + (math.log1p(avg_skill) * quality_sensitivity)

        produced_quantity = 0.0
        if total_labor_skill > 0 and effective_capital > 0:
            # Standard Cobb-Douglas
            produced_quantity = tfp * (total_labor_skill ** alpha_adjusted) * (effective_capital ** beta_adjusted)

        actual_produced = 0.0
        consumed_inputs = {}

        # Production Cost (if tracking specific batch costs)
        production_cost = 0

        if produced_quantity > 0:
            # Input Constraints
            input_config = context.input_goods

            if input_config:
                max_by_inputs = float('inf')
                input_inventory = context.inventory_raw_materials

                for mat, req_per_unit in input_config.items():
                    available = input_inventory.get(mat, 0.0)
                    if req_per_unit > 0:
                        max_by_inputs = min(max_by_inputs, available / req_per_unit)

                actual_produced = min(produced_quantity, max_by_inputs)
            else:
                actual_produced = produced_quantity

            # MIGRATION: Deterministic Integer Output
            actual_produced = math.floor(actual_produced)

            if input_config and actual_produced > 0:
                # Calculate consumed inputs based on integer output
                for mat, req_per_unit in input_config.items():
                    consumed_inputs[mat] = actual_produced * req_per_unit

        return ProductionIntentDTO(
            target_production_quantity=float(actual_produced),
            materials_to_use=consumed_inputs,
            estimated_cost_pennies=production_cost,
            capital_depreciation=int(capital_depreciation_val),
            automation_decay=automation_decay,
            quality=actual_quality
        )

    def decide_procurement(self, context: ProductionContextDTO) -> ProcurementIntentDTO:
        """
        Decides on procurement of raw materials based on production target.
        """
        orders: List[Order] = []
        if not context.input_goods:
            return ProcurementIntentDTO(purchase_orders=[])

        target_production = context.production_target
        if target_production <= 0:
            return ProcurementIntentDTO(purchase_orders=[])

        market_signals = context.market_snapshot.market_signals if context.market_snapshot else {}
        market_data = context.market_snapshot.market_data if context.market_snapshot else {}

        for mat, req_per_unit in context.input_goods.items():
            needed = target_production * req_per_unit
            current = context.inventory_raw_materials.get(mat, 0.0)
            deficit = needed - current

            if deficit > 0:
                bid_price = 1000 # Default 10.00 pennies

                # Check Market Signals (Last Traded)
                if mat in market_signals and market_signals[mat].last_traded_price:
                     bid_price = market_signals[mat].last_traded_price
                # Check Market Signals (Best Ask) if last traded is missing
                elif mat in market_signals and market_signals[mat].best_ask:
                     bid_price = market_signals[mat].best_ask
                # Legacy Fallback
                elif 'goods_market' in market_data:
                     key = f'{mat}_avg_traded_price'
                     if key in market_data['goods_market']:
                         bid_price = int(market_data['goods_market'][key])

                # Apply Premium
                bid_price_pennies = int(bid_price * 1.05)
                if bid_price_pennies <= 0: bid_price_pennies = 1000

                order = Order(
                    agent_id=context.firm_id,
                    side='BUY',
                    item_id=mat,
                    quantity=deficit,
                    price_pennies=bid_price_pennies,
                    price_limit=float(bid_price_pennies)/100.0,
                    market_id=mat
                )
                orders.append(order)

        return ProcurementIntentDTO(purchase_orders=orders)

    def produce(
        self,
        input_dto: ProductionInputDTO
    ) -> ProductionResultDTO:
        """
        Executes production logic.
        Delegates to decide_production for core logic.
        """
        try:
            # Build Context
            context = self._build_context(input_dto)

            # Execute Core Logic
            intent = self.decide_production(context)

            # Map back to Result
            return ProductionResultDTO(
                success=True,
                quantity_produced=intent.target_production_quantity,
                quality=intent.quality,
                specialization=context.specialization,
                inputs_consumed=intent.materials_to_use,
                production_cost=intent.estimated_cost_pennies,
                capital_depreciation=intent.capital_depreciation,
                automation_decay=intent.automation_decay
            )

        except Exception as e:
            logger.error(f'PRODUCTION_ERROR | Firm {input_dto.firm_snapshot.id}: {e}')
            return ProductionResultDTO(
                success=False,
                quantity_produced=0.0,
                quality=0.0,
                specialization=input_dto.firm_snapshot.production.specialization,
                error_message=str(e),
                production_cost=0,
                capital_depreciation=0
            )

    def _build_context(self, input_dto: ProductionInputDTO) -> ProductionContextDTO:
        firm_snapshot = input_dto.firm_snapshot
        config = firm_snapshot.config
        prod_state = firm_snapshot.production
        hr_state = firm_snapshot.hr

        # Calculate derived values
        employees_data = hr_state.employees_data
        num_employees = len(employees_data)
        total_labor_skill = sum(emp.get("skill", 1.0) for emp in employees_data.values())
        avg_skill = total_labor_skill / num_employees if num_employees > 0 else 0.0

        item_config = config.goods.get(prod_state.specialization, {})

        # technology_level = productivity_factor * input_dto.productivity_multiplier
        tech_level = prod_state.productivity_factor * input_dto.productivity_multiplier

        return ProductionContextDTO(
            firm_id=AgentID(firm_snapshot.id),
            tick=0, # Not available in InputDTO, defaulting to 0 as it's unused in calculation
            budget_pennies=0, # Not used in current logic
            market_snapshot=MarketSnapshotDTO(tick=0, market_signals={}, market_data={}), # Dummy
            available_cash_pennies=0, # Not used
            is_solvent=True, # Not used

            inventory_raw_materials=prod_state.input_inventory,
            inventory_finished_goods=prod_state.inventory,
            current_workforce_count=num_employees,
            production_target=prod_state.production_target, # Populated from snapshot
            technology_level=tech_level,
            production_efficiency=1.0,

            capital_stock=prod_state.capital_stock,
            automation_level=prod_state.automation_level,

            input_goods=item_config.get("inputs", {}),
            output_good_id=prod_state.specialization,

            labor_alpha=config.labor_alpha,
            automation_labor_reduction=config.automation_labor_reduction,
            labor_elasticity_min=config.labor_elasticity_min,
            capital_depreciation_rate=config.capital_depreciation_rate,
            specialization=prod_state.specialization,
            base_quality=prod_state.base_quality,
            quality_sensitivity=item_config.get("quality_sensitivity", 0.5),
            employees_avg_skill=avg_skill
        )
