from _typeshed import Incomplete
from modules.common.financial.api import IFinancialAgent
from modules.common.financial.dtos import Claim, MoneyDTO as MoneyDTO
from modules.common.interfaces import IPropertyOwner
from modules.finance.api import EquityStake, ICreditFrozen, IFinancialFirm, ILiquidatable, ISalesTracker, IShareholderRegistry as IShareholderRegistry, InsufficientFundsError as InsufficientFundsError, LiquidationContext as LiquidationContext
from modules.finance.wallet.wallet import Wallet as Wallet
from modules.firm.api import AssetManagementInputDTO as AssetManagementInputDTO, AssetManagementResultDTO as AssetManagementResultDTO, BudgetPlanDTO as BudgetPlanDTO, FirmBrainScanContextDTO as FirmBrainScanContextDTO, FirmBrainScanResultDTO, FirmSnapshotDTO, HRDecisionInputDTO as HRDecisionInputDTO, HRDecisionOutputDTO as HRDecisionOutputDTO, HRIntentDTO as HRIntentDTO, IAssetManagementEngine, IBankruptcyHandler as IBankruptcyHandler, IBrainScanReady, IBrandEngine, IBudgetGatekeeper as IBudgetGatekeeper, IFinanceEngine, IFinancialComponent as IFinancialComponent, IHREngine, IInventoryComponent as IInventoryComponent, IPricingEngine, IProductionEngine, IRDEngine, ISalesEngine, LiquidationResultDTO as LiquidationResultDTO, PricingResultDTO as PricingResultDTO, ProductionInputDTO as ProductionInputDTO, ProductionIntentDTO as ProductionIntentDTO, ProductionResultDTO as ProductionResultDTO, RDInputDTO as RDInputDTO, RDResultDTO as RDResultDTO, SalesIntentDTO as SalesIntentDTO
from modules.firm.constants import INSIGHT_BOOST_FACTOR as INSIGHT_BOOST_FACTOR, INSIGHT_DECAY_RATE as INSIGHT_DECAY_RATE, INSIGHT_ERROR_THRESHOLD as INSIGHT_ERROR_THRESHOLD
from modules.government.political.api import ILobbyist, LobbyingEffortDTO, PaymentRequestDTO
from modules.inventory.manager import InventoryManager as InventoryManager
from modules.memory.api import MemoryV2Interface as MemoryV2Interface
from modules.simulation.api import AgentCoreConfigDTO as AgentCoreConfigDTO, AgentSensorySnapshotDTO as AgentSensorySnapshotDTO, AgentStateDTO, IConfigurable, IDecisionEngine as IDecisionEngine, IInventoryHandler, IOrchestratorAgent, ISensoryDataProvider, InventorySlot, LiquidationConfigDTO
from modules.simulation.dtos.api import FirmConfigDTO as FirmConfigDTO, FirmStateDTO, IFirmStateProvider
from modules.system.api import CurrencyCode as CurrencyCode, ICurrencyHolder, MarketContextDTO
from simulation.agents.government import Government as Government
from simulation.ai.enums import Personality as Personality
from simulation.ai.firm_system2_planner import FirmSystem2Planner as FirmSystem2Planner
from simulation.components.engines.asset_management_engine import AssetManagementEngine as AssetManagementEngine
from simulation.components.engines.finance_engine import FinanceEngine as FinanceEngine
from simulation.components.engines.hr_engine import HREngine as HREngine
from simulation.components.engines.production_engine import ProductionEngine as ProductionEngine
from simulation.components.engines.rd_engine import RDEngine as RDEngine
from simulation.components.engines.real_estate_component import RealEstateUtilizationComponent as RealEstateUtilizationComponent
from simulation.components.engines.sales_engine import SalesEngine as SalesEngine
from simulation.components.state.firm_state_models import FinanceState as FinanceState, HRState as HRState, ProductionState as ProductionState, SalesState as SalesState
from simulation.core_agents import Household as Household
from simulation.decisions.base_decision_engine import BaseDecisionEngine as BaseDecisionEngine
from simulation.dtos import DecisionContext as DecisionContext, DecisionInputDTO as DecisionInputDTO, FiscalContext as FiscalContext
from simulation.dtos.context_dtos import FinancialTransactionContext as FinancialTransactionContext, PayrollProcessingContext as PayrollProcessingContext, SalesContext as SalesContext
from simulation.dtos.hr_dtos import HRPayrollContextDTO as HRPayrollContextDTO, TaxPolicyDTO as TaxPolicyDTO
from simulation.dtos.sales_dtos import SalesMarketingContextDTO as SalesMarketingContextDTO, SalesPostAskContextDTO as SalesPostAskContextDTO
from simulation.dtos.scenario import StressScenarioConfig as StressScenarioConfig
from simulation.finance.api import ISettlementSystem as ISettlementSystem
from simulation.loan_market import LoanMarket as LoanMarket
from simulation.markets.order_book_market import OrderBookMarket as OrderBookMarket
from simulation.markets.stock_market import StockMarket as StockMarket
from simulation.models import Order as Order, Transaction as Transaction
from simulation.systems.api import ILearningAgent as ILearningAgent, LearningUpdateContext as LearningUpdateContext
from simulation.systems.tech.api import FirmTechInfoDTO as FirmTechInfoDTO
from typing import Any, override

