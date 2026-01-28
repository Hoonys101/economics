from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.enums import Tactic
from simulation.dtos import DecisionContext, FirmStateDTO

if TYPE_CHECKING:
    from simulation.dtos import MacroFinancialContext

class RuleBasedFirmDecisionEngine(BaseDecisionEngine):
    """
    Rule-Based Decision Engine for Firms.
    Implements mechanistic logic for production, pricing, and sales.
    """

    def __init__(
        self, config_module: Any, logger: Optional[logging.Logger] = None
    ) -> None:
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

    def _make_decisions_internal(
        self,
        context: DecisionContext,
        macro_context: Optional[MacroFinancialContext] = None,
    ) -> Tuple[List[Order], Tactic]:
        """
        Executes rule-based logic.
        """
        orders: List[Order] = []
        firm_state = context.state
        market_data = context.market_data
        current_tick = context.current_time

        # 1. Sales Logic (Sell Inventory)
        specialization = firm_state.specialization
        inventory = firm_state.inventory.get(specialization, 0.0)

        if inventory > 0:
            # Determine Price
            market_price = 10.0
            if "goods_market" in market_data:
                market_price = market_data["goods_market"].get(f"{specialization}_current_sell_price", 10.0)

            # Simple Undercut Strategy to ensure liquidity
            sell_price = max(0.1, market_price * 0.98)

            orders.append(Order(
                agent_id=firm_state.id,
                order_type="SELL",
                item_id=specialization,
                quantity=inventory,
                price=sell_price,
                market_id=specialization
            ))

        # 2. Production Adjustment (Target Setting)
        # Use existing logic helper
        prod_orders = self._adjust_production(firm_state, current_tick)
        orders.extend(prod_orders)

        # 3. Wage & Hiring Logic
        # Use existing logic helper
        wage_orders = self._adjust_wages(firm_state, current_tick, market_data)
        orders.extend(wage_orders)

        # 4. Firing Logic (Cost Cutting)
        needed_labor = self._calculate_needed_labor(firm_state)
        current_employees = len(firm_state.employees)

        # Simple firing logic: if we have more than needed + 1 (buffer), fire excess
        if current_employees > needed_labor + 1:
             fire_orders = self._fire_excess_labor(firm_state, needed_labor)
             orders.extend(fire_orders)

        return orders, Tactic.MAINTAIN_STATUS_QUO

    def _fire_excess_labor(self, firm: FirmStateDTO, needed_labor: float) -> List[Order]:
        """
        Fires excess employees if current workforce exceeds needed labor (with tolerance).
        """
        current_employees = len(firm.employees)
        excess = current_employees - int(needed_labor)
        # Always keep at least 1 employee unless shutting down? (Let's keep 1)
        excess = min(excess, max(0, current_employees - 1))

        if excess <= 0:
            return []

        # Fire from the list (FIFO logic - first in list)
        candidates = firm.employees[:excess]
        orders = []

        severance_weeks = getattr(self.config_module, "SEVERANCE_PAY_WEEKS", 4)
        min_wage = getattr(self.config_module, "LABOR_MARKET_MIN_WAGE", 5.0)

        # Access employee details via DTO if available, else use defaults.
        # Assuming FirmStateDTO could be extended or we assume standard wage for RuleBased.
        # However, for robustness, we should try to use actual data if possible.
        # Since BaseDecisionEngine operates on DTOs, and DTOs might not have deep employee data,
        # we will use a conservative estimate or look for 'employees_data' if it exists.

        employees_data = getattr(firm, "employees_data", {})

        for emp_id in candidates:
            emp_info = employees_data.get(emp_id, {})
            current_wage = emp_info.get("wage", min_wage)
            # Skill multiplier? RuleBased usually assumes standard skill 1.0 or stored in DTO
            skill = emp_info.get("skill", 1.0)

            severance_pay = current_wage * severance_weeks * skill

            orders.append(Order(
                firm.id,
                "FIRE",
                "internal",
                1,
                severance_pay,
                "internal",
                target_agent_id=emp_id
            ))

            self.logger.info(
                f"RuleBased Firing: Firm {firm.id} planning to fire Agent {emp_id}. Severance: {severance_pay:.2f}",
                extra={"tick": 0, "agent_id": firm.id, "tags": ["firing"]}
            )

        return orders

    def _adjust_production(self, firm: FirmStateDTO, current_tick: int) -> List[Order]:
        """
        재고 수준에 따라 생산 목표를 조정한다.
        """
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        target_quantity = firm.production_target

        overstock_threshold = getattr(self.config_module, "OVERSTOCK_THRESHOLD", 1.2)
        understock_threshold = getattr(self.config_module, "UNDERSTOCK_THRESHOLD", 0.8)
        adj_factor = getattr(self.config_module, "PRODUCTION_ADJUSTMENT_FACTOR", 0.1)
        min_target = getattr(self.config_module, "FIRM_MIN_PRODUCTION_TARGET", 10.0)
        max_target = getattr(self.config_module, "FIRM_MAX_PRODUCTION_TARGET", 500.0)

        new_target = target_quantity

        is_overstocked = current_inventory > target_quantity * overstock_threshold
        is_understocked = current_inventory < target_quantity * understock_threshold

        if is_overstocked:
            new_target = max(
                min_target,
                target_quantity * (1 - adj_factor),
            )
        elif is_understocked:
            new_target = min(
                max_target,
                target_quantity * (1 + adj_factor),
            )

        if new_target != target_quantity:
            return [Order(firm.id, "SET_TARGET", "internal", new_target, 0.0, "internal")]

        return []

    def _adjust_wages(
        self, firm: FirmStateDTO, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        필요 노동력과 현재 고용 상태에 따라 임금을 조정하고 고용 주문을 생성한다.
        """
        orders = []

        needed_labor = self._calculate_needed_labor(firm)
        offered_wage = self._calculate_dynamic_wage_offer(firm)

        current_employees = len(firm.employees)

        min_employees = getattr(self.config_module, "FIRM_MIN_EMPLOYEES", 1)
        max_employees = getattr(self.config_module, "FIRM_MAX_EMPLOYEES", 100)

        if current_employees < min_employees:
            to_hire = min_employees - current_employees
            order = Order(firm.id, "BUY", "labor", float(to_hire), offered_wage, "labor")
            orders.append(order)
        elif (
            needed_labor > current_employees
            and current_employees < max_employees
        ):
            to_hire = min(needed_labor - current_employees, max_employees - current_employees)
            order = Order(firm.id, "BUY", "labor", float(to_hire), offered_wage, "labor")
            orders.append(order)

        return orders

    def _calculate_needed_labor(self, firm: FirmStateDTO) -> float:
        """
        생산 목표 달성에 필요한 총 노동력을 계산한다.
        """
        item_id = firm.specialization
        target_quantity = firm.production_target
        current_inventory = firm.inventory.get(item_id, 0)
        needed_production = max(0, target_quantity - current_inventory)
        if firm.productivity_factor <= 0:
            return 999999.0 # Impossible to produce without productivity

        needed_labor = needed_production / firm.productivity_factor
        return needed_labor

    def _calculate_dynamic_wage_offer(self, firm: FirmStateDTO) -> float:
        """기업의 수익성 이력을 바탕으로 동적인 임금 제시액을 계산합니다."""
        # Use default values safely
        base_wage = getattr(self.config_module, "BASE_WAGE", 10.0)
        sensitivity = getattr(self.config_module, "WAGE_PROFIT_SENSITIVITY", 0.1)
        max_premium = getattr(self.config_module, "MAX_WAGE_PREMIUM", 2.0)

        if not firm.profit_history:
            return base_wage

        avg_profit = sum(firm.profit_history) / len(firm.profit_history)
        profit_based_premium = avg_profit / (base_wage * 10.0)
        wage_premium = max(
            0,
            min(
                profit_based_premium * sensitivity,
                max_premium,
            ),
        )

        return base_wage * (1 + wage_premium)
