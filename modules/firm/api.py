from __future__ import annotations
from typing import Protocol, Any, Optional, Dict, List, Literal, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum

from modules.simulation.dtos.api import FirmConfigDTO, FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from modules.system.api import MarketSnapshotDTO, MarketContextDTO
from modules.simulation.api import IInventoryHandler
from modules.finance.api import IFinancialAgent
from simulation.models import Order, Transaction

# DTO Imports for Protocols
from simulation.dtos.sales_dtos import SalesPostAskContextDTO, SalesMarketingContextDTO, MarketingAdjustmentResultDTO

# ==============================================================================
# 1. ARCHITECTURAL RESOLUTION: ASSET PROTOCOLS
# ==============================================================================

@runtime_checkable
class ICollateralizableAsset(Protocol):
    """
    NEW DEFINITION: Interface for assets that can be locked, have liens placed
    against them, or be transferred as a whole unit (e.g., real estate).
    This isolates functionality from the original, aspirational IInventoryHandler.
    """
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Atomically places a lock on an asset, returns False if already locked."""
        ...

    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool:
        """Releases a lock, returns False if not owned by the lock_owner_id."""
        ...

    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool:
        """Transfers ownership of the asset."""
        ...

    def add_lien(self, asset_id: Any, lien_details: Any) -> Optional[str]:
        """Adds a lien to a property, returns lien_id on success."""
        ...

    def remove_lien(self, asset_id: Any, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

# ==============================================================================
# 2. DTO DEFINITIONS
# ==============================================================================

class FirmStrategy(Enum):
    PROFIT_MAXIMIZATION = "PROFIT_MAXIMIZATION"
    MARKET_SHARE = "MARKET_SHARE"
    SURVIVAL = "SURVIVAL"

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
    strategy: FirmStrategy = FirmStrategy.PROFIT_MAXIMIZATION

# --- Finance Engine DTOs ---

@dataclass(frozen=True)
class FinanceDecisionInputDTO:
    """Input for FinanceEngine."""
    firm_snapshot: FirmSnapshotDTO
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    current_tick: int
    credit_rating: float = 0.0

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

# --- HR Engine DTOs ---

@dataclass(frozen=True)
class HRDecisionInputDTO:
    """Input for HREngine."""
    firm_snapshot: FirmSnapshotDTO
    budget_plan: BudgetPlanDTO
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    current_tick: int
    labor_market_avg_wage: int = 1000 # Pennies

@dataclass(frozen=True)
class HRDecisionOutputDTO:
    """Output from HREngine."""
    hiring_orders: List[Order]
    firing_ids: List[int]
    wage_updates: Dict[int, int]
    target_headcount: int

# --- Production Engine DTOs ---

@dataclass(frozen=True)
class ProductionInputDTO:
    """Input for the ProductionEngine."""
    firm_snapshot: FirmSnapshotDTO
    productivity_multiplier: float # From external factors like technology
    # Legacy fields support (optional, or mapped)
    # The spec uses firm_snapshot, but ProductionEngine logic needs specific inputs.
    # We will rely on firm_snapshot to provide state data.

@dataclass(frozen=True)
class ProductionResultDTO:
    """Result from the ProductionEngine."""
    success: bool
    quantity_produced: float
    quality: float
    specialization: str
    inputs_consumed: Dict[str, float] = field(default_factory=dict)
    production_cost: int = 0 # MIGRATION: int pennies
    capital_depreciation: int = 0 # MIGRATION: int pennies (monetary value lost)

    automation_decay: float = 0.0
    error_message: Optional[str] = None

# --- Asset Management Engine DTOs ---

@dataclass(frozen=True)
class AssetManagementInputDTO:
    """Input for the AssetManagementEngine."""
    firm_snapshot: FirmSnapshotDTO
    investment_type: Literal["CAPEX", "AUTOMATION"]
    investment_amount: int # MIGRATION: int pennies

@dataclass(frozen=True)
class AssetManagementResultDTO:
    """Result from the AssetManagementEngine."""
    success: bool
    capital_stock_increase: int = 0 # MIGRATION: int pennies
    automation_level_increase: float = 0.0
    actual_cost: int = 0 # MIGRATION: int pennies
    message: Optional[str] = None

# --- Liquidation DTOs (Asset Management) ---

@dataclass(frozen=True)
class LiquidationExecutionDTO:
    """Input for liquidation calculation."""
    firm_snapshot: FirmSnapshotDTO
    current_tick: int

@dataclass(frozen=True)
class LiquidationResultDTO:
    """Result of liquidation calculation."""
    assets_returned: Dict[str, int]
    inventory_to_remove: Dict[str, float]
    capital_stock_to_write_off: int # MIGRATION: int pennies
    automation_level_to_write_off: float
    is_bankrupt: bool = True

# --- R&D Engine DTOs ---

@dataclass(frozen=True)
class RDInputDTO:
    """Input for the R&D Engine."""
    firm_snapshot: FirmSnapshotDTO
    investment_amount: int # MIGRATION: int pennies
    current_time: int

@dataclass(frozen=True)
class RDResultDTO:
    """Result from the R&D Engine."""
    success: bool
    quality_improvement: float = 0.0
    productivity_multiplier_change: float = 1.0 # Multiplier (e.g. 1.05 for 5% increase)
    actual_cost: int = 0 # MIGRATION: int pennies
    message: Optional[str] = None

# --- Pricing Engine DTOs ---

@dataclass(frozen=True)
class PricingInputDTO:
    """Input for PricingEngine."""
    item_id: str
    current_price: int # MIGRATION: int pennies
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    unit_cost_estimate: int = 0 # MIGRATION: int pennies
    inventory_level: float = 0.0
    production_target: float = 0.0

@dataclass(frozen=True)
class PricingResultDTO:
    """Result from PricingEngine."""
    new_price: int # MIGRATION: int pennies
    shadow_price: float # Shadow price can remain float for analysis? Or int?
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
    orders: List[Order]
    price_updates: Dict[str, int] # item_id -> new_price_pennies

# ==============================================================================
# 3. ENGINE PROTOCOLS
# ==============================================================================

@runtime_checkable
class IFinanceEngine(Protocol):
    """Stateless engine for financial planning."""
    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO:
        ...

    def get_estimated_unit_cost(self, finance_state: Any, item_id: str, config: FirmConfigDTO) -> int:
         """Calculates estimated unit cost for an item."""
         ...

    def record_expense(self, finance_state: Any, amount: int, currency: Any) -> None:
         ...

    def calculate_valuation(self, finance_state: Any, balances: Any, config: Any, inventory_value: int, capital_stock: int, context: Any) -> int:
        ...

    def generate_financial_transactions(self, finance_state: Any, firm_id: int, balances: Any, config: Any, current_time: int, context: Any, inventory_value: int) -> List[Transaction]:
        ...

@runtime_checkable
class IHREngine(Protocol):
    """Stateless engine for human resources management."""
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        ...

    def process_payroll(self, hr_state: Any, context: Any, config: Any) -> Any:
        ...

    def finalize_firing(self, hr_state: Any, employee_id: int) -> None:
        ...

@runtime_checkable
class IProductionEngine(Protocol):
    """
    Stateless engine for handling the firm's production process.
    """
    def produce(self, input_dto: ProductionInputDTO) -> ProductionResultDTO:
        """
        Calculates production output based on labor, capital, and technology.
        Returns a DTO describing the result of the production cycle.
        """
        ...


@runtime_checkable
class IAssetManagementEngine(Protocol):
    """
    Stateless engine for handling investments in capital and automation.
    """
    def invest(self, input_dto: AssetManagementInputDTO) -> AssetManagementResultDTO:
        """
        Calculates the outcome of an investment in CAPEX or Automation.
        Returns a DTO describing the resulting state changes.
        """
        ...

    def calculate_liquidation(self, input_dto: LiquidationExecutionDTO) -> LiquidationResultDTO:
        """
        Calculates the result of liquidating the firm.
        """
        ...


@runtime_checkable
class IPricingEngine(Protocol):
    """
    Stateless engine for handling product pricing logic.
    """
    def calculate_price(self, input_dto: PricingInputDTO) -> PricingResultDTO:
        """
        Calculates the new price based on market signals and internal state.
        """
        ...


@runtime_checkable
class IRDEngine(Protocol):
    """
    Stateless engine for handling investments in Research and Development.
    """
    def research(self, input_dto: RDInputDTO) -> RDResultDTO:
        """
        Calculates the outcome of R&D spending.
        Returns a DTO describing improvements to quality or technology.
        """
        ...

@runtime_checkable
class ISalesEngine(Protocol):
    """
    Stateless Engine for Sales operations.
    Handles pricing, marketing, and order generation.
    """
    def post_ask(self, state: Any, context: SalesPostAskContextDTO) -> Order:
        """Posts an ask order to the market."""
        ...

    def adjust_marketing_budget(self, state: Any, market_context: MarketContextDTO, revenue_this_turn: int, last_revenue: int=0, last_marketing_spend: int=0) -> MarketingAdjustmentResultDTO:
        """Adjusts marketing budget based on ROI or simple heuristic."""
        ...

    def generate_marketing_transaction(self, state: Any, context: SalesMarketingContextDTO) -> Optional[Transaction]:
        """Generates marketing spend transaction."""
        ...

    def check_and_apply_dynamic_pricing(self, state: Any, orders: List[Order], current_time: int, config: Optional[FirmConfigDTO]=None, unit_cost_estimator: Optional[Any]=None) -> DynamicPricingResultDTO:
        """Overrides prices in orders if dynamic pricing logic dictates. Returns new orders and price updates."""
        ...

@runtime_checkable
class IBrandEngine(Protocol):
    """
    Stateless engine for managing firm brand equity.
    """
    def update(
        self,
        state: Any,
        config: FirmConfigDTO,
        marketing_spend: float,
        actual_quality: float,
        firm_id: int
    ) -> BrandMetricsDTO:
        """Calculates updated brand metrics based on marketing spend and quality."""
        ...

# ==============================================================================
# 4. COMPONENT PROTOCOLS (NEW)
# ==============================================================================

@runtime_checkable
class IFirmComponent(Protocol):
    """Base protocol for Firm components."""
    def attach(self, owner: Any) -> None: ...

@dataclass
class InventoryComponentConfigDTO:
    initial_inventory: Optional[Dict[str, float]] = None

@runtime_checkable
class IInventoryComponent(IInventoryHandler, IFirmComponent, Protocol):
    """
    Component responsible for managing physical goods.
    Encapsulates raw inventory dictionaries.
    """
    @property
    def main_inventory(self) -> Dict[str, float]: ...

    @property
    def input_inventory(self) -> Dict[str, float]: ...

    @property
    def inventory_quality(self) -> Dict[str, float]: ...

@dataclass
class FinancialComponentConfigDTO:
    initial_balance: int = 0
    initial_shares: float = 1000.0

@runtime_checkable
class IFinancialComponent(IFinancialAgent, IFirmComponent, Protocol):
    """
    Component responsible for managing monetary assets (Wallet).
    Encapsulates Wallet instance.
    """
    @property
    def wallet_balance(self) -> int: ...

    def force_reset_wallet(self) -> None: ...

# Re-exporting existing DTOs for completeness in this refactor context
__all__ = [
    'ICollateralizableAsset',
    'FirmSnapshotDTO',
    'FirmStrategy',
    'FinanceDecisionInputDTO',
    'BudgetPlanDTO',
    'HRDecisionInputDTO',
    'HRDecisionOutputDTO',
    'ProductionInputDTO',
    'ProductionResultDTO',
    'AssetManagementInputDTO',
    'AssetManagementResultDTO',
    'LiquidationExecutionDTO',
    'LiquidationResultDTO',
    'RDInputDTO',
    'RDResultDTO',
    'PricingInputDTO',
    'PricingResultDTO',
    'BrandMetricsDTO',
    'DynamicPricingResultDTO',
    'IFinanceEngine',
    'IHREngine',
    'IProductionEngine',
    'IAssetManagementEngine',
    'IPricingEngine',
    'IRDEngine',
    'ISalesEngine',
    'IBrandEngine',
    'IFirmComponent',
    'IInventoryComponent',
    'InventoryComponentConfigDTO',
    'IFinancialComponent',
    'FinancialComponentConfigDTO',
    'FirmConfigDTO',
    'FirmStateDTO',
    'FinanceStateDTO',
    'ProductionStateDTO',
    'SalesStateDTO',
    'HRStateDTO'
]
