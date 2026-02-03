```markdown
# Refactoring Spec: TD-161, TD-204, TD-205

This document outlines the detailed specifications for three interconnected refactoring tasks aimed at improving modularity and adhering to the Single Responsibility Principle (SRP).

---

## 1. TD-161: Decouple RealEstateUnit & Create HousingService

### 1.1. Logic Steps (Pseudo-code)

1.  **Create Pure DTO**: Define a `RealEstateUnitDTO` in `modules/housing/dtos.py`. This will be a `TypedDict` or `dataclass` containing only data fields (`id`, `owner_id`, `occupant_id`, `liens`, etc.). It will have no methods.
2.  **Define Service Interface**: Create `IHousingService` in `modules/housing/api.py`. This interface will centralize all business logic related to real estate.
3.  **Implement HousingService**:
    - Create `HousingService` implementing `IHousingService`.
    - Move all real estate logic from `simulation.systems.registry.Registry` into `HousingService`. This includes methods for transferring ownership, managing liens, and handling contract status.
    - The `HousingService` will hold the collection of `RealEstateUnitDTO` objects, becoming the source of truth for housing state.
4.  **Refactor Registry**:
    - Remove the `real_estate_units` collection and all real-estate-specific methods (`_handle_real_estate_registry`, `_handle_housing_registry`, `add_lien`, `remove_lien`, `transfer_ownership`, `is_under_contract`, `set_under_contract`, `release_contract`) from `Registry`.
    - Inject `IHousingService` into `Registry`.
    - The `Registry.update_ownership` method will now delegate to `HousingService` if the transaction type is housing-related.
5.  **Refactor Call Sites**:
    - Perform a project-wide search for usages of the old `RealEstateUnit` object's methods (e.g., `unit.is_under_contract()`).
    - Replace these direct calls with calls to the new `HousingService` (e.g., `housing_service.is_under_contract(unit.id)`).
    - Update any code that directly modifies `RealEstateUnit` properties to use the service's methods (e.g., `housing_service.transfer_ownership(...)`).

### 1.2. Exception Handling

- The `HousingService` will be responsible for handling invalid operations, such as attempting to modify a non-existent unit. It should return `bool` status flags and log errors, consistent with the existing `Registry` pattern.
- Example: `transfer_ownership` will return `False` if `property_id` is not found.

### 1.3. Interface Specification (`modules/housing/api.py`)

```python
from typing import TypedDict, List, Optional, Protocol
from uuid import UUID

# DTO placed in modules/housing/dtos.py
class LienDTO(TypedDict):
    loan_id: str
    lienholder_id: int
    principal_remaining: float
    lien_type: str # e.g., 'MORTGAGE'

class RealEstateUnitDTO(TypedDict):
    id: int
    owner_id: int
    occupant_id: Optional[int]
    liens: List[LienDTO]
    # ... other data fields like address, size, quality

