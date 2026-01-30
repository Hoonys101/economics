# Project Plan: Operation Green Light - Test Suite Restoration

## 1. Project Overview

- **Goal**: Restore the critically degraded test suite to a 100% pass rate. This operation will address the ~85 failures identified in `test_failures_audit.txt`, which primarily stem from recent, fundamental architectural refactoring (DTO adoption, Dependency Injection).
- **Scope**: This plan focuses exclusively on fixing existing tests. It does not include writing new tests or refactoring application logic beyond what is necessary to make tests pass. The primary areas of focus are constructor signature errors, DTO contract mismatches, and broken mocking strategies.
- **Key Metric**: `pytest` command exits with 0 failures and 0 errors.

## 2. Phases and Milestones

### Phase 1: Foundational Test Infrastructure (The "Scaffolding")

- **Objective**: Fix the most basic setup and configuration errors that block test execution.
- **Milestones**:
    - [ ] **Task 1.1: Fix Test Data Path**: Relocate or re-path the `goods.json` file to resolve `FileNotFoundError` in `test_household_ai.py`.
    - [ ] **Task 1.2: Create DTO Factories**: In a central `tests/utils/factories.py`, create helper functions to generate valid `HouseholdConfigDTO` and `FirmConfigDTO` instances with sensible defaults. This addresses the `FirmConfigDTO.__init__()` `TypeError`.
    - [ ] **Task 1.3: Create Core System Fixtures**: In `tests/conftest.py`, create fixtures for commonly injected dependencies like `SettlementSystem` and `ConfigManager` to resolve constructor errors in various system tests (e.g., `ImmigrationManager`, `EventSystem`).

### Phase 2: Agent Initialization & Core API (The "Agents")

- **Objective**: Resolve all constructor and `MagicMock`-related errors for the `Household` and `Firm` agents.
- **Milestones**:
    - [ ] **Task 2.1: Refactor `Household` Test Setups**: Systematically replace all `Household(config_module=...)` instantiations with `Household(config_dto=...)` using the factory from Task 1.2. This targets the `TypeError: Household.__init__() missing 1 required positional argument: 'config_dto'` errors.
    - [ ] **Task 2.2: Refactor `Firm` Test Setups**: Systematically replace all `Firm(config_module=...)` instantiations with the new correct signature, likely using the `FirmConfigDTO` factory from Task 1.2. This targets the `TypeError: Firm.__init__() got an unexpected keyword argument 'config_module'` errors.
    - [ ] **Task 2.3: Resolve `DecisionContext` Mismatches**: Update tests that create `DecisionContext` to use its new constructor signature, removing the incorrect `firm` and `household` keyword arguments.
    - [ ] **Task 2.4: Purge `MagicMock`-Induced `TypeError`s**: Using the DTO factories and `GoldenLoader` where appropriate, populate DTOs with real numeric values to fix comparison errors (e.g., `TypeError: '>' not supported between instances of 'MagicMock' and 'float'`). This is a critical step to ensure logic can be evaluated.

### Phase 3: System & Integration Failures (The "Wiring")

- **Objective**: Address failures in the integration test suite and complex system interactions.
- **Milestones**:
    - [ ] **Task 3.1: Fix Orchestration Logic**: Remove references to the obsolete `Phase4_Lifecycle` and adapt tests to the new `tick_orchestrator.py` sequence as defined in `WO-103`.
    - [ ] **Task 3.2: Correct `make_decision` Unpacking**: Update tests that call `agent.make_decision()` to handle the new, non-iterable return value, fixing the `TypeError: cannot unpack non-iterable Mock object`.
    - [ ] **Task 3.3: Repair `AttributeError`s**: Investigate and fix `AttributeError` failures by updating method calls (e.g., `_attempt_secondary_offering`) and mock object attributes to match the current codebase.

### Phase 4: Logic & Assertion Failures (The "Final Polish")

- **Objective**: Fix the final layer of failures, which likely represent true application logic bugs uncovered by the architectural fixes.
- **Milestones**:
    - [ ] **Task 4.1: Triage Production & Economic Logic**: Investigate and fix assertion failures like `test_production_boost_from_fertilizer_tech` (`assert 0.0 > 0`), which were likely masked by `MagicMock` errors.
    - [ ] **Task 4.2: Triage Financial & Transactional Logic**: Debug and resolve failures in `test_finance_bailout.py`, `test_double_entry.py`, and `test_inheritance_manager.py`. These are likely caused by incorrect mock setups for the `SettlementSystem` or other financial components.
    - [ ] **Task 4.3: Full Regression Sweep**: Execute the entire test suite (`pytest`) and address any remaining, isolated failures until a 100% pass rate is achieved.

## 3. Risk Assessment

- **Primary Risk**: High interconnectedness. Fixes in core components (Phase 1 & 2) may cause new, unexpected failures in downstream tests (Phase 3 & 4).
- **Mitigation**: A phased approach is designed to manage this. After each phase, a partial test run will be executed on the fixed modules to ensure stability before proceeding.
- **Secondary Risk**: "God Class" brittleness (`Household`, `Firm`). Changes to fix one test may break another.
- **Mitigation**: Extreme care will be taken when modifying shared fixtures for these classes. Changes will be minimal and targeted. This plan does not scope a full refactor of these classes, only the restoration of their tests.

## 4. Communication Plan

- This `task.md` will serve as the single source of truth for progress.
- Upon completion of the entire plan, a final report confirming the 100% pass rate will be generated.
