# `modules/firm/api.py`

```python
from __future__ in annotations
from typing import Protocol, Any, Optional, Dict, List, Literal
from dataclasses import dataclass, field

from modules.finance.dtos import MoneyDTO
from simulation.dtos.config_dtos import FirmConfigDTO
from simulation.dtos.firm_state_dto import FinanceStateDTO, ProductionStateDTO, SalesStateDTO, HRStateDTO

# ==============================================================================
# 1. ARCHITECTURAL RESOLUTION: INVENTORY & ASSET PROTOCOLS
# ==============================================================================

class IInventoryHandler(Protocol):
    """
    CANONICAL DEFINITION: Interface for managing an agent's inventory of consumable
    or sellable goods. Reflects the de-facto implementation across the codebase.
    This protocol supersedes the previous conflicting definition.
    """
    def add_item(self, item_id: str, quantity: float, quality: float = 1.0) -> bool:
        """Adds a specified quantity of an item to the inventory."""
        ...

    def remove_item(self, item_id: str, quantity: float) -> bool:
        """Removes a specified quantity of an item from the inventory. Returns False on failure."""
        ...

    def get_quantity(self, item_id: str) -> float:
        """Gets the current quantity of a specified item."""
        ...

    def get_quality(self, item_id: str) -> float:
        """Gets the average quality of a specified item."""
        ...

    def get_all_items(self) -> Dict[str, float]:
        """Returns a copy of the entire inventory (item_id -> quantity)."""
        ...

    def clear_inventory(self) -> None:
        """Removes all items from the inventory."""
        ...


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

@dataclass(frozen=True)
class ProductionResultDTO:
    """Result from the ProductionEngine."""
    success: bool
    quantity_produced: float
    quality: float
    inputs_consumed: Dict[str, float] = field(default_factory=dict)
    production_cost: float = 0.0

# --- Asset Management Engine DTOs ---

@dataclass(frozen=True)
class AssetManagementInputDTO:
    """Input for the AssetManagementEngine."""
    firm_snapshot: FirmSnapshotDTO
    investment_type: Literal["CAPEX", "AUTOMATION"]
    investment_amount: float

@dataclass(frozen=True)
class AssetManagementResultDTO:
    """Result from the AssetManagementEngine."""
    success: bool
    capital_stock_increase: float = 0.0
    automation_level_increase: float = 0.0
    actual_cost: float = 0.0

# --- R&D Engine DTOs ---

@dataclass(frozen=True)
class RDInputDTO:
    """Input for the R&D Engine."""
    firm_snapshot: FirmSnapshotDTO
    investment_amount: float

@dataclass(frozen=True)
class RDResultDTO:
    """Result from the R&D Engine."""
    success: bool
    quality_improvement: float = 0.0
    actual_cost: float = 0.0

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
```

# `design/3_work_artifacts/specs/firm_engine_refactor_spec.md`

