modules/firm/api.py
```python
from __future__ import annotations
from typing import Protocol, Dict, List, Any, Optional, TypedDict, runtime_checkable, Union
from dataclasses import dataclass
from enum import Enum

from modules.simulation.dtos.api import FirmConfigDTO, SalesStateDTO, FirmStateDTO, ProductionStateDTO, FinanceStateDTO, HRStateDTO
from modules.system.api import MarketSnapshotDTO, MarketContextDTO
from simulation.models import Order, Transaction

# ==============================================================================
# 1. Component Protocols (Decoupled)
# ==============================================================================

@runtime_checkable
class IFirmComponent(Protocol):
    """
    Marker interface for Firm components.
    MUST NOT have .attach() or .parent references.
    """
    id: str

@runtime_checkable
class IInventoryComponent(IFirmComponent, Protocol):
    """
    Pure data structure for Inventory.
    """
    def add_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, quality: float = 1.0, slot: Any = None) -> bool: ...
    def remove_item(self, item_id: str, quantity: float, transaction_id: Optional[str] = None, slot: Any = None) -> bool: ...
    def get_quantity(self, item_id: str, slot: Any = None) -> float: ...
    def get_all_items(self, slot: Any = None) -> Dict[str, float]: ...
    def clear_inventory(self, slot: Any = None) -> None: ...

@runtime_checkable
class IFinancialComponent(IFirmComponent, Protocol):
    """
    Pure data structure for Finance (Wallet wrapper).
    """
    def get_balance(self, currency: str) -> int: ...
    def get_all_balances(self) -> Dict[str, int]: ...
    def deposit(self, amount: int, currency: str) -> None: ...
    def withdraw(self, amount: int, currency: str) -> None: ...

# ==============================================================================
# 2. Engine Input/Output DTOs (Stateless)
# ==============================================================================

@dataclass(frozen=True)
class FirmSnapshotDTO:
    """
    Immutable snapshot of the Firm's entire state.
    Passed to Engines to provide context without allowing mutation.
    """
    id: str
    is_active: bool
    config: FirmConfigDTO
    finance: FinanceStateDTO
    production: ProductionStateDTO
    sales: SalesStateDTO
    hr: HRStateDTO

# --- Brand Engine DTOs ---

@dataclass(frozen=True)
class BrandUpdateInputDTO:
    firm_snapshot: FirmSnapshotDTO
    marketing_spend: int
    productivity_factor: float
    current_tick: int

@dataclass(frozen=True)
class BrandUpdateResultDTO:
    """
    Result of BrandEngine calculation.
    """
    new_brand_awareness: float
    new_perceived_quality: float
    awareness_change: float
    quality_change: float
    decay_applied: float

# --- Pricing Engine DTOs (Refinement) ---

@dataclass(frozen=True)
class DynamicPricingInputDTO:
    firm_snapshot: FirmSnapshotDTO
    active_orders: List[Order]
    current_tick: int
    unit_cost_estimator: Any # Callable[[str], int] - but DTOs shouldn't have callables usually. 
                             # Better: pass a Dict[item_id, cost] or similar.
                             # For now, we will assume pre-calculated costs are passed or the engine estimates.
    estimated_unit_costs: Dict[str, int]

@dataclass(frozen=True)
class DynamicPricingResultDTO:
    """
    Result of PricingEngine dynamic adjustment.
    """
    updated_prices: Dict[str, int] # item_id -> new_price_pennies
    price_adjustments: Dict[str, str] # item_id -> reason/log

# ==============================================================================
# 3. Engine Protocols (Updated for Purity)
# ==============================================================================

@runtime_checkable
class IBrandEngine(Protocol):
    """
    Calculates brand evolution based on spending and performance.
    Stateless: Returns result, does not mutate state.
    """
    def calculate_update(self, input_dto: BrandUpdateInputDTO) -> BrandUpdateResultDTO:
        ...

    # Deprecated:
    # def update(self, state: SalesState, ...) -> None: ...

@runtime_checkable
class ISalesEngine(Protocol):
    """
    Handles sales logic, marketing, and pricing adjustments.
    """
    def adjust_marketing_budget(self, state: Any, context: Any, revenue: float, last_revenue: float, last_marketing_spend: float) -> Any:
        # Existing method seems close to pure, check impl
        ...

    def check_and_apply_dynamic_pricing(self, input_dto: DynamicPricingInputDTO) -> DynamicPricingResultDTO:
        """
        Pure version of check_and_apply_dynamic_pricing.
        """
        ...
    
    # ... other methods ...

@runtime_checkable
class IProductionEngine(Protocol):
    def produce(self, input_dto: Any) -> Any: ...

@runtime_checkable
class IFinanceEngine(Protocol):
    def plan_budget(self, input_dto: Any) -> Any: ...
    def generate_financial_transactions(self, state: Any, firm_id: str, balances: Dict[str, int], config: Any, current_tick: int, context: Any, inventory_value: int) -> List[Transaction]: ...
    def get_estimated_unit_cost(self, state: Any, item_id: str, config: Any) -> int: ...
    def calculate_valuation(self, state: Any, balances: Dict[str, int], config: Any, inventory_value: int, capital_stock: int, context: Any) -> int: ...

@runtime_checkable
class IHREngine(Protocol):
    def manage_workforce(self, input_dto: Any) -> Any: ...
    def process_payroll(self, state: Any, context: Any, config: Any) -> Any: ...

```

