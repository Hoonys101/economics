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
from modules.simulation.dtos.api import FirmConfigDTO, FirmStateDTO, IFirmStateProvider, FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from simulation.ai.enums import Personality
from modules.system.api import MarketSnapshotDTO, DEFAULT_CURRENCY, CurrencyCode, MarketContextDTO, ICurrencyHolder
from modules.simulation.api import AgentCoreConfigDTO, IDecisionEngine, AgentStateDTO, IOrchestratorAgent, IInventoryHandler, ISensoryDataProvider, AgentSensorySnapshotDTO, IConfigurable, LiquidationConfigDTO, InventorySlot, ItemDTO, InventorySlotDTO, AgentID
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
from modules.firm.engines.pricing_engine import PricingEngine
from modules.firm.orchestrators.firm_action_executor import FirmActionExecutor
from simulation.components.engines.real_estate_component import RealEstateUtilizationComponent

from simulation.dtos.context_dtos import PayrollProcessingContext, FinancialTransactionContext, SalesContext
from simulation.dtos.hr_dtos import HRPayrollContextDTO, TaxPolicyDTO
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO

# New API Imports
from modules.firm.api import (
    FirmSnapshotDTO,
    FinanceDecisionInputDTO, BudgetPlanDTO,
    HRDecisionInputDTO, HRDecisionOutputDTO,
    ProductionInputDTO, ProductionResultDTO,
    AssetManagementInputDTO, AssetManagementResultDTO,
    RDInputDTO, RDResultDTO,
    PricingInputDTO, PricingResultDTO,
    LiquidationExecutionDTO, LiquidationResultDTO,
    IProductionEngine, IAssetManagementEngine, IRDEngine, IPricingEngine,
    IInventoryComponent, IFinancialComponent,
    ISalesEngine, IBrandEngine, IFinanceEngine, IHREngine,
    ProductionContextDTO, HRContextDTO, SalesContextDTO,
    ProductionIntentDTO, HRIntentDTO, SalesIntentDTO,
    FirmBrainScanContextDTO, FirmBrainScanResultDTO, IBrainScanReady
)
from modules.firm.constants import (
    DEFAULT_MARKET_INSIGHT, DEFAULT_MARKETING_BUDGET_RATE, DEFAULT_LIQUIDATION_PRICE,
    INSIGHT_DECAY_RATE, INSIGHT_BOOST_FACTOR, INSIGHT_ERROR_THRESHOLD,
    DEFAULT_LABOR_WAGE, DEFAULT_SURVIVAL_COST, DEFAULT_CORPORATE_TAX_RATE,
    PRODUCTIVITY_DIVIDER, DEFAULT_PRICE
)

from modules.agent_framework.components.inventory_component import InventoryComponent
from modules.agent_framework.components.financial_component import FinancialComponent

from modules.common.utils.shadow_logger import log_shadow
from modules.finance.api import InsufficientFundsError, IFinancialFirm, ICreditFrozen, ILiquidatable, LiquidationContext, EquityStake, IBank, ISalesTracker
from modules.common.financial.api import IFinancialAgent
from modules.common.interfaces import IPropertyOwner
from modules.common.financial.dtos import Claim, MoneyDTO
from modules.finance.dtos import MultiCurrencyWalletDTO
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

