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
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine, AgentStateDTO
from dataclasses import replace

# Orchestrator-Engine Refactor
from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
from simulation.components.engines.hr_engine import HREngine
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.components.engines.production_engine import ProductionEngine
from simulation.components.engines.sales_engine import SalesEngine

from simulation.utils.shadow_logger import log_shadow
from modules.finance.api import InsufficientFundsError, IFinancialEntity
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO
from simulation.systems.api import ILearningAgent, LearningUpdateContext
from simulation.systems.tech.api import FirmTechInfoDTO

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.loan_market import LoanMarket
    from simulation.ai.firm_system2_planner import FirmSystem2Planner
    from simulation.markets.stock_market import StockMarket
    from simulation.agents.government import Government
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.memory.api import MemoryV2Interface
    from modules.finance.api import IShareholderRegistry

logger = logging.getLogger(__name__)

class Firm(BaseAgent, ILearningAgent, IFinancialEntity):
    """
    Firm Agent (Orchestrator).
    Manages state and delegates logic to stateless engines.
    """

    def __init__(
        self,
        core_config: AgentCoreConfigDTO,
        engine: IDecisionEngine,
        specialization: str,
        productivity_factor: float,
        config_dto: FirmConfigDTO,
        initial_inventory: Optional[Dict[str, float]] = None,
        loan_market: Optional[LoanMarket] = None,
        sector: str = "FOOD",
        personality: Optional[Personality] = None,
    ) -> None:
        super().__init__(core_config, engine)
        self.config = config_dto

        # State Initialization
        self.hr_state = HRState()
        self.finance_state = FinanceState()
        self.production_state = ProductionState()
        self.sales_state = SalesState()

        # Engine Initialization (Stateless)
        self.hr_engine = HREngine()
        self.finance_engine = FinanceEngine()
        self.production_engine = ProductionEngine()
        self.sales_engine = SalesEngine()

        # Initialize core attributes in State
        self.production_state.specialization = specialization
        self.production_state.sector = sector
        self.production_state.productivity_factor = productivity_factor
        self.production_state.production_target = self.config.firm_min_production_target

        self.finance_state.total_shares = self.config.ipo_initial_shares
        self.finance_state.treasury_shares = self.config.ipo_initial_shares # Initially all treasury
        self.finance_state.dividend_rate = self.config.dividend_rate

        self.sales_state.marketing_budget_rate = 0.05

        # Phase 16-B: Personality
        self.personality = personality or Personality.BALANCED

        # Inventory Initialization
        if initial_inventory is not None:
            for item_id, qty in initial_inventory.items():
                self.add_item(item_id, qty)

        # Brand Manager (Kept as component for now, or could be moved to SalesState/Engine)
        self.brand_manager = BrandManager(self.id, self.config, self.logger)
        
        # Loan Market
        self.decision_engine.loan_market = loan_market
        
        # Tracking variables
        self.age = 0

        # Legacy/Compatibility attributes (mapped to State where possible or kept if transient)
        # These properties route to State

    # --- Properties routing to State ---

    @property
    def specialization(self) -> str:
        return self.production_state.specialization

    @specialization.setter
    def specialization(self, value: str):
        self.production_state.specialization = value

    @property
    def productivity_factor(self) -> float:
        return self.production_state.productivity_factor

    @productivity_factor.setter
    def productivity_factor(self, value: float):
        self.production_state.productivity_factor = value

    @property
    def current_production(self) -> float:
        return self.production_state.current_production

    @current_production.setter
    def current_production(self, value: float):
        self.production_state.current_production = value

    @property
    def production_target(self) -> float:
        return self.production_state.production_target

    @production_target.setter
    def production_target(self, value: float):
        self.production_state.production_target = value

    @property
    def capital_stock(self) -> float:
        return self.production_state.capital_stock

    @capital_stock.setter
    def capital_stock(self, value: float):
        self.production_state.capital_stock = value

    @property
    def automation_level(self) -> float:
        return self.production_state.automation_level

    @automation_level.setter
    def automation_level(self, value: float):
        self.production_state.automation_level = value
        
    @property
    def is_bankrupt(self) -> bool:
        return self.finance_state.is_bankrupt
        
    @is_bankrupt.setter
    def is_bankrupt(self, value: bool):
        self.finance_state.is_bankrupt = value

    @property
    def valuation(self) -> float:
        return self.finance_state.valuation

    @valuation.setter
    def valuation(self, value: float):
        self.finance_state.valuation = value

    @property
    def total_shares(self) -> float:
        return self.finance_state.total_shares

    @total_shares.setter
    def total_shares(self, value: float):
        self.finance_state.total_shares = value

    @property
    def treasury_shares(self) -> float:
        return self.finance_state.treasury_shares

    @treasury_shares.setter
    def treasury_shares(self, value: float):
        self.finance_state.treasury_shares = value

    @property
    def dividend_rate(self) -> float:
        return self.finance_state.dividend_rate

    @dividend_rate.setter
    def dividend_rate(self, value: float):
        self.finance_state.dividend_rate = value

    @property
    def marketing_budget(self) -> float:
        return self.sales_state.marketing_budget

    @marketing_budget.setter
    def marketing_budget(self, value: float):
        self.sales_state.marketing_budget = value

    @property
    def last_prices(self) -> Dict[str, float]:
        return self.sales_state.last_prices

    @property
    def research_history(self) -> Dict[str, Any]:
        return self.production_state.research_history

    @property
    def inventory_quality(self) -> Dict[str, float]:
        return self.production_state.inventory_quality

    @property
    def input_inventory(self) -> Dict[str, float]:
        return self.production_state.input_inventory

    @property
    def base_quality(self) -> float:
        return self.production_state.base_quality

    @base_quality.setter
    def base_quality(self, value: float):
        self.production_state.base_quality = value

    @property
    def sector(self) -> str:
        return self.production_state.sector

    @property
    def has_bailout_loan(self) -> bool:
        return self.finance_state.has_bailout_loan

    @has_bailout_loan.setter
    def has_bailout_loan(self, value: bool):
        self.finance_state.has_bailout_loan = value

    @property
    def inventory_last_sale_tick(self) -> Dict[str, int]:
        return self.sales_state.inventory_last_sale_tick

    # --- Methods ---

    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
        usd_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
        par_value = usd_balance / self.total_shares if self.total_shares > 0 else 1.0
        stock_market.update_shareholder(self.id, self.id, self.treasury_shares)
        self.logger.info(
            f"IPO | Firm {self.id} initialized IPO with {self.total_shares} shares. Par value: {par_value:.2f}",
            extra={"agent_id": self.id, "tags": ["ipo", "stock_market"]}
        )

    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None:
        self.sales_state.inventory_last_sale_tick[item_id] = current_tick

    def liquidate_assets(self, current_tick: int = -1) -> Dict[CurrencyCode, float]:
        """Liquidate assets using Protocol Purity."""
        # 1. Write off Inventory
        for item_id in list(self._inventory.keys()):
            self.remove_item(item_id, self.get_quantity(item_id))
        
        # 2. Write off Capital Stock
        self.capital_stock = 0.0
        
        # 3. Write off Automation
        self.automation_level = 0.0

        self.is_bankrupt = True

        assets_to_return = self.wallet.get_all_balances().copy()

        if self.memory_v2:
            from modules.memory.V2.dtos import MemoryRecordDTO
            record = MemoryRecordDTO(
                tick=current_tick,
                agent_id=self.id,
                event_type="BANKRUPTCY",
                data={"assets_returned": assets_to_return}
            )
            self.memory_v2.add_record(record)

        return assets_to_return

    # --- IInventoryHandler Overrides ---

    @override
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0) -> bool:
        self._add_inventory_internal(item_id, quantity, quality)
        return True

    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None) -> bool:
        if quantity < 0: return False
        current = self._inventory.get(item_id, 0.0)
        if current < quantity: return False
        self._inventory[item_id] = current - quantity
        if self._inventory[item_id] <= 1e-9:
             del self._inventory[item_id]
        return True

    @override
    def get_quantity(self, item_id: str) -> float:
        return self._inventory.get(item_id, 0.0)

    @override
    def get_quality(self, item_id: str) -> float:
        return self.inventory_quality.get(item_id, 1.0)

    def _add_inventory_internal(self, item_id: str, quantity: float, quality: float):
        current_inventory = self._inventory.get(item_id, 0)
        current_quality = self.inventory_quality.get(item_id, 1.0)

        total_qty = current_inventory + quantity
        if total_qty > 0:
            new_avg_quality = ((current_inventory * current_quality) + (quantity * quality)) / total_qty
            self.inventory_quality[item_id] = new_avg_quality

        self._inventory[item_id] = total_qty

    def post_ask(self, item_id: str, price: float, quantity: float, market: OrderBookMarket, current_tick: int) -> Order:
        return self.sales_engine.post_ask(
            self.sales_state, self.id, item_id, price, quantity, market, current_tick, self.get_quantity(item_id)
        )

    def calculate_brand_premium(self, market_data: Dict[str, Any]) -> float:
        item_id = self.specialization
        market_avg_key = f"{item_id}_avg_traded_price"
        market_avg_price = market_data.get("goods_market", {}).get(market_avg_key, 0.0)
        my_price = self.last_prices.get(item_id, market_avg_price)
        return my_price - market_avg_price if market_avg_price > 0 else 0.0

    def _adjust_marketing_budget(self, market_context: MarketContextDTO = None) -> None:
        if market_context is None:
            market_context = {"exchange_rates": {DEFAULT_CURRENCY: 1.0}, "benchmark_rates": {}}

        # Calculate primary revenue for budget adjustment
        exchange_rates = market_context['exchange_rates']
        total_revenue = 0.0
        for cur, amount in self.finance_state.revenue_this_turn.items():
             rate = exchange_rates.get(cur, 1.0) if cur != DEFAULT_CURRENCY else 1.0
             total_revenue += amount * rate

        self.sales_engine.adjust_marketing_budget(self.sales_state, market_context, total_revenue)

    def produce(self, current_time: int, technology_manager: Optional[Any] = None) -> None:
        self.current_production = self.production_engine.produce(
            self.production_state,
            self, # IInventoryHandler
            self.hr_state,
            self.config,
            current_time,
            self.id,
            technology_manager
        )

    @override
    def clone(self, new_id: int, initial_assets_from_parent: float, current_tick: int) -> "Firm":
        cloned_decision_engine = copy.deepcopy(self.decision_engine)

        new_core_config = replace(self.get_core_config(), id=new_id, name=f"Firm_{new_id}")

        new_firm = Firm(
            core_config=new_core_config,
            engine=cloned_decision_engine,
            specialization=self.specialization,
            productivity_factor=self.productivity_factor,
            config_dto=self.config,
            initial_inventory=copy.deepcopy(self._inventory),
            loan_market=self.decision_engine.loan_market,
            personality=self.personality
        )

        # Hydrate State
        initial_state = AgentStateDTO(
            assets={DEFAULT_CURRENCY: initial_assets_from_parent},
            inventory=copy.deepcopy(self._inventory),
            is_active=True
        )
        new_firm.load_state(initial_state)

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
        """AI Data Provider."""
        return {
            "assets": MultiCurrencyWalletDTO(balances=self.wallet.get_all_balances()),
            "needs": self.needs.copy(),
            "inventory": self._inventory.copy(),
            "input_inventory": self.input_inventory.copy(),
            "employees": [emp.id for emp in self.hr_state.employees],
            "is_active": self.is_active,
            "current_production": self.current_production,
            "productivity_factor": self.productivity_factor,
            "production_target": self.production_target,
            "revenue_this_turn": self.finance_state.revenue_this_turn,
            "expenses_this_tick": self.finance_state.expenses_this_tick,
            "consecutive_loss_turns": self.finance_state.consecutive_loss_turns,
            "total_shares": self.total_shares,
            "treasury_shares": self.treasury_shares,
            "dividend_rate": self.dividend_rate,
            "capital_stock": self.capital_stock,
            "base_quality": self.base_quality,
            "inventory_quality": self.inventory_quality.copy(),
            "automation_level": self.automation_level,
        }

    def get_state_dto(self) -> FirmStateDTO:
        return FirmStateDTO.from_firm(self)

    def get_pre_state_data(self) -> Dict[str, Any]:
        return getattr(self, "pre_state_snapshot", self.get_agent_data())

    def get_tech_info(self) -> FirmTechInfoDTO:
        return {
            "id": self.id,
            "sector": self.sector,
            "current_rd_investment": self.production_state.research_history.get("total_spent", 0.0)
        }

    @override
    def make_decision(
        self, input_dto: DecisionInputDTO
    ) -> tuple[list[Order], Any]:
        # ... Decision Logic ...
        goods_data = input_dto.goods_data
        market_data = input_dto.market_data
        current_time = input_dto.current_time
        fiscal_context = input_dto.fiscal_context
        stress_scenario_config = input_dto.stress_scenario_config
        market_snapshot = input_dto.market_snapshot
        government_policy = input_dto.government_policy
        agent_registry = input_dto.agent_registry or {}
        market_context = input_dto.market_context

        log_extra = {"tick": current_time, "agent_id": self.id, "tags": ["firm_action"]}
        current_assets_val = self.wallet.get_balance(DEFAULT_CURRENCY)
        self.logger.debug(
            f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={current_assets_val:.2f}, Employees={len(self.hr_state.employees)}, is_active={self.is_active}",
            extra={
                **log_extra,
                "assets_before": self.wallet.get_all_balances(),
                "num_employees_before": len(self.hr_state.employees),
                "is_active_before": self.is_active,
            },
        )

        state_dto = self.get_state_dto()

        context = DecisionContext(
            state=state_dto,
            config=self.config,
            goods_data=goods_data,
            market_data=market_data,
            current_time=current_time,
            stress_scenario_config=stress_scenario_config,
            market_snapshot=market_snapshot,
            government_policy=government_policy,
            agent_registry=agent_registry or {},
            market_context=market_context
        )
        decision_output = self.decision_engine.make_decisions(context)
        
        if hasattr(decision_output, "orders"):
            decisions = decision_output.orders
            tactic = decision_output.metadata
        else:
            decisions, tactic = decision_output

        # Command Bus execution
        external_orders = []
        for order in decisions:
            if order.market_id == "internal":
                gov_proxy = fiscal_context.government if fiscal_context else None
                self._execute_internal_order(order, gov_proxy, current_time)
            else:
                external_orders.append(order)

        self.sales_engine.check_and_apply_dynamic_pricing(self.sales_state, external_orders, current_time)

        if market_snapshot:
             self._calculate_invisible_hand_price(market_snapshot, current_time)

        current_assets_val_after = self.wallet.get_balance(DEFAULT_CURRENCY)
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={current_assets_val_after:.2f}, Employees={len(self.hr_state.employees)}, is_active={self.is_active}, Decisions={len(external_orders)}",
            extra={
                **log_extra,
                "assets_after": self.wallet.get_all_balances(),
                "num_employees_after": len(self.hr_state.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(external_orders),
            },
        )
        return external_orders, tactic

    def _execute_internal_order(self, order: Order, government: Optional[Any], current_time: int) -> None:
        """
        Command Bus: Routes internal orders to the correct engine.
        """
        def get_amount(o: Order) -> float:
            return o.monetary_amount['amount'] if o.monetary_amount else o.quantity

        def get_currency(o: Order) -> CurrencyCode:
             return o.monetary_amount['currency'] if o.monetary_amount else DEFAULT_CURRENCY

        if order.order_type == "SET_TARGET":
            self.production_state.production_target = order.quantity
            self.logger.info(f"INTERNAL_EXEC | Firm {self.id} set production target to {order.quantity:.1f}")

        elif order.order_type == "INVEST_AUTOMATION":
            amount = get_amount(order)
            if self.finance_engine.invest_in_automation(self.finance_state, self, self.wallet, amount, government, self.settlement_system):
                 gained = self.production_engine.invest_in_automation(
                     self.production_state, amount, self.config.automation_cost_per_pct
                 )
                 self.logger.info(f"INTERNAL_EXEC | Firm {self.id} invested {amount:.1f} in automation (+{gained:.4f}).")

        elif order.order_type == "PAY_TAX":
            amount = get_amount(order)
            currency = get_currency(order)
            reason = order.item_id
            # Use engine for consistency
            self.finance_engine.pay_ad_hoc_tax(
                self.finance_state, self, self.wallet, amount, currency, reason, government, self.settlement_system, current_time
            )

        elif order.order_type == "INVEST_RD":
            amount = get_amount(order)
            if self.finance_engine.invest_in_rd(self.finance_state, self, self.wallet, amount, government, self.settlement_system):
                revenue = self.finance_state.last_revenue
                if self.production_engine.execute_rd_outcome(self.production_state, self.hr_state, revenue, amount, current_time):
                    self.logger.info(f"INTERNAL_EXEC | Firm {self.id} R&D SUCCESS (Budget: {amount:.1f})")

        elif order.order_type == "INVEST_CAPEX":
            amount = get_amount(order)
            if self.finance_engine.invest_in_capex(self.finance_state, self, self.wallet, amount, government, self.settlement_system):
                self.production_engine.invest_in_capex(self.production_state, amount, self.config.capital_to_output_ratio)
                self.logger.info(f"INTERNAL_EXEC | Firm {self.id} invested {amount:.1f} in CAPEX.")

        elif order.order_type == "SET_DIVIDEND":
            self.finance_state.dividend_rate = order.quantity

        elif order.order_type == "SET_PRICE":
            # Just logs logic, actual pricing happens in post_ask
            pass

        elif order.order_type == "FIRE":
            self.hr_engine.fire_employee(
                self.hr_state, self.id, self, self.wallet, self.settlement_system, order.target_agent_id, order.price
            )

    def _calculate_invisible_hand_price(self, market_snapshot: MarketSnapshotDTO, current_tick: int) -> None:
        if not market_snapshot.market_signals: return
        signal = market_snapshot.market_signals.get(self.specialization)
        if not signal: return
        demand = signal.total_bid_quantity
        supply = signal.total_ask_quantity
        if supply > 0:
            excess_demand_ratio = (demand - supply) / supply
        else:
            excess_demand_ratio = 1.0 if demand > 0 else 0.0

        sensitivity = self.config.invisible_hand_sensitivity
        current_price = self.last_prices.get(self.specialization, 10.0)
        candidate_price = current_price * (1.0 + (sensitivity * excess_demand_ratio))
        shadow_price = (candidate_price * 0.2) + (current_price * 0.8)

        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Firm",
            metric="shadow_price",
            current_value=current_price,
            shadow_value=shadow_price,
            details=f"Item={self.specialization}, D={demand:.1f}, S={supply:.1f}, Ratio={excess_demand_ratio:.2f}"
        )

    def generate_transactions(self, government: Optional[Any], market_data: Dict[str, Any], shareholder_registry: IShareholderRegistry, current_time: int, market_context: MarketContextDTO) -> List[Transaction]:
        transactions = []

        # 1. Payroll
        tx_payroll = self.hr_engine.process_payroll(
            self.hr_state, self.id, self.wallet, self.config, current_time, government, market_data, market_context
        )
        transactions.extend(tx_payroll)

        # 2. Finance
        # Calculate inventory value for holding cost
        inventory_value = 0.0
        for item, qty in self._inventory.items():
            price = self.last_prices.get(item, 10.0)
            inventory_value += qty * price

        tx_finance = self.finance_engine.generate_financial_transactions(
            self.finance_state, self.id, self.wallet, self.config, government, shareholder_registry, current_time, market_context, inventory_value
        )
        transactions.extend(tx_finance)

        # 3. Marketing
        tx_marketing = self.sales_engine.generate_marketing_transaction(
            self.sales_state, self.id, self.wallet.get_balance(DEFAULT_CURRENCY), government, current_time
        )
        if tx_marketing:
            transactions.append(tx_marketing)

        # Brand Update
        self.brand_manager.update(self.sales_state.marketing_budget, self.productivity_factor / 10.0)
        self.sales_engine.adjust_marketing_budget(self.sales_state, market_context, self.finance_state.last_revenue)

        # Finance cleanup for next tick
        self.finance_state.reset_tick_counters(DEFAULT_CURRENCY)

        return transactions

    @override
    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, technology_manager: Optional[Any] = None) -> None:
        pass

    # --- IFinancialEntity Implementation ---
    # These are handled by BaseAgent and wallet, but we expose properties for convenience or protocol satisfaction

    @property
    @override
    def assets(self) -> float:
        return self.wallet.get_balance(DEFAULT_CURRENCY)

    @override
    def deposit(self, amount: float) -> None:
         self.wallet.add(amount, DEFAULT_CURRENCY)

    @override
    def withdraw(self, amount: float) -> None:
         current_bal = self.wallet.get_balance(DEFAULT_CURRENCY)
         if current_bal < amount:
            raise InsufficientFundsError(
                f"Insufficient funds", required=MoneyDTO(amount=amount, currency=DEFAULT_CURRENCY), available=MoneyDTO(amount=current_bal, currency=DEFAULT_CURRENCY)
            )
         self.wallet.subtract(amount, DEFAULT_CURRENCY)

    # --- Facade Methods ---

    def get_book_value_per_share(self) -> float:
        outstanding = self.total_shares - self.treasury_shares
        if outstanding <= 0: return 0.0
        net_assets = self.wallet.get_balance(DEFAULT_CURRENCY) - self.finance_state.total_debt
        return max(0.0, net_assets) / outstanding

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        if stock_price is None:
            stock_price = self.get_book_value_per_share()
        return (self.total_shares - self.treasury_shares) * stock_price

    def calculate_valuation(self, market_context: MarketContextDTO = None) -> float:
        inventory_value = sum(self.get_quantity(i) * self.last_prices.get(i, 10.0) for i in self._inventory)
        return self.finance_engine.calculate_valuation(
            self.finance_state, self.wallet, self.config, inventory_value, market_context
        )

    def get_financial_snapshot(self) -> Dict[str, Any]:
        inventory_value = sum(self.get_quantity(i) * self.last_prices.get(i, 10.0) for i in self._inventory)
        total_assets = self.wallet.get_balance(DEFAULT_CURRENCY) + inventory_value + self.capital_stock
        return {
             "wallet": MultiCurrencyWalletDTO(balances=self.wallet.get_all_balances()),
             "total_assets": total_assets,
             "total_debt": self.finance_state.total_debt,
             "retained_earnings": self.finance_state.retained_earnings,
             "average_profit": sum(self.finance_state.profit_history)/len(self.finance_state.profit_history) if self.finance_state.profit_history else 0.0
        }

    def update_learning(self, context: LearningUpdateContext) -> None:
        reward = context["reward"]
        next_agent_data = context["next_agent_data"]
        next_market_data = context["next_market_data"]
        if hasattr(self.decision_engine, 'ai_engine'):
            self.decision_engine.ai_engine.update_learning_v2(
                reward=reward,
                next_agent_data=next_agent_data,
                next_market_data=next_market_data,
            )

    # Compatibility methods for other agents/tests
    # e.g., hr property exposing employees if accessed directly?
    # No, we removed self.hr. Any code accessing firm.hr.employees will break.
    # We should add a property if needed, or fix call sites.
    # The user instruction was "Rewriting Firm tests". This implies we accept breaking changes.
    # However, other agents (like Government) might access firm internal structure?
    # No, usually they access via public API.
    # HRDepartment was "SoC Refactor" previously.

    @property
    def hr(self):
        # Backward compatibility proxy
        class HRProxy:
            def __init__(self, firm):
                self.firm = firm
            @property
            def employees(self):
                return self.firm.hr_state.employees
            @employees.setter
            def employees(self, value):
                self.firm.hr_state.employees = value
            def get_total_labor_skill(self):
                return self.firm.hr_engine.get_total_labor_skill(self.firm.hr_state)
            def get_avg_skill(self):
                 return self.firm.hr_engine.get_avg_skill(self.firm.hr_state)
            @property
            def employee_wages(self):
                return self.firm.hr_state.employee_wages
        return HRProxy(self)

    @property
    def finance(self):
        # Backward compatibility proxy
        class FinanceProxy:
            def __init__(self, firm):
                self.firm = firm
            @property
            def balance(self):
                return self.firm.wallet.get_all_balances()
            def get_balance(self, cur):
                return self.firm.wallet.get_balance(cur)
            @property
            def revenue_this_turn(self):
                return self.firm.finance_state.revenue_this_turn
            @property
            def expenses_this_tick(self):
                return self.firm.finance_state.expenses_this_tick
            @property
            def consecutive_loss_turns(self):
                return self.firm.finance_state.consecutive_loss_turns
            @property
            def profit_history(self):
                 return self.firm.finance_state.profit_history
            def get_book_value_per_share(self):
                return {'amount': self.firm.get_book_value_per_share()}
            def get_market_cap(self, p):
                return self.firm.get_market_cap(p)
            def calculate_valuation(self, ctx):
                return {'amount': self.firm.calculate_valuation(ctx)}
            def get_financial_snapshot(self):
                return self.firm.get_financial_snapshot()

            def check_bankruptcy(self):
                return self.firm.finance_engine.check_bankruptcy(self.firm.finance_state, self.firm.config)

            def check_cash_crunch(self):
                return False

            def get_inventory_value(self):
                return 0.0

            def trigger_emergency_liquidation(self):
                return []

            def record_revenue(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY):
                self.firm.finance_state.revenue_this_turn[currency] += amount

            def record_expense(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY):
                self.firm.finance_state.expenses_this_tick[currency] += amount

            def __getattr__(self, name):
                return getattr(self.firm.finance_state, name)

        return FinanceProxy(self)
