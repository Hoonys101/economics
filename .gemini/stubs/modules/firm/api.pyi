from dataclasses import dataclass, field
from enum import Enum
from modules.common.enums import IndustryDomain
from modules.finance.api import IFinancialAgent
from modules.simulation.api import AgentID, IInventoryHandler
from modules.simulation.dtos.api import FinanceStateDTO as FinanceStateDTO, FirmConfigDTO as FirmConfigDTO, HRStateDTO as HRStateDTO, ProductionStateDTO as ProductionStateDTO, SalesStateDTO as SalesStateDTO
from modules.system.api import MarketContextDTO, MarketSnapshotDTO
from simulation.dtos.sales_dtos import MarketingAdjustmentResultDTO, SalesMarketingContextDTO, SalesPostAskContextDTO
from simulation.models import Order, Transaction
from typing import Any, Literal, Protocol

__all__ = ['ICollateralizableAsset', 'FirmSnapshotDTO', 'FirmStrategy', 'FirmBrainScanContextDTO', 'FirmBrainScanResultDTO', 'FinanceDecisionInputDTO', 'BudgetPlanDTO', 'HRDecisionInputDTO', 'HRDecisionOutputDTO', 'ProductionInputDTO', 'ProductionResultDTO', 'AssetManagementInputDTO', 'AssetManagementResultDTO', 'LiquidationExecutionDTO', 'LiquidationResultDTO', 'RDInputDTO', 'RDResultDTO', 'PricingInputDTO', 'PricingResultDTO', 'BrandMetricsDTO', 'DynamicPricingResultDTO', 'IBrainScanReady', 'BaseDepartmentContextDTO', 'ProductionContextDTO', 'ProductionIntentDTO', 'ProcurementIntentDTO', 'HRContextDTO', 'HRIntentDTO', 'SalesContextDTO', 'SalesIntentDTO', 'IFinanceEngine', 'IHREngine', 'IProductionEngine', 'IAssetManagementEngine', 'IPricingEngine', 'IRDEngine', 'ISalesEngine', 'IBrandEngine', 'IDepartmentEngine', 'IProductionDepartment', 'IHRDepartment', 'ISalesDepartment', 'IFirmComponent', 'IInventoryComponent', 'InventoryComponentConfigDTO', 'IFinancialComponent', 'FinancialComponentConfigDTO', 'FirmConfigDTO', 'FirmStateDTO', 'FinanceStateDTO', 'ProductionStateDTO', 'SalesStateDTO', 'HRStateDTO']

class ICollateralizableAsset(Protocol):
    """
    NEW DEFINITION: Interface for assets that can be locked, have liens placed
    against them, or be transferred as a whole unit (e.g., real estate).
    This isolates functionality from the original, aspirational IInventoryHandler.
    """
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Atomically places a lock on an asset, returns False if already locked."""
    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Releases a lock, returns False if not owned by the lock_owner_id."""
    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool:
        """Transfers ownership of the asset."""
    def add_lien(self, asset_id: Any, lien_details: Any) -> str | None:
        """Adds a lien to a property, returns lien_id on success."""
    def remove_lien(self, asset_id: Any, lien_id: str) -> bool:
        """Removes a lien from a property."""

class FirmStrategy(Enum):
    PROFIT_MAXIMIZATION = 'PROFIT_MAXIMIZATION'
    MARKET_SHARE = 'MARKET_SHARE'
    SURVIVAL = 'SURVIVAL'

@dataclass(frozen=True)
class FirmSnapshotDTO:
    """
    Immutable snapshot of a Firm's state, used as input for stateless engines.
    """
    id: int
    is_active: bool
    config: FirmConfigDTO
    finance: FinanceStateDTO
    production: ProductionStateDTO
    sales: SalesStateDTO
    hr: HRStateDTO
    strategy: FirmStrategy = ...

@dataclass(frozen=True)
class FirmBrainScanContextDTO:
    '''
    Context override for hypothetical Brain Scan simulations.
    Allows injecting "What-If" market conditions or configs.
    '''
    agent_id: AgentID
    current_tick: int
    market_snapshot_override: MarketSnapshotDTO | None = ...
    config_override: FirmConfigDTO | None = ...
    mock_responses: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class FirmBrainScanResultDTO:
    """
    The result of a Brain Scan simulation.
    Contains the strategic intent (Decision) the firm would make under the hypothetical context.
    """
    agent_id: AgentID
    tick: int
    intent_type: str
    intent_payload: Any
    predicted_outcome: dict[str, Any] | None = ...

