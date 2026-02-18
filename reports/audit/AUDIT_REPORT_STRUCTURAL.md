# AUDIT_REPORT_STRUCTURAL: Structural Integrity Audit (v2.0)

**Date**: 2024-05-22
**Auditor**: Jules
**Scope**: God Class Identification & Abstraction Leak Detection

## 1. Executive Summary
This audit evaluates the structural integrity of the codebase against the `DTO-based Decoupling` and `Component SoC` architecture specifications. The audit focused on identifying God Classes exceeding 800 lines and tracing abstraction leaks where raw agent objects are passed into decision engines or DTOs.

**Key Findings**:
- **Two major God Classes identified**: `Firm` (1309 lines) and `Household` (1046 lines).
- **Critical Abstraction Leak in Decision Phase**: `DecisionInputDTO` leaks the raw `housing_system` object, allowing agents to execute side effects during the decision phase, violating the "Sacred Sequence".
- **Widespread Mutable State Leak**: `SimulationState` DTO exposes raw lists of `Household` and `Firm` objects to system services.

## 2. God Class Analysis

### criteria
- **Threshold**: > 800 lines of code.
- **Definition**: A class that knows too much or does too much.

### Findings

#### 1. `simulation/firms.py`
- **Class**: `Firm`
- **Lines of Code**: 1309
- **Responsibilities**:
    - Implements `ILearningAgent`, `IFinancialFirm`, `IFinancialAgent`, `ILiquidatable`, `IOrchestratorAgent`, `ICreditFrozen`, `IInventoryHandler`, `ICurrencyHolder`, `ISensoryDataProvider`, `IConfigurable`, `IPropertyOwner`, `IFirmStateProvider`.
    - Orchestrates Finance, Production, Sales, HR, Asset Management, R&D, Pricing, and Brand engines.
    - Manages direct state updates and side effects for all these domains.
- **Recommendation**:
    - Further decompose `Firm` into distinct, loosely coupled components (e.g., `ProductionManager`, `SalesManager`, `HRManager`).
    - Move orchestration logic into specialized handlers or services.

#### 2. `simulation/core_agents.py`
- **Class**: `Household`
- **Lines of Code**: 1046
- **Responsibilities**:
    - Implements `ILearningAgent`, `IEmployeeDataProvider`, `IEducated`, `IHousingTransactionParticipant`, `IFinancialEntity`, `IOrchestratorAgent`, `ICreditFrozen`, `IInventoryHandler`, `ISensoryDataProvider`, `IInvestor`, `HouseholdStateAccessMixin`.
    - Orchestrates Lifecycle, Needs, Social, Budget, Consumption, Belief, and Crisis engines.
    - Manages bio-state, econ-state, and social-state directly.
- **Recommendation**:
    - Continue decomposition into `BioComponent`, `EconComponent`, `SocialComponent`.
    - Extract `Household` orchestration logic into a lighter-weight controller.

## 3. Abstraction Leak Analysis

### Criteria
- **Leaky Abstraction**: Passing raw agent instances (`self`, `Household`, `Firm`) or system objects where DTOs should be used.
- **Sacred Sequence Violation**: Executing actions/side-effects during the Decision phase.

### Findings

#### 1. Housing System Leak in `DecisionInputDTO`
- **Location**: `simulation/dtos/api.py`
- **Code**:
    ```python
    @dataclass
    class DecisionInputDTO:
        # ...
        housing_system: Optional[Any] = None # Added for Saga initiation
    ```
- **Violation**: The `housing_system` field (typed as `Optional[Any]`) allows the raw system object to be passed into the decision-making context.
- **Impact**: In `Household.make_decision` (`simulation/core_agents.py`), this leaked object is used to execute side effects immediately:
    ```python
    # Execute Housing Action (Side Effect)
    if housing_action and input_dto.housing_system:
        # Dispatch to Housing System
        self._execute_housing_action(housing_action, input_dto.housing_system)
    ```
    This violates the "Pure Decision" principle and the "Sacred Sequence" (Decisions -> Matching -> Transactions), as actions are taken *during* the decision phase.

#### 2. Simulation State Leak in `SimulationState`
- **Location**: `simulation/dtos/api.py`
- **Code**:
    ```python
    @dataclass
    class SimulationState:
        # ...
        households: List[Household]
        firms: List[Firm]
        government: Any  # Government
        # ...
    ```
- **Violation**: The `SimulationState` DTO, intended for passing state to system services, contains lists of mutable `Household` and `Firm` objects instead of read-only DTOs or IDs.
- **Impact**: Any system service receiving `SimulationState` has full write access to all agents, bypassing any intended encapsulation or transaction boundaries.

#### 3. DecisionContext (Status: CLEAN)
- **Review**: The `DecisionContext` class in `simulation/dtos/api.py` correctly uses `state: Union[HouseholdStateDTO, FirmStateDTO]` and does not expose raw agent objects. Usage in `Household` and `Firm` adheres to this contract.

## 4. Recommendations

1.  **Strict DTO Enforcement**:
    - Remove `housing_system` from `DecisionInputDTO`. Housing actions should be returned as `Orders` or `Commands` (e.g., `HousingOrder`) from `make_decision` and processed by the `HousingSystem` in the Transaction/Matching phase.
    - Deprecate `SimulationState`'s raw agent lists. Replace `households: List[Household]` with `household_states: List[HouseholdStateDTO]` or require services to request specific agent data via an ID-based registry interface.

2.  **God Class Decomposition**:
    - Prioritize `Firm` refactoring. 1300+ lines indicates high coupling. Even with "Engine" delegation, the Orchestrator (Firm) is doing too much state management.
    - `Household` (1000+ lines) should also be trimmed, likely by moving interface implementations (e.g., `IEmployeeDataProvider`, `IInventoryHandler`) into separate component classes that the `Household` delegates to.

3.  **Purity Gates**:
    - Expand `tests/integration/test_purity_gate.py` to specifically test `DecisionInputDTO` and `SimulationState` for raw object presence, ensuring no future regressions reintroduce these leaks.
