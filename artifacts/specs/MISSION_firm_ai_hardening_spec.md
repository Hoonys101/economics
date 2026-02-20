# Design Document: Firm Refactor & AI Hardening

## 1. Introduction

-   **Purpose**: To align the `Firm` agent and its components with the **Stateless Engine & Orchestrator (SEO)** pattern by removing legacy stateful coupling (`.attach()`), and to harden the System 2 AI Planner (`FirmSystem2Planner`) against debt blindness.
-   **Scope**:
    -   Refactor `InventoryComponent` and `FinancialComponent` interfaces and implementations.
    -   Update `Firm` agent initialization and state snapshotting.
    -   Enhance `FirmSystem2Planner` to incorporate debt service and leverage ratios into NPV calculations.
    -   Update `FinanceStateDTO` to carry necessary debt context.
-   **Goals**:
    -   **Decoupling**: Components should not hold references to their owner (`self.parent`).
    -   **Reliability**: AI strategic planning must respect financial reality (debt obligations), preventing "Intent Spam" and liquidity traps.
    -   **Compliance**: Satisfy `TD-ARCH-FIRM-COUP` and `TD-AI-DEBT-AWARE`.

## 2. System Architecture (High-Level)

### 2.1. Component Decoupling (SEO Pattern)
The `IFirmComponent` protocol currently enforces a bidirectional link via `attach(self, owner)`. This violates the SEO pattern where components should be self-contained data managers or stateless logic providers.

-   **Change**: Remove `attach()` from `IFirmComponent`.
-   **Impact**: `Firm` agent will instantiate components but will NOT pass itself to them. Components will operate strictly on the data they own or arguments passed to their methods.

### 2.2. AI Debt Awareness
The `FirmSystem2Planner` currently projects future cash flows based solely on revenue and operating costs, ignoring the cost of capital (interest) and principal repayments.

-   **Change**: Inject `total_debt_pennies` and `average_interest_rate` into the AI's decision context via `FinanceStateDTO`.
-   **Logic**:
    -   `Free Cash Flow (FCF)` = `Revenue` - `Expenses` - `Debt Service`.
    -   `NPV` calculation will discount these FCFs.
    -   Apply a **Leverage Penalty** to the "Hurdle Rate" for new investments if `Debt/Equity` ratio is high.

## 3. Detailed Design

### 3.1. API Updates (`modules/firm/api.py`)

#### 3.1.1. Protocol Update: `IFirmComponent`
```python
@runtime_checkable
class IFirmComponent(Protocol):
    """Base protocol for Firm components."""
    # REMOVED: def attach(self, owner: Any) -> None: ...
    pass
```

#### 3.1.2. DTO Update: `FinanceStateDTO`
We need to ensure the `FinanceStateDTO` carries sufficient information for the AI to calculate debt service.

```python
@dataclass(frozen=True)
class FinanceStateDTO:
    # ... existing fields ...
    total_debt_pennies: int
    average_interest_rate: float # Weighted average interest rate on outstanding debt
```

### 3.2. Implementation: Component Refactor

-   **`modules/agent_framework/components/inventory_component.py`**: Remove `attach` method and `self.owner_id` usage if it relies on the parent object. (The current implementation stores `owner_id` string in `__init__`, which is fine, but `attach` is no-op or sets parent. We remove `attach`).
-   **`modules/agent_framework/components/financial_component.py`**: Remove `attach` method.

### 3.3. Implementation: Firm Agent (`simulation/firms.py`)

-   **Initialization**: Remove `self.inventory_component.attach(self)` and `self.financial_component.attach(self)`.
-   **Snapshotting (`get_snapshot_dto`)**:
    -   Populate the new fields in `FinanceStateDTO`.
    -   `total_debt_pennies`: Already available in `self.finance_state`.
    -   `average_interest_rate`: Calculated from `self.decision_engine.loan_market.get_interest_rate()` (marginal) or derived from existing loans if tracked. For now, we will use the `FinanceState` to track a weighted average if possible, or fallback to the current market rate if the agent is stateless regarding specific loan details (Engine limitation).
    -   *Strategy*: Since `FinanceState` tracks `total_debt_pennies` but maybe not individual loan rates, we will populate `average_interest_rate` using `self.finance_state.average_interest_rate` (if exists) or the `GovernmentPolicy.base_interest_rate` + risk premium as a proxy.

