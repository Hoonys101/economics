# Technical Specification: TD-181/TD-182 Decision Chain Abstraction Leak Resolution

- **Author**: Gemini Scribe
- **Date**: 2026-02-01
- **Status**: Proposed
- **JIRA**: TD-181, TD-182

## 1. Overview

This document proposes a refactoring of the `Household` agent's decision-making chain to eliminate critical abstraction leaks identified in Audit TD-181/TD-182. The current implementation passes live, stateful objects (e.g., `markets`, `agent_registry`) deep into the call stack, culminating in the `modules.household.decision_unit.DecisionUnit` directly accessing the internal attributes of market objects.

This tight coupling violates the Single Responsibility Principle (SRP) and Encapsulation, making the system fragile, difficult to test, and prone to cascading failures during refactoring.

The proposed solution is to enforce a strict **DTO-only data flow**. The `Household` agent will act as an Anti-Corruption Layer, translating live engine objects into pure data DTOs before passing them to the now-stateless `DecisionUnit` for orchestration.

## 2. Proposed Changes

### 2.1. New Data Transfer Objects (DTOs)

To facilitate a data-only workflow, the following DTOs will be introduced in `modules/household/api.py`.

-   **`HousingMarketUnitDTO`**: Represents a single property for sale, decoupling the `DecisionUnit` from the housing market's internal structure.
-   **`MarketSnapshotDTO`**: A comprehensive, data-only snapshot of all relevant markets, replacing the live `markets` dictionary and the unstructured `market_data` dictionary.
-   **`OrchestrationContextDTO`**: A single, unified context object for the `DecisionUnit`, containing the `MarketSnapshotDTO` and other necessary data like `current_time`.

### 2.2. Interface & Signature Changes

The method signatures for core components in the decision chain will be updated to enforce DTO usage.

#### `IDecisionUnit.orchestrate_economic_decisions`

-   **BEFORE:**
    ```python
    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: EconContextDTO, # Contained live markets object
        orders: List[Order],
        ...
    ) -> Tuple[EconStateDTO, List[Order]]:
    ```
-   **AFTER:**
    ```python
    def orchestrate_economic_decisions(
        self,
        state: EconStateDTO,
        context: OrchestrationContextDTO, # New DTO-only context
        initial_orders: List[Order]
    ) -> Tuple[EconStateDTO, List[Order]]:
    ```

#### `Household.make_decision`

The `Household` agent's `make_decision` method will be internally refactored to orchestrate this new data flow. Its external signature remains the same, but its responsibility now includes the critical DTO conversion step.

## 3. Logic & Implementation (Pseudo-code)

### 3.1. `Household.make_decision` (Refactored)

This method becomes the **Anti-Corruption Layer**.

```python
# In simulation.core_agents.Household

@override
def make_decision(self, input_dto: DecisionInputDTO) -> ...:
    # 1. Unpack live objects from the simulation engine
    markets = input_dto.markets
    market_data = input_dto.market_data
    # ... other inputs

    # 2. [NEW] Create the DTO-only Market Snapshot
    # This is the primary responsibility of the refactoring
    housing_market_obj = markets.get("housing")
    for_sale_units = []
    if housing_market_obj and hasattr(housing_market_obj, "sell_orders"):
        # Safely access and convert to DTO
        for item_id, sell_orders in housing_market_obj.sell_orders.items():
            if item_id.startswith("unit_") and sell_orders:
                ask_price = sell_orders[0].price
                # Assume quality is accessible or defaults to 1.0
                quality = getattr(sell_orders[0], 'quality', 1.0)
                for_sale_units.append(HousingMarketUnitDTO(
                    unit_id=item_id, price=ask_price, quality=quality
                ))

    housing_snapshot = HousingMarketSnapshotDTO(
        for_sale_units=for_sale_units,
        avg_rent_price=market_data.get("housing_market", {}).get("avg_rent_price", 100.0),
        avg_sale_price=market_data.get("housing_market", {}).get("avg_sale_price", 24000.0)
    )
    # ... create snapshots for loan_market, labor_market etc.
    market_snapshot = MarketSnapshotDTO(housing=housing_snapshot, ...)

    # 3. [NEW] Create the unified Orchestration Context DTO
    orchestration_context = OrchestrationContextDTO(
        market_snapshot=market_snapshot,
        current_time=input_dto.current_time,
        stress_scenario_config=input_dto.stress_scenario_config,
        config=self.config
    )

    # 4. Run the stateful decision engine to get initial orders
    # The engine still runs in the agent's context, but its output is handled safely.
    decision_context_for_engine = ... # Build the context needed by the old engine
    initial_orders, tactic = self.decision_engine.make_decisions(decision_context_for_engine, ...)

    # 5. [NEW] Delegate to the stateless DecisionUnit with DTOs only
    econ_state, refined_orders = self.decision_unit.orchestrate_economic_decisions(
        state=self._econ_state,
        context=orchestration_context,
        initial_orders=initial_orders
    )

    # 6. Update state and return results
    self._econ_state = econ_state
    return refined_orders, tactic
```

