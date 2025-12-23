from collections import deque
from typing import List, Dict, Any, Optional, override
import logging
import copy

from simulation.models import Order, Transaction
from simulation.core_agents import Household  # Household 클래스 임포트
from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext

logger = logging.getLogger(__name__)


class Firm(BaseAgent):
    """기업 주체. 생산과 고용의 주체."""

    def __init__(
        self,
        id: int,
        initial_capital: float,
        initial_liquidity_need: float,
        specialization: str,
        productivity_factor: float,
        decision_engine: BaseDecisionEngine,
        value_orientation: str,
        config_module: Any,
        initial_inventory: Optional[Dict[str, float]] = None,
        loan_market: Any = None,
        logger: Any = None,
    ) -> None:
        super().__init__(
            id,
            initial_capital,
            {"liquidity_need": initial_liquidity_need},
            decision_engine,
            value_orientation,
            name=f"Firm_{id}",
            logger=logger,
        )
        self.config_module = config_module  # Store config_module
        if initial_inventory is not None:
            self.inventory.update(initial_inventory)
        self.specialization = specialization
        self.production_target: float = (
            config_module.FIRM_MIN_PRODUCTION_TARGET
        )  # Initialize production target
        self.employees: List[Household] = []
        self.consecutive_loss_turns: int = 0
        self.current_profit: float = 0.0
        self.revenue_this_turn: float = 0.0
        self.cost_this_turn: float = 0.0
        self.current_production: float = 0.0
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = 100.0
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0
        # --- GEMINI_PROPOSED_ADDITION_START ---
        # design/project_management/dynamic_wage_design_spec.md
        self.profit_history: deque[float] = deque(maxlen=self.config_module.PROFIT_HISTORY_TICKS)
        self.revenue_this_tick = 0.0
        self.expenses_this_tick = 0.0
        # --- GEMINI_PROPOSED_ADDITION_END ---

        self.decision_engine.loan_market = loan_market

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float) -> "Firm":
        """
        현재 기업 인스턴스를 복제하여 새로운 기업을 생성합니다.
        AI 모델(decision_engine)을 포함하여 깊은 복사를 수행합니다.
        """
        cloned_decision_engine = copy.deepcopy(self.decision_engine)

        new_firm = Firm(
            id=new_id,
            initial_capital=initial_assets_from_parent,  # 현재 자산을 초기 자본으로 설정
            initial_liquidity_need=self.config_module.INITIAL_FIRM_LIQUIDITY_NEED,  # 초기 유동성 필요는 설정값으로 리셋
            specialization=self.specialization,
            productivity_factor=self.productivity_factor,
            decision_engine=cloned_decision_engine,
            value_orientation=self.value_orientation,
            config_module=self.config_module,
            initial_inventory=copy.deepcopy(self.inventory),
            loan_market=self.decision_engine.loan_market,  # loan_market은 공유
            logger=self.logger,
        )
        new_firm.logger.info(
            f"Firm {self.id} was cloned to new Firm {new_id}",
            extra={
                "original_agent_id": self.id,
                "new_agent_id": new_id,
                "tags": ["lifecycle", "clone"],
            },
        )
        return new_firm

    def distribute_dividends(self, households: List[Household], current_time: int) -> List[Transaction]:
        transactions = []
        distributable_profit = max(
            0, self.current_profit * self.config_module.DIVIDEND_RATE
        )

        if distributable_profit > 0:
            for household in households:
                shares = household.shares_owned.get(self.id, 0.0)
                if shares > 0:
                    dividend_amount = distributable_profit * (
                        shares / self.total_shares
                    )
                    transactions.append(
                        Transaction(
                            buyer_id=household.id,
                            seller_id=self.id,
                            item_id="dividend",
                            quantity=dividend_amount,
                            price=1.0,
                            market_id="financial",
                            transaction_type="dividend",
                            time=current_time,
                        )
                    )
                    self.logger.info(
                        f"Firm {self.id} distributed {dividend_amount:.2f} dividend to Household {household.id}.",
                        extra={
                            "tick": current_time,
                            "agent_id": self.id,
                            "household_id": household.id,
                            "amount": dividend_amount,
                            "tags": ["dividend"],
                        },
                    )

        self.current_profit = 0.0
        self.revenue_this_turn = 0.0
        self.cost_this_turn = 0.0
        return transactions

    @override
    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        return {
            "assets": self.assets,
            "needs": self.needs.copy(),
            "inventory": self.inventory.copy(),
            "employees": [emp.id for emp in self.employees],  # Only pass employee IDs
            "is_active": self.is_active,
            "current_production": self.current_production,
            "productivity_factor": self.productivity_factor,
            "production_target": self.production_target,
            "revenue_this_turn": self.revenue_this_turn,
            "expenses_this_tick": self.expenses_this_tick,
            "consecutive_loss_turns": self.consecutive_loss_turns,
        }

    def get_pre_state_data(self) -> Dict[str, Any]:
        """AI 학습을 위한 이전 상태 데이터를 반환합니다."""
        return getattr(self, "pre_state_snapshot", self.get_agent_data())


    @override
    def make_decision(
        self, markets: Dict[str, Any], goods_data: list[Dict[str, Any]], market_data: Dict[str, Any], current_time: int
    ) -> tuple[list[Order], Any]:
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_action"]}
        self.logger.debug(
            f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "assets_before": self.assets,
                "num_employees_before": len(self.employees),
                "is_active_before": self.is_active,
            },
        )
        context = DecisionContext(
            firm=self,
            markets=markets,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
        )
        decisions, tactic = self.decision_engine.make_decisions(context)
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}, Decisions={len(decisions)}",
            extra={
                **log_extra,
                "assets_after": self.assets,
                "num_employees_after": len(self.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(decisions),
            },
        )
        return decisions, tactic

    def produce(self, current_time: int) -> None:
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["production"]}

        total_labor_skill = sum(employee.labor_skill for employee in self.employees)
        # The firm's production capacity is based on its employees' skills and its productivity factor.
        produced_quantity = total_labor_skill * self.productivity_factor
        self.current_production = 0.0

        self.logger.info(
            f"Starting production for {self.specialization}. Total capacity: {produced_quantity:.2f} (Labor: {total_labor_skill:.1f}, ProdFactor: {self.productivity_factor:.2f})",
            extra={
                **log_extra,
                "total_capacity": produced_quantity,
                "total_labor_skill": total_labor_skill,
                "productivity_factor": self.productivity_factor,
            },
        )

        if produced_quantity > 0:
            item_id = self.specialization
            current_inventory = self.inventory.get(item_id, 0)
            self.inventory[item_id] = current_inventory + produced_quantity
            self.current_production = produced_quantity
            self.logger.info(
                f"Produced {produced_quantity:.1f} of {item_id}. New inventory: {self.inventory[item_id]:.1f}",
                extra={
                    **log_extra,
                    "item_id": item_id,
                    "produced_quantity": produced_quantity,
                    "new_inventory": self.inventory[item_id],
                },
            )
        else:
            self.logger.info("No employees, no production.", extra=log_extra)

    @override
    def update_needs(self, current_time: int) -> None:
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_needs"]}
        self.logger.debug(
            f"FIRM_NEEDS_UPDATE_START | Firm {self.id} needs before update: Liquidity={self.needs['liquidity_need']:.1f}, Assets={self.assets:.2f}, Employees={len(self.employees)}",
            extra={
                **log_extra,
                "needs_before": self.needs,
                "assets_before": self.assets,
                "num_employees_before": len(self.employees),
            },
        )

        inventory_value = sum(self.inventory.values())
        holding_cost = inventory_value * self.config_module.INVENTORY_HOLDING_COST_RATE
        self.assets -= holding_cost
        self.cost_this_turn += holding_cost
        if holding_cost > 0:
            self.logger.info(
                f"Paid inventory holding cost: {holding_cost:.2f}",
                extra={**log_extra, "holding_cost": holding_cost},
            )

        self.needs["liquidity_need"] += self.config_module.LIQUIDITY_NEED_INCREASE_RATE
        self.needs["liquidity_need"] = min(100.0, self.needs["liquidity_need"])

        if self.current_profit < 0:
            self.consecutive_loss_turns += 1
        else:
            self.consecutive_loss_turns = 0

        if (
            self.assets <= self.config_module.ASSETS_CLOSURE_THRESHOLD
            or self.consecutive_loss_turns
            >= self.config_module.FIRM_CLOSURE_TURNS_THRESHOLD
        ):
            self.is_active = False
            self.logger.warning(
                f"FIRM_INACTIVE | Firm {self.id} closed down. Assets: {self.assets:.2f}, Consecutive Loss Turns: {self.consecutive_loss_turns}",
                extra={
                    **log_extra,
                    "assets": self.assets,
                    "consecutive_loss_turns": self.consecutive_loss_turns,
                    "tags": ["firm_closure"],
                },
            )
        self.logger.debug(
            f"FIRM_NEEDS_UPDATE_END | Firm {self.id} needs after update: Liquidity={self.needs['liquidity_need']:.1f}, Assets={self.assets:.2f}, Employees={len(self.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "needs_after": self.needs,
                "assets_after": self.assets,
                "num_employees_after": len(self.employees),
                "is_active_after": self.is_active,
            },
        )
