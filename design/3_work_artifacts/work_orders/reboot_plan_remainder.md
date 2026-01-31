# Work Order: .2 - DTO Schema Alignment

**Phase:** Refactoring
**Priority:** CRITICAL
**Prerequisite:** .1
**Successor:** .3

## 1. Problem Statement

Following the creation of the `ConfigFactory` in .1, the project's data transfer objects (DTOs) remain scattered, inconsistent, and lack a single, authoritative source of truth. To enforce the "Abstraction Wall," a centralized and strict data contract definition is required before agent logic can be safely refactored.

## 2. Objective

1. **Establish Authoritative API**: Create a single `simulation/api.py` file to serve as the canonical source for all major data contracts used in the simulation.
2. **Define Core DTOs**: Populate `simulation/api.py` with strictly-typed `dataclass` definitions for all configuration and state DTOs, including `HouseholdConfigDTO`, `FirmConfigDTO`, and their nested data structures like `GoodsDTO` and `MarketHistoryDTO`.
3. **Ensure Configuration Parity**: The newly defined DTOs must remain perfectly synchronized with the central `config.py` module, as validated by the test created in .1.

## 3. Implementation Plan

1. **Create `simulation/api.py`**: This file will contain all public-facing data contracts.
2. **Define Configuration DTOs**:
 * In `simulation/api.py`, define `HouseholdConfigDTO` and `FirmConfigDTO` using `dataclasses`.
 * These DTOs will encapsulate all configuration parameters previously accessed manually from the `config` module.
3. **Define State and Nested DTOs**:
 * Define `GoodsDTO` as a `dataclass` to represent an agent's inventory of a single good (e.g., `name: str`, `quantity: float`).
 * Define `MarketHistoryDTO` as a `dataclass` to represent historical price and volume data.
 * Define `HouseholdStateDTO` and `FirmStateDTO` which will use the above DTOs to represent the complete state of an agent at a point in time (e.g., `inventory: list[GoodsDTO]`).

## 4. Verification

- The `simulation/api.py` file must be free of syntax errors and pass a `ruff check .` quality scan.
- **CRITICAL**: The `tests/test_config_parity.py` test, created in .1, **must pass**. This is non-negotiable and proves that the new DTO definitions are in perfect sync with the `config.py` master configuration file.
- This work order introduces no new business logic; therefore, existing simulation tests are not expected to change, but they will fail in the next phase if this step is incorrect.

## 5. 🚨 Risk & Impact Audit

- **Impact**: This WO is purely declarative and foundational. It creates the "contract" for all subsequent refactoring. While it doesn't alter logic itself, any error in the DTO definitions will cause cascading failures in .3.
- **Constraint**: This work directly implements the **DTO (Data Transfer Object) 필수** principle from `PROTOCOL_ENGINEERING.md`. All subsequent work must adhere to these new DTOs.
- **Dependency**: The success of .3 is entirely dependent on the correctness and completeness of the DTOs defined here.

---

# Work Order: .3 - Core Agent/Engine Refactor

**Phase:** Refactoring
**Priority:** CRITICAL
**Prerequisite:** .2
**Successor:** .4

## 1. Problem Statement

The core agent logic in `modules/household/` and `modules/firm/` violates fundamental architectural principles ("Data-Driven Purity," "SoC"). Agents currently access the monolithic `config.py` directly and are tightly coupled to the simulation's stateful services. This makes them difficult to test, maintain, and reason about.

## 2. Objective

1. **Decouple from Config**: Refactor `Household` and `Firm` agents to be completely unaware of `config.py`. All configuration must be injected via the DTOs defined in `simulation/api.py` and instantiated by the `ConfigFactory` (from .1).
2. **Enforce Data-Driven Purity**: Refactor agent decision-making methods (`make_decision`, etc.) to operate *only* on immutable state DTOs (`HouseholdStateDTO`, `MarketSnapshotDTO`) passed via a `DecisionContext` object. Direct access to live market or bank services is strictly forbidden.
3. **Prove Behavioral Equivalence**: The refactoring must not alter the macroscopic behavior of the simulation. This will be proven by ensuring all existing tests that rely on "Golden Sample" fixtures continue to pass.

## 3. Implementation Plan

1. **Refactor Agent `__init__`**:
 * Modify `modules/household/agent.py` and `modules/firm/agent.py`.
 * Remove all `import config` statements from these files and their sub-modules.
 * Update the `__init__` methods to accept a `HouseholdConfigDTO` or `FirmConfigDTO` as an argument. All internal constants and thresholds must be derived from this DTO.
2. **Refactor Decision Logic**:
 * Identify all methods responsible for making economic decisions.
 * Update their signatures to accept a single `DecisionContext` dataclass, which will contain all necessary external state (e.g., `market_snapshot: MarketSnapshotDTO`, `current_tick: int`).
 * Replace all logic that previously called services like `market.get_price()` with pure functions that operate on the data within the `DecisionContext`.
