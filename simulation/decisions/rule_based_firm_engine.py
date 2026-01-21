from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.enums import Tactic
from simulation.dtos import DecisionContext

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
        self, tactic: Tactic, firm: Firm, current_tick: int, market_data: Dict[str, Any]
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

    def _adjust_production(self, firm: Firm, current_tick: int) -> List[Order]:
        """
        재고 수준에 따라 생산 목표를 조정한다.
        """
        item_id = firm.specialization
        current_inventory = firm.inventory.get(item_id, 0)
        target_quantity = firm.production_target

        is_overstocked = (
            current_inventory > target_quantity * self.config_module.OVERSTOCK_THRESHOLD
        )
        is_understocked = (
            current_inventory
            < target_quantity * self.config_module.UNDERSTOCK_THRESHOLD
        )

        if is_overstocked:
            firm.production_target = max(
                self.config_module.FIRM_MIN_PRODUCTION_TARGET,
                target_quantity * (1 - self.config_module.PRODUCTION_ADJUSTMENT_FACTOR),
            )
            self.logger.info(
                f"Overstock of {item_id}. Reducing production target to {firm.production_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["production_target"],
                },
            )
        elif is_understocked:
            firm.production_target = min(
                self.config_module.FIRM_MAX_PRODUCTION_TARGET,
                target_quantity * (1 + self.config_module.PRODUCTION_ADJUSTMENT_FACTOR),
            )
            self.logger.info(
                f"Understock of {item_id}. Increasing production target to {firm.production_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm.id,
                    "tags": ["production_target"],
                },
            )

        return []  # 생산 목표 조정은 직접적인 주문을 생성하지 않음

    def _adjust_wages(
        self, firm: Firm, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        필요 노동력과 현재 고용 상태에 따라 임금을 조정하고 고용 주문을 생성한다.
        """
        orders = []

        needed_labor = self._calculate_needed_labor(firm)
        offered_wage = self._calculate_dynamic_wage_offer(firm)

        # SoC Refactor: use hr.employees
        if len(firm.hr.employees) < self.config_module.FIRM_MIN_EMPLOYEES:
            # WO-098 Fix: Use correct market ID "labor"
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
            needed_labor > len(firm.hr.employees)
            and len(firm.hr.employees) < self.config_module.FIRM_MAX_EMPLOYEES
        ):
            # WO-098 Fix: Use correct market ID "labor"
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

    def _calculate_needed_labor(self, firm: Firm) -> float:
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

    def _calculate_dynamic_wage_offer(self, firm: Firm) -> float:
        """기업의 수익성 이력을 바탕으로 동적인 임금 제시액을 계산합니다."""
        # SoC Refactor: use finance.profit_history
        if not firm.finance.profit_history:
            return self.config_module.BASE_WAGE

        avg_profit = sum(firm.finance.profit_history) / len(firm.finance.profit_history)
        profit_based_premium = avg_profit / (self.config_module.BASE_WAGE * 10.0)
        wage_premium = max(
            0,
            min(
                profit_based_premium * self.config_module.WAGE_PROFIT_SENSITIVITY,
                self.config_module.MAX_WAGE_PREMIUM,
            ),
        )

        return self.config_module.BASE_WAGE * (1 + wage_premium)
