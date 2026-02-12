# Insight Report: God-Class Decomposition (Part 2 - Factories)

## 1. Overview
This report documents the execution of Phase 2 of the God-Class decomposition, focusing on extracting creation and cloning logic from `Firm` and `Household` orchestrators into dedicated factories, and extracting domain logic into stateless engines (`BrandEngine`, `ConsumptionEngine`).

## 2. Architecture Changes

### 2.1. Factories (Simulation Layer)
- **`simulation/factories/household_factory.py`**: Created to consolidate household creation logic. Merged logic from `modules/household/factory.py` and `simulation/factories/agent_factory.py`. Uses `HouseholdFactoryContext` for dependency injection.
- **`simulation/factories/firm_factory.py`**: Created to handle `Firm` creation and cloning. Implements deep copy logic for mitosis, ensuring inventory quality is preserved (fixing a potential bug in the legacy `Firm.clone` method).
- **`simulation/factories/agent_factory.py`**: Deprecated. Retained as a wrapper/stub for legacy test compatibility but issues a `DeprecationWarning`.

### 2.2. Domain Engines (Module Layer)
- **`modules/firm/engines/brand_engine.py`**: Created stateless `BrandEngine`. Replaces the stateful `BrandManager` component. Operates directly on `SalesState` which now includes brand metrics (`adstock`, `brand_awareness`, `perceived_quality`).
- **`modules/household/engines/consumption_engine.py`**: Renamed from `consumption.py`. Enhanced to include `apply_leisure_effect` logic, allowing `Household` to delegate this calculation.

### 2.3. Orchestrator Updates
- **`Household` (`simulation/core_agents.py`)**:
    - Removed `clone()` method.
    - Delegated `apply_leisure_effect` to `ConsumptionEngine`.
    - Line count reduced (~1058 lines). Still a God Class, but responsibilities are cleaner.
- **`Firm` (`simulation/firms.py`)**:
    - Removed `clone()` method.
    - Removed `BrandManager` component.
    - Integrated `BrandEngine` (stateless).
    - Line count is ~1400 lines (due to imports and verbose DTO mapping). Further decomposition of `finance_engine` and `production_engine` logic needed to reach <800 lines.

## 3. Dependency Injection & Integration
- **`DemographicManager`**: Refactored to accept `IHouseholdFactory` via constructor injection. Removed internal factory instantiation.
- **`Initializer`**: Updated to instantiate `HouseholdFactory` early (after markets and AI trainer) and inject it into `DemographicManager` and `AgentLifecycleManager`.

## 4. Testing & Verification
- **Unit Tests**:
    - `tests/unit/test_firms.py`: Updated to assert against `sales_state` instead of `brand_manager`.
    - `tests/simulation/factories/test_agent_factory.py`: Updated to handle Zero-Sum Integrity (assets not auto-loaded via state) by explicitly depositing funds in tests.
    - `tests/unit/test_household_factory.py`: Verified new factory logic.
- **Integrity**: Zero-Sum constraints on asset initialization are enforced by the factory (requiring explicit transfer logic) and `Household.load_state`.

## 5. Technical Debt & Future Work
- **Firm System Integration**: `FirmSystem` still manually instantiates `Firm` agents. It should be refactored to use `FirmFactory`.
- **God Class Size**: Both `Firm` and `Household` remain large. Next phases should focus on extracting `FinanceEngine` (Firm) and `BudgetEngine` (Household) logic more aggressively, moving state management entirely to DTOs and making orchestrators thin shells.
- **Legacy Factory Cleanup**: `simulation/factories/agent_factory.py` should be removed once all tests are updated to use the new factory directly.

## 6. Conclusion
Phase 2 successfully decoupled creation logic and extracted key domain logic. The architecture is more modular, with clearer separation of concerns between state (DTOs), logic (Engines), and lifecycle management (Factories).
