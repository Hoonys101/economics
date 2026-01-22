from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional, Tuple
import logging

from simulation.models import Order
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.ai.enums import Tactic
from simulation.dtos import DecisionContext
from simulation.dtos.firm_state_dto import FirmStateDTO


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
        self, tactic: Tactic, firm_state: FirmStateDTO, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        선택된 전술에 따라 실제 행동(주문 생성)을 수행한다.
        """
        self.logger.info(
            f"Firm {firm_state.id} chose Tactic: {tactic.name}",
            extra={"tick": current_tick, "agent_id": firm_state.id, "tactic": tactic.name},
        )

        if tactic == Tactic.ADJUST_PRODUCTION:
            return self._adjust_production(firm_state, current_tick)
        elif tactic == Tactic.ADJUST_WAGES:
            return self._adjust_wages(firm_state, current_tick, market_data)

        return []

    def _adjust_production(self, firm_state: FirmStateDTO, current_tick: int) -> List[Order]:
        """
        재고 수준에 따라 생산 목표를 조정한다.
        """
        orders = []
        item_id = firm_state.specialization
        current_inventory = firm_state.inventory.get(item_id, 0)
        target_quantity = firm_state.production_target

        is_overstocked = (
            current_inventory > target_quantity * self.config_module.OVERSTOCK_THRESHOLD
        )
        is_understocked = (
            current_inventory
            < target_quantity * self.config_module.UNDERSTOCK_THRESHOLD
        )

        new_target = target_quantity

        if is_overstocked:
            new_target = max(
                self.config_module.FIRM_MIN_PRODUCTION_TARGET,
                target_quantity * (1 - self.config_module.PRODUCTION_ADJUSTMENT_FACTOR),
            )
            self.logger.info(
                f"Overstock of {item_id}. Reducing production target to {new_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm_state.id,
                    "tags": ["production_target"],
                },
            )
        elif is_understocked:
            new_target = min(
                self.config_module.FIRM_MAX_PRODUCTION_TARGET,
                target_quantity * (1 + self.config_module.PRODUCTION_ADJUSTMENT_FACTOR),
            )
            self.logger.info(
                f"Understock of {item_id}. Increasing production target to {new_target:.1f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm_state.id,
                    "tags": ["production_target"],
                },
            )

        # WO-107: Return internal order instead of modifying state
        if abs(new_target - target_quantity) > 1e-6:
             orders.append(
                 Order(firm_state.id, "SET_PRODUCTION_TARGET", "production_target", new_target, 0.0, "internal")
             )

        return orders

    def _adjust_wages(
        self, firm_state: FirmStateDTO, current_tick: int, market_data: Dict[str, Any]
    ) -> List[Order]:
        """
        필요 노동력과 현재 고용 상태에 따라 임금을 조정하고 고용 주문을 생성한다.
        """
        orders = []

        needed_labor = self._calculate_needed_labor(firm_state)
        offered_wage = self._calculate_dynamic_wage_offer(firm_state)

        # SoC Refactor: use firm_state.employee_count
        if firm_state.employee_count < self.config_module.FIRM_MIN_EMPLOYEES:
            # WO-098 Fix: Use correct market ID "labor"
            order = Order(firm_state.id, "BUY", "labor", 1.0, offered_wage, "labor")
            orders.append(order)
            self.logger.info(
                f"Hiring to meet minimum employee count. Offering dynamic wage: {offered_wage:.2f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm_state.id,
                    "tags": ["hiring", "dynamic_wage"],
                },
            )
        elif (
            needed_labor > firm_state.employee_count
            and firm_state.employee_count < self.config_module.FIRM_MAX_EMPLOYEES
        ):
            # WO-098 Fix: Use correct market ID "labor"
            order = Order(firm_state.id, "BUY", "labor", 1.0, offered_wage, "labor")
            orders.append(order)
            self.logger.info(
                f"Planning to BUY labor for dynamic wage {offered_wage:.2f}",
                extra={
                    "tick": current_tick,
                    "agent_id": firm_state.id,
                    "tags": ["hiring", "dynamic_wage"],
                },
            )

        return orders

    def _calculate_needed_labor(self, firm_state: FirmStateDTO) -> float:
        """
        생산 목표 달성에 필요한 총 노동력을 계산한다.
        """
        item_id = firm_state.specialization
        target_quantity = firm_state.production_target
        current_inventory = firm_state.inventory.get(item_id, 0)
        needed_production = max(0, target_quantity - current_inventory)
        if firm_state.productivity_factor <= 0:
            return 999999.0 # Impossible to produce without productivity

        needed_labor = needed_production / firm_state.productivity_factor
        return needed_labor

    def _calculate_dynamic_wage_offer(self, firm_state: FirmStateDTO) -> float:
        """기업의 수익성 이력을 바탕으로 동적인 임금 제시액을 계산합니다."""
        # SoC Refactor: use firm_state.profit_history
        if not firm_state.profit_history:
            return self.config_module.BASE_WAGE

        avg_profit = sum(firm_state.profit_history) / len(firm_state.profit_history)
        profit_based_premium = avg_profit / (self.config_module.BASE_WAGE * 10.0)
        wage_premium = max(
            0,
            min(
                profit_based_premium * self.config_module.WAGE_PROFIT_SENSITIVITY,
                self.config_module.MAX_WAGE_PREMIUM,
            ),
        )

        return self.config_module.BASE_WAGE * (1 + wage_premium)
