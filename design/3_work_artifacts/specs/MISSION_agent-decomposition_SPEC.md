File: modules/agent_framework/api.py
```python
"""
modules/agent_framework/api.py

Defines the reusable Component Interfaces for the "Agent Shell" pattern.
This module facilitates the decomposition of God Class Agents (Firm/Household)
into lightweight orchestrators composed of specialized components.
"""
from typing import Protocol, Dict, Any, Optional, List, TypeVar, RuntimeCheckable
from abc import abstractmethod
from dataclasses import dataclass

from modules.system.api import InventorySlot, ItemDTO
from modules.finance.api import CurrencyCode, IFinancialEntity
from modules.common.interfaces import IInventoryHandler

@dataclass(frozen=True)
class ComponentConfigDTO:
    """Base configuration for agent components."""
    owner_id: str
    debug_mode: bool = False

@RuntimeCheckable
class IAgentComponent(Protocol):
    """Base protocol for all agent components."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the component with specific config."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset component state for a new tick/cycle."""
        ...

@RuntimeCheckable
class IInventoryComponent(IInventoryHandler, Protocol):
    """
    Component responsible for managing agent inventory storage and quality.
    Strictly typed to replace ad-hoc dictionary manipulation.
    """
    
    @abstractmethod
    def load_from_state(self, inventory_data: Dict[str, Any]) -> None:
        """Restores inventory state from a snapshot/DTO."""
        ...

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Returns a serializable snapshot of the inventory."""
        ...

    @abstractmethod
    def get_inventory_value(self, price_map: Dict[str, int]) -> int:
        """Calculates total value based on provided prices (pennies)."""
        ...

@RuntimeCheckable
class IFinancialComponent(IFinancialEntity, Protocol):
    """
    Component responsible for wrapping the Wallet and enforcing financial protocols.
    Handles strict integer arithmetic and currency management.
    """
    
    @property
    @abstractmethod
    def wallet_balance(self) -> int:
        """Primary currency balance in pennies."""
        ...

    @abstractmethod
    def get_net_worth(self, valuation_func: Optional[Any] = None) -> int:
        """Calculates total agent net worth (assets - liabilities)."""
        ...

@RuntimeCheckable
class ITransactionOrchestrator(Protocol):
    """
    Encapsulates complex transaction generation logic previously embedded in Agents.
    """
    
    @abstractmethod
    def orchestrate(self, context: Any) -> List[Any]:
        """
        Executes the transaction generation pipeline.
        Returns a list of Transaction objects (opaque Any for loose coupling here).
        """
        ...

# DTOs for Component State
@dataclass
class InventoryStateDTO:
    main_slot: Dict[str, float]
    main_quality: Dict[str, float]
    input_slot: Dict[str, float]
    input_quality: Dict[str, float]

@dataclass
class FinancialStateDTO:
    balances: Dict[CurrencyCode, int]
    credit_frozen_until: int
```

