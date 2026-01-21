# Spec: WO-102 - Decouple DecisionContext

**Objective:** Complete the DTO-based refactoring by removing the monolithic agent object (`household`, `firm`) from `DecisionContext`, enforcing a strict data-passing architecture and eliminating the root cause of the circular dependency identified in Audit Report #1.

---

## 1. Problem Statement

The `DecisionContext` DTO currently carries both the new `HouseholdStateDTO` and the legacy `Household` object. This "compatibility" feature creates significant technical debt:

-   **Architectural Drift**: It encourages new logic to rely on the old, monolithic agent object, undermining the DTO refactoring.
-   **Circular Dependency**: It forces `dtos/api.py` to have a type-checking-only import of `core_agents.py`, tightly coupling the modules.
-   **Test Brittleness**: Tests rely on the full agent object being available in the context, making them fragile and hard to maintain.
-   **Inconsistency**: The context is inconsistent for different agent types. `Household` has a `state` DTO, but `Firm` does not, passing the entire object.

This work order mandates the final removal of the legacy agent object from the context.

## 2. Implementation Plan

The refactoring will be executed in three distinct, sequential phases to manage risk and ensure a smooth transition.

### Phase 1: API Contract Enforcement

1.  **Define `FirmStateDTO`**: Create a new `FirmStateDTO` in `simulation/dtos/api.py` to mirror the structure of `HouseholdStateDTO`. This DTO will be populated from the `firm.get_agent_data()` method.
2.  **Redefine `DecisionContext`**: Modify `DecisionContext` in `simulation/dtos/api.py`.
    -   **REMOVE** `household: Optional[Household]`
    -   **REMOVE** `firm: Optional[Firm]`
    -   The existing `state: Optional[HouseholdStateDTO]` will be made more generic or specific states will be added. The preferred approach is explicit DTOs.
    -   **ADD** `household_state: Optional[HouseholdStateDTO]`
    -   **ADD** `firm_state: Optional[FirmStateDTO]`
    -   This change intentionally breaks the circular dependency and acts as a hard contract for all decision engines.

### Phase 2: Decision Engine & Agent Refactoring

1.  **Refactor `Household.make_decision`**:
    -   In `simulation/core_agents.py`, modify the `make_decision` method.
    -   When creating `DecisionContext`, it must now populate `household_state` instead of the legacy `household` and `state` fields.
    -   Remove the `context.state = state_dto` dynamic attachment.
    -   It should now be: `context = DecisionContext(..., household_state=state_dto, ...)`

2.  **Refactor `Firm.make_decision`**:
    -   In `simulation/firms.py`, create a `create_state_dto()` method that returns the new `FirmStateDTO`.
    -   Modify the `make_decision` method to pass this new DTO to `DecisionContext`: `context = DecisionContext(..., firm_state=state_dto, ...)`

3.  **Refactor Decision Engines**:
    -   Update all classes that consume `DecisionContext`, primarily `AIDrivenHouseholdDecisionEngine` and `RuleBasedHouseholdDecisionEngine`.
    -   All logic must now source its data from `context.household_state` or `context.firm_state`.
    -   **All access to `context.household` or `context.firm` MUST be removed.**

### Phase 3: Test Suite Modernization

1.  **Update Test Fixtures**:
    -   Identify all tests for decision engines that are now failing.
    -   Instead of creating full mock `Household` or `Firm` objects, create instances of `HouseholdStateDTO` and `FirmStateDTO` with the required test data.
    -   Pass these mock DTOs into the `DecisionContext` during test setup.
    -   This aligns the test suite with the new, decoupled architecture and improves test performance and stability.

## 3. API & DTO Specification (`api.py`)

### `simulation/dtos/api.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# (Keep existing DTOs like TransactionData, etc.)

# NEW: FirmStateDTO
@dataclass
class FirmStateDTO:
    """A snapshot of a Firm's state for decision-making."""
    id: int
    assets: float
    needs: Dict[str, float]
    inventory: Dict[str, float]
    input_inventory: Dict[str, float]
    employees: List[int]
    is_active: bool
    current_production: float
    productivity_factor: float
    production_target: float
    revenue_this_turn: float
    expenses_this_tick: float
    consecutive_loss_turns: int
    total_shares: float
    treasury_shares: float
    dividend_rate: float
    capital_stock: float
    base_quality: float
    inventory_quality: Dict[str, float]
    automation_level: float

# REVISED: DecisionContext
@dataclass
class DecisionContext:
    """
    Revised context object for decision engines.
    Carries market data and a state DTO, but NOT the full agent object.
    """
    markets: Dict[str, Any]
    goods_data: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    current_time: int
    
    # --- State DTOs (The New Contract) ---
    household_state: Optional[HouseholdStateDTO] = None
    firm_state: Optional[FirmStateDTO] = None

    # --- Global Systems ---
    government: Optional[Any] = None
    reflux_system: Optional[Any] = None
    stress_scenario_config: Optional["StressScenarioConfig"] = None

    # --- DEPRECATED ---
    # household: Optional[Household] = None -> REMOVED
    # firm: Optional[Firm] = None -> REMOVED
    # state: Optional[HouseholdStateDTO] = None -> REMOVED (in favor of explicit DTOs)

    def __post_init__(self):
        if self.household_state is None and self.firm_state is None:
            raise ValueError("DecisionContext must be initialized with at least one state DTO (household_state or firm_state).")
        if self.household_state is not None and self.firm_state is not None:
            raise ValueError("DecisionContext cannot have both household_state and firm_state.")

```

## 4. Risk & Impact Audit

-   **High Impact on Existing Code**: This change is intentionally breaking. It will cause compilation and runtime errors in all decision engines and their tests. This is a necessary step to enforce the new architecture.
-   **Test Suite Overhaul Required**: A significant portion of the test suite for agents and decisions will fail and require refactoring as outlined in Phase 3. This effort should not be underestimated.
-   **Benefit**: Successfully completing this WO will:
    -   Permanently eliminate the circular dependency.
    -   Vastly simplify the `DecisionContext` and the cognitive load for developers.
    -   Make the system more robust and easier to test.
    -   Complete a major piece of outstanding technical debt.

## 5. Verification Plan

1.  After Phase 1, confirm that `python -m mypy .` reports errors in `core_agents.py` and `firms.py` related to `DecisionContext` instantiation.
2.  After Phase 2, confirm that all decision engines now reference `context.household_state` or `context.firm_state`. A global search for `context.household` and `context.firm` should yield zero results within decision logic.
3.  After Phase 3, the full test suite (`pytest`) must pass.
4.  A full simulation run must complete without errors related to the `DecisionContext`.

---

## 🚨 Mandatory Reporting (Jules)

As you implement this refactoring, any unforeseen complexities, shortcuts taken, or new technical debt incurred must be documented and saved to a new file in `communications/insights/WO-102-Refactor-Log.md`. Specifically, log any decision logic that was difficult to convert due to its reliance on methods from the full agent object, as this may indicate a need for further componentization.
