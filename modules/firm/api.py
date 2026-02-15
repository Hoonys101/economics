from __future__ import annotations
from typing import Protocol, Any, Optional, Dict, List, Literal
from dataclasses import dataclass, field

from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.dtos.department_dtos import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
from modules.system.api import MarketSnapshotDTO

# ==============================================================================
# 1. ARCHITECTURAL RESOLUTION: ASSET PROTOCOLS
# ==============================================================================

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

# ==============================================================================
# 3. ENGINE PROTOCOLS
# ==============================================================================

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


class IPricingEngine(Protocol):
    """
    Stateless engine for handling product pricing logic.
    """
    def calculate_price(self, input_dto: PricingInputDTO) -> PricingResultDTO:
        """
        Calculates the new price based on market signals and internal state.
        """
        ...


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
