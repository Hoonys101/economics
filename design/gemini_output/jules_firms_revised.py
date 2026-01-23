from __future__ import annotations
from collections import deque
from typing import List, Dict, Any, Optional, override, TYPE_CHECKING
import logging
import copy
import math

from simulation.models import Order, Transaction
from simulation.brands.brand_manager import BrandManager
from simulation.core_agents import Household
from simulation.markets.order_book_market import OrderBookMarket
from simulation.base_agent import BaseAgent
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext
from simulation.ai.enums import Personality

# SoC Refactor
from simulation.components.hr_department import HRDepartment
from simulation.components.finance_department import FinanceDepartment
from simulation.utils.shadow_logger import log_shadow

if TYPE_CHECKING:
    from simulation.loan_market import LoanMarket
    from simulation.ai.firm_system2_planner import FirmSystem2Planner
    from simulation.markets.stock_market import StockMarket

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
        # Phase 14-2: Innovation
        sector: str = "FOOD",
        is_visionary: bool = False,
        # Phase 16-B: Personality
        personality: Optional[Personality] = None,
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
        self.inventory_quality: Dict[
            str, float
        ] = {}  # Phase 15: Weighted Average Quality
        self.input_inventory: Dict[str, float] = {}  # WO-030: Raw Materials

        # Phase 14-2 attributes
        self.sector = sector
        self.is_visionary = is_visionary
        self.owner_id: Optional[int] = None  # Phase 14-1: Shareholder System

        # Phase 16-B: Personality & Innovation Attributes
        self.personality = personality or Personality.BALANCED
        self.base_quality: float = 1.0
        self.research_history: Dict[str, Any] = {
            "total_spent": 0.0,
            "success_count": 0,
            "last_success_tick": -1,
        }

        # SoC Refactor: HR and Finance Components
        self.hr = HRDepartment(self)
        self.finance = FinanceDepartment(self, config_module)

        # Set bankruptcy threshold based on visionary status
        base_threshold = getattr(
            config_module, "BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD", 5
        )
        if self.is_visionary:
            self.consecutive_loss_ticks_for_bankruptcy_threshold = base_threshold * 2
        else:
            self.consecutive_loss_ticks_for_bankruptcy_threshold = base_threshold

        self.production_target: float = (
            config_module.FIRM_MIN_PRODUCTION_TARGET
        )  # Initialize production target

        # Property redirections for compatibility
        # self.employees -> self.hr.employees
        # self.employee_wages -> self.hr.employee_wages

        self.current_production: float = 0.0
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = getattr(config_module, "IPO_INITIAL_SHARES", 1000.0)
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0  # Handled in HR but maybe exposed here?

        # --- Phase 9: M&A Attributes ---
        self.is_bankrupt: bool = False
        self.valuation: float = 0.0
        self.consecutive_loss_ticks_for_bankruptcy: int = (
            0  # Track separately strictly for rule
        )

        # --- Phase 6: Brand Engine ---
        self.brand_manager = BrandManager(self.id, config_module, logger)
        self.marketing_budget: float = 0.0  # Decision variable
        self.prev_awareness: float = 0.0  # For AI Reward Calculation
        # ROI Optimization
        self.marketing_budget_rate: float = 0.05  # Initial 5%

        # --- 주식 시장 관련 속성 ---
        self.founder_id: Optional[int] = None  # 창업자 가계 ID
        self.is_publicly_traded: bool = True  # 상장 여부
        self.dividend_rate: float = getattr(
            config_module, "DIVIDEND_RATE", 0.3
        )  # 기업별 배당률 (기본값: config)
        self.treasury_shares: float = self.total_shares  # 자사주 보유량
        self.capital_stock: float = 100.0  # 실물 자본재 (초기값: 100)

        # Phase 16-B: Rewards Tracking (Delta storage)
        self.prev_market_share: float = 0.0
        self.prev_assets: float = self.assets
        self.prev_avg_quality: float = 1.0

        # Phase 21: Automation
        self.automation_level: float = 0.0  # 0.0 to 1.0
        self.system2_planner: Optional[FirmSystem2Planner] = None  # Initialized later

        self.age = 0
        self.cash_reserve = initial_capital
        self.decision_engine.loan_market = loan_market

    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
        par_value = self.assets / self.total_shares if self.total_shares > 0 else 1.0
        stock_market.update_shareholder(self.id, self.id, self.treasury_shares)
        self.logger.info(
            f"IPO | Firm {self.id} initialized IPO with {self.total_shares} shares. Par value: {par_value:.2f}",
            extra={"agent_id": self.id, "tags": ["ipo", "stock_market"]},
        )

    # --- Properties to maintain Interface Compatibility ---
    @property
    def employees(self) -> List[Household]:
        return self.hr.employees

    @employees.setter
    def employees(self, value):
        self.hr.employees = value

    @property
    def employee_wages(self) -> Dict[int, float]:
        return self.hr.employee_wages

    @employee_wages.setter
    def employee_wages(self, value):
        self.hr.employee_wages = value

    @property
    def retained_earnings(self) -> float:
        return self.finance.retained_earnings

    @retained_earnings.setter
    def retained_earnings(self, value):
        self.finance.retained_earnings = value

    @property
    def dividends_paid_last_tick(self) -> float:
        return self.finance.dividends_paid_last_tick

    @dividends_paid_last_tick.setter
    def dividends_paid_last_tick(self, value):
        self.finance.dividends_paid_last_tick = value

    @property
    def consecutive_loss_turns(self) -> int:
        return self.finance.consecutive_loss_turns

    @consecutive_loss_turns.setter
    def consecutive_loss_turns(self, value):
        self.finance.consecutive_loss_turns = value

    @property
    def current_profit(self) -> float:
        return self.finance.current_profit

    @current_profit.setter
    def current_profit(self, value):
        self.finance.current_profit = value

    @property
    def revenue_this_turn(self) -> float:
        return self.finance.revenue_this_turn

    @revenue_this_turn.setter
    def revenue_this_turn(self, value):
        self.finance.revenue_this_turn = value

    @property
    def cost_this_turn(self) -> float:
        return self.finance.cost_this_turn

    @cost_this_turn.setter
    def cost_this_turn(self, value):
        self.finance.cost_this_turn = value

    @property
    def revenue_this_tick(self) -> float:
        return self.finance.revenue_this_tick

    @revenue_this_tick.setter
    def revenue_this_tick(self, value):
        self.finance.revenue_this_tick = value

    @property
    def expenses_this_tick(self) -> float:
        return self.finance.expenses_this_tick

    @expenses_this_tick.setter
    def expenses_this_tick(self, value):
        self.finance.expenses_this_tick = value

    @property
    def profit_history(self) -> deque[float]:
        return self.finance.profit_history

    @profit_history.setter
    def profit_history(self, value):
        self.finance.profit_history = value

    @property
    def last_revenue(self) -> float:
        return self.finance.last_revenue

    @last_revenue.setter
    def last_revenue(self, value):
        self.finance.last_revenue = value

    @property
    def last_marketing_spend(self) -> float:
        return self.finance.last_marketing_spend

    @last_marketing_spend.setter
    def last_marketing_spend(self, value):
        self.finance.last_marketing_spend = value

    @property
    def last_daily_expenses(self) -> float:
        return self.finance.last_daily_expenses

    @last_daily_expenses.setter
    def last_daily_expenses(self, value):
        self.finance.last_daily_expenses = value

    @property
    def last_sales_volume(self) -> float:
        return self.finance.last_sales_volume

    @last_sales_volume.setter
    def last_sales_volume(self, value):
        self.finance.last_sales_volume = value

    @property
    def sales_volume_this_tick(self) -> float:
        return self.finance.sales_volume_this_tick

    @sales_volume_this_tick.setter
    def sales_volume_this_tick(self, value):
        self.finance.sales_volume_this_tick = value

    def calculate_valuation(self) -> float:
        """
        Calculate Firm Valuation based on Net Assets + Profit Potential.
        Formula: Net Assets + (Max(0, Avg_Profit_Last_10) * PER Multiplier)
        """
        net_assets = self.assets + self.get_inventory_value() + self.capital_stock

        avg_profit = 0.0
        if len(self.finance.profit_history) > 0:
            avg_profit = sum(self.finance.profit_history) / len(
                self.finance.profit_history
            )

        profit_premium = max(0.0, avg_profit) * getattr(
            self.config_module, "VALUATION_PER_MULTIPLIER", 10.0
        )

        self.valuation = net_assets + profit_premium
        return self.valuation

    def get_inventory_value(self) -> float:
        """Calculate market value of current inventory."""
        total_value = 0.0
        for item_id, qty in self.inventory.items():
            # Use last known market price or book value? Market price is better.
            # But Firm stores last_prices?
            price = self.last_prices.get(item_id, 0.0)  # Or fetch from market?
            # If no price known, assume 0 or cost? Use valid price if possible.
            total_value += qty * price
        return total_value

    def liquidate_assets(self) -> float:
        """
        Liquidate assets.
        CRITICAL FIX (WO-018): Inventory and Capital Stock are written off to zero
        instead of being converted to cash, to prevent money creation from thin air.
        Only existing cash (assets) is returned.
        """
        # 1. Write off Inventory
        self.inventory.clear()

        # 2. Write off Capital Stock
        self.capital_stock = 0.0

        # 3. Write off Automation
        self.automation_level = 0.0

        self.is_bankrupt = True
        return self.assets

    def post_ask(
        self,
        item_id: str,
        price: float,
        quantity: float,
        market: OrderBookMarket,
        current_tick: int,
    ) -> Order:
        """
        판매 주문을 생성하고 시장에 제출합니다.
        Brand Metadata를 자동으로 주입합니다.
        """
        # 1. 브랜드 정보 스냅샷
        brand_snapshot = {
            "brand_awareness": self.brand_manager.brand_awareness,
            "perceived_quality": self.brand_manager.perceived_quality,
            "quality": self.inventory_quality.get(
                item_id, 1.0
            ),  # Phase 15: Physical Quality
        }

        # 2. 주문 생성 (brand_info 자동 주입)
        order = Order(
            agent_id=self.id,
            order_type="SELL",
            item_id=item_id,
            quantity=quantity,
            price=price,
            market_id=market.id,
            brand_info=brand_snapshot,  # <-- Critical Injection
        )

        # 3. 시장에 제출
        market.place_order(order, current_tick)

        self.logger.debug(
            f"FIRM_POST_ASK | Firm {self.id} posted SELL order for {quantity:.1f} {item_id} @ {price:.2f} with brand_info",
            extra={
                "agent_id": self.id,
                "tick": current_tick,
                "brand_awareness": brand_snapshot["brand_awareness"],
            },
        )

        return order

    def calculate_brand_premium(self, market_data: Dict[str, Any]) -> float:
        """
        브랜드 프리미엄 = 내 판매가격 - 시장 평균가격
        """
        item_id = self.specialization
        market_avg_key = f"{item_id}_avg_traded_price"

        market_avg_price = market_data.get("goods_market", {}).get(market_avg_key, 0.0)

        # 내 최근 판매가 (last_prices에서 조회)
        my_price = self.last_prices.get(item_id, market_avg_price)

        if market_avg_price > 0:
            brand_premium = my_price - market_avg_price
        else:
            brand_premium = 0.0

        return brand_premium

    def _adjust_marketing_budget(self) -> None:
        """Adjust marketing budget rate based on ROI."""
        delta_spend = self.marketing_budget  # Current tick spend

        # Skip first tick or zero previous spend
        # Note: We use last_marketing_spend from PREVIOUS tick to calculate ROI of THAT spend.
        # But we also need to avoid division by zero.
        if delta_spend <= 0 or self.finance.last_marketing_spend <= 0:
            self.finance.last_revenue = self.finance.revenue_this_turn
            self.finance.last_marketing_spend = self.marketing_budget
            return

        delta_revenue = self.finance.revenue_this_turn - self.finance.last_revenue
        efficiency = delta_revenue / self.finance.last_marketing_spend

        # Decision Rules
        saturation_level = getattr(
            self.config_module, "BRAND_AWARENESS_SATURATION", 0.9
        )
        high_eff_threshold = getattr(
            self.config_module, "MARKETING_EFFICIENCY_HIGH_THRESHOLD", 1.5
        )
        low_eff_threshold = getattr(
            self.config_module, "MARKETING_EFFICIENCY_LOW_THRESHOLD", 0.8
        )
        min_rate = getattr(self.config_module, "MARKETING_BUDGET_RATE_MIN", 0.01)
        max_rate = getattr(self.config_module, "MARKETING_BUDGET_RATE_MAX", 0.20)

        if self.brand_manager.brand_awareness >= saturation_level:
            pass  # Maintain (Saturation)
        elif efficiency > high_eff_threshold:
            self.marketing_budget_rate = min(max_rate, self.marketing_budget_rate * 1.1)
        elif efficiency < low_eff_threshold:
            self.marketing_budget_rate = max(min_rate, self.marketing_budget_rate * 0.9)

        # Update tracking
        self.finance.last_revenue = self.finance.revenue_this_turn
        self.finance.last_marketing_spend = self.marketing_budget

    def produce(
        self, current_time: int, technology_manager: Optional[Any] = None
    ) -> None:
        """
        Cobb-Douglas 생산 함수를 사용한 생산 로직.
        Phase 21: Modified Cobb-Douglas with Automation.
        """
        try:
            # [EARLY EXIT]
            if len(self.hr.employees) == 0:
                self.current_production = 0.0
                return

            log_extra = {
                "tick": current_time,
                "agent_id": self.id,
                "tags": ["production"],
            }

            # 1. 감가상각 처리
            depreciation_rate = getattr(
                self.config_module, "CAPITAL_DEPRECIATION_RATE", 0.05
            )
            self.capital_stock *= 1.0 - depreciation_rate

            # Phase 21: Automation Decay
            self.automation_level *= 0.995  # Slow decay (0.5% per tick)
            if self.automation_level < 0.001:
                self.automation_level = 0.0

            # 2. 노동 및 자본 투입량 계산
            # SoC Refactor: Get total labor skill from HR
            total_labor_skill = self.hr.get_total_labor_skill()

            # 3. Cobb-Douglas Parameters
            base_alpha = getattr(self.config_module, "LABOR_ALPHA", 0.7)
            automation_reduction = getattr(
                self.config_module, "AUTOMATION_LABOR_REDUCTION", 0.5
            )

            # Phase 21: Adjusted Alpha
            # alpha_adjusted = base_alpha * (1 - automation_level * 0.5)
            # If Automation = 1.0, Alpha = 0.7 * 0.5 = 0.35 (Capital dependent)
            alpha_raw = base_alpha * (
                1.0 - (self.automation_level * automation_reduction)
            )
            alpha_adjusted = max(
                getattr(self.config_module, "LABOR_ELASTICITY_MIN", 0.3), alpha_raw
            )
            beta_adjusted = 1.0 - alpha_adjusted

            # Effective Labor & Capital
            capital = max(self.capital_stock, 0.01)

            # Technology Multiplier (WO-053)
            tech_multiplier = 1.0

            tfp = (
                self.productivity_factor * tech_multiplier
            )  # Total Factor Productivity

            if technology_manager:
                tech_multiplier = technology_manager.get_productivity_multiplier(
                    self.id, self.sector
                )
                tfp *= tech_multiplier

            # Phase 15: Quality Calculation
            avg_skill = self.hr.get_avg_skill()

            item_config = self.config_module.GOODS.get(self.specialization, {})
            quality_sensitivity = item_config.get("quality_sensitivity", 0.5)
            actual_quality = self.base_quality + (
                math.log1p(avg_skill) * quality_sensitivity
            )

            self.current_production = 0.0

            if total_labor_skill > 0 and capital > 0:
                produced_quantity = (
                    tfp * (total_labor_skill**alpha_adjusted) * (capital**beta_adjusted)
                )
            else:
                produced_quantity = 0.0

            if produced_quantity > 0:
                # WO-030: Input Constraints Logic
                input_config = self.config_module.GOODS.get(
                    self.specialization, {}
                ).get("inputs", {})

                if input_config:
                    max_by_inputs = float("inf")
                    for mat, req_per_unit in input_config.items():
                        available = self.input_inventory.get(mat, 0.0)
                        if req_per_unit > 0:
                            max_by_inputs = min(max_by_inputs, available / req_per_unit)

                    # Constrain production
                    actual_produced = min(produced_quantity, max_by_inputs)

                    # Deduct used inputs
                    for mat, req_per_unit in input_config.items():
                        amount_to_deduct = actual_produced * req_per_unit
                        self.input_inventory[mat] = max(
                            0.0, self.input_inventory.get(mat, 0.0) - amount_to_deduct
                        )
                else:
                    actual_produced = produced_quantity

                if actual_produced > 0:
                    item_id = self.specialization
                    current_inventory = self.inventory.get(item_id, 0)
                    current_quality = self.inventory_quality.get(item_id, 1.0)

                    total_qty = current_inventory + actual_produced
                    new_avg_quality = (
                        (current_inventory * current_quality)
                        + (actual_produced * actual_quality)
                    ) / total_qty

                    self.inventory_quality[item_id] = new_avg_quality
                    self.inventory[item_id] = total_qty
                    self.current_production = actual_produced
                else:
                    self.current_production = 0.0
        except Exception as e:
            import traceback

            logger.error(f"FIRM_CRASH_PREVENTED | Firm {self.id}: {e}")
            logger.debug(traceback.format_exc())
            self.current_production = 0.0
            return

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
                "tags": ["stock", "issue"],
            },
        )
        return raised_capital

    def get_book_value_per_share(self) -> float:
        """주당 순자산가치(BPS)를 계산합니다. (유통주식수 기준)"""
        outstanding_shares = self.total_shares - self.treasury_shares
        if outstanding_shares <= 0:
            return 0.0

        # Calculate liabilities from bank loans
        liabilities = 0.0
        try:
            loan_market = getattr(self.decision_engine, "loan_market", None)
            if loan_market and hasattr(loan_market, "bank") and loan_market.bank:
                debt_summary = loan_market.bank.get_debt_summary(self.id)
                liabilities = debt_summary.get("total_principal", 0.0)
        except Exception:
            pass  # Graceful fallback

        net_assets = self.assets - liabilities
        return max(0.0, net_assets) / outstanding_shares

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
            personality=self.personality,  # Propagate personality
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

    def distribute_dividends(
        self, households: List[Household], current_time: int
    ) -> List[Transaction]:
        # SoC Refactor
        return self.finance.distribute_dividends(households, current_time)

    @override
    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        return {
            "assets": self.assets,
            "needs": self.needs.copy(),
            "inventory": self.inventory.copy(),
            "input_inventory": self.input_inventory.copy(),  # WO-030
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
            "base_quality": self.base_quality,  # AI needs to know this
            "inventory_quality": self.inventory_quality.copy(),
            "automation_level": self.automation_level,  # Phase 21
        }

    def get_pre_state_data(self) -> Dict[str, Any]:
        """AI 학습을 위한 이전 상태 데이터를 반환합니다."""
        return getattr(self, "pre_state_snapshot", self.get_agent_data())

    @override
    def make_decision(
        self,
        markets: Dict[str, Any],
        goods_data: list[Dict[str, Any]],
        market_data: Dict[str, Any],
        current_time: int,
        government: Optional[Any] = None,
        reflux_system: Optional[Any] = None,
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
            reflux_system=reflux_system,
        )
        decisions, tactic = self.decision_engine.make_decisions(context)

        # WO-056: Shadow Mode Calculation
        self._calculate_invisible_hand_price(markets, current_time)

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

    def _calculate_invisible_hand_price(
        self, markets: Dict[str, Any], current_tick: int
    ) -> None:
        """
        WO-056: Stage 1 Shadow Mode (Price Discovery 2.0).
        Calculates and logs the shadow price based on Excess Demand.
        """
        market = markets.get(self.specialization)
        # Check if market supports order book inspection
        if not market or not hasattr(market, "get_all_bids"):
            return

        # 1. Get Demand and Supply (Market-wide for this good)
        bids = market.get_all_bids(self.specialization)
        asks = market.get_all_asks(self.specialization)

        demand = sum(o.quantity for o in bids)
        supply = sum(o.quantity for o in asks)

        # 2. Calculate Excess Demand Ratio
        # Formula: (Demand - Supply) / Supply
        if supply > 0:
            excess_demand_ratio = (demand - supply) / supply
        else:
            # If supply is 0, treat as high demand pressure if demand exists
            excess_demand_ratio = 1.0 if demand > 0 else 0.0

        # 3. Calculate Candidate Price
        # Sensitivity: Default 0.1 if not configured
        sensitivity = getattr(self.config_module, "INVISIBLE_HAND_SENSITIVITY", 0.1)

        # Current Price: Use firm's last price or market avg fallback
        current_price = self.last_prices.get(self.specialization, 10.0)

        candidate_price = current_price * (1.0 + (sensitivity * excess_demand_ratio))

        # 4. Smoothing (Shadow Price)
        # Shadow_Price = (Candidate * 0.2) + (Current * 0.8)
        shadow_price = (candidate_price * 0.2) + (current_price * 0.8)

        # 5. Log
        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Firm",
            metric="shadow_price",
            current_value=current_price,
            shadow_value=shadow_price,
            details=f"Item={self.specialization}, D={demand:.1f}, S={supply:.1f}, Ratio={excess_demand_ratio:.2f}",
        )

    @override
    def update_needs(
        self,
        current_time: int,
        government: Optional[Any] = None,
        market_data: Optional[Dict[str, Any]] = None,
        reflux_system: Optional[Any] = None,
    ) -> None:
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
        self.finance.record_expense(holding_cost)

        # Phase 8-B: Capture holding cost (Storage Service Fee)
        if holding_cost > 0:
            if reflux_system:
                reflux_system.capture(holding_cost, str(self.id), "fixed_cost")
            self.logger.info(
                f"Paid inventory holding cost: {holding_cost:.2f}",
                extra={**log_extra, "holding_cost": holding_cost},
            )

        # Pay wages to employees (SoC: HR Delegate)
        total_wages = self.hr.process_payroll(current_time, government, market_data)
        if total_wages > 0:
            self.finance.record_expense(total_wages)
            self.logger.info(
                f"Paid total wages: {total_wages:.2f} to {len(self.employees)} employees.",
                extra={**log_extra, "total_wages": total_wages},
            )

        # --- Phase 6: Marketing Spend & Brand Update ---
        # Adaptive Budgeting
        marketing_spend = 0.0
        if self.assets > 100.0:
            marketing_spend = max(
                10.0, self.finance.revenue_this_turn * self.marketing_budget_rate
            )

        # Check affordability
        if self.assets < marketing_spend:
            marketing_spend = 0.0

        # Apply spend
        if marketing_spend > 0:
            self.assets -= marketing_spend
            self.finance.record_expense(marketing_spend)
            # Phase 8-B: Capture marketing spend (Ad Agency Fee)
            if reflux_system:
                reflux_system.capture(marketing_spend, str(self.id), "marketing")

        # Update state for AI/ROI (Explicitly assign to instance variable)
        self.marketing_budget = marketing_spend

        # Update Brand Assets
        actual_quality = self.productivity_factor / 10.0
        self.brand_manager.update(marketing_spend, actual_quality)

        # Adjust Budget Rate based on ROI
        self._adjust_marketing_budget()

        # --- Phase 2: System Stabilization (Tax & Fees) ---
        if government:
            # SoC: Finance Delegate
            self.finance.pay_maintenance(government, reflux_system, current_time)
            self.finance.pay_taxes(government, current_time)
        # ---------------------------------------------

        brand_premium = (
            self.calculate_brand_premium(market_data) if market_data else 0.0
        )
        self.logger.info(
            f"FIRM_BRAND_METRICS | Firm {self.id}: Awareness={self.brand_manager.brand_awareness:.4f}, "
            f"Quality={self.brand_manager.perceived_quality:.4f}, Premium={brand_premium:.2f}",
            extra={
                **log_extra,
                "brand_awareness": self.brand_manager.brand_awareness,
                "perceived_quality": self.brand_manager.perceived_quality,
                "brand_premium": brand_premium,
            },
        )

        self.needs["liquidity_need"] += self.config_module.LIQUIDITY_NEED_INCREASE_RATE
        self.needs["liquidity_need"] = min(100.0, self.needs["liquidity_need"])

        self.finance.check_bankruptcy()

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
                "brand_awareness": self.brand_manager.brand_awareness,
                "perceived_quality": self.brand_manager.perceived_quality,
            },
        )

    # Legacy: _pay_maintenance and _pay_taxes removed as they are now in FinanceDepartment

    def distribute_profit(self, agents: Dict[int, Any], current_time: int) -> float:
        """
        Phase 14-1: Mandatory Dividend Rule.
        Distribute surplus cash to owner if reserves are met.
        """
        return self.finance.distribute_profit_private(agents, current_time)
