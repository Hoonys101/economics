from __future__ import annotations
from collections import deque
from typing import List, Dict, Any, Optional, override, TYPE_CHECKING, Tuple
import logging
import copy
import math

from simulation.models import Order, Transaction
from simulation.core_agents import Household
from simulation.markets.order_book_market import OrderBookMarket
from simulation.decisions.base_decision_engine import BaseDecisionEngine
from simulation.dtos import DecisionContext, FiscalContext, DecisionInputDTO
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.dtos.firm_state_dto import FirmStateDTO, IFirmStateProvider
from simulation.dtos.department_dtos import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from simulation.ai.enums import Personality
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO, ICurrencyHolder
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine, AgentStateDTO, IOrchestratorAgent, IInventoryHandler, ISensoryDataProvider, AgentSensorySnapshotDTO, IConfigurable, LiquidationConfigDTO, InventorySlot, ItemDTO, InventorySlotDTO
from dataclasses import replace

# Orchestrator-Engine Refactor
from simulation.components.state.firm_state_models import HRState, FinanceState, ProductionState, SalesState
from simulation.components.engines.hr_engine import HREngine
from simulation.components.engines.finance_engine import FinanceEngine
from simulation.components.engines.production_engine import ProductionEngine
from simulation.components.engines.sales_engine import SalesEngine
from simulation.components.engines.asset_management_engine import AssetManagementEngine
from simulation.components.engines.rd_engine import RDEngine
from modules.firm.engines.brand_engine import BrandEngine
from simulation.components.engines.real_estate_component import RealEstateUtilizationComponent

from simulation.dtos.context_dtos import PayrollProcessingContext, FinancialTransactionContext, SalesContext
from simulation.dtos.hr_dtos import HRPayrollContextDTO, TaxPolicyDTO
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO

# New API Imports
from modules.firm.api import (
    FirmSnapshotDTO,
    ProductionInputDTO, ProductionResultDTO,
    AssetManagementInputDTO, AssetManagementResultDTO,
    RDInputDTO, RDResultDTO,
    IProductionEngine, IAssetManagementEngine, IRDEngine
)

from simulation.utils.shadow_logger import log_shadow
from modules.finance.api import InsufficientFundsError, IFinancialAgent, ICreditFrozen, ILiquidatable, LiquidationContext, EquityStake
from modules.common.interfaces import IPropertyOwner
from modules.common.dtos import Claim
from modules.finance.dtos import MoneyDTO, MultiCurrencyWalletDTO
from modules.finance.wallet.wallet import Wallet
from modules.inventory.manager import InventoryManager
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