@dataclass(frozen=True)
class BaseDepartmentContextDTO:
    """Base context shared by all departments."""
    firm_id: AgentID
    tick: int
    budget_pennies: int
    market_snapshot: MarketSnapshotDTO
    available_cash_pennies: int
    is_solvent: bool

@dataclass(frozen=True)
class ProductionContextDTO(BaseDepartmentContextDTO):
    """Context for Production Department."""
    inventory_raw_materials: dict[str, float]
    inventory_finished_goods: dict[str, float]
    current_workforce_count: int
    production_target: float
    technology_level: float
    production_efficiency: float
    capital_stock: float
    automation_level: float
    input_goods: dict[str, float]
    output_good_id: str
    labor_alpha: float
    automation_labor_reduction: float
    labor_elasticity_min: float
    capital_depreciation_rate: float
    specialization: str
    base_quality: float
    quality_sensitivity: float
    employees_avg_skill: float

@dataclass(frozen=True)
class ProductionIntentDTO:
    """Intent from Production Department."""
    target_production_quantity: float
    materials_to_use: dict[str, float]
    estimated_cost_pennies: int
    insufficient_materials: bool = ...
    capital_depreciation: int = ...
    automation_decay: float = ...
    quality: float = ...

@dataclass(frozen=True)
class ProcurementIntentDTO:
    """Intent for procurement (buying inputs) from Production Department."""
    purchase_orders: list[Order]

@dataclass(frozen=True)
class HRContextDTO(BaseDepartmentContextDTO):
    """Context for HR Department."""
    current_employees: list[AgentID]
    current_headcount: int
    employee_wages: dict[AgentID, int]
    employee_skills: dict[AgentID, float]
    target_workforce_count: int
    labor_market_avg_wage: int
    marginal_labor_productivity: float
    happiness_avg: float
    profit_history: list[int]
    min_employees: int
    max_employees: int
    severance_pay_weeks: int
    specialization: str
    major: IndustryDomain
    hires_prev_tick: int = ...
    target_hires_prev_tick: int = ...
    wage_offer_prev_tick: int = ...

@dataclass(frozen=True)
class HRIntentDTO:
    """Intent from HR Department."""
    hiring_target: int
    wage_updates: dict[AgentID, int]
    fire_employee_ids: list[AgentID] = field(default_factory=list)
    hiring_wage_offer: int = ...

@dataclass(frozen=True)
class SalesContextDTO(BaseDepartmentContextDTO):
    """Context for Sales Department."""
    inventory_to_sell: dict[str, float]
    current_prices: dict[str, int]
    previous_sales_volume: float
    competitor_prices: dict[str, int]
    marketing_budget_rate: float
    brand_awareness: float
    perceived_quality: float
    inventory_quality: dict[str, float]
    last_revenue_pennies: int
    last_marketing_spend_pennies: int
    inventory_last_sale_tick: dict[str, int]
    sale_timeout_ticks: int
    dynamic_price_reduction_factor: float

@dataclass(frozen=True)
class SalesIntentDTO:
    """Intent from Sales Department."""
    price_adjustments: dict[str, int]
    sales_orders: list[dict[str, Any]]
    marketing_spend_pennies: int = ...
    new_marketing_budget_rate: float = ...

@dataclass(frozen=True)
class FinanceDecisionInputDTO:
    """Input for FinanceEngine."""
    firm_snapshot: FirmSnapshotDTO
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    current_tick: int
    credit_rating: float = ...

@dataclass(frozen=True)
class BudgetPlanDTO:
    """Output from FinanceEngine. Determines constraints for other engines."""
    total_budget_pennies: int
    labor_budget_pennies: int
    capital_budget_pennies: int
    marketing_budget_pennies: int
    dividend_payout_pennies: int
    debt_repayment_pennies: int
    is_solvent: bool

@dataclass(frozen=True)
class HRDecisionInputDTO:
    """Input for HREngine."""
    firm_snapshot: FirmSnapshotDTO
    budget_plan: BudgetPlanDTO
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    current_tick: int
    labor_market_avg_wage: int = ...

@dataclass(frozen=True)
class HRDecisionOutputDTO:
    """Output from HREngine."""
    hiring_orders: list[Order]
    firing_ids: list[int]
    wage_updates: dict[int, int]
    target_headcount: int