### 3.2. `DecisionUnit.orchestrate_economic_decisions` (Refactored)

This method is now purely functional and stateless.

```python
# In modules.household.decision_unit.DecisionUnit

def orchestrate_economic_decisions(
    self,
    state: EconStateDTO,
    context: OrchestrationContextDTO,
    initial_orders: List[Order]
) -> Tuple[EconStateDTO, List[Order]]:
    
    new_state = state.copy()
    refined_orders = list(initial_orders)

    # All context data is now from the DTO
    market_snapshot = context.market_snapshot
    current_time = context.current_time
    config = context.config

    # --- System 2 Housing Logic ---
    if new_state.is_homeless or current_time % 30 == 0:
        # Access market data ONLY from the snapshot DTO
        housing_snapshot = market_snapshot.housing
        loan_snapshot = market_snapshot.loan

        # OLD: market_rent = housing_market.get("avg_rent_price", 100.0)
        # NEW:
        market_rent = housing_snapshot.avg_rent_price
        market_price = housing_snapshot.avg_sale_price
        
        # ... housing decision logic (NPV, DTI) remains the same ...

    # --- Generate Housing Orders ---
    if new_state.housing_target_mode == "BUY" and new_state.is_homeless:
        target_unit = None
        best_price = float('inf')

        # OLD: for item_id, sell_orders in housing_market_obj.sell_orders.items(): ...
        # NEW:
        for unit_dto in market_snapshot.housing.for_sale_units:
            if unit_dto.price < best_price:
                best_price = unit_dto.price
                target_unit = unit_dto

        if target_unit:
             down_payment = target_unit.price * 0.2
             if new_state.assets >= down_payment:
                 buy_order = Order(
                     ...,
                     item_id=target_unit.unit_id,
                     price_limit=target_unit.price,
                     ...
                 )
                 refined_orders.append(buy_order)

    # ... all other logic (Shadow Labor, Panic Selling) is updated to use the context DTO ...
    
    return new_state, refined_orders
```

## 4. Risk & Impact Audit

The proposed changes directly address the risks identified in the pre-flight audit.

-   **Risk 1: God Object & Tight Coupling (`markets` Dictionary)**
    -   **Finding**: `DecisionUnit` directly accesses `markets['housing'].sell_orders`.
    -   **Resolution**: This is fully resolved. The `markets` dictionary is no longer passed to `DecisionUnit`. All required data is provided via the `MarketSnapshotDTO`, completely decoupling the component from the market's implementation.

-   **Risk 2: Hidden Dependency (Live `agent_registry`)**
    -   **Finding**: A live `agent_registry` is passed down the call chain.
    -   **Resolution**: While this specific refactoring focuses on the `markets` object, it establishes a clear architectural pattern. A subsequent task **must** be created to apply the same "DTO snapshot" principle to the `agent_registry`, converting it to a `Dict[int, AgentStateDTO]` at the top level. This specification provides the blueprint for that future work.

