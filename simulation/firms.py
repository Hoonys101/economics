from __future__ import annotations
from collections import deque
from typing import List, Dict, Any, Optional, override, TYPE_CHECKING
import logging
import copy

from simulation.models import Order, Transaction
from simulation.core_agents import Household  # Household 클래스 임포트
from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext
from simulation.brands.brand_manager import BrandManager

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket

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
        loan_market: Optional[LoanMarket] = None,
        logger: Optional[logging.Logger] = None,
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
        self.employee_wages: Dict[int, float] = {}  # AgentID -> Wage
        self.consecutive_loss_turns: int = 0
        self.current_profit: float = 0.0
        self.revenue_this_turn: float = 0.0
        self.cost_this_turn: float = 0.0
        self.current_production: float = 0.0
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = self.config_module.FIRM_DEFAULT_TOTAL_SHARES
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0
        # --- GEMINI_PROPOSED_ADDITION_START ---
        # design/project_management/dynamic_wage_design_spec.md
        self.profit_history: deque[float] = deque(maxlen=self.config_module.PROFIT_HISTORY_TICKS)
        self.revenue_this_tick = 0.0
        self.expenses_this_tick = 0.0
        # --- GEMINI_PROPOSED_ADDITION_END ---
        
        # --- Phase 6: Brand Economy ---
        self.brand_manager = BrandManager(config_module)
        self.marketing_budget_this_tick: float = 0.0

        # --- 주식 시장 관련 속성 ---
        self.founder_id: Optional[int] = None  # 창업자 가계 ID
        self.is_publicly_traded: bool = True   # 상장 여부
        self.dividend_rate: float = getattr(
            config_module, "DIVIDEND_RATE", 0.3
        )  # 기업별 배당률 (기본값: config)
        self.treasury_shares: float = 0.0  # 자사주 보유량
        self.capital_stock: float = 100.0   # 실물 자본재 (초기값)

        self.decision_engine.loan_market = loan_market

    def issue_shares(self, quantity: float, price: float) -> float:
        """
        신규 주식을 발행합니다 (유상증자).
        
        Args:
            quantity: 발행할 주식 수량
            price: 주당 발행 가격
            
        Returns:
            조달된 자본금
        """
        if quantity <= 0 or price <= 0:
            return 0.0
        
        self.total_shares += quantity
        raised_capital = quantity * price
        self.assets += raised_capital
        
        self.logger.info(
            f"Firm {self.id} issued {quantity:.1f} shares at {price:.2f}, "
            f"raising {raised_capital:.2f} capital. Total shares: {self.total_shares:.1f}",
            extra={
                "agent_id": self.id,
                "quantity": quantity,
                "price": price,
                "raised_capital": raised_capital,
                "total_shares": self.total_shares,
                "tags": ["stock", "issue"]
            }
        )
        return raised_capital

    def get_book_value_per_share(self) -> float:
        """주당 순자산가치(BPS)를 계산합니다. (유통주식수 기준)"""
        outstanding_shares = self.total_shares - self.treasury_shares
        if outstanding_shares <= 0:
            return 0.0
        # TODO: 부채 차감 필요 (현재는 자산만 고려)
        net_assets = self.assets
        return net_assets / outstanding_shares

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        """
        시가총액을 계산합니다.
        
        Args:
            stock_price: 주가 (None이면 순자산가치 기반 계산)
            
        Returns:
            시가총액
        """
        if stock_price is None:
            stock_price = self.get_book_value_per_share()
        
        outstanding_shares = self.total_shares - self.treasury_shares
        return outstanding_shares * stock_price


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
            0, self.current_profit * self.dividend_rate
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
        self.revenue_this_tick = 0.0
        self.expenses_this_tick = 0.0
        self.marketing_budget_this_tick = 0.0
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
            "total_shares": self.total_shares,
            "treasury_shares": self.treasury_shares,
            "dividend_rate": self.dividend_rate,
            "capital_stock": self.capital_stock,
            # Phase 6
            "brand_awareness": self.brand_manager.brand_awareness,
            "perceived_quality": self.brand_manager.perceived_quality,
        }

    def get_pre_state_data(self) -> Dict[str, Any]:
        """AI 학습을 위한 이전 상태 데이터를 반환합니다."""
        return getattr(self, "pre_state_snapshot", self.get_agent_data())


    @override
    def make_decision(
        self, markets: Dict[str, Any], goods_data: list[Dict[str, Any]], market_data: Dict[str, Any], current_time: int, government: Optional[Any] = None
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
            government=government,
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
        """
        Cobb-Douglas 생산 함수를 사용한 생산 로직.
        Y = A * L^α * K^(1-α)
        - A: 총요소생산성 (productivity_factor)
        - L: 노동 투입량 (total_labor_skill)
        - K: 자본 투입량 (capital_stock)
        - α: 노동의 산출 탄력성 (LABOR_ALPHA)
        """
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["production"]}

        # 1. 감가상각 처리
        depreciation_rate = getattr(self.config_module, "CAPITAL_DEPRECIATION_RATE", 0.05)
        self.capital_stock *= (1.0 - depreciation_rate)

        # 2. 노동 및 자본 투입량 계산
        total_labor_skill = sum(employee.labor_skill for employee in self.employees)
        capital = max(self.capital_stock, 0.01)  # 0 방지

        # 3. Cobb-Douglas 생산 함수
        alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
        tfp = self.productivity_factor  # Total Factor Productivity

        if total_labor_skill > 0 and capital > 0:
            produced_quantity = tfp * (total_labor_skill ** alpha) * (capital ** (1 - alpha))
        else:
            produced_quantity = 0.0

        self.current_production = 0.0

        # Phase 6: Update Brand Manager with Quality
        # Actual Quality is defined as Productivity / 10.0 in spec
        actual_quality = self.productivity_factor / 10.0
        # Marketing update happens here or via make_decision?
        # Ideally, make_decision sets budget, and we spend it here or in update_needs?
        # Let's assume make_decision already deducted cash and set self.marketing_budget_this_tick.
        self.brand_manager.update(self.marketing_budget_this_tick, actual_quality)

        self.logger.info(
            f"Production (Cobb-Douglas) for {self.specialization}. "
            f"Y={produced_quantity:.2f} (A={tfp:.2f}, L={total_labor_skill:.1f}, K={capital:.1f}, α={alpha:.2f})",
            extra={
                **log_extra,
                "produced_quantity": produced_quantity,
                "tfp": tfp,
                "labor": total_labor_skill,
                "capital": capital,
                "alpha": alpha,
                "marketing_spend": self.marketing_budget_this_tick,
                "brand_awareness": self.brand_manager.brand_awareness,
                "perceived_quality": self.brand_manager.perceived_quality
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
            self.logger.info("No employees or no capital, no production.", extra=log_extra)

    @override
    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None) -> None:
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

        # Pay wages to employees
        total_wages = 0.0
        total_tax_withheld = 0.0

        # Calculate survival cost for tax logic (if government/market_data is available)
        survival_cost = 10.0 # Default fallback
        if government and market_data:
            survival_cost = government.get_survival_cost(market_data)

        for employee in list(self.employees):
            # Clean up employees who no longer work here (quit or hired elsewhere)
            if employee.employer_id != self.id or not employee.is_employed:
                self.employees.remove(employee)
                if employee.id in self.employee_wages:
                    del self.employee_wages[employee.id]
                continue

            wage = self.employee_wages.get(employee.id, self.config_module.LABOR_MARKET_MIN_WAGE)
            
            # Affordability check
            if self.assets >= wage:
                # Calculate Tax
                income_tax = 0.0
                if government:
                    income_tax = government.calculate_income_tax(wage, survival_cost)
                
                net_wage = wage - income_tax

                # Transactions
                self.assets -= wage
                employee.assets += net_wage # Pay Net Wage
                
                if income_tax > 0 and government:
                    government.collect_tax(income_tax, "income_tax", employee.id, current_time)
                    total_tax_withheld += income_tax

                total_wages += wage
                self.expenses_this_tick += wage
                self.cost_this_turn += wage
            else:
                # Cannot afford wage! Fire employee
                self.logger.warning(f"Firm {self.id} cannot afford wage for Household {employee.id}. Firing.")
                employee.quit()
                if employee.id in self.employee_wages:
                    del self.employee_wages[employee.id]
        
        if total_wages > 0:
            self.logger.info(
                f"Paid total wages: {total_wages:.2f} to {len(self.employees)} employees.",
                extra={**log_extra, "total_wages": total_wages},
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