@dataclass(frozen=True)
class ProductionInputDTO:
    """Input for the ProductionEngine."""
    firm_snapshot: FirmSnapshotDTO
    productivity_multiplier: float

@dataclass(frozen=True)
class ProductionResultDTO:
    """Result from the ProductionEngine."""
    success: bool
    quantity_produced: float
    quality: float
    specialization: str
    inputs_consumed: dict[str, float] = field(default_factory=dict)
    production_cost: int = ...
    capital_depreciation: int = ...
    automation_decay: float = ...
    error_message: str | None = ...

@dataclass(frozen=True)
class AssetManagementInputDTO:
    """Input for the AssetManagementEngine."""
    firm_snapshot: FirmSnapshotDTO
    investment_type: Literal['CAPEX', 'AUTOMATION']
    investment_amount: int

@dataclass(frozen=True)
class AssetManagementResultDTO:
    """Result from the AssetManagementEngine."""
    success: bool
    capital_stock_increase: int = ...
    automation_level_increase: float = ...
    actual_cost: int = ...
    message: str | None = ...

@dataclass(frozen=True)
class LiquidationExecutionDTO:
    """Input for liquidation calculation."""
    firm_snapshot: FirmSnapshotDTO
    current_tick: int

@dataclass(frozen=True)
class LiquidationResultDTO:
    """Result of liquidation calculation."""
    assets_returned: dict[str, int]
    inventory_to_remove: dict[str, float]
    capital_stock_to_write_off: int
    automation_level_to_write_off: float
    is_bankrupt: bool = ...

@dataclass(frozen=True)
class RDInputDTO:
    """Input for the R&D Engine."""
    firm_snapshot: FirmSnapshotDTO
    investment_amount: int
    current_time: int

@dataclass(frozen=True)
class RDResultDTO:
    """Result from the R&D Engine."""
    success: bool
    quality_improvement: float = ...
    productivity_multiplier_change: float = ...
    actual_cost: int = ...
    message: str | None = ...

@dataclass(frozen=True)
class PricingInputDTO:
    """Input for PricingEngine."""
    item_id: str
    current_price: int
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    unit_cost_estimate: int = ...
    inventory_level: float = ...
    production_target: float = ...

@dataclass(frozen=True)
class PricingResultDTO:
    """Result from PricingEngine."""
    new_price: int
    shadow_price: float
    demand: float
    supply: float
    excess_demand_ratio: float

@dataclass(frozen=True)
class BrandMetricsDTO:
    """Result from BrandEngine update."""
    adstock: float
    brand_awareness: float
    perceived_quality: float

@dataclass(frozen=True)
class DynamicPricingResultDTO:
    """Result from SalesEngine dynamic pricing."""
    orders: list[Order]
    price_updates: dict[str, int]

class IBrainScanReady(Protocol):
    """
    Protocol for agents that support Brain-Scan simulations (What-If analysis).
    """
    def brain_scan(self, context: FirmBrainScanContextDTO) -> FirmBrainScanResultDTO: ...

class IDepartmentEngine(Protocol):
    """
    Protocol for a stateless department engine.
    Must not hold reference to the parent firm.
    """

class IProductionDepartment(IDepartmentEngine, Protocol):
    def decide_production(self, context: ProductionContextDTO) -> ProductionIntentDTO: ...

class IHRDepartment(IDepartmentEngine, Protocol):
    def decide_workforce(self, context: HRContextDTO) -> HRIntentDTO: ...

class ISalesDepartment(IDepartmentEngine, Protocol):
    def decide_pricing(self, context: SalesContextDTO) -> SalesIntentDTO: ...

class IFinanceEngine(Protocol):
    """Stateless engine for financial planning."""
    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO: ...
    def get_estimated_unit_cost(self, finance_state: FinanceStateDTO, item_id: str, config: FirmConfigDTO) -> int:
        """Calculates estimated unit cost for an item."""
    def calculate_valuation(self, finance_state: FinanceStateDTO, balances: dict[str, int], config: FirmConfigDTO, inventory_value: int, capital_stock: int, context: MarketContextDTO | None) -> int: ...
    def generate_financial_transactions(self, finance_state: FinanceStateDTO, firm_id: int, balances: dict[str, int], config: FirmConfigDTO, current_time: int, context: Any, inventory_value: int) -> list[Transaction]:
        """
        Pure generation of financial transactions based on current state.
        Does NOT mutate state.
        """