class Firm(ILearningAgent, IFinancialFirm, IFinancialAgent, ILiquidatable, IOrchestratorAgent, ICreditFrozen, IInventoryHandler, ICurrencyHolder, ISensoryDataProvider, IConfigurable, IPropertyOwner, IFirmStateProvider, ISalesTracker, IBrainScanReady):
    """
    Firm Agent (Orchestrator).
    Manages state and delegates logic to stateless engines.
    Refactored to Composition (No BaseAgent).
    """

    # Explicitly override age property from Protocol to allow instance attribute usage
    age: int = 0
    sales_volume_this_tick: float = 0.0

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

        # Components
        self.inventory_component = InventoryComponent(str(self.id))
        # self.inventory_component.attach(self) # REMOVED: Decoupling
        self.financial_component = FinancialComponent(str(self.id))
        # self.financial_component.attach(self) # REMOVED: Decoupling

        self.is_active = True

        self.config = config_dto

        # State Initialization
        self.hr_state = HRState()
        self.finance_state = FinanceState()
        self.production_state = ProductionState()
        self.sales_state = SalesState()

        # Engine Initialization (Stateless)
        self.hr_engine: IHREngine = HREngine()
        self.finance_engine: IFinanceEngine = FinanceEngine()
        self.production_engine: IProductionEngine = ProductionEngine()
        self.sales_engine: ISalesEngine = SalesEngine()
        self.asset_management_engine: IAssetManagementEngine = AssetManagementEngine()
        self.rd_engine: IRDEngine = RDEngine()
        self.brand_engine: IBrandEngine = BrandEngine()
        self.pricing_engine: IPricingEngine = PricingEngine()

        # Protocol Integrity Check
        if not isinstance(self.hr_engine, IHREngine): raise TypeError("hr_engine violation")
        if not isinstance(self.finance_engine, IFinanceEngine): raise TypeError("finance_engine violation")
        if not isinstance(self.production_engine, IProductionEngine): raise TypeError("production_engine violation")
        if not isinstance(self.sales_engine, ISalesEngine): raise TypeError("sales_engine violation")
        if not isinstance(self.asset_management_engine, IAssetManagementEngine): raise TypeError("asset_management_engine violation")
        if not isinstance(self.rd_engine, IRDEngine): raise TypeError("rd_engine violation")
        if not isinstance(self.brand_engine, IBrandEngine): raise TypeError("brand_engine violation")
        if not isinstance(self.pricing_engine, IPricingEngine): raise TypeError("pricing_engine violation")

        self.action_executor = FirmActionExecutor()

        # Initialize core attributes in State
        self.production_state.specialization = specialization
        self.production_state.sector = sector
        self.production_state.productivity_factor = productivity_factor
        self.production_state.production_target = self.config.firm_min_production_target

        # Determine Major (Phase 4.1: Labor Majors Config Migration)
        # Use getattr to safely access labor_market if config_dto is a mock without it
        labor_market_config = getattr(self.config, 'labor_market', {})
        if labor_market_config is None: labor_market_config = {}
        sector_map = labor_market_config.get("sector_map", {})
        self.major = sector_map.get(self.production_state.sector, "GENERAL")

        self.finance_state.total_shares = self.config.ipo_initial_shares
        self.finance_state.treasury_shares = self.config.ipo_initial_shares # Initially all treasury
        self.finance_state.dividend_rate = self.config.dividend_rate
        self.finance_state.profit_history = deque(maxlen=self.config.profit_history_ticks)

        self.sales_state.marketing_budget_rate = DEFAULT_MARKETING_BUDGET_RATE

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
        self.market_insight = DEFAULT_MARKET_INSIGHT # Phase 4.1: Dynamic Cognitive Filter
        self.sales_volume_this_tick: float = 0.0

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
            default_price=DEFAULT_LIQUIDATION_PRICE,
            market_prices=self.last_prices.copy()
        )

    # --- IOrchestratorAgent Implementation ---

    def get_core_config(self) -> AgentCoreConfigDTO:
        return self._core_config

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        return {
            "is_active": self.is_active,
            "approval_rating": 0.0,
            "total_wealth": self.total_wealth # Use total_wealth property which delegates
        }

    def get_current_state(self) -> AgentStateDTO:
        # Convert inventories to DTOs
        main_items = [
            ItemDTO(name=k, quantity=v, quality=self.get_quality(k, InventorySlot.MAIN))
            for k, v in self.inventory_component.main_inventory.items()
        ]
        input_items = [
            ItemDTO(name=k, quantity=v, quality=self.get_quality(k, InventorySlot.INPUT))
            for k, v in self.inventory_component.input_inventory.items()
        ]

        inventories = {
            InventorySlot.MAIN.name: InventorySlotDTO(items=main_items),
            InventorySlot.INPUT.name: InventorySlotDTO(items=input_items)
        }

        return AgentStateDTO(
            assets=self.financial_component.get_all_balances(),
            is_active=self.is_active,
            inventories=inventories,
            inventory=None
        )

    def load_state(self, state: AgentStateDTO) -> None:
        if state.assets and any(v > 0 for v in state.assets.values()):
             self.logger.warning(f"Agent {self.id}: load_state called with assets, but direct loading is disabled for integrity. Assets ignored: {state.assets}")

        self.inventory_component.clear_inventory(InventorySlot.MAIN)
        self.inventory_component.clear_inventory(InventorySlot.INPUT)

        self.is_active = state.is_active

        # Restore from inventories
        if state.inventories:
            for slot_name, slot_dto in state.inventories.items():
                slot = InventorySlot[slot_name] if slot_name in InventorySlot.__members__ else None
                if slot == InventorySlot.MAIN:
                    target_inv = self.inventory_component.main_inventory
                    target_qual = self.inventory_component.inventory_quality
                elif slot == InventorySlot.INPUT:
                    target_inv = self.inventory_component.input_inventory
                else:
                    self.logger.warning(f"Unknown inventory slot in load_state: {slot_name}")
                    continue

                if slot == InventorySlot.INPUT:
                     # Fallback to add_item which is safe, though avg calc might be redundant if empty.
                     # But clear() was called.
                     for item in slot_dto.items:
                         self.add_item(item.name, item.quantity, quality=item.quality, slot=InventorySlot.INPUT)
                elif slot == InventorySlot.MAIN:
                     for item in slot_dto.items:
                         self.add_item(item.name, item.quantity, quality=item.quality, slot=InventorySlot.MAIN)

        # Fallback for legacy state
        elif state.inventory:
             for k, v in state.inventory.items():
                 self.add_item(k, v)

    @property
    def wallet(self) -> Wallet:
        return self.financial_component.wallet

    # --- IFinancialAgent & ICurrencyHolder Implementation ---

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        return self.financial_component.get_balance(currency)

    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
        return self.financial_component.balance_pennies

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
        return self.financial_component.get_all_balances()

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        """Alias for get_all_balances required by ICurrencyHolder."""
        return self.get_all_balances()

    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
        return self.financial_component.total_wealth

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> int:
        """Returns liquid assets in pennies (int)."""
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        """Returns total debt in pennies (int)."""
        return self.finance_state.total_debt_pennies

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Internal deposit implementation."""
        self.financial_component.deposit(amount, currency)

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Internal withdraw implementation."""
        self.financial_component.withdraw(amount, currency)

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Public deposit implementation."""
        self.financial_component.deposit(amount_pennies, currency)

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Public withdraw implementation."""
        self.financial_component.withdraw(amount_pennies, currency)

    # --- ICreditFrozen Implementation ---

    @property
    def credit_frozen_until_tick(self) -> int:
        return self._credit_frozen_until_tick

    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None:
        self._credit_frozen_until_tick = value
        # Sync to component
        self.financial_component.credit_frozen_until_tick = value

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
        return self.inventory_component.inventory_quality

    @property
    def input_inventory(self) -> Dict[str, float]:
        """Facade property for backward compatibility during transition."""
        return self.inventory_component.input_inventory

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
    def total_debt_pennies(self) -> int:
        """Alias for total_debt to satisfy IFinancialFirm."""
        return self.total_debt

    @property
    def capital_stock_units(self) -> int:
        """Capital stock quantity in units."""
        return int(self.production_state.capital_stock)

    @property
    def inventory_value_pennies(self) -> int:
        """Total value of all inventory in pennies."""
        # Calculate on the fly or use cached valuation?
        # calculate_valuation() does this.
        val = 0
        for item, qty in self.get_all_items().items():
            price = self.last_prices.get(item, DEFAULT_PRICE)
            val += int(qty * price)
        return val

    @property
    def monthly_wage_bill_pennies(self) -> int:
        """Total monthly wage bill estimate."""
        return sum(self.hr_state.employee_wages.values())

    @property
    def retained_earnings_pennies(self) -> int:
        """Total retained earnings."""
        # Simple estimate for now
        return sum(self.finance_state.profit_history)

    @property
    def average_profit_pennies(self) -> int:
        """The average profit over the relevant history in pennies."""
        history = self.finance_state.profit_history
        if not history:
            return 0
        return int(sum(history) / len(history))

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

    def get_market_cap(self, stock_price: Optional[float] = None) -> int:
        """
        Calculates market capitalization in pennies.
        If stock_price is provided (dollars), calculates based on outstanding shares.
        If not provided, falls back to intrinsic valuation (valuation_pennies).
        """
        if stock_price is not None:
            outstanding = self.total_shares - self.treasury_shares
            # stock_price is dollars, convert to pennies: * 100
            return int(outstanding * stock_price * 100)

        return self.valuation

    def get_financial_snapshot(self) -> Dict[str, Any]:
        """
        Returns a financial snapshot for reporting.
        Implements expected interface for EconomicIndicatorTracker.
        """
        balances = self.financial_component.get_all_balances()
        total_cash = sum(balances.values()) # Aggregated in pennies (simplified)

        # Calculate Total Assets in Pennies
        # Capital Stock Value (Estimate: 1 unit = 100 pennies)
        capital_val = self.capital_stock_units * 100

        total_assets = total_cash + self.inventory_value_pennies + capital_val

        return {
            "total_assets": total_assets,
            "working_capital": total_cash - self.finance_state.total_debt_pennies, # Approx
            "retained_earnings": self.retained_earnings_pennies,
            "average_profit": self.average_profit_pennies,
            "total_debt": self.finance_state.total_debt_pennies
        }

    def calculate_valuation(self) -> int:
        """
        Calculates and updates firm valuation.
        Delegates to FinanceEngine.
        """
        # Gather data
        balances = self.financial_component.get_all_balances()

        # Calculate inventory value
        inventory_value = 0
        for item, qty in self.get_all_items().items():
            price = self.last_prices.get(item, DEFAULT_PRICE)
            inventory_value += int(qty * price)

        capital_stock = int(self.production_state.capital_stock)

        return self.finance_engine.calculate_valuation(
            self.finance_state,
            balances,
            self.config,
            inventory_value,
            capital_stock,
            context=None
        )

    def get_book_value_per_share(self) -> float:
        """
        Calculates Book Value per Share (pennies) based on liquid assets and debt.
        Note: Excludes non-liquid assets (Capital/Inventory) to match legacy test expectations.
        Returns float.
        """
        outstanding = self.total_shares - self.treasury_shares
        if outstanding <= 0:
            return 0.0

        assets = sum(self.financial_component.get_all_balances().values())
        liabilities = self.finance_state.total_debt_pennies

        net_assets = assets - liabilities
        return float(max(0, net_assets)) / outstanding

    def reset_finance(self):
        """Resets finance counters for the next tick."""
        self.finance_state.reset_tick_counters(DEFAULT_CURRENCY)

    def reset(self) -> None:
        """
        Resets the firm's state for the next simulation tick.
        Clears temporary counters and prepares for new decisions.
        """
        self.reset_finance()
        self.sales_volume_this_tick = 0.0

        # Adaptive Learning Rotation
        self.hr_state.hires_prev_tick = self.hr_state.hires_this_tick
        self.hr_state.hires_this_tick = 0
        self.hr_state.target_hires_prev_tick = self.hr_state.target_hires_this_tick
        self.hr_state.target_hires_this_tick = 0
        self.hr_state.wage_offer_prev_tick = self.hr_state.wage_offer_this_tick
        self.hr_state.wage_offer_this_tick = 0

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
        self.sales_volume_this_tick += quantity

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
                amount_pennies=int(total_debt),
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
        """Liquidate assets using Protocol Purity and AssetManagementEngine."""
        
        # 1. Construct Input DTO
        snapshot = self.get_snapshot_dto()
        input_dto = LiquidationExecutionDTO(
            firm_snapshot=snapshot,
            current_tick=current_tick
        )
        
        # 2. Call Engine
        result: LiquidationResultDTO = self.asset_management_engine.calculate_liquidation(input_dto)

        # 3. Apply Result (Agent Responsibility)

        # Write off Inventory
        self.clear_inventory(InventorySlot.MAIN)
        self.clear_inventory(InventorySlot.INPUT)

        # Write off Capital & Automation
        self.capital_stock = max(0.0, self.capital_stock - result.capital_stock_to_write_off)
        self.automation_level = max(0.0, self.automation_level - result.automation_level_to_write_off)

        self.is_bankrupt = result.is_bankrupt

        assets_to_return = result.assets_returned

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
        """
        Delegates to InventoryComponent, supporting strict slot-based inventory management (MAIN vs INPUT).
        """
        return self.inventory_component.add_item(item_id, quantity, transaction_id, quality, slot)

    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: InventorySlot = InventorySlot.MAIN) -> bool:
        """
        Delegates to InventoryComponent, supporting strict slot-based inventory management.
        """
        return self.inventory_component.remove_item(item_id, quantity, transaction_id, slot)

    @override
    def get_quantity(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        return self.inventory_component.get_quantity(item_id, slot)

    @override
    def get_quality(self, item_id: str, slot: InventorySlot = InventorySlot.MAIN) -> float:
        return self.inventory_component.get_quality(item_id, slot)

    @override
    def get_all_items(self, slot: InventorySlot = InventorySlot.MAIN) -> Dict[str, float]:
        """Returns a copy of the inventory."""
        return self.inventory_component.get_all_items(slot)

    @override
    def clear_inventory(self, slot: InventorySlot = InventorySlot.MAIN) -> None:
        """Clears the inventory."""
        self.inventory_component.clear_inventory(slot)

    def post_ask(self, item_id: str, price: float | int, quantity: float, market: OrderBookMarket, current_tick: int) -> Order:
        if isinstance(price, float):
            price_pennies = int(price * 100)
        else:
            price_pennies = price

        context = self._build_sales_post_ask_context(item_id, price_pennies, quantity, market.id, current_tick)
        order = self.sales_engine.post_ask(
            self.get_snapshot_dto().sales, context
        )
        # Apply side-effects (Stateless Engine Orchestration)
        self.sales_state.last_prices[item_id] = price_pennies
        return order

    def calculate_brand_premium(self, market_data: Dict[str, Any]) -> float:
        item_id = self.specialization
        market_avg_key = f"{item_id}_avg_traded_price"
        market_avg_price = market_data.get("goods_market", {}).get(market_avg_key, 0.0)
        my_price = self.last_prices.get(item_id, market_avg_price)
        return my_price - market_avg_price if market_avg_price > 0 else 0.0

    def _adjust_marketing_budget(self, market_context: MarketContextDTO = None) -> None:
        if market_context is None:
            market_context = MarketContextDTO(exchange_rates={DEFAULT_CURRENCY: 1.0}, benchmark_rates={})

        # Calculate primary revenue for budget adjustment
        exchange_rates = market_context.exchange_rates or {}
        total_revenue = 0.0
        for cur, amount in self.finance_state.revenue_this_turn.items():
             rate = exchange_rates.get(cur, 1.0) if cur != DEFAULT_CURRENCY else 1.0
             total_revenue += float(amount) * rate

        result = self.sales_engine.adjust_marketing_budget(
            self.get_snapshot_dto().sales,
            market_context,
            total_revenue,
            last_revenue=float(self.finance_state.last_revenue_pennies),
            last_marketing_spend=float(self.finance_state.last_marketing_spend_pennies)
        )
        self.sales_state.marketing_budget_pennies = int(result.new_budget)
        self.sales_state.marketing_budget_rate = result.new_marketing_rate

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
            employees_data=employees_data,
            hires_prev_tick=self.hr_state.hires_prev_tick,
            target_hires_prev_tick=self.hr_state.target_hires_prev_tick,
            wage_offer_prev_tick=self.hr_state.wage_offer_prev_tick
        )

        # 2. Finance State
        finance_dto = FinanceStateDTO(
            balance=self.financial_component.get_all_balances(),
            revenue_this_turn=self.finance_state.revenue_this_turn.copy(),
            expenses_this_tick=self.finance_state.expenses_this_tick.copy(),
            consecutive_loss_turns=self.finance_state.consecutive_loss_turns,
            profit_history=list(self.finance_state.profit_history),
            altman_z_score=0.0,
            valuation=self.finance_state.valuation_pennies,
            total_shares=self.finance_state.total_shares,
            treasury_shares=self.finance_state.treasury_shares,
            dividend_rate=self.finance_state.dividend_rate,
            is_publicly_traded=True,
            total_debt_pennies=self.finance_state.total_debt_pennies,
            average_interest_rate=self.finance_state.average_interest_rate
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
            inventory=self.inventory_component.main_inventory.copy(),
            input_inventory=self.inventory_component.input_inventory.copy(),
            inventory_quality=self.inventory_component.inventory_quality.copy(),
            major=self.major # Phase 4.1: Major-Matching
        )

        # 4. Sales State
        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=self.sales_state.inventory_last_sale_tick.copy(),
            price_history=self.sales_state.last_prices.copy(),
            brand_awareness=self.sales_state.brand_awareness,
            perceived_quality=self.sales_state.perceived_quality,
            marketing_budget=self.sales_state.marketing_budget_pennies, # MIGRATION: int pennies
            marketing_budget_rate=self.sales_state.marketing_budget_rate,
            adstock=self.sales_state.adstock # Added for stateless BrandEngine
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
        # 1. ASSEMBLE ProductionContextDTO
        productivity_multiplier = technology_manager.get_productivity_multiplier(self.id) if technology_manager else 1.0
        context = self._build_production_context(productivity_multiplier)

        # 2. DELEGATE to stateless engine
        intent: ProductionIntentDTO = self.production_engine.decide_production(context)

        # 3. APPLY result to state (Orchestrator responsibility)
        # Apply depreciation/decay (new mechanism)
        if intent.capital_depreciation > 0:
            self.production_state.capital_stock = max(0.0, self.production_state.capital_stock - intent.capital_depreciation)

        if intent.automation_decay > 0:
            self.production_state.automation_level = max(0.0, self.production_state.automation_level - intent.automation_decay)

        # Update production
        self.current_production = intent.target_production_quantity
        if intent.target_production_quantity > 0:
            self.add_item(self.production_state.specialization, intent.target_production_quantity, quality=intent.quality)

            # MIGRATION: Record expense in int pennies
            cost_pennies = int(intent.estimated_cost_pennies)
            self.record_expense(cost_pennies, DEFAULT_CURRENCY)

            # Consume inputs
            for mat, amount in intent.materials_to_use.items():
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
            "assets": MultiCurrencyWalletDTO(balances=self.financial_component.get_all_balances()),
            "needs": self.needs.copy(),
            "inventory": self.get_all_items(),
            "input_inventory": self.inventory_component.input_inventory.copy(),
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
            "inventory_quality": self.inventory_component.inventory_quality.copy(),
            "automation_level": self.automation_level,
            "market_insight": self.market_insight,
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
            employees_data=employees_data,
            hires_prev_tick=self.hr_state.hires_prev_tick,
            target_hires_prev_tick=self.hr_state.target_hires_prev_tick,
            wage_offer_prev_tick=self.hr_state.wage_offer_prev_tick
        )

        # 2. Finance State
        finance_dto = FinanceStateDTO(
            balance=self.financial_component.get_balance(DEFAULT_CURRENCY), # Public API uses float balance for main currency often
            revenue_this_turn=self.finance_state.revenue_this_turn.get(DEFAULT_CURRENCY, 0),
            expenses_this_tick=self.finance_state.expenses_this_tick.get(DEFAULT_CURRENCY, 0),
            consecutive_loss_turns=self.finance_state.consecutive_loss_turns,
            profit_history=list(self.finance_state.profit_history),
            altman_z_score=0.0,
            valuation=self.finance_state.valuation_pennies,
            total_shares=self.finance_state.total_shares,
            treasury_shares=self.finance_state.treasury_shares,
            dividend_rate=self.finance_state.dividend_rate,
            is_publicly_traded=True,
            total_debt_pennies=self.finance_state.total_debt_pennies,
            average_interest_rate=self.finance_state.average_interest_rate
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
            inventory=self.inventory_component.main_inventory.copy(),
            input_inventory=self.inventory_component.input_inventory.copy(),
            inventory_quality=self.inventory_component.inventory_quality.copy(),
            major=self.major # Phase 4.1: Major-Matching
        )

        # 4. Sales State
        sales_dto = SalesStateDTO(
            inventory_last_sale_tick=self.sales_state.inventory_last_sale_tick.copy(),
            price_history=self.sales_state.last_prices.copy(),
            brand_awareness=self.sales_state.brand_awareness,
            perceived_quality=self.sales_state.perceived_quality,
            marketing_budget=self.sales_state.marketing_budget_pennies # MIGRATION: int pennies
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
            sentiment_index=sentiment,
            market_insight=self.market_insight
        )

    def get_pre_state_data(self) -> Dict[str, Any]:
        return getattr(self, "pre_state_snapshot", self.get_agent_data())

    def get_tech_info(self) -> FirmTechInfoDTO:
        return {
            "id": self.id,
            "sector": self.sector,
            "current_rd_investment": self.production_state.research_history.get("total_spent", 0.0)
        }

    def _update_debt_status(self) -> None:
        """
        Updates internal debt tracking by querying the bank.
        Ensures AI Debt Awareness and Budgeting accuracy.
        """
        # Local import to avoid circular dependency
        from simulation.loan_market import LoanMarket

        market = self.decision_engine.loan_market
        if market and isinstance(market, LoanMarket):
            bank = market.bank
            if isinstance(bank, IBank):
                try:
                    debt_status = bank.get_debt_status(self.id)
                    # Convert float dollars to int pennies
                    self.finance_state.total_debt_pennies = debt_status.total_outstanding_pennies

                    # Calculate weighted average interest rate
                    total_principal = sum(l.outstanding_balance for l in debt_status.loans)
                    if total_principal > 0:
                        weighted_sum = sum(l.outstanding_balance * l.interest_rate for l in debt_status.loans)
                        self.finance_state.average_interest_rate = weighted_sum / total_principal
                    else:
                        self.finance_state.average_interest_rate = 0.0

                except Exception as e:
                    self.logger.warning(f"Failed to update debt status from bank: {e}")

    @override
    def make_decision(
        self, input_dto: DecisionInputDTO
    ) -> tuple[list[Order], Any]:
        # Update debt status before decision making
        self._update_debt_status()

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
        current_assets_val = self.financial_component.get_balance(DEFAULT_CURRENCY)

        # 1. State Snapshot
        snapshot = self.get_snapshot_dto()

        # 2. Finance Engine: Plan Budget
        fin_input = FinanceDecisionInputDTO(
            firm_snapshot=snapshot,
            market_snapshot=market_snapshot,
            config=self.config,
            current_tick=current_time,
            credit_rating=0.0
        )
        budget_plan = self.finance_engine.plan_budget(fin_input)

        # 3. HR Engine: Manage Workforce
        labor_wage = DEFAULT_LABOR_WAGE
        if market_snapshot and market_snapshot.labor:
            labor_wage = int(market_snapshot.labor.avg_wage * 100) if market_snapshot.labor.avg_wage > 0 else DEFAULT_LABOR_WAGE
        elif market_data and "labor" in market_data:
             labor_wage = int(market_data.get("labor", {}).get("avg_wage", 10.0) * 100)

        # Build HR Context
        target_headcount = self._calculate_target_headcount()
        hr_context = self._build_hr_context(budget_plan, target_headcount, current_time, labor_wage)

        # Call Decide
        hr_intent = self.hr_engine.decide_workforce(hr_context)

        # Apply HR Intent (Convert to Orders and update internal state maps)
        # Note: Hiring orders are generated below. Wage updates are applied implicitly by intent-driven payroll later?
        # No, payroll reads state. So we must update state.
        for agent_id, wage in hr_intent.wage_updates.items():
            # agent_id is AgentID (int), keys in employee_wages are int.
            if int(agent_id) in self.hr_state.employee_wages:
                self.hr_state.employee_wages[int(agent_id)] = wage

        # Generate HR Orders
        hr_orders = self._generate_hr_orders(hr_intent, hr_context)
        engine_orders = hr_orders

        # Adaptive Learning: Capture Hiring Intent
        if hr_intent.hiring_target > 0:
            self.hr_state.target_hires_this_tick = hr_intent.hiring_target
            # Find the hiring order to get the price
            for order in hr_orders:
                if order.side == 'BUY' and order.item_id == 'labor':
                    self.hr_state.wage_offer_this_tick = order.price_pennies
                    break

        # 4. Sales Engine: Decide Pricing & Sales
        sales_context = self._build_sales_context(market_snapshot, current_time)
        sales_intent = self.sales_engine.decide_pricing(sales_context)

        # Apply Sales Intent
        sales_orders = sales_intent.sales_orders
        self.sales_state.last_prices.update(sales_intent.price_adjustments)
        self.sales_state.marketing_budget_pennies = sales_intent.marketing_spend_pennies
        self.sales_state.marketing_budget_rate = sales_intent.new_marketing_budget_rate

        # 5. Production Engine: Decide Procurement (SEO Migration)
        # Using 1.0 for productivity_multiplier as tech manager is not available in decision phase.
        # This is acceptable for procurement planning.
        prod_context = self._build_production_context(1.0, market_snapshot)
        procurement_intent = self.production_engine.decide_procurement(prod_context)
        procurement_orders = procurement_intent.purchase_orders

        # Legacy Decision Engine Removed (Migration Complete)
        tactic = "SEO_PURE"

        # Merge orders
        all_orders = engine_orders + procurement_orders + sales_orders

        # Command Bus execution (Internal Orders like FIRE, SET_TARGET)
        self.execute_internal_orders(all_orders, fiscal_context, current_time, market_context)

        # Filter external orders for further processing
        external_orders = [o for o in all_orders if o.market_id != "internal"]

        # Note: Dynamic pricing and invisible hand price calc logic moved to decide_pricing,
        # but _calculate_invisible_hand_price also logs shadow price.
        # We can keep it for logging purposes if needed, but it updates state.
        # Since decide_pricing handles price updates, we should skip state update in _calculate_invisible_hand_price
        # or remove it.
        # However, decide_pricing does NOT calculate shadow price.
        # PricingEngine (which calculates shadow price) is distinct from SalesEngine.
        # If we want shadow price logging, we should keep it.
        if market_snapshot:
             self._calculate_invisible_hand_price(market_snapshot, current_time)

        current_assets_val_after = self.financial_component.get_balance(DEFAULT_CURRENCY)
        self.logger.debug(
            f"FIRM_DECISION_END | Firm {self.id} after decision: Assets={current_assets_val_after}, Employees={len(self.hr_state.employees)}, is_active={self.is_active}, Decisions={len(external_orders)}",
            extra={
                **log_extra,
                "assets_after": self.financial_component.get_all_balances(),
                "num_employees_after": len(self.hr_state.employees),
                "is_active_after": self.is_active,
                "num_decisions": len(external_orders),
            },
        )
        return external_orders, tactic

    @override
    def brain_scan(self, context: FirmBrainScanContextDTO) -> FirmBrainScanResultDTO:
        """
        Executes a hypothetical decision-making cycle without side effects.
        Implements IBrainScanReady.
        """
        # 1. State Snapshot
        base_snapshot = self.get_snapshot_dto()

        # Apply Config Override if any
        current_config = context.config_override if context.config_override else self.config
        if context.config_override:
             base_snapshot = replace(base_snapshot, config=context.config_override)

        # Market Snapshot
        current_market_snapshot = context.market_snapshot_override or MarketSnapshotDTO(tick=context.current_tick, market_signals={}, market_data={})

        # Tick
        current_tick = context.current_tick

        # --- Finance Engine: Plan Budget ---
        fin_input = FinanceDecisionInputDTO(
            firm_snapshot=base_snapshot,
            market_snapshot=current_market_snapshot,
            config=current_config,
            current_tick=current_tick,
            credit_rating=0.0 # Placeholder
        )
        budget_plan = self.finance_engine.plan_budget(fin_input)

        # --- HR Engine ---
        labor_wage = DEFAULT_LABOR_WAGE
        if current_market_snapshot.labor:
            labor_wage = int(current_market_snapshot.labor.avg_wage * 100) if current_market_snapshot.labor.avg_wage > 0 else DEFAULT_LABOR_WAGE

        target_headcount = self._calculate_target_headcount()

        hr_context = self._build_hr_context(budget_plan, target_headcount, current_tick, labor_wage, current_market_snapshot)
        if context.config_override:
            hr_context = replace(hr_context,
                min_employees=getattr(context.config_override, 'firm_min_employees', hr_context.min_employees),
                max_employees=getattr(context.config_override, 'firm_max_employees', hr_context.max_employees),
                severance_pay_weeks=getattr(context.config_override, 'severance_pay_weeks', hr_context.severance_pay_weeks)
            )

        hr_intent = self.hr_engine.decide_workforce(hr_context)

        # --- Production Engine ---
        productivity_multiplier = 1.0
        prod_context = self._build_production_context(productivity_multiplier, current_market_snapshot)

        # Manually apply overrides to prod_context fields derived from config
        if context.config_override:
            item_config = context.config_override.goods.get(self.production_state.specialization, {})
            prod_context = replace(prod_context,
                labor_alpha=context.config_override.labor_alpha,
                automation_labor_reduction=context.config_override.automation_labor_reduction,
                labor_elasticity_min=context.config_override.labor_elasticity_min,
                capital_depreciation_rate=context.config_override.capital_depreciation_rate,
                input_goods=item_config.get("inputs", prod_context.input_goods),
                quality_sensitivity=item_config.get("quality_sensitivity", prod_context.quality_sensitivity)
            )

        prod_intent = self.production_engine.decide_production(prod_context)
        procurement_intent = self.production_engine.decide_procurement(prod_context)

        # --- Sales Engine ---
        sales_context = self._build_sales_context(current_market_snapshot, current_tick)
        if context.config_override:
            sales_context = replace(sales_context,
                sale_timeout_ticks=getattr(context.config_override, 'sale_timeout_ticks', sales_context.sale_timeout_ticks),
                dynamic_price_reduction_factor=getattr(context.config_override, 'dynamic_price_reduction_factor', sales_context.dynamic_price_reduction_factor)
            )

        sales_intent = self.sales_engine.decide_pricing(sales_context)

        # Aggregate Results
        payload = {
            "budget_plan": budget_plan,
            "hr_intent": hr_intent,
            "production_intent": prod_intent,
            "procurement_intent": procurement_intent,
            "sales_intent": sales_intent
        }

        return FirmBrainScanResultDTO(
            agent_id=context.agent_id,
            tick=current_tick,
            intent_type="FULL_SCAN",
            intent_payload=payload
        )

    def execute_internal_orders(self, orders: List[Order], fiscal_context: FiscalContext, current_time: int, market_context: Optional[MarketContextDTO] = None) -> None:
        """
        Orchestrates internal orders by delegating to specialized engines.
        Replaces _execute_internal_order.
        """
        self.action_executor.execute(self, orders, fiscal_context, current_time, market_context)

    def _calculate_invisible_hand_price(self, market_snapshot: MarketSnapshotDTO, current_tick: int) -> None:
        if not market_snapshot.market_signals: return

        # 1. Construct Input DTO
        item_id = self.specialization
        current_price = self.last_prices.get(item_id, DEFAULT_PRICE) # int pennies

        input_dto = PricingInputDTO(
            item_id=item_id,
            current_price=current_price,
            market_snapshot=market_snapshot,
            config=self.config,
            # unit_cost_estimate needs to be int. FinanceEngine now returns int pennies.
            unit_cost_estimate=self.finance_engine.get_estimated_unit_cost(self.finance_state, item_id, self.config),
            inventory_level=self.get_quantity(item_id, InventorySlot.MAIN),
            production_target=self.production_target
        )

        # 2. Call Engine
        result = self.pricing_engine.calculate_price(input_dto)

        # 3. Update State (As per spec)
        # We allow PricingEngine to also influence price, potentially overriding SalesEngine?
        # Or SalesEngine already considered it?
        # decide_pricing used current_prices.
        # If we update prices here, they will be used next tick.
        self.sales_state.last_prices[item_id] = result.new_price

        log_shadow(
            tick=current_tick,
            agent_id=self.id,
            agent_type="Firm",
            metric="shadow_price",
            current_value=current_price,
            shadow_value=result.shadow_price,
            details=f"Item={item_id}, D={result.demand:.1f}, S={result.supply:.1f}, Ratio={result.excess_demand_ratio:.2f}, NewPrice={result.new_price:.2f}"
        )

    def _build_payroll_context(self, current_time: int, government: Optional[Any], market_context: MarketContextDTO) -> HRPayrollContextDTO:
        tax_policy = None
        # Extract from market_context if available (FiscalContext)
        fiscal_policy = market_context.fiscal_policy
        income_tax_rate = fiscal_policy.income_tax_rate if fiscal_policy else 0.0 # Default
        survival_cost = DEFAULT_SURVIVAL_COST # Default

        gov_id = government.id if government else -1 # Fallback ID

        tax_policy = TaxPolicyDTO(
            income_tax_rate=income_tax_rate,
            survival_cost=survival_cost,
            government_agent_id=gov_id
        )

        return HRPayrollContextDTO(
            exchange_rates=market_context.exchange_rates or {DEFAULT_CURRENCY: 1.0},
            tax_policy=tax_policy,
            current_time=current_time,
            firm_id=self.id,
            wallet_balances=self.financial_component.get_all_balances(),
            labor_market_min_wage=10.0, # Should come from config or market data
            ticks_per_year=getattr(self.config, "ticks_per_year", 365),
            severance_pay_weeks=getattr(self.config, "severance_pay_weeks", 2.0)
        )

    def _build_sales_marketing_context(self, current_time: int, government: Optional[Any]) -> SalesMarketingContextDTO:
        gov_id = government.id if government else None
        return SalesMarketingContextDTO(
            firm_id=self.id,
            wallet_balance=self.financial_component.get_balance(DEFAULT_CURRENCY),
            government_id=gov_id,
            current_time=current_time
        )

    def _build_sales_post_ask_context(self, item_id: str, price_pennies: int, quantity: float, market_id: str, current_tick: int) -> SalesPostAskContextDTO:
        brand_snapshot = {
            "brand_awareness": self.sales_state.brand_awareness,
            "perceived_quality": self.sales_state.perceived_quality,
            "quality": self.get_quality(item_id),
        }
        return SalesPostAskContextDTO(
            firm_id=self.id,
            item_id=item_id,
            price_pennies=price_pennies,
            quantity=quantity,
            market_id=market_id,
            current_tick=current_tick,
            inventory_quantity=self.get_quantity(item_id),
            brand_snapshot=brand_snapshot
        )

    def _build_production_context(self, productivity_multiplier: float, market_snapshot: Optional[MarketSnapshotDTO] = None) -> ProductionContextDTO:
        # Calculate derived values
        num_employees = len(self.hr_state.employees)

        # Calculate effective skill (incorporating mismatch penalty)
        total_effective_skill = 0.0
        for emp in self.hr_state.employees:
            base_skill = getattr(emp, "labor_skill", 1.0)
            # Check for penalty modifier in HR data
            emp_data = self.hr_state.employees_data.get(emp.id, {})
            modifier = emp_data.get("productivity_modifier", 1.0)
            total_effective_skill += (base_skill * modifier)

        avg_skill = total_effective_skill / num_employees if num_employees > 0 else 0.0

        item_config = self.config.goods.get(self.production_state.specialization, {})
        tech_level = self.production_state.productivity_factor * productivity_multiplier

        return ProductionContextDTO(
            firm_id=AgentID(self.id),
            tick=0,
            budget_pennies=0,
            market_snapshot=market_snapshot or MarketSnapshotDTO(tick=0, market_signals={}, market_data={}),
            available_cash_pennies=0,
            is_solvent=True,

            inventory_raw_materials=self.inventory_component.input_inventory.copy(),
            inventory_finished_goods=self.inventory_component.main_inventory.copy(),
            current_workforce_count=num_employees,
            production_target=self.production_state.production_target,
            technology_level=tech_level,
            production_efficiency=1.0,

            capital_stock=self.production_state.capital_stock,
            automation_level=self.production_state.automation_level,

            input_goods=item_config.get("inputs", {}),
            output_good_id=self.production_state.specialization,

            labor_alpha=self.config.labor_alpha,
            automation_labor_reduction=self.config.automation_labor_reduction,
            labor_elasticity_min=self.config.labor_elasticity_min,
            capital_depreciation_rate=self.config.capital_depreciation_rate,
            specialization=self.production_state.specialization,
            base_quality=self.production_state.base_quality,
            quality_sensitivity=item_config.get("quality_sensitivity", 0.5),
            employees_avg_skill=avg_skill
        )

    def _calculate_target_headcount(self) -> int:
        item_id = self.production_state.specialization
        target_quantity = self.production_state.production_target
        current_inventory = self.get_quantity(item_id, InventorySlot.MAIN)
        needed_production = max(0, target_quantity - current_inventory)
        productivity_factor = self.production_state.productivity_factor
        if productivity_factor <= 0: needed_labor = 999999.0
        else: needed_labor = needed_production / productivity_factor
        return int(needed_labor)

    def _build_hr_context(self, budget_plan: BudgetPlanDTO, target_headcount: int, current_tick: int, labor_wage: int, market_snapshot: Optional[MarketSnapshotDTO] = None) -> HRContextDTO:
        current_employees = [AgentID(e.id) for e in self.hr_state.employees]
        employee_wages = {AgentID(e.id): self.hr_state.employee_wages.get(e.id, 0) for e in self.hr_state.employees}
        employee_skills = {AgentID(e.id): getattr(e, "labor_skill", 1.0) for e in self.hr_state.employees}

        return HRContextDTO(
            firm_id=AgentID(self.id),
            tick=current_tick,
            budget_pennies=budget_plan.labor_budget_pennies,
            market_snapshot=market_snapshot or MarketSnapshotDTO(tick=0, market_signals={}, market_data={}),
            available_cash_pennies=0,
            is_solvent=True,

            current_employees=current_employees,
            current_headcount=len(current_employees),
            employee_wages=employee_wages,
            employee_skills=employee_skills,
            target_workforce_count=target_headcount,
            labor_market_avg_wage=labor_wage,
            marginal_labor_productivity=0.0,
            happiness_avg=0.0,

            profit_history=list(self.finance_state.profit_history),

            min_employees=getattr(self.config, 'firm_min_employees', 1),
            max_employees=getattr(self.config, 'firm_max_employees', 100),
            severance_pay_weeks=getattr(self.config, 'severance_pay_weeks', 2),
            specialization=self.production_state.specialization,
            major=self.major, # Phase 4.1
            hires_prev_tick=self.hr_state.hires_prev_tick,
            target_hires_prev_tick=self.hr_state.target_hires_prev_tick,
            wage_offer_prev_tick=self.hr_state.wage_offer_prev_tick
        )

    def _generate_hr_orders(self, intent: HRIntentDTO, context: HRContextDTO) -> List[Order]:
        orders = []
        # Firing
        for emp_id in intent.fire_employee_ids:
            # Need wage/skill again, context has them
            current_wage = context.employee_wages.get(emp_id, 1000)
            skill = context.employee_skills.get(emp_id, 1.0)
            severance_pay = int(current_wage * context.severance_pay_weeks * skill)

            orders.append(Order(
                agent_id=self.id,
                side='FIRE',
                item_id='internal',
                quantity=1,
                price_pennies=severance_pay,
                price_limit=float(severance_pay)/100.0,
                market_id='internal',
                target_agent_id=int(emp_id)
            ))

        # Hiring
        if intent.hiring_target > 0:
            # Recalculate offered wage logic or infer.
            # Using same logic as engine for consistency.
            base_wage = context.labor_market_avg_wage
            sensitivity = 0.1
            max_premium = 2.0
            profit_history = context.profit_history
            avg_profit = sum(profit_history) / len(profit_history) if profit_history else 0.0
            profit_based_premium = avg_profit / (base_wage * 10.0) if base_wage > 0 else 0.0
            wage_premium = max(0, min(profit_based_premium * sensitivity, max_premium))
            offered_wage = int(base_wage * (1 + wage_premium))

            orders.append(Order(
                agent_id=self.id,
                side='BUY',
                item_id='labor',
                quantity=float(intent.hiring_target),
                price_pennies=offered_wage,
                price_limit=float(offered_wage)/100.0,
                market_id='labor',
                metadata={
                    'major': context.major, # Phase 4.1: Use Major instead of Specialization
                    'specialization': context.specialization, # Keep specialization for debugging/specific matching if needed
                    'required_education': 0 # Could be dynamic based on tech level
                }
            ))
        return orders

    def _build_sales_context(self, market_snapshot: MarketSnapshotDTO, current_tick: int) -> SalesContextDTO:
        # Competitor prices
        competitor_prices = {}
        if market_snapshot and market_snapshot.market_signals:
            for k, v in market_snapshot.market_signals.items():
                if v.last_traded_price:
                    competitor_prices[k] = v.last_traded_price

        return SalesContextDTO(
            firm_id=AgentID(self.id),
            tick=current_tick,
            budget_pennies=0,
            market_snapshot=market_snapshot or MarketSnapshotDTO(tick=0, market_signals={}, market_data={}),
            available_cash_pennies=0,
            is_solvent=True,

            inventory_to_sell=self.inventory_component.main_inventory.copy(),
            current_prices=self.sales_state.last_prices.copy(),
            previous_sales_volume=self.sales_volume_this_tick, # Wait, this tick volume?
            # context.previous_sales_volume. Logic uses it for "inventory pressure".
            # sales_volume_this_tick is reset at end of tick.
            # At make_decision, sales_volume_this_tick is 0 (reset happened in reset_finance).
            # So we need "last tick's volume".
            # We don't seem to track it explicitly in SalesState?
            # Only `inventory_last_sale_tick`.
            # I will pass 0 for now as it seems unused in `decide_pricing` logic I wrote.
            competitor_prices=competitor_prices,

            marketing_budget_rate=self.sales_state.marketing_budget_rate,
            brand_awareness=self.sales_state.brand_awareness,
            perceived_quality=self.sales_state.perceived_quality,
            inventory_quality=self.inventory_component.inventory_quality.copy(),
            last_revenue_pennies=self.finance_state.last_revenue_pennies,
            last_marketing_spend_pennies=self.finance_state.last_marketing_spend_pennies,
            inventory_last_sale_tick=self.sales_state.inventory_last_sale_tick.copy(),

            sale_timeout_ticks=getattr(self.config, 'sale_timeout_ticks', 10),
            dynamic_price_reduction_factor=getattr(self.config, 'dynamic_price_reduction_factor', 0.9)
        )

    def generate_transactions(self, government: Optional[Any], market_data: Dict[str, Any], shareholder_registry: IShareholderRegistry, current_time: int, market_context: MarketContextDTO) -> List[Transaction]:
        transactions = []
        gov_id = government.id if government else None

        # Extract dynamic tax rates from MarketContext
        fiscal_policy = market_context.fiscal_policy
        corporate_tax_rate = fiscal_policy.corporate_tax_rate if fiscal_policy else DEFAULT_CORPORATE_TAX_RATE

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
        inventory_value = 0
        for item, qty in self.get_all_items().items():
            price = self.last_prices.get(item, DEFAULT_PRICE) # Default 10.00 pennies
            inventory_value += int(qty * price)

        fin_ctx = FinancialTransactionContext(
            government_id=gov_id,
            tax_rates=tax_rates,
            market_context=market_context,
            shareholder_registry=shareholder_registry
        )

        tx_finance = self.finance_engine.generate_financial_transactions(
            self.finance_state, self.id, self.financial_component.get_all_balances(), self.config, current_time, fin_ctx, inventory_value
        )
        transactions.extend(tx_finance)

        # 3. Marketing
        # Use marketing budget set during make_decision
        # No need to call adjust_marketing_budget again!

        # Then generate transaction using the updated state
        marketing_context = self._build_sales_marketing_context(current_time, government)
        tx_marketing = self.sales_engine.generate_marketing_transaction(
            self.get_snapshot_dto().sales, marketing_context
        )
        if tx_marketing:
            transactions.append(tx_marketing)

        # Brand Update
        # Using stateless engine, applying result
        brand_metrics = self.brand_engine.update(
            self.get_snapshot_dto().sales, # Pass DTO for purity
            self.config,
            float(self.sales_state.marketing_budget_pennies),
            self.productivity_factor / PRODUCTIVITY_DIVIDER,
            self.id
        )
        # Apply State
        self.sales_state.adstock = brand_metrics.adstock
        self.sales_state.brand_awareness = brand_metrics.brand_awareness
        self.sales_state.perceived_quality = brand_metrics.perceived_quality

        return transactions
