from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.enums import Tactic
from simulation.dtos import DecisionContext, FirmStateDTO

if TYPE_CHECKING:
    from simulation.firms import Firm


class RuleBasedFirmDecisionEngine(BaseDecisionEngine):
    """기업의 규칙 기반 의사결정 로직을 담당하는 엔진.

    AI로부터 전술(Tactic)을 전달받아, 사전에 정의된 규칙에 따라
    구체적인 시장 주문을 생성한다.
    """

    def __init__(
        self, config_module: Any, logger: Optional[logging.Logger] = None
    ) -> None:
        self.config_module = config_module
        self.logger = logger if logger else logging.getLogger(__name__)

    def make_decisions(
        self,
        context: DecisionContext,
    ) -> Tuple[List[Order], Tactic]:
        """
        이 메서드는 더 이상 사용되지 않습니다. AIDrivenFirmDecisionEngine이 전체적인 결정을 담당합니다.
        """
        raise NotImplementedError(
            "This method is deprecated. Use AIDrivenFirmDecisionEngine."
        )

    def _execute_tactic(
        self, tactic: Tactic, firm: FirmStateDTO, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        선택된 전술에 따라 실제 행동(주문 생성)을 수행한다.
        """
        self.logger.info(
            f"Firm {firm.id} chose Tactic: {tactic.name}",
            extra={"tick": current_tick, "agent_id": firm.id, "tactic": tactic.name},
        )

        if tactic == Tactic.ADJUST_PRODUCTION:
            return self._adjust_production(firm, current_tick)
        elif tactic == Tactic.ADJUST_WAGES:
            return self._adjust_wages(firm, current_tick, market_data)

        return []

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
            self.logger.info(
                f"Overstock of {item_id}. Reducing production target to {new_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["production_target"],
                },
            )
        elif is_understocked:
            new_target = min(
                max_target,
                target_quantity * (1 + adj_factor),
            )
            self.logger.info(
                f"Understock of {item_id}. Increasing production target to {new_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["production_target"],
                },
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

        if current_employees < self.config_module.FIRM_MIN_EMPLOYEES:
            order = Order(firm.id, "BUY", "labor", 1.0, offered_wage, "labor")
            orders.append(order)
            self.logger.info(
                f"Hiring to meet minimum employee count. Offering dynamic wage: {offered_wage:.2f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["hiring", "dynamic_wage"],
                },
            )
        elif (
            needed_labor > current_employees
            and current_employees < self.config_module.FIRM_MAX_EMPLOYEES
        ):
            order = Order(firm.id, "BUY", "labor", 1.0, offered_wage, "labor")
            orders.append(order)
            self.logger.info(
                f"Planning to BUY labor for dynamic wage {offered_wage:.2f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["hiring", "dynamic_wage"],
                },
            )

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
        if not firm.profit_history:
            return self.config_module.BASE_WAGE

        avg_profit = sum(firm.profit_history) / len(firm.profit_history)
        profit_based_premium = avg_profit / (self.config_module.BASE_WAGE * 10.0)
        wage_premium = max(
            0,
            min(
                profit_based_premium * self.config_module.WAGE_PROFIT_SENSITIVITY,
                self.config_module.MAX_WAGE_PREMIUM,
            ),
        )

        return self.config_module.BASE_WAGE * (1 + wage_premium)

    def _fire_excess_labor(self, firm: FirmStateDTO, needed_labor: float) -> List[Order]:
        """
        WO-110: Firing logic for Rule-Based Firms.
        Fires excess employees if current workforce exceeds needed labor (with tolerance).
        Returns list of FIRE orders.
        """
        current_employees = len(firm.employees)

        # Guard: Check if we actually have employees
        if current_employees == 0:
            return []

        # Allow slight overstaffing (buffer) to prevent hire/fire churn
        if current_employees <= needed_labor:
            return []

        excess = current_employees - int(needed_labor)
        # Keep at least 1 employee (skeleton crew) unless specified otherwise
        excess = min(excess, max(0, current_employees - 1))

        if excess <= 0:
            return []

        # Fire from the list (FIFO logic)
        candidates = firm.employees[:excess]
        orders = []

        severance_weeks = getattr(self.config_module, "SEVERANCE_PAY_WEEKS", 4)
        min_wage = getattr(self.config_module, "LABOR_MARKET_MIN_WAGE", 5.0)

        for emp_id in candidates:
            emp_data = firm.employees_data.get(emp_id, {})
            wage = emp_data.get("wage", min_wage)
            skill = emp_data.get("skill", 1.0)

            severance_pay = wage * skill * severance_weeks

            # Create FIRE Order
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