class IHREngine(IHRDepartment, Protocol):
    """Stateless engine for human resources management."""
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO: ...
    def process_payroll(self, hr_state: HRStateDTO, context: Any, config: FirmConfigDTO) -> Any: ...

class IProductionEngine(IProductionDepartment, Protocol):
    """
    Stateless engine for handling the firm's production process.
    """
    def produce(self, input_dto: ProductionInputDTO) -> ProductionResultDTO:
        """
        Calculates production output based on labor, capital, and technology.
        Returns a DTO describing the result of the production cycle.
        """
    def decide_procurement(self, context: ProductionContextDTO) -> ProcurementIntentDTO:
        """
        Decides on procurement of raw materials.
        """

class IAssetManagementEngine(Protocol):
    """
    Stateless engine for handling investments in capital and automation.
    """
    def invest(self, input_dto: AssetManagementInputDTO) -> AssetManagementResultDTO:
        """
        Calculates the outcome of an investment in CAPEX or Automation.
        Returns a DTO describing the resulting state changes.
        """
    def calculate_liquidation(self, input_dto: LiquidationExecutionDTO) -> LiquidationResultDTO:
        """
        Calculates the result of liquidating the firm.
        """

class IPricingEngine(Protocol):
    """
    Stateless engine for handling product pricing logic.
    """
    def calculate_price(self, input_dto: PricingInputDTO) -> PricingResultDTO:
        """
        Calculates the new price based on market signals and internal state.
        """

class IRDEngine(Protocol):
    """
    Stateless engine for handling investments in Research and Development.
    """
    def research(self, input_dto: RDInputDTO) -> RDResultDTO:
        """
        Calculates the outcome of R&D spending.
        Returns a DTO describing improvements to quality or technology.
        """

class ISalesEngine(ISalesDepartment, Protocol):
    """
    Stateless Engine for Sales operations.
    Handles pricing, marketing, and order generation.
    """
    def post_ask(self, state: SalesStateDTO, context: SalesPostAskContextDTO) -> Order:
        """Posts an ask order to the market."""
    def adjust_marketing_budget(self, state: SalesStateDTO, market_context: MarketContextDTO, revenue_this_turn: int, last_revenue: int = 0, last_marketing_spend: int = 0) -> MarketingAdjustmentResultDTO:
        """Adjusts marketing budget based on ROI or simple heuristic."""
    def generate_marketing_transaction(self, state: SalesStateDTO, context: SalesMarketingContextDTO) -> Transaction | None:
        """Generates marketing spend transaction."""
    def check_and_apply_dynamic_pricing(self, state: SalesStateDTO, orders: list[Order], current_time: int, config: FirmConfigDTO | None = None, unit_cost_estimator: Any | None = None) -> DynamicPricingResultDTO:
        """Overrides prices in orders if dynamic pricing logic dictates. Returns new orders and price updates."""

class IBrandEngine(Protocol):
    """
    Stateless engine for managing firm brand equity.
    """
    def update(self, state: SalesStateDTO, config: FirmConfigDTO, marketing_spend: float, actual_quality: float, firm_id: int) -> BrandMetricsDTO:
        """Calculates updated brand metrics based on marketing spend and quality."""

class IFirmComponent(Protocol):
    """Base protocol for Firm components."""

@dataclass
class InventoryComponentConfigDTO:
    initial_inventory: dict[str, float] | None = ...

class IInventoryComponent(IInventoryHandler, IFirmComponent, Protocol):
    """
    Component responsible for managing physical goods.
    Encapsulates raw inventory dictionaries.
    """
    @property
    def main_inventory(self) -> dict[str, float]: ...
    @property
    def input_inventory(self) -> dict[str, float]: ...
    @property
    def inventory_quality(self) -> dict[str, float]: ...

@dataclass
class FinancialComponentConfigDTO:
    initial_balance: int = ...
    initial_shares: float = ...

class IFinancialComponent(IFinancialAgent, IFirmComponent, Protocol):
    """
    Component responsible for managing monetary assets (Wallet).
    Encapsulates Wallet instance.
    """
    @property
    def wallet_balance(self) -> int: ...
    def force_reset_wallet(self) -> None: ...

# Names in __all__ with no definition:
#   FirmStateDTO