-   **Risk 3: SRP Violation (`decision_engine` Object)**
    -   **Finding**: The stateful `decision_engine` object is passed into and managed by `DecisionUnit`.
    -   **Resolution**: This is resolved. The `decision_engine` is now invoked exclusively within the `Household` agent. The `DecisionUnit` becomes a stateless orchestrator that is unaware of the `decision_engine`'s existence, thus restoring its adherence to the Single Responsibility Principle.

-   **Risk 4: Test Fragility and Refactoring Scope**
    -   **Finding**: Existing tests rely on mocking complex, live objects.
    -   **Resolution**: This is a planned and accepted consequence. The specification mandates a **full refactoring of the test suite** for `DecisionUnit`. The new tests will be simpler and more robust, as they will only need to construct and pass data-only DTOs, eliminating the need for complex mocks of engine internals. This is a one-time cost for long-term architectural health.

## 5. Verification Plan

1.  **Unit Tests for `DecisionUnit`**:
    -   Create multiple `OrchestrationContextDTO` samples representing different market conditions (e.g., no houses for sale, expensive houses, cheap houses).
    -   Verify that `orchestrate_economic_decisions` produces the correct `buy_order` or no order, based on the input DTO.
    -   Test the shadow wage and panic selling logic by manipulating the context DTO.

2.  **Integration Tests for `Household`**:
    -   Create a test environment with mock `markets` and a real `Household` agent.
    -   Verify that `Household.make_decision` correctly translates the mock market's state into an accurate `MarketSnapshotDTO`.
    -   Verify that the final output orders are consistent with the combined logic of the `decision_engine` and the `DecisionUnit`'s orchestration.

3.  **Golden Sample Definition**: A JSON file representing a `golden_orchestration_context.json` will be created in `tests/fixtures/` to standardize testing.

---
```python
# modules/household/api.py

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Tuple, Protocol, TYPE_CHECKING

from simulation.models import Order

if TYPE_CHECKING:
    # Use string forward references to avoid circular imports at runtime
    from simulation.dtos.config_dtos import HouseholdConfigDTO
    from simulation.dtos.scenario import StressScenarioConfig
    from modules.household.dtos import EconStateDTO


# --- Data Contracts for Market Snapshots (NEW) ---

class HousingMarketUnitDTO(TypedDict):
    """Represents a single, sellable housing unit in the market."""
    unit_id: str
    price: float
    quality: float

class HousingMarketSnapshotDTO(TypedDict):
    """Contains a snapshot of the housing market's state."""
    for_sale_units: List[HousingMarketUnitDTO]
    avg_rent_price: float
    avg_sale_price: float

class LoanMarketSnapshotDTO(TypedDict):
    """Contains a snapshot of the loan market's state."""
    interest_rate: float

class LaborMarketSnapshotDTO(TypedDict):
    """Contains a snapshot of the labor market's state."""
    avg_wage: float

class MarketSnapshotDTO(TypedDict):
    """
    A comprehensive, data-only snapshot of all relevant markets.
    This DTO replaces the need to pass live market objects and the loose 'market_data' dict.
    """
    housing: HousingMarketSnapshotDTO
    loan: LoanMarketSnapshotDTO
    labor: LaborMarketSnapshotDTO


# --- Updated Context for Decision Making (NEW) ---

class OrchestrationContextDTO(TypedDict):
    """
    Data-only context for the DecisionUnit's orchestration logic.
    Replaces the legacy EconContextDTO that held live objects.
    """
    market_snapshot: MarketSnapshotDTO
    current_time: int
    stress_scenario_config: Optional["StressScenarioConfig"]
    config: "HouseholdConfigDTO"


# --- Updated Interface Definition ---

class IDecisionUnit(Protocol):
    """
    Stateless unit responsible for coordinating and refining economic decisions.
    Operates exclusively on DTOs.
    """
    def orchestrate_economic_decisions(
        self,
        state: "EconStateDTO",
        context: "OrchestrationContextDTO",
        initial_orders: List[Order]
    ) -> Tuple["EconStateDTO", List[Order]]:
        """
        Refines a list of proposed orders based on System 2 logic (e.g., housing)
        and returns the final list of orders. The entire process is stateless and
        driven by pure data DTOs. This replaces the old method that took live objects.
        """
        ...
```