3. **Update Agent Instantiation**:
 * Locate the part of the simulation loop where agents are created.
 * Use the `ConfigFactory` (`simulation.utils.config_factory.create_config_dto`) to generate the required config DTOs.
 * Inject these DTOs during agent instantiation.

## 4. Verification

- **CRITICAL**: All unit and integration tests that rely on the `golden_households` and `golden_firms` fixtures **must pass**. This is the primary validation criterion, proving that the refactored agents behave identically to their predecessors when given the same inputs.
- **CRITICAL**: The `scripts/audit_zero_sum.py` script must pass, ensuring the refactoring did not introduce any asset leaks.
- Unit tests for the agents themselves must be updated to use the `ConfigFactory` and DTOs for test setup, eliminating manual mocking of the old `config` module.

## 5. 🚨 Risk & Impact Audit

- **Risk**: ☠️ **High risk of subtle logic changes.** This is a major "heart surgery" on the simulation engine. Extreme care must be taken. The **only** safeguard is the comprehensive verification against the migrated Golden Sample fixtures (completed in .1).
- **Principle Adherence**: This work order is the primary implementation of the **Data-Driven Purity** and **No Mock-Magic** principles outlined in `PROTOCOL_ENGINEERING.md`. It directly addresses the "Data-Driven Purity Enforcement" risk from the pre-flight audit.
- **Failure Consequence**: Any failure in the verification step indicates a deviation from original behavior, which must be found and fixed before proceeding. This WO is the lynchpin of the entire "Abstraction Wall" initiative.

---

# Work Order: .4 - Purity Gate v2 Enforcement

**Phase:** Refactoring
**Priority:** HIGH
**Prerequisite:** .3
**Successor:** None

## 1. Problem Statement

The successful refactoring in .3 establishes a clean, data-driven architecture for core agents. However, there is no automated mechanism to prevent future code from regressing into old, impure patterns. Without an automated guardrail, the architectural integrity achieved will erode over time, re-introducing the technical debt this entire initiative was designed to eliminate.

## 2. Objective

1. **Create Purity Gate Script**: Implement a new static analysis script (`scripts/verify_purity.py`) that programmatically enforces the "Data-Driven Purity" and "DTO-only" contracts.
2. **Automate Enforcement**: The script will serve as an automated architectural linter ("Purity Gate") that can be integrated into CI/CD pipelines or pre-commit hooks to fail any commit that violates the core principles.
3. **Prevent Future Debt**: Establish a permanent, automated safeguard against architectural decay.

## 3. Implementation Plan

1. **Create `scripts/verify_purity.py`**:
 * The script will use Python's built-in `ast` (Abstract Syntax Tree) module to parse the source code of target files (e.g., all files within `modules/`).
2. **Implement Check 1: No Direct Config Import**:
 * The script will traverse the AST of each file.
 * It will search for `Import` or `ImportFrom` nodes that correspond to a direct `import config`.
 * If found within a file designated as "decision logic," the script will print an error and exit with a non-zero status code.
3. **Implement Check 2: DTO-Centric Signatures**:
 * The script will analyze `FunctionDef` and `AsyncFunctionDef` nodes within agent and engine modules.
 * It will inspect the type annotations of function arguments.
 * It will raise an error if it finds arguments that are type-hinted as "live services" (e.g., `Market`, `Bank`) instead of DTOs from `simulation.api`.
4. **Integrate into Workflow**:
 * Add a step to the project's `Makefile`, `tox.ini`, or `pre-commit-config.yaml` to run `python scripts/verify_purity.py` as part of the standard test/validation suite.

## 4. Verification

- The script must execute and pass (exit code 0) when run against the clean, refactored codebase resulting from .3.
- **Negative Test Case**: Create a temporary file (`temp_impure_agent.py`) that intentionally violates the rules (e.g., `import config`). The verification process must assert that `verify_purity.py` correctly identifies the violation and fails (exits with a non-zero status code).
- The script must be documented with comments explaining how the `ast` checks work.

## 5. 🚨 Risk & Impact Audit

- **Risk**: The AST parsing logic can be complex and may have edge cases. The script needs to be robust enough to avoid false positives.
- **Impact**: This work order provides a powerful, long-term guarantee of architectural integrity. It codifies the design principles into an executable test, making them non-negotiable for all future development.
- **Principle Embodied**: This script is the literal enforcement mechanism for the **Data-Driven Purity**, **DTO Pattern**, and **SoC** pillars defined in `PROTOCOL_ENGINEERING.md`. It acts as the final "lock" on the Abstraction Wall.