```markdown
# Spec: Firm Agent Refactoring into Specialized Engines

**Version**: 1.0
**Author**: Scribe (Gemini)
**Status**: Proposed

## 1. Introduction

This document outlines the specification for refactoring the `Firm` agent class (`simulation/firms.py`). The current implementation is a God Class that violates the Single Responsibility Principle and architectural guardrails by mixing state, orchestration, and direct business logic execution.

The goal is to extract business logic into three new, strictly stateless engines, with the `Firm` class acting as a pure orchestrator. This will improve modularity, testability, and adherence to the project's core architectural principles.

- **`ProductionEngine`**: Manages the core production process.
- **`AssetManagementEngine`**: Manages investments in CAPEX and automation.
- **`RDEngine`**: Manages investments in Research & Development.

This refactoring directly addresses the critical risks identified in the **Pre-flight Audit**.

## 2. Architectural Resolution (Prerequisites)

This refactoring is contingent on first resolving a critical architectural inconsistency.

### 2.1. Canonical `IInventoryHandler` Protocol

- **Problem**: The formal protocol at `modules/inventory/api.py` defines methods for asset locking and liens, while the de-facto implementations in `Firm`, `Household`, and `InventoryManager` use a different set of methods for item management (`add_item`, `remove_item`).
- **Resolution**:
    1. The `IInventoryHandler` protocol in `modules/inventory/api.py` **MUST** be overwritten to reflect its actual usage across the codebase. See the proposed `modules/firm/api.py` for the canonical definition.
    2. A new protocol, `ICollateralizableAsset`, will be created in `modules/firm/api.py` to house the aspirational methods (`lock_asset`, `add_lien`, etc.).
    3. All relevant agents (`Firm`, `Household`) and components (`InventoryManager`) must be updated to explicitly implement the new, correct `IInventoryHandler`.

**This is a blocking prerequisite.** Proceeding without this alignment will propagate technical debt.

## 3. New Engine and DTO Design

All new engines will be stateless and located in `simulation/components/engines/`. They will operate exclusively on immutable DTOs defined in `modules/firm/api.py`.

### 3.1. DTOs

- **`FirmSnapshotDTO`**: An immutable dataclass containing the complete state of the firm required for any decision. This is the primary input for all engines.
- **`ProductionResultDTO`**: Output from `ProductionEngine` detailing goods produced, quality, and costs.
- **`AssetManagementResultDTO`**: Output from `AssetManagementEngine` detailing increases in capital/automation and the associated cost.
- **`RDResultDTO`**: Output from `RDEngine` detailing quality improvements from research and the associated cost.

### 3.2. Engine Interfaces

- **`IProductionEngine`**: Defines a `produce` method that takes a `ProductionInputDTO` and returns a `ProductionResultDTO`.
- **`IAssetManagementEngine`**: Defines an `invest` method that takes an `AssetManagementInputDTO` and returns an `AssetManagementResultDTO`.
- **`IRDEngine`**: Defines a `research` method that takes an `RDInputDTO` and returns an `RDResultDTO`.

*(For full definitions, see the accompanying `modules/firm/api.py` file.)*

## 4. Refactoring Logic & Orchestration

The `Firm` class will be refactored from a monolith into a pure orchestrator.

### 4.1. Decommissioning God Methods

- **`Firm._execute_internal_order()`**: This method **will be deleted**. Its entire logic for handling `INVEST_AUTOMATION`, `INVEST_RD`, and `INVEST_CAPEX` will be moved into the `AssetManagementEngine` and `RDEngine`.
- **`Firm.produce()`**: The logic within this method will be moved to the `ProductionEngine`.

### 4.2. New Orchestration Flow

The `Firm` agent will now follow a strict "Assemble -> Delegate -> Apply" pattern.

#### `Firm.produce()` (New Logic)
```python
# In class Firm:
def produce(self, current_time: int, technology_manager: Optional[Any] = None, effects_queue: Optional[List[Dict[str, Any]]] = None) -> None:
    # 1. ASSEMBLE snapshot and input DTO
    snapshot = self.get_snapshot_dto() # New helper to create FirmSnapshotDTO
    productivity_multiplier = technology_manager.get_productivity_multiplier(self.id) if technology_manager else 1.0
    input_dto = ProductionInputDTO(
        firm_snapshot=snapshot,
        productivity_multiplier=productivity_multiplier
    )

    # 2. DELEGATE to stateless engine
    result: ProductionResultDTO = self.production_engine.produce(input_dto)

    # 3. APPLY result to state (Orchestrator responsibility)
    if result.success and result.quantity_produced > 0:
        self.add_item(snapshot.production.specialization, result.quantity_produced, quality=result.quality)
        self.record_expense(result.production_cost, DEFAULT_CURRENCY) # Using internal helper

    # ... existing real estate utilization logic remains here for now ...