logger: Incomplete

class Firm(ILearningAgent, IFinancialFirm, IFinancialAgent, ILiquidatable, IOrchestratorAgent, ICreditFrozen, IInventoryHandler, ICurrencyHolder, ISensoryDataProvider, IConfigurable, IPropertyOwner, IFirmStateProvider, ISalesTracker, IBrainScanReady, ILobbyist):
    """
    Firm Agent (Orchestrator).
    Manages state and delegates logic to stateless engines.
    Refactored to Composition (No BaseAgent).
    """
    age: int
    sales_volume_this_tick: float
    decision_engine: Incomplete
    id: Incomplete
    name: Incomplete
    logger: Incomplete
    memory_v2: Incomplete
    value_orientation: Incomplete
    needs: Incomplete
    inventory_component: Incomplete
    financial_component: Incomplete
    is_active: bool
    config: Incomplete
    hr_state: Incomplete
    finance_state: Incomplete
    production_state: Incomplete
    sales_state: Incomplete
    hr_engine: IHREngine
    finance_engine: IFinanceEngine
    production_engine: IProductionEngine
    sales_engine: ISalesEngine
    asset_management_engine: IAssetManagementEngine
    rd_engine: IRDEngine
    brand_engine: IBrandEngine
    pricing_engine: IPricingEngine
    action_executor: Incomplete
    budget_gatekeeper: IBudgetGatekeeper
    bankruptcy_handler: IBankruptcyHandler
    major: Incomplete
    personality: Incomplete
    real_estate_utilization_component: Incomplete
    market_insight: Incomplete
    def __init__(self, core_config: AgentCoreConfigDTO, engine: IDecisionEngine, specialization: str, productivity_factor: float, config_dto: FirmConfigDTO, initial_inventory: dict[str, float] | None = None, loan_market: LoanMarket | None = None, sector: str = 'FOOD', personality: Personality | None = None) -> None: ...
    def get_liquidation_config(self) -> LiquidationConfigDTO:
        """
        Implements IConfigurable.get_liquidation_config.
        Extracts liquidation parameters from the internal config DTO.
        """
    def get_core_config(self) -> AgentCoreConfigDTO: ...
    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO: ...
    def get_current_state(self) -> AgentStateDTO: ...
    def load_state(self, state: AgentStateDTO) -> None: ...
    @property
    def wallet(self) -> Wallet: ...
    def get_balance(self, currency: CurrencyCode = ...) -> int:
        """Returns the current balance for the specified currency."""
    @property
    def balance_pennies(self) -> int:
        """Returns the balance in the default currency (pennies)."""
    def get_all_balances(self) -> dict[CurrencyCode, int]:
        """Returns a copy of all currency balances."""
    def get_assets_by_currency(self) -> dict[CurrencyCode, int]:
        """Alias for get_all_balances required by ICurrencyHolder."""
    @property
    def total_wealth(self) -> int:
        """Returns the total wealth in default currency estimation."""
    def get_liquid_assets(self, currency: CurrencyCode = 'USD') -> int:
        """Returns liquid assets in pennies (int)."""
    def get_total_debt(self) -> int:
        """Returns total debt in pennies (int)."""
    def deposit(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Public deposit implementation."""
    def withdraw(self, amount_pennies: int, currency: CurrencyCode = ...) -> None:
        """Public withdraw implementation."""
    @property
    def credit_frozen_until_tick(self) -> int: ...
    @credit_frozen_until_tick.setter
    def credit_frozen_until_tick(self, value: int) -> None: ...
    @property
    def specialization(self) -> str: ...
    @specialization.setter
    def specialization(self, value: str): ...
    @property
    def productivity_factor(self) -> float: ...
    @productivity_factor.setter
    def productivity_factor(self, value: float): ...
    @property
    def current_production(self) -> float: ...
    @current_production.setter
    def current_production(self, value: float): ...
    @property
    def production_target(self) -> float: ...
    @production_target.setter
    def production_target(self, value: float): ...
    @property
    def capital_stock(self) -> float: ...
    @capital_stock.setter
    def capital_stock(self, value: float): ...
    @property
    def automation_level(self) -> float: ...
    @automation_level.setter
    def automation_level(self, value: float): ...
    @property
    def is_bankrupt(self) -> bool: ...
    @is_bankrupt.setter
    def is_bankrupt(self, value: bool): ...
    @property
    def valuation(self) -> int: ...
    @valuation.setter
    def valuation(self, value: int): ...
    @property
    def total_shares(self) -> float: ...
    @total_shares.setter
    def total_shares(self, value: float): ...
    @property
    def treasury_shares(self) -> float: ...
    @treasury_shares.setter
    def treasury_shares(self, value: float): ...
    @property
    def dividend_rate(self) -> float: ...
    @dividend_rate.setter
    def dividend_rate(self, value: float): ...
    @property
    def marketing_budget(self) -> float: ...
    @marketing_budget.setter
    def marketing_budget(self, value: float): ...
    @property
    def last_prices(self) -> dict[str, float]: ...
    @property
    def research_history(self) -> dict[str, Any]: ...
    @property
    def inventory_quality(self) -> dict[str, float]: ...
    @property
    def input_inventory(self) -> dict[str, float]:
        """Facade property for backward compatibility during transition."""
    @property
    def base_quality(self) -> float: ...
    @base_quality.setter
    def base_quality(self, value: float): ...
    @property
    def sector(self) -> str: ...
    @property
    def has_bailout_loan(self) -> bool: ...
    @has_bailout_loan.setter
    def has_bailout_loan(self, value: bool): ...
    @property
    def total_debt(self) -> int: ...
    @total_debt.setter
    def total_debt(self, value: int): ...
    @property
    def total_debt_pennies(self) -> int:
        """Alias for total_debt to satisfy IFinancialFirm."""
    @property
    def capital_stock_units(self) -> int:
        """Capital stock quantity in units."""
    @property
    def inventory_value_pennies(self) -> int:
        """Total value of all inventory in pennies."""
    @property
    def monthly_wage_bill_pennies(self) -> int:
        """Total monthly wage bill estimate."""
    @property
    def retained_earnings_pennies(self) -> int:
        """Total retained earnings."""
    @property
    def average_profit_pennies(self) -> int:
        """The average profit over the relevant history in pennies."""
    @property
    def inventory_last_sale_tick(self) -> dict[str, int]: ...
    @property
    def prev_awareness(self) -> float: ...
    @prev_awareness.setter
    def prev_awareness(self, value: float): ...
    @property
    def prev_avg_quality(self) -> float: ...
    @prev_avg_quality.setter
    def prev_avg_quality(self, value: float): ...
    @property
    def last_revenue(self) -> int: ...
    @property
    def revenue_this_turn(self) -> dict[CurrencyCode, int]: ...
    @property
    def expenses_this_tick(self) -> dict[CurrencyCode, int]: ...
    @property
    def cost_this_turn(self) -> dict[CurrencyCode, int]: ...
    def get_market_cap(self, stock_price: float | None = None) -> int:
        """
        Calculates market capitalization in pennies.
        If stock_price is provided (dollars), calculates based on outstanding shares.
        If not provided, falls back to intrinsic valuation (valuation_pennies).
        """
    def get_financial_snapshot(self) -> dict[str, Any]:
        """
        Returns a financial snapshot for reporting.
        Implements expected interface for EconomicIndicatorTracker.
        """
    def calculate_valuation(self) -> int:
        """
        Calculates and updates firm valuation.
        Delegates to FinanceEngine.
        """
    def get_book_value_per_share(self) -> float:
        """
        Calculates Book Value per Share (pennies) based on liquid assets and debt.
        Note: Excludes non-liquid assets (Capital/Inventory) to match legacy test expectations.
        Returns float.
        """
    def reset_finance(self) -> None:
        """Resets finance counters for the next tick."""
    def reset(self) -> None:
        """
        Resets the firm's state for the next simulation tick.
        Clears temporary counters and prepares for new decisions.
        """
    def init_ipo(self, stock_market: StockMarket):
        """Register firm in stock market order book."""
    def record_sale(self, item_id: str, quantity: float, current_tick: int) -> None: ...
    def record_revenue(self, amount: int, currency: CurrencyCode = ...) -> None:
        """
        Records revenue for the current turn.
        Required by GoodsTransactionHandler.
        """
    def record_expense(self, amount: int, currency: CurrencyCode = ...) -> None:
        """
        Records expense for the current tick.
        Required by GoodsTransactionHandler.
        """
    def get_all_claims(self, ctx: LiquidationContext) -> list[Claim]:
        """
        Implements ILiquidatable.get_all_claims.
        Delegates to specialized helpers to gather all claims.
        """
    def get_equity_stakes(self, ctx: LiquidationContext) -> list[EquityStake]:
        """
        Implements ILiquidatable.get_equity_stakes.
        Uses the Shareholder Registry to get ownership data.
        """
    def liquidate_assets(self, current_tick: int = -1) -> dict[CurrencyCode, int]:
        """Liquidate assets using Protocol Purity and AssetManagementEngine."""
    @override
    def add_item(self, item_id: str, quantity: float, transaction_id: str | None = None, quality: float = 1.0, slot: InventorySlot = ...) -> bool:
        """
        Delegates to InventoryComponent, supporting strict slot-based inventory management (MAIN vs INPUT).
        """
    @override
    def remove_item(self, item_id: str, quantity: float, transaction_id: str | None = None, slot: InventorySlot = ...) -> bool:
        """
        Delegates to InventoryComponent, supporting strict slot-based inventory management.
        """
    @override
    def get_quantity(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    @override
    def get_quality(self, item_id: str, slot: InventorySlot = ...) -> float: ...
    @override
    def get_all_items(self, slot: InventorySlot = ...) -> dict[str, float]:
        """Returns a copy of the inventory."""
    @override
    def clear_inventory(self, slot: InventorySlot = ...) -> None:
        """Clears the inventory."""
    def post_ask(self, item_id: str, price: float | int, quantity: float, market: OrderBookMarket, current_tick: int) -> Order: ...
    def calculate_brand_premium(self, market_data: dict[str, Any]) -> float: ...
    def get_snapshot_dto(self) -> FirmSnapshotDTO:
        """Helper to create FirmSnapshotDTO for engines."""
    def produce(self, current_time: int, technology_manager: Any | None = None, effects_queue: list[dict[str, Any]] | None = None) -> None: ...
    @override
    def get_agent_data(self) -> dict[str, Any]:
        """AI Data Provider."""
    def get_state_dto(self) -> FirmStateDTO: ...
    def get_pre_state_data(self) -> dict[str, Any]: ...
    def get_tech_info(self) -> FirmTechInfoDTO: ...
    @override
    def make_decision(self, input_dto: DecisionInputDTO) -> tuple[list[Order], Any]: ...
    @override
    def brain_scan(self, context: FirmBrainScanContextDTO) -> FirmBrainScanResultDTO:
        """
        Executes a hypothetical decision-making cycle without side effects.
        Implements IBrainScanReady.
        """
    def execute_internal_orders(self, orders: list[Order], fiscal_context: FiscalContext, current_time: int, market_context: MarketContextDTO | None = None) -> None:
        """
        Orchestrates internal orders by delegating to specialized engines.
        Replaces _execute_internal_order.
        """
    def generate_transactions(self, government: Any | None, market_data: dict[str, Any], shareholder_registry: IShareholderRegistry, current_time: int, market_context: MarketContextDTO) -> list[Transaction]:
        """
        Wave 3 Implementation: Intent -> Gatekeeper -> Execution Pipeline.
        """
    def formulate_lobbying_effort(self, current_tick: int, government_state: Any) -> tuple[LobbyingEffortDTO, PaymentRequestDTO] | None: ...
