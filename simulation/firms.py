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
from simulation.dtos import DecisionContext, FiscalContext, DecisionInputDTO
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.dtos.firm_state_dto import FirmStateDTO
from simulation.ai.enums import Personality
from modules.system.api import MarketSnapshotDTO

# SoC Refactor
from simulation.components.hr_department import HRDepartment
from simulation.components.finance_department import FinanceDepartment
from simulation.components.production_department import ProductionDepartment
from simulation.components.sales_department import SalesDepartment
from simulation.utils.shadow_logger import log_shadow
from modules.finance.api import InsufficientFundsError
from simulation.systems.api import ILearningAgent, LearningUpdateContext
from modules.system.api import MarketSnapshotDTO

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.loan_market import LoanMarket
    from simulation.ai.firm_system2_planner import FirmSystem2Planner
    from simulation.markets.stock_market import StockMarket
    from simulation.agents.government import Government
    from simulation.dtos.scenario import StressScenarioConfig

logger = logging.getLogger(__name__)

class Firm(BaseAgent, ILearningAgent):
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
        config_dto: FirmConfigDTO,
        initial_inventory: Optional[Dict[str, float]] = None,
        loan_market: Optional[LoanMarket] = None,
        logger: Optional[logging.Logger] = None,
        # Phase 14-2: Innovation
        sector: str = "FOOD",
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
        self.settlement_system: Optional["ISettlementSystem"] = None
        self.config = config_dto
        if initial_inventory is not None:
            self.inventory.update(initial_inventory)
        self.specialization = specialization
        self.inventory_quality: Dict[str, float] = {}  # Phase 15: Weighted Average Quality
        self.input_inventory: Dict[str, float] = {} # WO-030: Raw Materials
        
        # Phase 14-2 attributes
        self.sector = sector
        self.owner_id: Optional[int] = None # Phase 14-1: Shareholder System
        
        # Phase 16-B: Personality & Innovation Attributes
        self.personality = personality or Personality.BALANCED
        self.base_quality: float = 1.0
        self.research_history: Dict[str, Any] = {
            "total_spent": 0.0,
            "success_count": 0,
            "last_success_tick": -1
        }

        # SoC Refactor: HR and Finance Components
        self.hr = HRDepartment(self)
        # WO-103 Phase 1: Initialize Finance with buffered assets
        # Fix: Use initial_capital passed to constructor, or self._assets from BaseAgent
        self.finance = FinanceDepartment(self, self.config, initial_capital=initial_capital)

        self.production = ProductionDepartment(self, self.config)
        self.sales = SalesDepartment(self, self.config)

        # Set bankruptcy threshold
        self.consecutive_loss_ticks_for_bankruptcy_threshold = self.config.bankruptcy_consecutive_loss_threshold

        self.production_target: float = (
            self.config.firm_min_production_target
        )  # Initialize production target

        self.current_production: float = 0.0
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = self.config.ipo_initial_shares
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0 # Handled in HR but maybe exposed here?
        
        # --- Phase 9: M&A Attributes ---
        self.is_bankrupt: bool = False
        self.valuation: float = 0.0
        self.consecutive_loss_ticks_for_bankruptcy: int = 0 # Track separately strictly for rule
        
        # --- Phase 6: Brand Engine ---
        self.brand_manager = BrandManager(self.id, self.config, logger)
        self.marketing_budget: float = 0.0 # Decision variable
        self.prev_awareness: float = 0.0  # For AI Reward Calculation
        # ROI Optimization
        self.marketing_budget_rate: float = 0.05  # Initial 5%

        # --- 주식 시장 관련 속성 ---
        self.founder_id: Optional[int] = None  # 창업자 가계 ID
        self.is_publicly_traded: bool = True   # 상장 여부
        self.dividend_rate: float = self.config.dividend_rate  # 기업별 배당률 (기본값: config)
        self.treasury_shares: float = self.total_shares  # 자사주 보유량
        self.capital_stock: float = 100.0   # 실물 자본재 (초기값: 100)

        # Phase 16-B: Rewards Tracking (Delta storage)
        self.prev_market_share: float = 0.0
        # Refactor: Use finance.balance
        self.prev_assets: float = self.finance.balance
        self.prev_avg_quality: float = 1.0

        # Phase 21: Automation
        self.automation_level: float = 0.0 # 0.0 to 1.0
        self.system2_planner: Optional[FirmSystem2Planner] = None # Initialized later

        # WO-157: Sales Velocity Tracking
        self.inventory_last_sale_tick: Dict[str, int] = {}

        self.age = 0
        # WO-103 Phase 1: Removed self.cash_reserve redundancy. Using FinanceDepartment.
        self.has_bailout_loan = False
        self.decision_engine.loan_market = loan_market

    # [REMOVED] assets property. Now uses BaseAgent.assets (which delegates to _assets)
    # But Firm uses finance.balance for actual operations.

    def _add_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to FinanceDepartment."""
        if hasattr(self, 'finance'):
            self.finance.credit(amount, "Settlement Transfer")
        else:
            self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to FinanceDepartment."""
        if hasattr(self, 'finance'):
            self.finance.debit(amount, "Settlement Transfer")
        else:
            self._assets -= amount

    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
        # Refactor: Use finance.balance
        assets = self.finance.balance
        par_value = assets / self.total_shares if self.total_shares > 0 else 1.0
        stock_market.update_shareholder(self.id, self.id, self.treasury_shares)
        self.logger.info(
            f"IPO | Firm {self.id} initialized IPO with {self.total_shares} shares. Par value: {par_value:.2f}",
            extra={"agent_id": self.id, "tags": ["ipo", "stock_market"]}
        )

    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None:
        """
        WO-157: Records a sale event to track inventory velocity.
        """
        self.inventory_last_sale_tick[item_id] = current_tick

    def liquidate_assets(self, current_tick: int = -1) -> float:
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

        # WO-123: Memory Logging - Record Bankruptcy
        if self.memory_v2:
            from modules.memory.V2.dtos import MemoryRecordDTO
            record = MemoryRecordDTO(
                tick=current_tick,
                agent_id=self.id,
                event_type="BANKRUPTCY",
                data={"assets_returned": self.finance.balance}
            )
            self.memory_v2.add_record(record)

        return self.finance.balance

    def add_inventory(self, item_id: str, quantity: float, quality: float):
        """Adds items to the firm's inventory and updates the average quality."""
        current_inventory = self.inventory.get(item_id, 0)
        current_quality = self.inventory_quality.get(item_id, 1.0)

        total_qty = current_inventory + quantity
        if total_qty > 0:
            new_avg_quality = ((current_inventory * current_quality) + (quantity * quality)) / total_qty
            self.inventory_quality[item_id] = new_avg_quality

        self.inventory[item_id] = total_qty

    def post_ask(self, item_id: str, price: float, quantity: float, market: OrderBookMarket, current_tick: int) -> Order:
        return self.sales.post_ask(item_id, price, quantity, market, current_tick)

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
        self.sales.adjust_marketing_budget()

    def produce(self, current_time: int, technology_manager: Optional[Any] = None) -> None:
        self.current_production = self.production.produce(current_time, technology_manager)

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Firm":
        """
        현재 기업 인스턴스를 복제하여 새로운 기업을 생성합니다.
        AI 모델(decision_engine)을 포함하여 깊은 복사를 수행합니다.
        """
        cloned_decision_engine = copy.deepcopy(self.decision_engine)

        new_firm = Firm(
            id=new_id,
            initial_capital=initial_assets_from_parent,  # 현재 자산을 초기 자본으로 설정
            initial_liquidity_need=self.config.initial_firm_liquidity_need,  # 초기 유동성 필요는 설정값으로 리셋
            specialization=self.specialization,
            productivity_factor=self.productivity_factor,
            decision_engine=cloned_decision_engine,
            value_orientation=self.value_orientation,
            config_dto=self.config,
            initial_inventory=copy.deepcopy(self.inventory),
            loan_market=self.decision_engine.loan_market,  # loan_market은 공유
            logger=self.logger,
            personality=self.personality # Propagate personality
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

    @override
    def get_agent_data(self) -> Dict[str, Any]:
        """AI 의사결정에 필요한 에이전트의 현재 상태 데이터를 반환합니다."""
        return {
            "assets": self.finance.balance, # Direct Access
            "needs": self.needs.copy(),
            "inventory": self.inventory.copy(),
            "input_inventory": self.input_inventory.copy(), # WO-030
            # SoC Refactor
            "employees": [emp.id for emp in self.hr.employees],  # Only pass employee IDs
            "is_active": self.is_active,
            "current_production": self.current_production,
            "productivity_factor": self.productivity_factor,
            "production_target": self.production_target,
            # SoC Refactor
            "revenue_this_turn": self.finance.revenue_this_turn,
            "expenses_this_tick": self.finance.expenses_this_tick,
            "consecutive_loss_turns": self.finance.consecutive_loss_turns,
            "total_shares": self.total_shares,
            "treasury_shares": self.treasury_shares,
            "dividend_rate": self.dividend_rate,
            "capital_stock": self.capital_stock,
            "base_quality": self.base_quality, # AI needs to know this
            "inventory_quality": self.inventory_quality.copy(),
            "automation_level": self.automation_level, # Phase 21
        }

    def get_state_dto(self) -> FirmStateDTO:
        """
        Creates a FirmStateDTO representing the current state of the firm.
        WO-108: Added for parity and DTO compliance.
        """
        return FirmStateDTO.from_firm(self)

    def get_pre_state_data(self) -> Dict[str, Any]:
        """AI 학습을 위한 이전 상태 데이터를 반환합니다."""
        return getattr(self, "pre_state_snapshot", self.get_agent_data())


    @override
    def make_decision(
        self, input_dto: DecisionInputDTO
    ) -> tuple[list[Order], Any]:
        # Unpack
        # markets = input_dto.markets # Removed TD-194
        goods_data = input_dto.goods_data
        market_data = input_dto.market_data
        current_time = input_dto.current_time
        fiscal_context = input_dto.fiscal_context
        stress_scenario_config = input_dto.stress_scenario_config
        market_snapshot = input_dto.market_snapshot
        government_policy = input_dto.government_policy
        agent_registry = input_dto.agent_registry or {}

        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_action"]}
        # SoC Refactor
        self.logger.debug(
            f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={self.finance.balance:.2f}, Employees={len(self.hr.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "assets_before": self.finance.balance,
                "num_employees_before": len(self.hr.employees),
                "is_active_before": self.is_active,
            },
        )

        # Config DTO is already available
        config_dto = self.config
        state_dto = self.get_state_dto()

        context = DecisionContext(
            state=state_dto,
            config=config_dto,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            stress_scenario_config=stress_scenario_config,
            market_snapshot=market_snapshot,
            government_policy=government_policy,
            agent_registry=agent_registry or {}
        )
        decision_output = self.decision_engine.make_decisions(context)
        
        if hasattr(decision_output, "orders"):
            decisions = decision_output.orders
            tactic = decision_output.metadata
        else:
            decisions, tactic = decision_output

        # WO-114: Internal Order Interceptor (Purity Gate execution)
        external_orders = []
        for order in decisions:
            if order.market_id == "internal":
                gov_proxy = fiscal_context.government if fiscal_context else None
                self._execute_internal_order(order, gov_proxy, current_time)
            else:
                external_orders.append(order)

        # WO-157: Dynamic Pricing Override
        self.sales.check_and_apply_dynamic_pricing(external_orders, current_time)

        # WO-056: Shadow Mode Calculation
        if market_snapshot:
             self._calculate_invisible_hand_price(market_snapshot, current_time)

        # SoC Refactor
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={self.finance.balance:.2f}, Employees={len(self.hr.employees)}, is_active={self.is_active}, Decisions={len(external_orders)}",
            extra={
                **log_extra,
                "assets_after": self.finance.balance,
                "num_employees_after": len(self.hr.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(external_orders),
            },
        )
        return external_orders, tactic

    def _execute_internal_order(self, order: Order, government: Optional[Any], current_time: int) -> None:
        """
        [REFACTORED] Routes internal orders to the correct department.
        """
        if order.order_type == "SET_TARGET":
            self.production.set_production_target(order.quantity)

        elif order.order_type == "INVEST_AUTOMATION":
            self.production.invest_in_automation(order.quantity, government)

        elif order.order_type == "PAY_TAX":
            # Finance still handles this directly as it's purely financial
            amount = order.quantity
            reason = order.item_id
            if government:
                self.finance.pay_ad_hoc_tax(amount, reason, government, current_time)

        elif order.order_type == "INVEST_RD":
            self.production.invest_in_rd(order.quantity, government, current_time)

        elif order.order_type == "INVEST_CAPEX":
            self.production.invest_in_capex(order.quantity, government)

        elif order.order_type == "SET_DIVIDEND":
            self.finance.set_dividend_rate(order.quantity)

        elif order.order_type == "SET_PRICE":
            self.sales.set_price(order.item_id, order.quantity)

        elif order.order_type == "FIRE":
            self.hr.fire_employee(order.target_agent_id, order.price)

    def _calculate_invisible_hand_price(self, market_snapshot: MarketSnapshotDTO, current_tick: int) -> None:
        """
        WO-056: Stage 1 Shadow Mode (Price Discovery 2.0).
        Calculates and logs the shadow price based on Excess Demand.
        """
        if not market_snapshot.market_signals:
            return

        signal = market_snapshot.market_signals.get(self.specialization)
        if not signal:
            return

        # 1. Get Demand and Supply (from signals)
        demand = signal.total_bid_quantity
        supply = signal.total_ask_quantity

        # 2. Calculate Excess Demand Ratio
        # Formula: (Demand - Supply) / Supply
        if supply > 0:
            excess_demand_ratio = (demand - supply) / supply
        else:
            # If supply is 0, treat as high demand pressure if demand exists
            excess_demand_ratio = 1.0 if demand > 0 else 0.0

        # 3. Calculate Candidate Price
        # Sensitivity: Default 0.1 if not configured
        sensitivity = self.config.invisible_hand_sensitivity

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
            details=f"Item={self.specialization}, D={demand:.1f}, S={supply:.1f}, Ratio={excess_demand_ratio:.2f}"
        )

    def generate_transactions(self, government: Optional[Any], market_data: Dict[str, Any], all_households: List[Household], current_time: int) -> List[Transaction]:
        """
        Generates all financial transactions for the tick (Wages, Taxes, Dividends, etc.).
        Phase 3 Architecture.
        """
        transactions = []

        # 1. Wages & Income Tax (HR)
        tx_payroll = self.hr.process_payroll(current_time, government, market_data)
        transactions.extend(tx_payroll)

        # 2. Finance Transactions (Holding, Maint, Corp Tax, Dividends, Bailout Repayment)
        tx_finance = self.finance.generate_financial_transactions(government, all_households, current_time)
        transactions.extend(tx_finance)

        # 3. Marketing (Direct Calculation here as per old update_needs)
        if self.finance.balance > 100.0:
            marketing_spend = max(10.0, self.finance.revenue_this_turn * self.marketing_budget_rate)
        else:
            marketing_spend = 0.0

        if self.finance.balance < marketing_spend:
             marketing_spend = 0.0

        if marketing_spend > 0:
            tx_marketing = self.finance.generate_marketing_transaction(government, current_time, marketing_spend)
            if tx_marketing:
                transactions.append(tx_marketing)

        # State Update: Set budget for next decisions
        self.marketing_budget = marketing_spend
        # Brand Update: Needs to happen (optimistic about spend success)
        self.brand_manager.update(marketing_spend, self.productivity_factor / 10.0)
        self.sales.adjust_marketing_budget()

        return transactions

    @override
    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, technology_manager: Optional[Any] = None) -> None:
        """
        [DEPRECATED] This logic has been moved to AgentLifecycleManager._process_firm_lifecycle.
        Kept for BaseAgent interface compliance.
        """
        pass

    # Legacy: _pay_maintenance and _pay_taxes removed as they are now in FinanceDepartment

    def distribute_profit(self, agents: Dict[int, Any], current_time: int) -> float:
        """
        Legacy method kept for compatibility but should use generate_transactions.
        """
        return 0.0

    def deposit(self, amount: float) -> None:
        """Deposits a given amount into the firm's cash reserves."""
        if amount > 0:
            self.finance.credit(amount, "Deposit")

    def withdraw(self, amount: float) -> None:
        """Withdraws a given amount from the firm's cash reserves."""
        if amount > 0:
            if self.finance.balance < amount:
                raise InsufficientFundsError(f"Firm {self.id} has insufficient funds for withdrawal of {amount:.2f}. Available: {self.finance.balance:.2f}")
            self.finance.debit(amount, "Withdrawal")

    # --- Delegated Methods (Facade Pattern) ---

    def get_book_value_per_share(self) -> float:
        """Delegates to FinanceDepartment."""
        return self.finance.get_book_value_per_share()

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        """Delegates to FinanceDepartment."""
        return self.finance.get_market_cap(stock_price)

    def calculate_valuation(self) -> float:
        """Delegates to FinanceDepartment."""
        return self.finance.calculate_valuation()

    def get_financial_snapshot(self) -> Dict[str, float]:
        """Delegates to FinanceDepartment."""
        return self.finance.get_financial_snapshot()

    def update_learning(self, context: LearningUpdateContext) -> None:
        """
        ILearningAgent implementation.
        Updates the internal AI engine with the new state and reward.
        """
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]

        # 엔진은 더 이상 firm.decision_engine.ai_engine에 직접 접근하지 않고 이 메서드를 통해 요청합니다.
        if hasattr(self.decision_engine, 'ai_engine'):
            self.decision_engine.ai_engine.update_learning_v2(
                reward=reward,
                next_agent_data=next_agent_data,
                next_market_data=next_market_data,
            )
