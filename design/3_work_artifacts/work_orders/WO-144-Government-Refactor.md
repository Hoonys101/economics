# Work Order: - Government Structure Refactor

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** `TD-140`, `TD-141`, `TD-142` (God File Decomposition)

## 1. Objective
Decompose the monolithic government entity into a modern Facade/Component structure, following the architectural precedent set by the `Household` agent refactoring. This establishes a clean, extensible foundation for implementing sophisticated policy managers.

## 2. Implementation Plan

### Task A: Create New Module Structure
1. Create the directory structure for the new `government` module:
 ```
 modules/
 └── government/
 ├── api.py
 ├── government_agent.py
 ├── dtos.py
 └── components/
 ├── __init__.py
 ├── fiscal_policy_manager.py
 └── monetary_policy_manager.py
 ```

### Task B: Define Data Transfer Objects (DTOs)
1. In `modules/government/dtos.py`, define the core data structures for the module. These will be imported by `api.py`.
 - `TaxBracketDTO`
 - `FiscalPolicyDTO`
 - `MonetaryPolicyDTO`
 - `GovernmentStateDTO`

### Task C: Define Public API and Interfaces
1. In `modules/government/api.py`, define the public contract for the module:
 - Import all DTOs from `dtos.py`.
 - Define the `IFiscalPolicyManager` protocol.
 - Define the `IMonetaryPolicyManager` protocol.
 - Define the `Government` facade protocol for type hinting purposes.

## 3. Technical Constraints

- **Architectural Alignment**: The new structure MUST mirror the post-refactoring state defined in `design/3_work_artifacts/specs/GOD_FILE_DECOMPOSITION_SPEC.md`. No code should be written against the current, monolithic government entity.
- **DTO Purity**: All data exchange between the `Government` agent and its components, or between the `Government` and other systems (like the `TickScheduler`), MUST use the DTOs defined in `dtos.py`. Raw dictionaries are forbidden.
- **Interface Segregation**: The `api.py` file is the single public entry point. Internal components (`government_agent.py`, `components/*`) should not be imported directly by other modules.

## 4. Success Sign-off Criteria

- [ ] **Code Created**: The new directory structure and all specified files (`api.py`, `dtos.py`, empty component files) are created.
- [ ] **Linting & Type Check**: All new files pass `ruff` and `mypy` checks without errors.
- [ ] **Code Review**: A peer review confirms that the DTOs and Protocol interfaces in `api.py` and `dtos.py` perfectly match the definitions in Phase 28 Spec.