design/3_work_artifacts/specs/MISSION_wave7_firm_mutation_spec.md
```markdown
# MISSION SPEC: wave7-firm-mutation

## 🎯 Objective
Refactor the `Firm` agent and its subsystems to strictly enforce the **Stateless Engine & Orchestrator (SEO)** pattern. This involves removing structural coupling (`self.parent`) from components and eliminating in-place state mutation within Engines, specifically `BrandEngine` and `SalesEngine`.

## 🛡️ Architectural Standards (Compliance Check)
- **[SEO_PATTERN.md](../../1_governance/architecture/standards/SEO_PATTERN.md)**:
    - **Engine Purity**: Engines MUST accept DTOs and return DTOs. No `state.field = value` assignments inside engines.
    - **Orchestrator Responsibility**: The `Firm` agent is the only entity allowed to assign values to `self.sales_state`, `self.production_state`, etc.
- **[Component Decoupling]**: Components (`InventoryComponent`, `FinancialComponent`) must be passive data wrappers. They cannot call back to the `Firm`.

## 🛠️ Refactoring Plan

### 1. Component Decoupling (The "Cut the Cord" Phase)
**Goal**: Remove `attach(self)` and `self.parent` from `InventoryComponent` and `FinancialComponent`.

- **Action**: Modify `modules/agent_framework/components/inventory_component.py` and `financial_component.py`.
    - Remove `attach(owner)` method.
    - Remove `self.owner` or `self.parent` attributes.
    - Ensure `add_item`, `deposit`, etc., operate solely on internal storage.
    - **Impact**: If these components were logging via `self.owner.logger`, the methods must now accept a `logger` argument, or return a result that the caller logs.
    - **Resolution**: `Firm` methods delegating to components (e.g., `Firm.add_item`) must handle any side effects (logging, stats tracking) *after* the component call returns.

### 2. BrandEngine Purity
**Goal**: Convert `BrandEngine.update(state, ...)` to `calculate_update(dto) -> Result`.

- **Input DTO**: `BrandUpdateInputDTO` (defined in API).
- **Output DTO**: `BrandUpdateResultDTO`.
- **Logic Change**:
    - Current: `state.brand_awareness = new_value`
    - New: `return BrandUpdateResultDTO(new_brand_awareness=new_value, ...)`
- **Orchestrator Update (`Firm.generate_transactions`)**:
    ```python
    # OLD
    # self.brand_engine.update(self.sales_state, ...)

    # NEW
    input_dto = BrandUpdateInputDTO(
        firm_snapshot=self.get_snapshot_dto(),
        marketing_spend=int(self.sales_state.marketing_budget_pennies),
        productivity_factor=self.productivity_factor,
        current_tick=current_time
    )
    result = self.brand_engine.calculate_update(input_dto)
    
    # Orchestrator applies state change
    self.sales_state.brand_awareness = result.new_brand_awareness
    self.sales_state.perceived_quality = result.new_perceived_quality
    ```

### 3. SalesEngine Pricing Purity
**Goal**: Convert `check_and_apply_dynamic_pricing` to return price adjustments instead of modifying `state.last_prices`.

- **Input DTO**: `DynamicPricingInputDTO`.
- **Output DTO**: `DynamicPricingResultDTO`.
- **Orchestrator Update (`Firm.make_decision`)**:
    ```python
    # OLD
    # self.sales_engine.check_and_apply_dynamic_pricing(self.sales_state, ...)

    # NEW
    pricing_input = DynamicPricingInputDTO(
        firm_snapshot=self.get_snapshot_dto(),
        active_orders=external_orders,
        current_tick=current_time,
        estimated_unit_costs={item: self.finance_engine.get_estimated_unit_cost(...) for item in items}
    )
    pricing_result = self.sales_engine.check_and_apply_dynamic_pricing(pricing_input)

    # Apply changes
    for item_id, new_price in pricing_result.updated_prices.items():
        self.sales_state.last_prices[item_id] = new_price
    ```

## ⚠️ Risk & Impact Audit

### 1. Test Regressions (High Risk)
- **Affected Tests**: `tests/modules/firm/test_firm.py`, `tests/modules/firm/test_brand_engine.py`, `tests/modules/firm/test_sales_engine.py`.
- **Cause**: Tests likely mock the engines and expect the old call signatures or verify state mutation on the mock arguments.
- **Mitigation**:
    - Update `test_brand_engine.py` to assert return values, not state mutation.
    - Update `test_firm.py` mocks: `mock_brand_engine.calculate_update.return_value = BrandUpdateResultDTO(...)`.

### 2. Component Call Sites
- `InventoryComponent` is used by `Household` and `Firm`. Both must be checked to ensure they aren't relying on `attach()`.
- **Search**: `grep -r "attach(" modules/` to find all usages.

### 3. Circular Dependencies
- `FirmSnapshotDTO` includes `FirmConfigDTO`. Ensure `FirmConfigDTO` does not import `Firm`.
- **Verification**: Check imports in `modules/simulation/dtos/api.py`.

## 🧪 Verification Plan

### 1. Static Analysis
- Run `mypy modules/firm` to ensure DTO types match.

### 2. Unit Tests
- `pytest tests/modules/firm/test_brand_engine.py` (Verify engine purity)
- `pytest tests/modules/firm/test_sales_engine.py` (Verify pricing purity)
- `pytest tests/modules/agent_framework/test_components.py` (Verify decoupled components)

### 3. Integration Check
- `pytest tests/simulation/test_firm_integration.py` (Verify the `Firm` orchestrator correctly wires the new inputs/outputs)

## 📝 Insight Recording
- Record findings in `communications/insights/wave7-firm-mutation.md`.
- Note any unexpected state dependencies found during component decoupling.
```