# API Interface
class IHousingService(Protocol):
    def get_unit(self, property_id: int) -> Optional[RealEstateUnitDTO]:
        """Retrieves a real estate unit by its ID."""
        ...

    def is_under_contract(self, property_id: int) -> bool:
        """Checks if a property is currently under a contract lock."""
        ...

    def set_under_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Locks a property for a transaction saga."""
        ...

    def release_contract(self, property_id: int, saga_id: UUID) -> bool:
        """Releases a property lock."""
        ...

    def add_lien(self, property_id: int, loan_id: str, lienholder_id: int, principal: float) -> Optional[str]:
        """Adds a lien to a property."""
        ...

    def remove_lien(self, property_id: int, lien_id: str) -> bool:
        """Removes a lien from a property."""
        ...

    def transfer_ownership(self, property_id: int, new_owner_id: int) -> bool:
        """Transfers ownership of a property."""
        ...

    def update_occupancy(self, property_id: int, occupant_id: Optional[int]) -> bool:
        """Updates the occupant of a property."""
        ...
```

### 1.4. Verification Plan

1.  **Unit Tests**: All new `HousingService` methods must have dedicated unit tests.
2.  **Integration Tests**: Create integration tests that verify the `Registry` correctly delegates to `HousingService` for housing transactions.
3.  **System-wide Search**: Execute a full-text search across the codebase for `.owner_id =`, `.liens.append`, and `.is_under_contract` to find and refactor all call sites.
4.  **Golden Sample Update**: All tests relying on `RealEstateUnit` objects (e.g., `golden_households`) must be updated. The objects themselves will become DTOs, and test logic must be adapted to use `HousingService` mocks for state changes.

### 1.5. Mocking Guide

- Tests requiring housing logic should be injected with a `Mock(spec=IHousingService)`.
- Configure the mock's return values for methods like `is_under_contract` and `get_unit`.
- **DO NOT** mock the `RealEstateUnitDTO`. It is a simple data container.

### 1.6. Risk & Impact Audit (TD-161)

- **Critical Risk**: High. The change from a smart object to a DTO is a breaking change that will affect numerous modules. `HousingSaga`, `Household` decision logic, `LifecycleManager` (for inheritance), and any system that directly inspects or modifies `RealEstateUnit` objects are impacted.
- **Architectural Constraint**: The new `HousingService` must be the **single source of truth** and the **only** component that mutates `RealEstateUnitDTO` state. The `Registry` must be fully stripped of its direct real estate logic.
- **Test Impact**: Massive. A significant number of tests will fail and require refactoring. Any test that creates `RealEstateUnit` instances with methods will break. These tests must be updated to interact with a mocked `IHousingService`.
- ** 선행 작업 권고**: A comprehensive audit of the codebase is required to identify all call sites *before* implementation begins. The `scripts/analyze_call_sites.py` script should be used to find all instances of direct property access and method calls on `RealEstateUnit` objects.

---

## 2. TD-204: Split BubbleObservatory

### 2.1. Logic Steps (Pseudo-code)

1.  **Define Interfaces**:
    - `IBubbleTracker`: Responsible for collecting and calculating market metrics.
    - `IBubbleAlerter`: Responsible for analyzing metrics and generating alerts.
2.  **Define DTOs**:
    - `MarketMetricSetDTO`: A container for metrics like price velocity, volume spikes, etc.
    - `BubbleAlertDTO`: Represents a detected bubble, containing severity, market, and supporting data.
3.  **Implement Tracker**:
    - Create `BubbleTracker` implementing `IBubbleTracker`.
    - It will have methods like `track_market(market_snapshot: MarketSnapshotDTO)` to ingest data.
    - It will have a method `get_metrics() -> Dict[str, MarketMetricSetDTO]` to expose its findings.
4.  **Implement Alerter**:
    - Create `BubbleAlerter` implementing `IBubbleAlerter`.
    - It will take an `IBubbleTracker` as a dependency in its constructor.
    - Its main method, `check_for_bubbles() -> List[BubbleAlertDTO]`, will:
        a. Call `tracker.get_metrics()`.
        b. Analyze the metrics against pre-defined thresholds from `config`.
        c. Return a list of `BubbleAlertDTO`s if any bubbles are detected.
5.  **Orchestration**:
    - A new phase, `Phase_MarketAnalysis`, will be introduced.
    - This phase will first call `bubble_tracker.track_market(...)` for all relevant markets.
    - It will then call `bubble_alerter.check_for_bubbles()` and store the results in `SimulationState`.

### 2.2. Exception Handling

- The `BubbleTracker` should handle missing data in snapshots gracefully (e.g., log a warning but not fail).
- The `BubbleAlerter` should not fail if metrics for a market are unavailable.

### 2.3. Interface Specification (`modules/analytics/api.py`)

```python
from typing import TypedDict, List, Dict, Protocol

# DTOs (can be moved to modules/analytics/dtos.py)
class MarketMetricSetDTO(TypedDict):
    market_id: str
    price_moving_avg_short: float
    price_moving_avg_long: float
    price_velocity: float # Rate of change
    volume_moving_avg: float

class BubbleAlertDTO(TypedDict):
    market_id: str
    severity: str # 'LOW', 'MEDIUM', 'HIGH'
    message: str
    supporting_metrics: MarketMetricSetDTO

# API Interfaces
class IBubbleTracker(Protocol):
    def track_market(self, market_snapshot: object) -> None: # Using 'object' for MarketSnapshotDTO
        """Updates internal metrics with data from a market snapshot."""
        ...

    def get_metrics(self) -> Dict[str, MarketMetricSetDTO]:
        """Returns the latest calculated metrics for all tracked markets."""
        ...

class IBubbleAlerter(Protocol):
    def check_for_bubbles(self) -> List[BubbleAlertDTO]:
        """Analyzes metrics from the tracker and returns any detected bubble alerts."""
        ...
```

### 2.4. Verification Plan

1.  **Tracker Tests**: Test `BubbleTracker` with various `MarketSnapshotDTO` inputs and verify that the calculated metrics in `get_metrics()` are correct.
2.  **Alerter Tests**: Test `BubbleAlerter` by providing a mocked `IBubbleTracker` with different `MarketMetricSetDTO` outputs. Verify that alerts are correctly generated based on the mocked metrics and configuration thresholds.
3.  **Integration Test**: Test the new `Phase_MarketAnalysis` to ensure it correctly calls the tracker and then the alerter, and that alerts are stored in the `SimulationState`.

### 2.5. Mocking Guide

- When testing the `BubbleAlerter`, provide a `Mock(spec=IBubbleTracker)` and configure the `get_metrics` method to return specific metric sets that should or should not trigger an alert.
- When testing components that depend on alerts, mock the `IBubbleAlerter` and configure `check_for_bubbles` to return a predefined list of `BubbleAlertDTO`s.

### 2.6. Risk & Impact Audit (TD-204)

- **Critical Risk**: Low-Medium. The main risk is that other systems may have relied on the "God Class" for convenient, synchronous access to both raw data and alerts. These systems must be identified and refactored.
- **Architectural Constraint**: The dependency must be one-way: `BubbleAlerter` depends on `IBubbleTracker`. The tracker must not have any knowledge of the alerter. This enforces a clean separation of data collection from rule-based analysis.
- **Test Impact**: All tests for the original `BubbleObservatory` must be rewritten for the two new components. Any test that relied on the observatory will need to be updated to use one or both of the new mockable interfaces.

---

## 3. TD-205: Decompose Phase3_Transaction

### 3.1. Logic Steps (Pseudo-code)

1.  **Identify Sub-Processes**: Analyze `Phase3_Transaction.execute` and break it into logically distinct, sequential steps.
2.  **Create New Phase Classes**: For each step, create a new class implementing `IPhaseStrategy`. The original order MUST be preserved.
    -   `Phase3_0_InterTickQueue`: Processes `state.inter_tick_queue`.
    -   `Phase3_1_BankLedger`: Executes `state.bank.run_tick()`.
    -   `Phase3_2_FirmObligations`: Executes `firm.generate_transactions()` for all firms.
    -   `Phase3_3_DebtServicing`: Executes `finance_system.service_debt()`.
    -   `Phase3_4_GovernmentFiscal`: Executes welfare, infrastructure, and education checks.
    -   `Phase3_5_TaxCollection`: Executes `taxation_system.generate_corporate_tax_intents()`.
3.  **Create Final Settlement Phase**:
    - Rename/refactor the original `Phase3_Transaction` to `Phase4_Settlement`.
    - This phase's `execute` method will now **only** call `self.world_state.transaction_processor.execute()`. It will process the cumulative list of transactions gathered throughout the preceding `Phase3_X` stages.
4.  **Update Orchestrator**:
    - Modify the main `TickOrchestrator`.
    - Replace the single call to `Phase3_Transaction` with a sequence of calls to the new phases in their correct order: `Phase3_0`, `Phase3_1`, ..., `Phase3_5`, and finally `Phase4_Settlement`.

### 3.2. Preserved Execution Order

The new phases will be executed in this exact sequence:

1.  `Phase3_0_InterTickQueue` (Handles carry-over transactions)
2.  `Phase3_1_BankLedger` (Bank interest and fees)
3.  `Phase3_2_FirmObligations` (Firm payments like wages, dividends)
4.  `Phase3_3_DebtServicing` (System-wide debt servicing)
5.  `Phase3_4_GovernmentFiscal` (Welfare, infrastructure, education spending)
6.  `Phase3_5_TaxCollection` (Corporate tax intent generation)
7.  `Phase4_Settlement` (Processes all transactions generated above)

### 3.3. Interface Specification

- No new API interfaces are needed. All new classes will implement the existing `simulation.orchestration.api.IPhaseStrategy`.
- The `SimulationState` object will act as the data bus, with its `transactions` list being appended to by each new phase.

### 3.4. Verification Plan

1.  **Original State Capture**: Before refactoring, run a full simulation and save the state and transaction logs at several key ticks (e.g., 10, 50, 100).
2.  **Comparison Test**: After refactoring, run the same simulation with the new phase orchestration.
3.  **Assert Equivalence**: Compare the transaction logs and final state of the refactored simulation against the captured original state. They must be identical to prove that the economic logic has been preserved. Any deviation indicates a failure in preserving the execution order.
4.  **Individual Phase Tests**: Each new phase should have a unit test to verify it correctly calls its target system (e.g., `Phase3_1_BankLedger` test verifies `bank.run_tick` is called).

### 3.5. Mocking Guide

- When testing a specific new phase (e.g., `Phase3_2_FirmObligations`), provide a `SimulationState` with mock objects for the relevant systems (e.g., mock firms). Verify that the `state.transactions` list is correctly appended to after the phase executes.

### 3.6. Risk & Impact Audit (TD-205)

- **Critical Risk**: High. The primary risk is altering the implicit economic cause-and-effect by changing the execution order. For example, processing firm wages *after* government welfare would fundamentally change household income for that tick and lead to different outcomes. The verification plan's comparison test is **mandatory and critical** to mitigate this risk.
- **Architectural Constraint**: The execution order specified in `Phase3_Transaction` is not arbitrary; it represents a chain of economic events. **This sequence is law and must be preserved.**
- **Complexity Risk**: The number of phases in the orchestrator increases, making the overall tick flow more complex to trace. Clear naming and documentation are essential.
- **State Management Risk**: Each new phase mutates the shared `SimulationState` object. There is a risk of one phase leaving the state inconsistent for the next. The "settlement" at the end helps, but the integrity of the `transactions` list as it's passed between phases is paramount.
```