class Firm(ILearningAgent, IFinancialAgent, ILiquidatable, IOrchestratorAgent, ICreditFrozen, IInventoryHandler, ICurrencyHolder, ISensoryDataProvider, IConfigurable, IPropertyOwner, IFirmStateProvider):
    """
    Firm Agent (Orchestrator).
    Manages state and delegates logic to stateless engines.
    Refactored to Composition (No BaseAgent).
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
        # Composition: Initialize Core Attributes manually (No BaseAgent)
        self._core_config = core_config
        self.decision_engine = engine
        self.id = core_config.id
        self.name = core_config.name
        self.logger = core_config.logger
        self.memory_v2 = core_config.memory_interface
        self.value_orientation = core_config.value_orientation
        self.needs = core_config.initial_needs.copy()

        # ICreditFrozen
        self._credit_frozen_until_tick = 0

        # Wallet & Inventory
        self._wallet = Wallet(self.id, {})
        self._inventory: Dict[str, float] = {} # Direct dict for IInventoryHandler
        self._input_inventory: Dict[str, float] = {} # New INPUT inventory
        self._input_inventory_quality: Dict[str, float] = {}

        self.is_active = True

        self.config = config_dto

        # State Initialization
        self.hr_state = HRState()
        self.finance_state = FinanceState()
        self.production_state = ProductionState()
        self.sales_state = SalesState()

        # Engine Initialization (Stateless)
        self.hr_engine = HREngine()
        self.finance_engine = FinanceEngine()
        self.production_engine: IProductionEngine = ProductionEngine()
        self.sales_engine = SalesEngine()
        self.asset_management_engine: IAssetManagementEngine = AssetManagementEngine()
        self.rd_engine: IRDEngine = RDEngine()
        self.brand_engine = BrandEngine()

        # Initialize core attributes in State
        self.production_state.specialization = specialization
        self.production_state.sector = sector
        self.production_state.productivity_factor = productivity_factor
        self.production_state.production_target = self.config.firm_min_production_target

        self.finance_state.total_shares = self.config.ipo_initial_shares
        self.finance_state.treasury_shares = self.config.ipo_initial_shares # Initially all treasury
        self.finance_state.dividend_rate = self.config.dividend_rate
        self.finance_state.profit_history = deque(maxlen=self.config.profit_history_ticks)

        self.sales_state.marketing_budget_rate = 0.05

        # Phase 16-B: Personality
        self.personality = personality or Personality.BALANCED

        # Inventory Initialization
        if initial_inventory is not None:
            for item_id, qty in initial_inventory.items():
                self.add_item(item_id, qty)

        # TD-271: Real Estate Utilization
        self.real_estate_utilization_component = RealEstateUtilizationComponent()

        # Loan Market
        self.decision_engine.loan_market = loan_market
        
        # Tracking variables
        self.age = 0

    # --- IConfigurable Implementation ---

    def get_liquidation_config(self) -> LiquidationConfigDTO:
        """
        Implements IConfigurable.get_liquidation_config.
        Extracts liquidation parameters from the internal config DTO.
        """
        initial_prices = {}
        if self.config.goods and isinstance(self.config.goods, dict):
             for k, v in self.config.goods.items():
                 if isinstance(v, dict) and "initial_price" in v:
                     initial_prices[k] = v["initial_price"]

        return LiquidationConfigDTO(
            haircut=self.config.fire_sale_discount,
            initial_prices=initial_prices,
            default_price=10.0,
            market_prices=self.last_prices.copy()
        )

    # --- IOrchestratorAgent Implementation ---

    def get_core_config(self) -> AgentCoreConfigDTO:
        return self._core_config

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        return {
            "is_active": self.is_active,
            "approval_rating": 0.0,
            "total_wealth": self.wallet.get_balance(DEFAULT_CURRENCY) # Returns int pennies
        }

    def get_current_state(self) -> AgentStateDTO:
        # Convert inventories to DTOs
        main_items = [
            ItemDTO(name=k, quantity=v, quality=self.get_quality(k, InventorySlot.MAIN))
            for k, v in self._inventory.items()
        ]
        input_items = [
            ItemDTO(name=k, quantity=v, quality=self.get_quality(k, InventorySlot.INPUT))
            for k, v in self._input_inventory.items()
        ]

        inventories = {
            InventorySlot.MAIN.name: InventorySlotDTO(items=main_items),
            InventorySlot.INPUT.name: InventorySlotDTO(items=input_items)
        }

        return AgentStateDTO(
            assets=self._wallet.get_all_balances(),
            is_active=self.is_active,
            inventories=inventories,
            inventory=None
        )

    def load_state(self, state: AgentStateDTO) -> None:
        if state.assets and any(v > 0 for v in state.assets.values()):
             self.logger.warning(f"Agent {self.id}: load_state called with assets, but direct loading is disabled for integrity. Assets ignored: {state.assets}")

        self._inventory.clear()
        self.inventory_quality.clear()
        self._input_inventory.clear()
        self._input_inventory_quality.clear()
        self.is_active = state.is_active

        # Restore from inventories
        if state.inventories:
            for slot_name, slot_dto in state.inventories.items():
                slot = InventorySlot[slot_name] if slot_name in InventorySlot.__members__ else None
                if slot == InventorySlot.MAIN:
                    target_inv = self._inventory
                    target_qual = self.inventory_quality
                elif slot == InventorySlot.INPUT:
                    target_inv = self._input_inventory
                    target_qual = self._input_inventory_quality
                else:
                    self.logger.warning(f"Unknown inventory slot in load_state: {slot_name}")
                    continue

                for item in slot_dto.items:
                    target_inv[item.name] = item.quantity
                    target_qual[item.name] = item.quality

        # Fallback for legacy state
        elif state.inventory:
             self._inventory.update(state.inventory)

    @property
    def wallet(self) -> Wallet:
        return self._wallet

    # --- ICreditFrozen Implementation ---

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value

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
    def valuation(self) -> int:
        return self.finance_state.valuation_pennies

    @valuation.setter
    def valuation(self, value: int):
        self.finance_state.valuation_pennies = value

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
        return float(self.sales_state.marketing_budget_pennies) # Adapter

    @marketing_budget.setter
    def marketing_budget(self, value: float):
        self.sales_state.marketing_budget_pennies = int(value) # Adapter

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
        """Facade property for backward compatibility during transition."""
        return self.get_all_items(slot=InventorySlot.INPUT)

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
    def total_debt(self) -> int:
        return self.finance_state.total_debt_pennies

    @total_debt.setter
    def total_debt(self, value: int):
        self.finance_state.total_debt_pennies = value

    @property
    def inventory_last_sale_tick(self) -> Dict[str, int]:
        return self.sales_state.inventory_last_sale_tick

    @property
    def prev_awareness(self) -> float:
        return self.sales_state.prev_awareness

    @prev_awareness.setter
    def prev_awareness(self, value: float):
        self.sales_state.prev_awareness = value

    @property
    def prev_avg_quality(self) -> float:
        return self.sales_state.prev_avg_quality

    @prev_avg_quality.setter
    def prev_avg_quality(self, value: float):
        self.sales_state.prev_avg_quality = value

    @property
    def last_revenue(self) -> int:
        return self.finance_state.last_revenue_pennies

    @property
    def revenue_this_turn(self) -> Dict[CurrencyCode, int]:
        return self.finance_state.revenue_this_turn

    @property
    def expenses_this_tick(self) -> Dict[CurrencyCode, int]:
        return self.finance_state.expenses_this_tick

    @property
    def cost_this_turn(self) -> Dict[CurrencyCode, int]:
        return self.finance_state.cost_this_turn

    # --- Methods ---

    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
        usd_balance = self.wallet.get_balance(DEFAULT_CURRENCY)
        par_value = float(usd_balance) / self.total_shares if self.total_shares > 0 else 1.0
        stock_market.update_shareholder(self.id, self.id, self.treasury_shares)
        self.logger.info(
            f"IPO | Firm {self.id} initialized IPO with {self.total_shares} shares. Par value: {par_value:.2f}",
            extra={"agent_id": self.id, "tags": ["ipo", "stock_market"]}
        )

    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None:
        self.sales_state.inventory_last_sale_tick[item_id] = current_tick

    def record_revenue(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Records revenue for the current turn.
        Required by GoodsTransactionHandler.
        """
        if currency not in self.finance_state.revenue_this_turn:
            self.finance_state.revenue_this_turn[currency] = 0
            self.finance_state.current_profit[currency] = 0 # Initialize if missing

        self.finance_state.revenue_this_turn[currency] += amount
        if currency not in self.finance_state.current_profit:
             self.finance_state.current_profit[currency] = 0
        self.finance_state.current_profit[currency] += amount

    def record_expense(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Records expense for the current tick.
        Required by GoodsTransactionHandler.
        """
        self.finance_engine.record_expense(self.finance_state, amount, currency)

    def get_all_claims(self, ctx: LiquidationContext) -> List[Claim]:
        """
        Implements ILiquidatable.get_all_claims.
        Delegates to specialized helpers to gather all claims.
        """
        all_claims: List[Claim] = []

        # 1. Get HR Claims (Tier 1)
        if ctx.hr_service:
            employee_claims = ctx.hr_service.calculate_liquidation_employee_claims(self, ctx.current_tick)
            all_claims.extend(employee_claims)

        # 2. Get Tax Claims (Tier 3)
        if ctx.tax_service:
            tax_claims = ctx.tax_service.calculate_liquidation_tax_claims(self)
            all_claims.extend(tax_claims)

        # 3. Get Secured Debt Claims (Tier 2)
        # Abstracts away knowledge of LoanMarket
        total_debt = self.finance_state.total_debt_pennies
        bank_agent_id = "BANK_UNKNOWN" # Default
        if self.decision_engine.loan_market and self.decision_engine.loan_market.bank:
            bank_agent_id = self.decision_engine.loan_market.bank.id

        if total_debt > 0:
            all_claims.append(Claim(
                creditor_id=bank_agent_id,
                amount=total_debt,
                tier=2,
                description="Secured Loan"
            ))

        return all_claims

    def get_equity_stakes(self, ctx: LiquidationContext) -> List[EquityStake]:
        """
        Implements ILiquidatable.get_equity_stakes.
        Uses the Shareholder Registry to get ownership data.
        """
        if not ctx.shareholder_registry:
            return []

        shareholders = ctx.shareholder_registry.get_shareholders_of_firm(self.id)
        outstanding_shares = self.total_shares - self.treasury_shares

        if outstanding_shares <= 0:
            return []

        return [
            EquityStake(shareholder_id=sh['agent_id'], ratio=sh['quantity'] / outstanding_shares)
            for sh in shareholders
        ]

    def liquidate_assets(self, current_tick: int = -1) -> Dict[CurrencyCode, int]:
        """Liquidate assets using Protocol Purity."""
        # 1. Write off Inventory
        for item_id in list(self.get_all_items(slot=InventorySlot.MAIN).keys()):
            self.remove_item(item_id, self.get_quantity(item_id, slot=InventorySlot.MAIN), slot=InventorySlot.MAIN)
        for item_id in list(self.get_all_items(slot=InventorySlot.INPUT).keys()):
            self.remove_item(item_id, self.get_quantity(item_id, slot=InventorySlot.INPUT), slot=InventorySlot.INPUT)
        
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
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        self._add_inventory_internal(item_id, quantity, quality, slot)
        return True

    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        if quantity < 0: return False

        if slot == InventorySlot.MAIN:
            inventory = self._inventory
        elif slot == InventorySlot.INPUT:
            inventory = self._input_inventory
        else:
            return False

        current = inventory.get(item_id, 0.0)
        if current < quantity: return False
        inventory[item_id] = current - quantity
        if inventory[item_id] <= 1e-9:
             del inventory[item_id]
        return True

    @override
    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot == InventorySlot.MAIN:
            return self._inventory.get(item_id, 0.0)
        elif slot == InventorySlot.INPUT:
            return self._input_inventory.get(item_id, 0.0)
        return 0.0

    @override
    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        if slot == InventorySlot.MAIN:
            return self.inventory_quality.get(item_id, 1.0)
        elif slot == InventorySlot.INPUT:
            return self._input_inventory_quality.get(item_id, 1.0)
        return 1.0

    @override
    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        """Returns a copy of the inventory."""
        if slot == InventorySlot.MAIN:
            return self._inventory.copy()
        elif slot == InventorySlot.INPUT:
            return self._input_inventory.copy()
        return {}

    @override
    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        """Clears the inventory."""
        if slot == InventorySlot.MAIN:
            self._inventory.clear()
            self.inventory_quality.clear()
        elif slot == InventorySlot.INPUT:
            self._input_inventory.clear()
            self._input_inventory_quality.clear()

    def _add_inventory_internal(self, item_id: str, quantity: float, quality: float, slot: InventorySlot):
        current_inventory = self.get_quantity(item_id, slot)
        current_quality = self.get_quality(item_id, slot)

        total_qty = current_inventory + quantity

        if slot == InventorySlot.MAIN:
            quality_ref = self.inventory_quality
            inventory_ref = self._inventory
        else:
            quality_ref = self._input_inventory_quality
            inventory_ref = self._input_inventory

        if total_qty > 0:
            new_avg_quality = ((current_inventory * current_quality) + (quantity * quality)) / total_qty
            quality_ref[item_id] = new_avg_quality

        inventory_ref[item_id] = total_qty # Implementation

    def post_ask(self, item_id: str, price: float, quantity: float, market: OrderBookMarket, current_tick: int) -> Order:
        context = self._build_sales_post_ask_context(item_id, price, quantity, market.id, current_tick)
        return self.sales_engine.post_ask(
            self.sales_state, context
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
             total_revenue += float(amount) * rate

        result = self.sales_engine.adjust_marketing_budget(self.sales_state, market_context, total_revenue)
        self.sales_state.marketing_budget_pennies = int(result.new_budget)

    def get_snapshot_dto(self) -> FirmSnapshotDTO:
        """Helper to create FirmSnapshotDTO for engines."""
        # Note: We are creating fresh state DTOs here to ensure purity.
        # Ideally, state DTOs should be cached or updated, but here we construct them on the fly
        # effectively snapshotting the current mutable state.

        # We reuse get_state_dto logic but split it into component parts if needed.
        # But FirmSnapshotDTO takes separate State DTOs.

        # 1. HR State
        employee_ids = [e.id for e in self.hr_state.employees]
        employees_data = {}
        for e in self.hr_state.employees:
            employees_data[e.id] = {
                "id": e.id,
                "wage": self.hr_state.employee_wages.get(e.id, 0.0),
                "skill": getattr(e, 'labor_skill', 1.0),
                "age": getattr(e, 'age', 0),
                "education_level": getattr(e, 'education_level', 0)
            }

        hr_dto = HRStateDTO(
            employees=employee_ids,
            employees_data=employees_data
        )

        # 2. Finance State
        finance_dto = FinanceStateDTO(
            balance=self.wallet.get_all_balances(),
            revenue_this_turn=self.finance_state.revenue_this_turn.copy(),
            expenses_this_tick=self.finance_state.expenses_this_tick.copy(),
            consecutive_loss_turns=self.finance_state.consecutive_loss_turns,
            profit_history=list(self.finance_state.profit_history),
            altman_z_score=0.0,
            valuation=self.finance_state.valuation_pennies,
            total_shares=self.finance_state.total_shares,
            treasury_shares=self.finance_state.treasury_shares,
            dividend_rate=self.finance_state.dividend_rate,
            is_publicly_traded=True
        )

        # 3. Production State
        production_dto = ProductionStateDTO(
            current_production=self.production_state.current_production,
            productivity_factor=self.production_state.productivity_factor,
            production_target=self.production_state.production_target,
            capital_stock=self.production_state.capital_stock,
            base_quality=self.production_state.base_quality,
            automation_level=self.production_state.automation_level,
            specialization=self.production_state.specialization,
            inventory=self._inventory.copy(),
            input_inventory=self._input_inventory.copy(),
            inventory_quality=self.production_state.inventory_quality.copy()
        )

        # 4. Sales State
        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=self.sales_state.inventory_last_sale_tick.copy(),
            price_history=self.sales_state.last_prices.copy(),
            brand_awareness=self.sales_state.brand_awareness,
            perceived_quality=self.sales_state.perceived_quality,
            marketing_budget=float(self.sales_state.marketing_budget_pennies)
        )
        
        return FirmSnapshotDTO(
            id=self.id,
            is_active=self.is_active,
            config=self.config,
            finance=finance_dto,
            production=production_dto,
            sales=sales_dto,
            hr=hr_dto
        )

    def produce(self, current_time: int, technology_manager: Optional[Any] = None, effects_queue: Optional[List[Dict[str, Any]]] = None) -> None:
        # 1. ASSEMBLE snapshot and input DTO
        snapshot = self.get_snapshot_dto()
        productivity_multiplier = technology_manager.get_productivity_multiplier(self.id) if technology_manager else 1.0

        input_dto = ProductionInputDTO(
            firm_snapshot=snapshot,
            productivity_multiplier=productivity_multiplier
        )

        # 2. DELEGATE to stateless engine
        result: ProductionResultDTO = self.production_engine.produce(input_dto)

        # 3. APPLY result to state (Orchestrator responsibility)
        # Apply depreciation/decay (new mechanism)
        if result.capital_depreciation > 0:
            self.production_state.capital_stock = max(0.0, self.production_state.capital_stock - result.capital_depreciation)

        if result.automation_decay > 0:
            self.production_state.automation_level = max(0.0, self.production_state.automation_level - result.automation_decay)

        # Update production
        self.current_production = result.quantity_produced
        if result.success and result.quantity_produced > 0:
            self.add_item(result.specialization, result.quantity_produced, quality=result.quality)

            # MIGRATION: Record expense in int pennies
            # Result production_cost might be float from engine?
            # I will update engine later. For now, cast.
            cost_pennies = int(result.production_cost)
            self.record_expense(cost_pennies, DEFAULT_CURRENCY)

            # Consume inputs
            for mat, amount in result.inputs_consumed.items():
                self.remove_item(mat, amount, slot=InventorySlot.INPUT)

        # TD-271: Real Estate Utilization
        effect, amount = self.real_estate_utilization_component.apply(
            self.finance_state.owned_properties,
            self.config,
            self.id,
            current_time
        )
        if amount > 0:
            self.record_revenue(amount, DEFAULT_CURRENCY)

        if effect and effects_queue is not None:
            effects_queue.append(effect)


    @override
    def get_agent_data(self) -> Dict[str, Any]:
        """AI Data Provider."""
        return {
            "assets": MultiCurrencyWalletDTO(balances=self.wallet.get_all_balances()),
            "needs": self.needs.copy(),
            "inventory": self.get_all_items(),
            "input_inventory": self._input_inventory.copy(),
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
        # Implementation moved from FirmStateDTO.from_firm to here for Protocol Purity
        # Note: This is duplicative with get_snapshot_dto but serves the public API AgentStateDTO (different purpose)
        # get_snapshot_dto is for Engines (all state components). get_state_dto is for DecisionEngine/Output.

        # Reuse logic where possible or keep separate.
        # For now, keeping as is to avoid breaking existing public API.

        # 1. HR State
        employee_ids = [e.id for e in self.hr_state.employees]
        employees_data = {}
        for e in self.hr_state.employees:
            employees_data[e.id] = {
                "id": e.id,
                "wage": self.hr_state.employee_wages.get(e.id, 0.0),
                "skill": getattr(e, 'labor_skill', 1.0),
                "age": getattr(e, 'age', 0),
                "education_level": getattr(e, 'education_level', 0)
            }

        hr_dto = HRStateDTO(
            employees=employee_ids,
            employees_data=employees_data
        )

        # 2. Finance State
        finance_dto = FinanceStateDTO(
            balance=self.wallet.get_balance(DEFAULT_CURRENCY), # Public API uses float balance for main currency often
            revenue_this_turn=self.finance_state.revenue_this_turn.get(DEFAULT_CURRENCY, 0),
            expenses_this_tick=self.finance_state.expenses_this_tick.get(DEFAULT_CURRENCY, 0),
            consecutive_loss_turns=self.finance_state.consecutive_loss_turns,
            profit_history=list(self.finance_state.profit_history),
            altman_z_score=0.0,
            valuation=self.finance_state.valuation_pennies,
            total_shares=self.finance_state.total_shares,
            treasury_shares=self.finance_state.treasury_shares,
            dividend_rate=self.finance_state.dividend_rate,
            is_publicly_traded=True
        )

        # 3. Production State
        production_dto = ProductionStateDTO(
            current_production=self.production_state.current_production,
            productivity_factor=self.production_state.productivity_factor,
            production_target=self.production_state.production_target,
            capital_stock=self.production_state.capital_stock,
            base_quality=self.production_state.base_quality,
            automation_level=self.production_state.automation_level,
            specialization=self.production_state.specialization,
            inventory=self._inventory.copy(),
            input_inventory=self._input_inventory.copy(),
            inventory_quality=self.production_state.inventory_quality.copy()
        )

        # 4. Sales State
        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=self.sales_state.inventory_last_sale_tick.copy(),
            price_history=self.sales_state.last_prices.copy(),
            brand_awareness=self.sales_state.brand_awareness,
            perceived_quality=self.sales_state.perceived_quality,
            marketing_budget=float(self.sales_state.marketing_budget_pennies)
        )

        sentiment = 1.0 / (1.0 + self.finance_state.consecutive_loss_turns)

        return FirmStateDTO(
            id=self.id,
            is_active=self.is_active,
            finance=finance_dto,
            production=production_dto,
            sales=sales_dto,
            hr=hr_dto,
            agent_data=self.get_agent_data(),
            system2_guidance={},
            sentiment_index=sentiment
        )

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
            f"FIRM_DECISION_START | Firm {self.id} before decision: Assets={current_assets_val}, Employees={len(self.hr_state.employees)}, is_active={self.is_active}",
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
        self.execute_internal_orders(decisions, fiscal_context, current_time, market_context)

        # Filter external orders for further processing
        external_orders = [o for o in decisions if o.market_id != "internal"]

        self.sales_engine.check_and_apply_dynamic_pricing(
            self.sales_state, external_orders, current_time,
            config=self.config,
            unit_cost_estimator=lambda item_id: self.finance_engine.get_estimated_unit_cost(self.finance_state, item_id, self.config)
        )

        if market_snapshot:
             self._calculate_invisible_hand_price(market_snapshot, current_time)

        current_assets_val_after = self.wallet.get_balance(DEFAULT_CURRENCY)
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={current_assets_val_after}, Employees={len(self.hr_state.employees)}, is_active={self.is_active}, Decisions={len(external_orders)}",
            extra={
                **log_extra,
                "assets_after": self.wallet.get_all_balances(),
                "num_employees_after": len(self.hr_state.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(external_orders),
            },
        )
        return external_orders, tactic

    def execute_internal_orders(self, orders: List[Order], fiscal_context: FiscalContext, current_time: int, market_context: Optional[MarketContextDTO] = None) -> None:
        """
        Orchestrates internal orders by delegating to specialized engines.
        Replaces _execute_internal_order.
        """
        snapshot = self.get_snapshot_dto()
        government = fiscal_context.government if fiscal_context else None
        gov_id = government.id if government else None

        fin_ctx = FinancialTransactionContext(
            government_id=gov_id,
            tax_rates={},
            market_context=market_context or {},
            shareholder_registry=None
        )

        def get_amount(o: Order) -> int:
            val = o.monetary_amount['amount_pennies'] if o.monetary_amount else o.quantity
            return int(val)

        def get_currency(o: Order) -> CurrencyCode:
             return o.monetary_amount['currency'] if o.monetary_amount else DEFAULT_CURRENCY

        for order in orders:
            if order.market_id != "internal":
                continue

            amount = get_amount(order)

            # --- Delegate to AssetManagementEngine ---
            if order.order_type in ["INVEST_AUTOMATION", "INVEST_CAPEX"]:
                investment_type = "AUTOMATION" if order.order_type == "INVEST_AUTOMATION" else "CAPEX"

                # Check funds first via FinanceEngine simulation or just check wallet
                # The engine doesn't check funds in wallet, it checks logical possibility.
                # But we should check if we can pay.
                # Old code used self.finance_engine.invest_in_automation which checked funds/created tx.
                # Now we want to separate logic.

                # Payment flow:
                # 1. Check if we have funds.
                if self.wallet.get_balance(DEFAULT_CURRENCY) < amount:
                    self.logger.warning(f"INTERNAL_EXEC | Firm {self.id} failed to invest {amount} (Insufficient Funds).")
                    continue

                asset_input = AssetManagementInputDTO(
                    firm_snapshot=snapshot,
                    investment_type=investment_type,
                    investment_amount=amount
                )
                asset_result: AssetManagementResultDTO = self.asset_management_engine.invest(asset_input)

                if asset_result.success:
                    # Transfer funds
                    if self.settlement_system and self.settlement_system.transfer(self, government, int(asset_result.actual_cost), order.order_type):
                        # Apply state changes
                        self.production_state.automation_level += asset_result.automation_level_increase
                        self.production_state.capital_stock += asset_result.capital_stock_increase

                        self.record_expense(int(asset_result.actual_cost), DEFAULT_CURRENCY)
                        self.logger.info(f"INTERNAL_EXEC | Firm {self.id} invested {asset_result.actual_cost} in {order.order_type}.")
                    else:
                         self.logger.warning(f"INTERNAL_EXEC | Firm {self.id} failed transfer for {order.order_type}.")
                else:
                    self.logger.warning(f"INTERNAL_EXEC | Firm {self.id} failed {order.order_type}: {asset_result.message}")

            # --- Delegate to RDEngine ---
            elif order.order_type == "INVEST_RD":
                # Check funds
                if self.wallet.get_balance(DEFAULT_CURRENCY) < amount:
                    self.logger.warning(f"INTERNAL_EXEC | Firm {self.id} failed to invest R&D {amount} (Insufficient Funds).")
                    continue

                rd_input = RDInputDTO(firm_snapshot=snapshot, investment_amount=amount, current_time=current_time)
                rd_result: RDResultDTO = self.rd_engine.research(rd_input)

                if self.settlement_system and self.settlement_system.transfer(self, government, amount, "R&D"):
                    self.record_expense(amount, DEFAULT_CURRENCY)

                    if rd_result.success:
                         self.production_state.base_quality += rd_result.quality_improvement
                         self.production_state.productivity_factor *= rd_result.productivity_multiplier_change
                         self.production_state.research_history["success_count"] += 1
                         self.production_state.research_history["last_success_tick"] = current_time
                         self.logger.info(f"INTERNAL_EXEC | Firm {self.id} R&D SUCCESS (Budget: {amount:.1f})")

                    self.production_state.research_history["total_spent"] += amount

            # --- Existing Handlers (HR, Finance) ---
            elif order.order_type == "SET_TARGET":
                self.production_state.production_target = order.quantity
                self.logger.info(f"INTERNAL_EXEC | Firm {self.id} set production target to {order.quantity:.1f}")

            elif order.order_type == "PAY_TAX":
                amount = get_amount(order)
                currency = get_currency(order)
                reason = order.item_id

                tx = self.finance_engine.pay_ad_hoc_tax(
                    self.finance_state, self.id, self.wallet.get_all_balances(), amount, currency, reason, fin_ctx, current_time
                )
                if tx:
                    if self.settlement_system and self.settlement_system.transfer(self, government, amount, reason, currency=currency):
                        self.finance_engine.record_expense(self.finance_state, amount, currency)

            elif order.order_type == "SET_DIVIDEND":
                self.finance_state.dividend_rate = order.quantity

            elif order.order_type == "SET_PRICE":
                pass

            elif order.order_type == "FIRE":
                 tx = self.hr_engine.create_fire_transaction(
                    self.hr_state, self.id, self.wallet.get_balance(DEFAULT_CURRENCY), order.target_agent_id, order.price, current_time
                 )
                 if tx:
                    employee = next((e for e in self.hr_state.employees if e.id == order.target_agent_id), None)
                    if employee and self.settlement_system and self.settlement_system.transfer(self, employee, int(tx.price), "Severance", currency=tx.currency):
                        self.hr_engine.finalize_firing(self.hr_state, order.target_agent_id)
                        self.logger.info(f"INTERNAL_EXEC | Firm {self.id} fired employee {order.target_agent_id}.")
                    else:
                        self.logger.warning(f"INTERNAL_EXEC | Firm {self.id} failed to fire {order.target_agent_id} (transfer failed).")

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

    def _build_payroll_context(self, current_time: int, government: Optional[Any], market_context: MarketContextDTO) -> HRPayrollContextDTO:
        tax_policy = None
        # Extract from market_context if available (FiscalContext)
        fiscal_policy = market_context.get("fiscal_policy")
        income_tax_rate = fiscal_policy.income_tax_rate if fiscal_policy else 0.0 # Default
        survival_cost = 10.0 # Default

        gov_id = government.id if government else -1 # Fallback ID

        tax_policy = TaxPolicyDTO(
            income_tax_rate=income_tax_rate,
            survival_cost=survival_cost,
            government_agent_id=gov_id
        )

        return HRPayrollContextDTO(
            exchange_rates=market_context.get("exchange_rates", {DEFAULT_CURRENCY: 1.0}),
            tax_policy=tax_policy,
            current_time=current_time,
            firm_id=self.id,
            wallet_balances=self.wallet.get_all_balances(),
            labor_market_min_wage=10.0, # Should come from config or market data
            ticks_per_year=getattr(self.config, "ticks_per_year", 365),
            severance_pay_weeks=getattr(self.config, "severance_pay_weeks", 2.0)
        )

    def _build_sales_marketing_context(self, current_time: int, government: Optional[Any]) -> SalesMarketingContextDTO:
        gov_id = government.id if government else None
        return SalesMarketingContextDTO(
            firm_id=self.id,
            wallet_balance=self.wallet.get_balance(DEFAULT_CURRENCY),
            government_id=gov_id,
            current_time=current_time
        )

    def _build_sales_post_ask_context(self, item_id: str, price: float, quantity: float, market_id: str, current_tick: int) -> SalesPostAskContextDTO:
        brand_snapshot = {
            "brand_awareness": self.sales_state.brand_awareness,
            "perceived_quality": self.sales_state.perceived_quality,
            "quality": self.get_quality(item_id),
        }
        return SalesPostAskContextDTO(
            firm_id=self.id,
            item_id=item_id,
            price=price,
            quantity=quantity,
            market_id=market_id,
            current_tick=current_tick,
            inventory_quantity=self.get_quantity(item_id),
            brand_snapshot=brand_snapshot
        )

    def generate_transactions(self, government: Optional[Any], market_data: Dict[str, Any], shareholder_registry: IShareholderRegistry, current_time: int, market_context: MarketContextDTO) -> List[Transaction]:
        transactions = []
        gov_id = government.id if government else None

        # Extract dynamic tax rates from MarketContext
        fiscal_policy = market_context.get("fiscal_policy")
        corporate_tax_rate = fiscal_policy.corporate_tax_rate if fiscal_policy else 0.2

        tax_rates = {"income_tax": corporate_tax_rate}

        # 1. Payroll
        payroll_context = self._build_payroll_context(current_time, government, market_context)
        payroll_result = self.hr_engine.process_payroll(
            self.hr_state, payroll_context, self.config
        )
        transactions.extend(payroll_result.transactions)

        # Apply employee updates
        for update in payroll_result.employee_updates:
            # Find the actual agent instance in our state list
            employee = next((e for e in self.hr_state.employees if e.id == update.employee_id), None)
            if not employee: continue

            # Apply income update
            if update.net_income > 0:
                employee.labor_income_this_tick = (employee.labor_income_this_tick or 0) + int(update.net_income)

            # Apply firing
            if update.fire_employee:
                employee.quit()
                self.hr_engine.finalize_firing(self.hr_state, update.employee_id)

        # 2. Finance
        # Calculate inventory value for holding cost
        inventory_value = 0.0
        for item, qty in self.get_all_items().items():
            price = self.last_prices.get(item, 10.0)
            inventory_value += qty * price

        fin_ctx = FinancialTransactionContext(
            government_id=gov_id,
            tax_rates=tax_rates,
            market_context=market_context,
            shareholder_registry=shareholder_registry
        )

        tx_finance = self.finance_engine.generate_financial_transactions(
            self.finance_state, self.id, self.wallet.get_all_balances(), self.config, current_time, fin_ctx, inventory_value
        )
        transactions.extend(tx_finance)

        # 3. Marketing
        # Adjust budget first (ask Engine what the budget should be)
        marketing_result = self.sales_engine.adjust_marketing_budget(
            self.sales_state, market_context, float(self.finance_state.last_revenue_pennies) # Engine uses float revenue?
        )
        # Apply result
        self.sales_state.marketing_budget_pennies = marketing_result.new_budget

        # Then generate transaction using the updated state
        marketing_context = self._build_sales_marketing_context(current_time, government)
        tx_marketing = self.sales_engine.generate_marketing_transaction(
            self.sales_state, marketing_context
        )
        if tx_marketing:
            transactions.append(tx_marketing)

        # Brand Update
        self.brand_engine.update(
            self.sales_state,
            self.config,
            float(self.sales_state.marketing_budget_pennies),
            self.productivity_factor / 10.0,
            self.id
        )

        # WO-4.6: Finance cleanup is now handled in Post-Sequence via reset()
        # This ensures expenses_this_tick accumulates for the full tick duration.

        return transactions

    @override
    def update_needs(self, current_time: int, government: Optional[Any] = None, market_data: Optional[Dict[str, Any]] = None, technology_manager: Optional[Any] = None) -> None:
        pass

    # --- IPropertyOwner Implementation ---
    @property
    def owned_properties(self) -> List[int]:
        return self.finance_state.owned_properties

    def add_property(self, property_id: int) -> None:
        if property_id not in self.finance_state.owned_properties:
            self.finance_state.owned_properties.append(property_id)

    def remove_property(self, property_id: int) -> None:
        if property_id in self.finance_state.owned_properties:
            self.finance_state.owned_properties.remove(property_id)

    # --- IFinancialAgent Implementation ---

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
         self.wallet.add(amount, currency)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
         current_bal = self.wallet.get_balance(currency)
         if current_bal < amount:
            raise InsufficientFundsError(
                f"Insufficient funds", required=MoneyDTO(amount_pennies=amount, currency=currency), available=MoneyDTO(amount_pennies=current_bal, currency=currency)
            )
         self.wallet.subtract(amount, currency)

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Implements IFinancialAgent.get_balance."""
        return self.wallet.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        return self.wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        """
        Returns the total wealth in default currency estimation.
        TD-270: Standardized multi-currency summation.
        """
        balances = self.wallet.get_all_balances()
        total = 0
        # For now, we assume 1:1 exchange rate as per spec draft for simple conversion.
        # Future implementations should use an IExchangeRateService.
        for amount in balances.values():
            total += amount
        return total

    @override
    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        """Implementation of ICurrencyHolder."""
        return self.wallet.get_all_balances()

    # --- Facade Methods ---

    def get_book_value_per_share(self) -> float:
        outstanding = self.total_shares - self.treasury_shares
        if outstanding <= 0: return 0.0
        net_assets = self.wallet.get_balance(DEFAULT_CURRENCY) - self.finance_state.total_debt_pennies
        return max(0.0, float(net_assets)) / outstanding

    def get_market_cap(self, stock_price: Optional[float] = None) -> float:
        if stock_price is None:
            stock_price = self.get_book_value_per_share()
        return (self.total_shares - self.treasury_shares) * stock_price

    def calculate_valuation(self, market_context: MarketContextDTO = None) -> int:
        inventory_value = sum(self.get_quantity(i) * self.last_prices.get(i, 10.0) for i in self.get_all_items())
        # Wrap market_context in FinancialTransactionContext if needed, or update Engine to accept optional context
        # Engine expects FinancialTransactionContext.
        fin_ctx = None
        if market_context:
            fin_ctx = FinancialTransactionContext(
                government_id=None, # Not needed for valuation?
                tax_rates={},
                market_context=market_context,
                shareholder_registry=None
            )

        return int(self.finance_engine.calculate_valuation(
            self.finance_state, self.wallet.get_all_balances(), self.config, inventory_value, self.capital_stock, fin_ctx
        ))

    def get_financial_snapshot(self) -> Dict[str, Any]:
        inventory_value = sum(self.get_quantity(i) * self.last_prices.get(i, 10.0) for i in self.get_all_items())
        cash = self.wallet.get_balance(DEFAULT_CURRENCY)
        total_assets = cash + inventory_value + self.capital_stock
        working_capital = cash + inventory_value # Simplified: Current Assets

        return {
             "wallet": MultiCurrencyWalletDTO(balances=self.wallet.get_all_balances()),
             "total_assets": int(total_assets),
             "total_debt": self.finance_state.total_debt_pennies,
             "retained_earnings": self.finance_state.retained_earnings_pennies,
             "average_profit": sum(self.finance_state.profit_history)/len(self.finance_state.profit_history) if self.finance_state.profit_history else 0.0,
             "working_capital": int(working_capital),
             "ebit": self.finance_state.current_profit.get(DEFAULT_CURRENCY, 0), # Current EBIT proxy
             "market_value_equity": self.get_market_cap()
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

    def reset_finance(self) -> None:
        """
        Resets the financial state for the next tick.
        Called by the simulation orchestrator's post-processing phase.
        Delegates to FinanceState.
        """
        self.finance_state.reset_tick_counters(DEFAULT_CURRENCY)

    def reset(self) -> None:
        """
        Alias for reset_finance.
        Called by the simulation orchestrator for general agent reset.
        """
        self.reset_finance()