### 3.4. Implementation: AI Planner (`simulation/ai/firm_system2_planner.py`)

-   **`_calculate_npv`**:
    -   Add `debt_service_flow` parameter.
    -   `cash_flow = rev - cost - investment_flow - debt_service_flow`.
-   **`project_future`**:
    -   Extract `debt` and `rate` from `firm_state.finance`.
    -   Calculate `annual_debt_service = debt * rate`.
    -   Calculate `Leverage Ratio` = `Debt / (Assets - Debt)`.
    -   Adjust `hurdle_rate`: `hurdle *= (1 + leverage_ratio * risk_factor)`.

## 4. Technical Considerations

-   **Risk**: Removing `attach` might break tests that mock components and expect `attach` to be called.
-   **Mitigation**: Update `tests/test_firm.py` to remove assertions on `attach`.
-   **Performance**: Minimal impact. Adding simple arithmetic to NPV.

## 5. Design Checklist

-   [ ] **SEO Pattern**: Components are decoupled from the Agent instance.
-   [ ] **Debt Awareness**: AI logic explicitly accounts for liability costs.
-   [ ] **Test Coverage**: Existing tests pass; new logic covered by unit tests.
-   [ ] **DTO Purity**: No raw objects passed to AI; only `FinanceStateDTO`.

---

# API Draft: `modules/firm/api.py`