File: design/3_work_artifacts/specs/god_class_decomposition_spec.md
```markdown
# Spec: God Class Decomposition (Firm & Household)

**Mission Key**: `firm-household-decomp-spec`
**Status**: DRAFT
**Owner**: Gemini (Scribe)
**Target Phase**: Phase 16.1 (Lane 3)

## 1. Executive Summary

The `Firm` and `Household` classes have accumulated excessive responsibilities, acting as "God Orchestrators" that directly manage state, implement numerous protocols, and orchestrate complex engine pipelines. This specification outlines a structural refactoring using the **Component-Entity-System (CES) Lite** pattern to reduce code volume, improve testability, and enforce strict separation of concerns without altering public APIs.

## 2. Problem Statement

1.  **Protocol Bloat**: `Firm` implements 10+ interfaces directly (`IInventoryHandler`, `IFinancialAgent`, etc.), resulting in hundreds of lines of getter/setter boilerplate.
2.  **State Exposure**: Internal state (e.g., `_inventory`, `_wallet`) is manipulated directly by the Agent, bypassing encapsulation and making it hard to enforce invariants (e.g., negative inventory checks).
3.  **Orchestration Coupling**: Complex methods like `generate_transactions` (Firm) and `update_needs` (Household) mix logic with orchestration, making them hard to unit test without full agent instantiation.
4.  **Testing Fragility**: Tests rely on mocking the entire Agent, leading to "Mock Hell" when internal implementations change.

## 3. Solution Architecture: Agent Shell Pattern

We will transform `Firm` and `Household` into **Agent Shells**. A Shell is a lightweight container that:
1.  **Holds Components**: Owns `InventoryComponent`, `FinancialComponent`, etc.
2.  **Delegates Protocols**: Implements public interfaces by forwarding calls to components.
3.  **Orchestrates Engines**: Uses `TransactionOrchestrator` to wire stateless engines together.

### 3.1. New Components (`modules/agent_framework/components/`)

#### A. `InventoryComponent`
-   **Responsibility**: Manages `main` and `input` inventory slots, quality tracking, and serialization.
-   **Implements**: `IInventoryHandler`, `IInventoryComponent`.
-   **State**: Holds `InventoryStateDTO`.

#### B. `FinancialComponent`
-   **Responsibility**: Wraps `Wallet`, enforces `IFinancialEntity` (Penny Standard), tracks `credit_frozen` state.
-   **Implements**: `IFinancialEntity`, `ICreditFrozen`, `IFinancialComponent`.
-   **State**: Holds `Wallet` instance.

#### C. `FirmTransactionOrchestrator` (Service)
-   **Responsibility**: Encapsulates the `generate_transactions` pipeline.
-   **Input**: `FirmStateDTO`, `FiscalContext`, `MarketContext`.
-   **Output**: `List[Transaction]`.
-   **Logic**: Calls `HREngine`, `FinanceEngine`, `SalesEngine` in sequence.

### 3.2. Refactored Agent Structure (Pseudo-Code)

```python
class Firm(ILearningAgent, IFinancialFirm, ...):
    def __init__(self, ...):
        # Composition
        self.inventory_comp = InventoryComponent()
        self.financial_comp = FinancialComponent()
        self.txn_orchestrator = FirmTransactionOrchestrator()
        
        # ... Engines ...

    # Protocol Delegation (Boilerplate Reducer)
    @property
    def inventory(self): return self.inventory_comp.get_all_items()
    
    def add_item(self, *args): return self.inventory_comp.add_item(*args)
    
    @property
    def balance_pennies(self): return self.financial_comp.balance_pennies

    # Simplified Orchestration
    def generate_transactions(self, ...):
        # Delegate complex wiring to the orchestrator
        return self.txn_orchestrator.orchestrate(
            state=self.get_snapshot_dto(),
            engines=(self.hr_engine, self.finance_engine, self.sales_engine),
            context=...
        )