```

#### Post-`make_decision` Orchestration (Replaces `_execute_internal_order`)
```python
# In class Firm, after make_decision() returns orders:
def execute_internal_orders(self, orders: List[Order], fiscal_context: FiscalContext, current_time: int) -> None:
    # This new method replaces the logic of _execute_internal_order

    snapshot = self.get_snapshot_dto()
    gov_proxy = fiscal_context.government if fiscal_context else None

    for order in orders:
        if order.market_id != "internal":
            continue

        amount = order.monetary_amount['amount'] if order.monetary_amount else order.quantity

        # --- Delegate to AssetManagementEngine ---
        if order.order_type in ["INVEST_AUTOMATION", "INVEST_CAPEX"]:
            asset_input = AssetManagementInputDTO(
                firm_snapshot=snapshot,
                investment_type=order.order_type.replace("INVEST_", ""), # "AUTOMATION" or "CAPEX"
                investment_amount=amount
            )
            asset_result: AssetManagementResultDTO = self.asset_management_engine.invest(asset_input)

            if asset_result.success and self.settlement_system.transfer(self, gov_proxy, asset_result.actual_cost, order.order_type):
                # Apply state changes
                self.production_state.automation_level += asset_result.automation_level_increase
                self.production_state.capital_stock += asset_result.capital_stock_increase
                self.record_expense(asset_result.actual_cost, DEFAULT_CURRENCY)
                self.logger.info(f"INTERNAL_EXEC | Firm {self.id} invested {asset_result.actual_cost} in {order.order_type}.")

        # --- Delegate to RDEngine ---
        elif order.order_type == "INVEST_RD":
            rd_input = RDInputDTO(firm_snapshot=snapshot, investment_amount=amount)
            rd_result: RDResultDTO = self.rd_engine.research(rd_input)

            if rd_result.success and self.settlement_system.transfer(self, gov_proxy, rd_result.actual_cost, "R&D"):
                # Apply state changes
                self.production_state.base_quality += rd_result.quality_improvement
                # (Further logic for updating research history can be added)
                self.record_expense(rd_result.actual_cost, DEFAULT_CURRENCY)
                self.logger.info(f"INTERNAL_EXEC | Firm {self.id} R&D SUCCESS (Budget: {rd_result.actual_cost})")

        # ... other internal order types (SET_TARGET, PAY_TAX, etc.) ...
```

## 5. Verification & Testing Strategy

This refactoring carries a high risk of breaking existing functionality. A rigorous testing strategy is non-negotiable.

- **New Unit Tests**: Each new engine (`ProductionEngine`, `AssetManagementEngine`, `RDEngine`) **MUST** be accompanied by a dedicated test file with 100% logic coverage. Tests must be pure, only checking that a given input DTO produces the expected output DTO.
- **Test Migration Plan**:
    - Existing integration tests relying on `Firm.make_decision()` are now considered **legacy** and **will break**.
    - These tests **MUST** be migrated. The new tests should focus on the `Firm`'s role as an orchestrator.
    - **Example Migrated Test**:
        1.  `GIVEN` a Firm instance.
        2.  `WHEN` `make_decision` is called and returns an `INVEST_CAPEX` order.
        3.  `MOCK` the `AssetManagementEngine` to return a specific `AssetManagementResultDTO`.
        4.  `THEN` assert that `AssetManagementEngine.invest` was called with the correct `AssetManagementInputDTO`.
        5.  `AND` assert that the `Firm`'s state (`capital_stock`, `wallet`) was correctly updated based on the mocked `AssetManagementResultDTO`.
- **Integration Check**: After refactoring, the `scripts/audit_zero_sum.py` script and a full, multi-tick simulation scenario must be run to ensure no financial leakages or deadlocks were introduced.

## 6. Risk & Impact Mitigation

This specification directly mitigates the risks identified by the Pre-flight Audit.

- **Risk: God Method Refactoring**: By deleting `_execute_internal_order` and replacing it with a clean orchestration flow delegating to new engines, we dismantle the god method. The test migration plan explicitly addresses the high blast radius.
- **Risk: Architectural Inconsistency (`IInventoryHandler`)**: Section 2 of this spec makes resolving the protocol conflict a mandatory prerequisite, preventing the propagation of technical debt.
- **Risk: Circular Dependencies**:
    - New engine files will be placed in `simulation/components/engines/`.
    - New DTOs will be placed in `modules/firm/api.py` or a new `simulation/dtos/firm_dtos.py` file to be accessible by both engines and agents without creating import loops.
    - A manual review of `TYPE_CHECKING` blocks will be a required step in the final code review to ensure correctness.

## 7. Mandatory Reporting Verification

All insights, unforeseen challenges, or newly identified technical debt encountered during the implementation of this specification will be documented in a new file under `communications/insights/firm_engine_refactor_YYYYMMDD.md`. This report is a mandatory deliverable for the completion of this task.
```