```python
from __future__ import annotations
from typing import Protocol, Any, Optional, Dict, List, Literal, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum

from modules.simulation.dtos.api import FirmConfigDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO
# Note: FinanceStateDTO is redefined here/below or imported. 
# If imported, we assume the source is updated. 
# For this draft, we redefine/extend expectations or assume the import carries the change.
# To be safe and explicit for the worker, we define the expected structure here if we can't edit the source DTO file directly.
# However, usually DTOs are in dtos.py. We will assume we update the source definition or use a local extension.
# Let's import it but acknowledge the field addition requirement in the Spec.
from modules.simulation.dtos.api import FinanceStateDTO 

from modules.system.api import MarketSnapshotDTO
from modules.simulation.api import IInventoryHandler
from modules.finance.api import IFinancialAgent
from simulation.models import Order

# ==============================================================================
# 1. ARCHITECTURAL RESOLUTION: ASSET PROTOCOLS
# ==============================================================================

@runtime_checkable
class ICollateralizableAsset(Protocol):
    """
    Interface for assets that can be locked, have liens placed
    against them, or be transferred as a whole unit.
    """
    def lock_asset(self, asset_id: Any, lock_owner_id: Any) -> bool: ...
    def release_asset(self, asset_id: Any, lock_owner_id: Any) -> bool: ...
    def transfer_asset(self, asset_id: Any, new_owner_id: Any) -> bool: ...
    def add_lien(self, asset_id: Any, lien_details: Any) -> Optional[str]: ...
    def remove_lien(self, asset_id: Any, lien_id: str) -> bool: ...

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
    firm_snapshot: FirmSnapshotDTO
    budget_plan: BudgetPlanDTO
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    current_tick: int
    labor_market_avg_wage: int = 1000

@dataclass(frozen=True)
class HRDecisionOutputDTO:
    hiring_orders: List[Order]
    firing_ids: List[int]
    wage_updates: Dict[int, int]
    target_headcount: int

# --- Production Engine DTOs ---

@dataclass(frozen=True)
class ProductionInputDTO:
    firm_snapshot: FirmSnapshotDTO
    productivity_multiplier: float

@dataclass(frozen=True)
class ProductionResultDTO:
    success: bool
    quantity_produced: float
    quality: float
    specialization: str
    inputs_consumed: Dict[str, float] = field(default_factory=dict)
    production_cost: int = 0
    capital_depreciation: int = 0
    automation_decay: float = 0.0
    error_message: Optional[str] = None

# --- Asset Management Engine DTOs ---

@dataclass(frozen=True)
class AssetManagementInputDTO:
    firm_snapshot: FirmSnapshotDTO
    investment_type: Literal["CAPEX", "AUTOMATION"]
    investment_amount: int

@dataclass(frozen=True)
class AssetManagementResultDTO:
    success: bool
    capital_stock_increase: int = 0
    automation_level_increase: float = 0.0
    actual_cost: int = 0
    message: Optional[str] = None

@dataclass(frozen=True)
class LiquidationExecutionDTO:
    firm_snapshot: FirmSnapshotDTO
    current_tick: int

@dataclass(frozen=True)
class LiquidationResultDTO:
    assets_returned: Dict[str, int]
    inventory_to_remove: Dict[str, float]
    capital_stock_to_write_off: int
    automation_level_to_write_off: float
    is_bankrupt: bool = True

# --- R&D Engine DTOs ---

@dataclass(frozen=True)
class RDInputDTO:
    firm_snapshot: FirmSnapshotDTO
    investment_amount: int
    current_time: int

@dataclass(frozen=True)
class RDResultDTO:
    success: bool
    quality_improvement: float = 0.0
    productivity_multiplier_change: float = 1.0
    actual_cost: int = 0
    message: Optional[str] = None

# --- Pricing Engine DTOs ---

@dataclass(frozen=True)
class PricingInputDTO:
    item_id: str
    current_price: int
    market_snapshot: MarketSnapshotDTO
    config: FirmConfigDTO
    unit_cost_estimate: int = 0
    inventory_level: float = 0.0
    production_target: float = 0.0

@dataclass(frozen=True)
class PricingResultDTO:
    new_price: int
    shadow_price: float
    demand: float
    supply: float
    excess_demand_ratio: float

# ==============================================================================
# 3. ENGINE PROTOCOLS
# ==============================================================================

@runtime_checkable
class IFinanceEngine(Protocol):
    def plan_budget(self, input_dto: FinanceDecisionInputDTO) -> BudgetPlanDTO: ...

@runtime_checkable
class IHREngine(Protocol):
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO: ...

@runtime_checkable
class IProductionEngine(Protocol):
    def produce(self, input_dto: ProductionInputDTO) -> ProductionResultDTO: ...

@runtime_checkable
class IAssetManagementEngine(Protocol):
    def invest(self, input_dto: AssetManagementInputDTO) -> AssetManagementResultDTO: ...
    def calculate_liquidation(self, input_dto: LiquidationExecutionDTO) -> LiquidationResultDTO: ...

@runtime_checkable
class IPricingEngine(Protocol):
    def calculate_price(self, input_dto: PricingInputDTO) -> PricingResultDTO: ...

@runtime_checkable
class IRDEngine(Protocol):
    def research(self, input_dto: RDInputDTO) -> RDResultDTO: ...

# ==============================================================================
# 4. COMPONENT PROTOCOLS (UPDATED)
# ==============================================================================

@runtime_checkable
class IFirmComponent(Protocol):
    """Base protocol for Firm components."""
    # Removed attach(self, owner) for SEO Pattern Compliance
    pass

@dataclass
class InventoryComponentConfigDTO:
    initial_inventory: Optional[Dict[str, float]] = None

@runtime_checkable
class IInventoryComponent(IInventoryHandler, IFirmComponent, Protocol):
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
    @property
    def wallet_balance(self) -> int: ...
    def force_reset_wallet(self) -> None: ...

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
    'IFinanceEngine',
    'IHREngine',
    'IProductionEngine',
    'IAssetManagementEngine',
    'IPricingEngine',
    'IRDEngine',
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
```