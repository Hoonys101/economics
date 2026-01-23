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
from simulation.dtos import DecisionContext, FirmConfigDTO
from simulation.dtos.firm_state_dto import FirmStateDTO
from simulation.ai.enums import Personality

# SoC Refactor
from simulation.components.hr_department import HRDepartment
from simulation.components.finance_department import FinanceDepartment
from simulation.components.production_department import ProductionDepartment
from simulation.components.sales_department import SalesDepartment
from simulation.utils.shadow_logger import log_shadow
from modules.finance.api import InsufficientFundsError
from simulation.systems.api import ILearningAgent, LearningUpdateContext

if TYPE_CHECKING:
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
        # WO-103 Phase 1: Initialize buffer for assets property
        self._assets_buffer: float = 0.0

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
        self.inventory_quality: Dict[str, float] = {}  # Phase 15: Weighted Average Quality
        self.input_inventory: Dict[str, float] = {} # WO-030: Raw Materials
        
        # Phase 14-2 attributes
        self.sector = sector
        self.is_visionary = is_visionary
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
        self.finance = FinanceDepartment(self, config_module, initial_capital=initial_capital)

        self.production = ProductionDepartment(self, config_module)
        self.sales = SalesDepartment(self, config_module)

        # Set bankruptcy threshold based on visionary status
        base_threshold = getattr(config_module, "BANKRUPTCY_CONSECUTIVE_LOSS_THRESHOLD", 5)
        if self.is_visionary:
            self.consecutive_loss_ticks_for_bankruptcy_threshold = base_threshold * 2
        else:
             self.consecutive_loss_ticks_for_bankruptcy_threshold = base_threshold

        self.production_target: float = (
            config_module.FIRM_MIN_PRODUCTION_TARGET
        )  # Initialize production target

        self.current_production: float = 0.0
        self.productivity_factor: float = productivity_factor
        self.total_shares: float = getattr(config_module, "IPO_INITIAL_SHARES", 1000.0)
        self.last_prices: Dict[str, float] = {}
        self.hires_last_tick: int = 0 # Handled in HR but maybe exposed here?
        
        # --- Phase 9: M&A Attributes ---
        self.is_bankrupt: bool = False
        self.valuation: float = 0.0
        self.consecutive_loss_ticks_for_bankruptcy: int = 0 # Track separately strictly for rule
        
        # --- Phase 6: Brand Engine ---
        self.brand_manager = BrandManager(self.id, config_module, logger)
        self.marketing_budget: float = 0.0 # Decision variable
        self.prev_awareness: float = 0.0  # For AI Reward Calculation
        # ROI Optimization
        self.marketing_budget_rate: float = 0.05  # Initial 5%

        # --- 주식 시장 관련 속성 ---
        self.founder_id: Optional[int] = None  # 창업자 가계 ID
        self.is_publicly_traded: bool = True   # 상장 여부
        self.dividend_rate: float = getattr(
            config_module, "DIVIDEND_RATE", 0.3
        )  # 기업별 배당률 (기본값: config)
        self.treasury_shares: float = self.total_shares  # 자사주 보유량
        self.capital_stock: float = 100.0   # 실물 자본재 (초기값: 100)

        # Phase 16-B: Rewards Tracking (Delta storage)
        self.prev_market_share: float = 0.0
        self.prev_assets: float = self.assets
        self.prev_avg_quality: float = 1.0

        # Phase 21: Automation
        self.automation_level: float = 0.0 # 0.0 to 1.0
        self.system2_planner: Optional[FirmSystem2Planner] = None # Initialized later

        self.age = 0
        # WO-103 Phase 1: Removed self.cash_reserve redundancy. Using FinanceDepartment.
        self.has_bailout_loan = False
        self.decision_engine.loan_market = loan_market

    # WO-103 Phase 1: Assets Property to delegate to FinanceDepartment
    @property
    def assets(self) -> float:
        if hasattr(self, 'finance'):
            return self.finance.balance
        return self._assets_buffer

    def _add_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to FinanceDepartment."""
        if hasattr(self, 'finance'):
            self.finance.credit(amount, "Settlement Transfer")
        else:
            self._assets_buffer += amount

    def _sub_assets(self, amount: float) -> None:
        """[PROTECTED] Delegate to FinanceDepartment."""
        if hasattr(self, 'finance'):
            self.finance.debit(amount, "Settlement Transfer")
        else:
            self._assets_buffer -= amount

    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
        par_value = self.assets / self.total_shares if self.total_shares > 0 else 1.0
        stock_market.update_shareholder(self.id, self.id, self.treasury_shares)
        self.logger.info(
            f"IPO | Firm {self.id} initialized IPO with {self.total_shares} shares. Par value: {par_value:.2f}",
            extra={"agent_id": self.id, "tags": ["ipo", "stock_market"]}
        )

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
            initial_liquidity_need=self.config_module.INITIAL_FIRM_LIQUIDITY_NEED,  # 초기 유동성 필요는 설정값으로 리셋
            specialization=self.specialization,
            productivity_factor=self.productivity_factor,
            decision_engine=cloned_decision_engine,
            value_orientation=self.value_orientation,
            config_module=self.config_module,
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
            "assets": self.assets,
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
        self, markets: Dict[str, Any], goods_data: list[Dict[str, Any]], market_data: Dict[str, Any], current_time: int, government: Optional[Any] = None, reflux_system: Optional[Any] = None, stress_scenario_config: Optional["StressScenarioConfig"] = None
    ) -> tuple[list[Order], Any]:
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_action"]}
        # SoC Refactor
        self.logger.debug(
            f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={self.assets:.2f}, Employees={len(self.hr.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "assets_before": self.assets,
                "num_employees_before": len(self.hr.employees),
                "is_active_before": self.is_active,
            },
        )
        config_dto = FirmConfigDTO(
            firm_min_production_target=self.config_module.FIRM_MIN_PRODUCTION_TARGET
        )
        state_dto = self.get_state_dto()

        context = DecisionContext(
            firm=self, # DEPRECATED
            state=state_dto,
            config=config_dto,
            markets=markets,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            government=government,
            reflux_system=reflux_system,
            stress_scenario_config=stress_scenario_config,
        )
        decisions, tactic = self.decision_engine.make_decisions(context)

        # WO-056: Shadow Mode Calculation
        self._calculate_invisible_hand_price(markets, current_time)

        # SoC Refactor
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={self.assets:.2f}, Employees={len(self.hr.employees)}, is_active={self.is_active}, Decisions={len(decisions)}",
            extra={
                **log_extra,
                "assets_after": self.assets,
                "num_employees_after": len(self.hr.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(decisions),
            },
        )
        return decisions, tactic

    def _calculate_invisible_hand_price(self, markets: Dict[str, Any], current_tick: int) -> None:
        """
        WO-056: Stage 1 Shadow Mode (Price Discovery 2.0).
        Calculates and logs the shadow price based on Excess Demand.
        """
        market = markets.get(self.specialization)
        # Check if market supports order book inspection
        if not market or not hasattr(market, 'get_all_bids'):
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
            details=f"Item={self.specialization}, D={demand:.1f}, S={supply:.1f}, Ratio={excess_demand_ratio:.2f}"
        )

    @override
    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, reflux_system: Optional[Any] = None, technology_manager: Optional[Any] = None) -> None:
        self.age += 1
        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_needs"]}
        # SoC Refactor
        self.logger.debug(
            f"FIRM_NEEDS_UPDATE_START | Firm {self.id} needs before update: Liquidity={self.needs['liquidity_need']:.1f}, Assets={self.assets:.2f}, Employees={len(self.hr.employees)}",
            extra={
                **log_extra,
                "needs_before": self.needs,
                "assets_before": self.assets,
                "num_employees_before": len(self.hr.employees),
            },
        )

        # --- Core Operations (SoC Refactor) ---
        # 1. Produce
        self.produce(current_time, technology_manager)

        # 2. Pay Wages & Holding Costs
        # WO-103 Phase 1: Delegated Holding Cost Calculation
        holding_cost = self.finance.calculate_and_debit_holding_costs()

        if holding_cost > 0:
            if reflux_system:
                reflux_system.capture(holding_cost, str(self.id), "fixed_cost")
            self.logger.info(
                f"Paid inventory holding cost: {holding_cost:.2f}",
                extra={**log_extra, "holding_cost": holding_cost},
            )

        total_wages = self.hr.process_payroll(current_time, government, market_data)
        if total_wages > 0:
            self.finance.record_expense(total_wages)
            self.logger.info(
                f"Paid total wages: {total_wages:.2f} to {len(self.hr.employees)} employees.",
                extra={**log_extra, "total_wages": total_wages},
            )

        # 3. Marketing & Brand Update
        marketing_spend = 0.0
        # SoC Refactor
        if self.assets > 100.0:
            marketing_spend = max(10.0, self.finance.revenue_this_turn * self.marketing_budget_rate)
        
        if self.assets < marketing_spend:
             marketing_spend = 0.0

        if marketing_spend > 0:
             # WO-103 Phase 1: Transactional method
             self.finance.debit(marketing_spend, "Marketing")
             self.finance.record_expense(marketing_spend)
             if reflux_system:
                 reflux_system.capture(marketing_spend, str(self.id), "marketing")

        self.marketing_budget = marketing_spend
        self.brand_manager.update(marketing_spend, self.productivity_factor / 10.0)
        self.sales.adjust_marketing_budget() # Note: Renamed from _adjust_marketing_budget

        # 4. Pay Taxes (after all other expenses)
        if government:
            self.finance.pay_maintenance(government, reflux_system, current_time)
            self.finance.pay_taxes(government, current_time)

        brand_premium = self.calculate_brand_premium(market_data) if market_data else 0.0
        self.logger.info(
            f"FIRM_BRAND_METRICS | Firm {self.id}: Awareness={self.brand_manager.brand_awareness:.4f}, "
            f"Quality={self.brand_manager.perceived_quality:.4f}, Premium={brand_premium:.2f}",
            extra={
                **log_extra,
                "brand_awareness": self.brand_manager.brand_awareness,
                "perceived_quality": self.brand_manager.perceived_quality,
                "brand_premium": brand_premium
            }
        )

        # --- Final State Updates & Checks ---
        self.needs["liquidity_need"] = min(100.0, self.needs["liquidity_need"] + self.config_module.LIQUIDITY_NEED_INCREASE_RATE)
        self.finance.check_bankruptcy()

        # SoC Refactor
        if self.assets <= self.config_module.ASSETS_CLOSURE_THRESHOLD or self.finance.consecutive_loss_turns >= self.config_module.FIRM_CLOSURE_TURNS_THRESHOLD:
            self.is_active = False
            self.logger.warning(
                f"FIRM_INACTIVE | Firm {self.id} closed down. Assets: {self.assets:.2f}, Consecutive Loss Turns: {self.finance.consecutive_loss_turns}",
                extra={
                    **log_extra,
                    "assets": self.assets,
                    "consecutive_loss_turns": self.finance.consecutive_loss_turns,
                    "tags": ["firm_closure"],
                },
            )

        self.logger.debug(
            f"FIRM_NEEDS_UPDATE_END | Firm {self.id} needs after update: Liquidity={self.needs['liquidity_need']:.1f}, Assets={self.assets:.2f}, Employees={len(self.hr.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "needs_after": self.needs,
                "assets_after": self.assets,
                "num_employees_after": len(self.hr.employees),
                "is_active_after": self.is_active,
                "brand_awareness": self.brand_manager.brand_awareness,
                "perceived_quality": self.brand_manager.perceived_quality
            },
        )

    # Legacy: _pay_maintenance and _pay_taxes removed as they are now in FinanceDepartment

    def distribute_profit(self, agents: Dict[int, Any], current_time: int) -> float:
        """
        Phase 14-1: Mandatory Dividend Rule.
        Distribute surplus cash to owner if reserves are met.
        """
        return self.finance.distribute_profit_private(agents, current_time)

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

    @property
    def current_profit(self) -> float:
        return self.finance.current_profit

    @current_profit.setter
    def current_profit(self, value: float) -> None:
        self.finance.current_profit = value

    @property
    def revenue_this_turn(self) -> float:
        return self.finance.revenue_this_turn

    @revenue_this_turn.setter
    def revenue_this_turn(self, value: float) -> None:
        self.finance.revenue_this_turn = value

    @property
    def expenses_this_tick(self) -> float:
        return self.finance.expenses_this_tick

    @expenses_this_tick.setter
    def expenses_this_tick(self, value: float) -> None:
        self.finance.expenses_this_tick = value

    @property
    def sales_volume_this_tick(self) -> float:
        return self.finance.sales_volume_this_tick

    @sales_volume_this_tick.setter
    def sales_volume_this_tick(self, value: float) -> None:
        self.finance.sales_volume_this_tick = value

    @property
    def last_sales_volume(self) -> float:
        return self.finance.last_sales_volume

    @last_sales_volume.setter
    def last_sales_volume(self, value: float) -> None:
        self.finance.last_sales_volume = value

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
