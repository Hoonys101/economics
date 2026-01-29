# Implementation Spec: Modularization of `AIDrivenHouseholdDecisionEngine` (TD-141)

## 1. Objective

This document provides the detailed implementation specification for refactoring the monolithic `AIDrivenHouseholdDecisionEngine` into a modular coordinator-delegate pattern. This addresses the technical debt identified in `GOD_FILE_DECOMPOSITION_SPEC.md` and the risks highlighted in the Pre-flight Audit. The goal is to improve maintainability, testability, and adherence to the Single Responsibility Principle (SRP).

## 2. Architecture & Design

The refactored design will consist of a central **Coordinator** (`AIDrivenHouseholdDecisionEngine`) that orchestrates several specialized **Delegate Managers**. Each manager will be responsible for a distinct area of household decision-making.

### 2.1. Coordinator-Delegate Pattern

-   **`AIDrivenHouseholdDecisionEngine` (Coordinator)**:
    -   Its sole responsibility is to instantiate and coordinate the delegate managers.
    -   It fetches the `action_vector` from the AI engine.
    -   It creates tailored `Context` DTOs for each manager to enforce data boundaries (Interface Segregation).
    -   It calls each manager's `make_decisions` method and aggregates the returned `Order` objects.
    -   It will **not** contain any direct business logic for consumption, labor, or asset management.

-   **Delegate Managers**:
    -   `ConsumptionManager`: Handles all goods purchasing decisions.
    -   `LaborManager`: Handles all employment-related decisions.
    -   `AssetManager`: A sub-coordinator for all financial decisions, using a `StockTrader` for equity management.
    -   `HousingManager`: Handles all real-estate decisions.

### 2.2. Data Flow & Dependency Management

-   **One-Way Dependency**: The dependency flow is strictly one-way: `Coordinator -> Manager`. Managers are stateless and must not hold references to the coordinator or to each other.
-   **Context DTOs**: To prevent passing the god-object `DecisionContext`, we will introduce new, specific context DTOs for each manager (defined in `simulation/decisions/household/api.py`). This ensures each manager only receives the data it absolutely needs.
-   **God Config Object**: For the initial implementation, the full `config_module` will be passed to managers. A follow-up ticket **(TD-142)** will be automatically created to refactor this into domain-specific configuration DTOs.

## 3. Interface Specifications (`simulation/decisions/household/api.py`)

The public contract for the new managers will be defined as abstract base classes.

```python
# See simulation/decisions/household/api.py for full definitions

# --- Context DTOs to enforce Interface Segregation ---
@dataclass
class ConsumptionContext: ...

@dataclass
class LaborContext: ...

@dataclass
class AssetManagementContext: ...

@dataclass
class HousingContext: ...


# --- Manager Interfaces ---
class AbstractConsumptionManager(abc.ABC):
    @abc.abstractmethod
    def make_decisions(self, context: ConsumptionContext) -> List[Order]: ...

class AbstractLaborManager(abc.ABC):
    @abc.abstractmethod
    def make_decisions(self, context: LaborContext) -> List[Order]: ...

class AbstractStockTrader(abc.ABC):
    @abc.abstractmethod
    def place_buy_orders(self, amount: float) -> List[StockOrder]: ...
    
    @abc.abstractmethod
    def place_sell_orders(self, amount: float) -> List[StockOrder]: ...

class AbstractAssetManager(abc.ABC):
    @abc.abstractmethod
    def make_decisions(self, context: AssetManagementContext) -> List[Union[Order, StockOrder]]: ...

class AbstractHousingManager(abc.ABC):
    @abc.abstractmethod
    def make_decisions(self, context: HousingContext) -> List[Order]: ...

```

## 4. Refactored Coordinator Logic (Pseudo-code)

The `_make_decisions_internal` method of `AIDrivenHouseholdDecisionEngine` will be replaced with the following logic:

```python
def _make_decisions_internal(self, context: DecisionContext, ...) -> Tuple[List[Order], Any]:
    # 1. Initialization
    all_orders = []
    household_state = context.state
    action_vector = self.ai_engine.decide_action_vector(...)

    # 2. Instantiate Managers (Dependencies are injected here)
    # Managers are stateless and created per-call.
    consumption_manager = ConsumptionManager(household_state, self.config_module)
    labor_manager = LaborManager(household_state, self.config_module)
    asset_manager = AssetManager(household_state, self.config_module)
    housing_manager = HousingManager(household_state, self.config_module)

    # 3. Delegate Decision Making
    # Create specific contexts to pass only necessary data
    
    # --- Consumption ---
    cons_context = ConsumptionContext(
        market_data=context.market_data,
        action_vector=action_vector.consumption_aggressiveness,
        stress_config=context.stress_scenario_config
    )
    all_orders.extend(consumption_manager.make_decisions(cons_context))

    # --- Labor ---
    labor_context = LaborContext(
        market_data=context.market_data,
        current_time=context.current_time,
        action_vector=action_vector.job_mobility_aggressiveness
    )
    all_orders.extend(labor_manager.make_decisions(labor_context))

    # --- Asset Management ---
    asset_context = AssetManagementContext(
        market_snapshot=context.market_snapshot,
        market_data=context.market_data,
        current_time=context.current_time,
        macro_context=macro_context
    )
    all_orders.extend(asset_manager.make_decisions(asset_context))

    # --- Housing ---
    housing_context = HousingContext(
        market_snapshot=context.market_snapshot,
        market_data=context.market_data,
        current_time=context.current_time,
    )
    all_orders.extend(housing_manager.make_decisions(housing_context))
    
    # 4. Return aggregated orders and the original action vector
    return all_orders, action_vector
```

## 5. Verification Plan

**CRITICAL**: To ensure this major refactoring does not alter simulation behavior, a **Behavioral Equivalence Test** must be implemented as part of this task.

**File**: `tests/decisions/test_household_engine_refactor.py`

```python
import pytest
from simulation.dtos import DecisionContext
# ... other imports

# Old Engine (for comparison)
from simulation.decisions.ai_driven_household_engine_legacy import AIDrivenHouseholdDecisionEngine as LegacyEngine
# New Refactored Engine
from simulation.decisions.ai_driven_household_engine import AIDrivenHouseholdDecisionEngine as NewEngine

def test_household_engine_refactoring_equivalence(complex_decision_context_fixture: DecisionContext):
    """
    Asserts that the refactored engine produces the exact same orders as the legacy engine
    given an identical, complex input context.
    """
    # 1. Arrange: Instantiate both engine versions
    legacy_engine = LegacyEngine(ai_engine, config_module)
    new_engine = NewEngine(ai_engine, config_module)
    
    # 2. Act: Run both engines with the same complex fixture
    legacy_orders, _ = legacy_engine._make_decisions_internal(complex_decision_context_fixture)
    new_orders, _ = new_engine._make_decisions_internal(complex_decision_context_fixture)
    
    # 3. Assert: The outputs must be identical
    # A helper function might be needed to sort orders for comparison to ignore order differences.
    assert len(legacy_orders) == len(new_orders)
    
    sorted_legacy = sorted(legacy_orders, key=lambda o: (o.agent_id, o.order_type, o.item_id))
    sorted_new = sorted(new_orders, key=lambda o: (o.agent_id, o.order_type, o.item_id))

    for i, legacy_order in enumerate(sorted_legacy):
        # Use dataclass comparison
        assert legacy_order == sorted_new[i], f"Order mismatch at index {i}"

```
This test will be the primary gate for completing the refactoring.

## 6. Risk & Impact Audit (Mitigation Plan)

This specification directly addresses the risks from the Pre-flight Audit:

-   **Data Flow (`DecisionContext`)**: Mitigated by introducing specific `Context` DTOs for each manager, enforcing the Interface Segregation Principle.
-   **SRP (`AssetManager` Ambiguity)**: Mitigated by defining `AssetManager` as a coordinator that delegates to `StockTrader` and other internal logic, preventing it from becoming a smaller god class.
-   **Risks to Existing Tests**: Mitigated by the mandatory **Behavioral Equivalence Test**, which guarantees that the refactoring is behavior-neutral before the legacy code is removed.
-   **Circular Imports**: Mitigated by the strict one-way `Coordinator -> Manager` dependency model.

## 7. Golden Data & Mock Strategy

-   All tests for the new managers MUST use existing golden data fixtures (`golden_households`, etc.) from `tests/conftest.py`.
-   The equivalence test (`test_household_engine_refactoring_equivalence`) will require a new, complex fixture (`complex_decision_context_fixture`) that provides a rich `DecisionContext` to ensure all decision branches in the legacy code are executed. This fixture can be generated using `scripts/fixture_harvester.py`.

## 8. [Routine] Mandatory Reporting

Upon completion of this task, the implementing agent (Jules) MUST create a report in `communications/insights/TD-141_Refactor_Insights.md`. This report must document any unexpected challenges, discovered edge cases, or suggestions for improving the new manager APIs. This is a non-negotiable part of the task's definition of done.