```

## 4. Implementation Plan (Parallel Lane 3)

This work is assigned to **Lane 3** of the Parallel Technical Debt Clearance Strategy.

### Step 1: Component Creation (Safe)
-   Create `modules/agent_framework/components/inventory_component.py`.
-   Create `modules/agent_framework/components/financial_component.py`.
-   Create `modules/firm/orchestrators/transaction_orchestrator.py`.
-   **Verification**: Unit test components in isolation.

### Step 2: Firm Refactoring (Lane 3A)
-   Replace `Firm._inventory` with `Firm.inventory_comp`.
-   Replace `Firm._wallet` usage with `Firm.financial_comp`.
-   Delegate protocol methods.
-   **Verification**: Run `tests/simulation/agents/test_firm.py` (Must pass without modification to tests).

### Step 3: Household Refactoring (Lane 3B)
-   Follow similar pattern for `Household`.
-   Extract `HouseholdLifecycleOrchestrator` to handle the `update_needs` pipeline.
-   **Verification**: Run `tests/simulation/agents/test_household.py`.

## 5. Verification Strategy

### 5.1. Component Tests
-   **Test**: `tests/modules/agent_framework/test_inventory_component.py`
-   **Scenario**: Add item, Remove item, Check Quality, Snapshot/Restore.
-   **Success**: 100% logic coverage of inventory math.

### 5.2. Integration Tests (Regression)
-   **Test**: `tests/simulation/agents/test_firm_decomposition.py`
-   **Scenario**:
    1.  Instantiate Refactored Firm.
    2.  Perform `add_item`.
    3.  Verify item is in `firm.inventory_comp`.
    4.  Verify `firm.get_quantity()` returns correct value.
    5.  Run full `make_decision` cycle to ensure orchestration wiring holds.

## 6. Risk Analysis

-   **Risk**: `load_state` / `get_current_state` logic drift.
    -   *Mitigation*: The `Component` must provide `to_dto()` and `from_dto()` methods. The Agent's `load_state` must explicitly call these.
-   **Risk**: Performance overhead of delegation.
    -   *Mitigation*: Python method calls are cheap enough for this simulation scale. The structural clarity outweighs micro-optimization.
-   **Risk**: Circular Imports.
    -   *Mitigation*: Components must NOT import the Agent class. They only import DTOs and Protocols.

## 7. Mandatory Reporting Instruction

**[INSTRUCTION FOR ASSIGNED AGENT]**
Upon drafting this spec, you MUST create the insight report at `communications/insights/firm-household-decomp-spec.md` with the following content:
1.  Confirmation of Decomposition Strategy (CES Lite).
2.  List of created Component Interfaces.
3.  Verification that this approach adheres to SEO Pattern (Components are stateful helpers, Engines remain stateless).
```

File: communications/insights/firm-household-decomp-spec.md
```markdown
# Insight Report: God Class Decomposition Specification

**Mission**: `firm-household-decomp-spec`
**Date**: 2026-02-16
**Author**: Gemini (Scribe)
**Status**: SPECIFICATION COMPLETE

## 1. Architectural Strategy: CES Lite (Agent Shell)
We have defined a **Component-Entity-System (CES) Lite** approach to decompose the `Firm` and `Household` God Classes.
-   **Agent = Shell**: The Agent class becomes a thin wrapper (Shell) that aggregates reusable **Components**.
-   **Composition over Inheritance**: Instead of inheriting `InventoryMixin` or implementing protocols directly in the class body, the Agent holds `InventoryComponent`, `FinancialComponent`, etc.
-   **Orchestrators**: Complex procedural logic (e.g., transaction generation pipelines) is extracted into stateless **TransactionOrchestrators**.

## 2. Defined Interfaces
The following interfaces have been defined in `modules/agent_framework/api.py`:
-   `IAgentComponent`: Lifecycle management (init, reset).
-   `IInventoryComponent`: Typed inventory management (replaces dicts).
-   `IFinancialComponent`: Strict penny-based financial operations (replaces `Wallet` direct usage).
-   `ITransactionOrchestrator`: Pipeline encapsulation.

## 3. SEO Pattern Adherence
This decomposition **strictly adheres** to the Stateless Engine & Orchestrator (SEO) pattern:
-   **Engines** remain pure and stateless.
-   **Components** hold the state (Data) and provide atomic mutation methods (Logic for data integrity, e.g., "cannot remove more than you have").
-   **Agents (Orchestrators)** wire Components and Engines together. The Agent is the "Owner" of the state but delegates the "How" to Components and Engines.

## 4. Technical Debt Resolution
This specification directly addresses `TD-STR-GOD-DECOMP` by:
-   Reducing `Firm` class size by estimated 40-50% (removing boilerplate).
-   Centralizing inventory/finance logic, eliminating duplication between Firm/Household.
-   Enabling isolated unit testing of storage logic.

## 5. Next Steps
-   **Lane 3 Execution**: Proceed with Component implementation and iterative refactoring of Agents.
-   **Audit**: Verify that no circular dependencies are introduced between `simulation.agents` and `modules.agent_framework`.
```