---
# API Definition: `simulation/decisions/household/api.py`

```python
"""
Interfaces and Data Transfer Objects for Household Decision Managers.
This API defines the contract for the modularized household decision-making process.
"""
from __future__ import annotations
import abc
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Optional

# --- Forward References ---
from modules.household.dtos import HouseholdStateDTO
from simulation.models import Order, StockOrder
from simulation.dtos.api import MarketSnapshotDTO, MacroFinancialContext
from simulation.dtos.scenario import StressScenarioConfig
from simulation.dtos.config_dtos import HouseholdConfigDTO

# ==============================================================================
#  1. CONTEXT DTOs: Enforcing Interface Segregation Principle
# ==============================================================================

@dataclass
class ConsumptionContext:
    """Data needed for consumption decisions."""
    market_data: Dict[str, Any]
    consumption_aggressiveness: Dict[str, float]
    stress_scenario_config: Optional[StressScenarioConfig]
    expected_inflation: Dict[str, float]

@dataclass
class LaborContext:
    """Data needed for labor decisions."""
    market_data: Dict[str, Any]
    current_time: int
    job_mobility_aggressiveness: float

@dataclass
class AssetManagementContext:
    """Data needed for financial asset decisions."""
    market_snapshot: Optional[MarketSnapshotDTO]
    market_data: Dict[str, Any]
    current_time: int
    macro_context: Optional[MacroFinancialContext]
    stress_scenario_config: Optional[StressScenarioConfig] # For deflationary debt aversion

@dataclass
class HousingContext:
    """Data needed for real estate decisions."""
    market_snapshot: Optional[MarketSnapshotDTO]
    market_data: Dict[str, Any]
    current_time: int

# ==============================================================================
#  2. ABSTRACT MANAGER INTERFACES (ABC)
# ==============================================================================

class AbstractConsumptionManager(abc.ABC):
    """Interface for a manager that decides on goods purchases."""
    
    @abc.abstractmethod
    def __init__(self, state: HouseholdStateDTO, config: HouseholdConfigDTO):
        """Managers are stateful for the duration of a single decision pass."""
        ...

    @abc.abstractmethod
    def make_decisions(self, context: ConsumptionContext) -> List[Order]:
        """
        Generates buy orders for goods based on household state and market context.
        
        Returns:
            A list of `Order` objects for goods purchases.
        """
        ...

class AbstractLaborManager(abc.ABC):
    """Interface for a manager that handles employment decisions."""

    @abc.abstractmethod
    def __init__(self, state: HouseholdStateDTO, config: HouseholdConfigDTO):
        ...

    @abc.abstractmethod
    def make_decisions(self, context: LaborContext) -> List[Order]:
        """
        Generates orders to quit a job or seek employment.
        
        Returns:
            A list of `Order` objects related to labor market actions.
        """
        ...

class AbstractStockTrader(abc.ABC):
    """Interface for a manager that executes stock trades to meet a target."""

    @abc.abstractmethod
    def __init__(self, state: HouseholdStateDTO, config: HouseholdConfigDTO, market_snapshot: MarketSnapshotDTO):
        ...

    @abc.abstractmethod
    def place_buy_orders(self, amount_to_invest: float) -> List[StockOrder]:
        """Generates buy orders for a given investment amount."""
        ...
    
    @abc.abstractmethod
    def place_sell_orders(self, amount_to_sell: float) -> List[StockOrder]:
        """Generates sell orders for a given divestment amount."""
        ...

class AbstractAssetManager(abc.ABC):
    """Interface for a coordinator of financial decisions."""

    @abc.abstractmethod
    def __init__(self, state: HouseholdStateDTO, config: HouseholdConfigDTO):
        ...

    @abc.abstractmethod
    def make_decisions(self, context: AssetManagementContext) -> List[Union[Order, StockOrder]]:
        """
        Orchestrates portfolio rebalancing, liquidity management, and stock trading.
        
        Returns:
            A list of `Order` and `StockOrder` objects.
        """
        ...

class AbstractHousingManager(abc.ABC):
    """Interface for a manager that handles real estate decisions."""

    @abc.abstractmethod
    def __init__(self, state: HouseholdStateDTO, config: HouseholdConfigDTO):
        ...

    @abc.abstractmethod
    def make_decisions(self, context: HousingContext) -> List[Order]:
        """
        Decides whether to buy a primary residence or make speculative purchases.
        
        Returns:
            A list of `Order` objects for the housing market.
        """
        ...
```
