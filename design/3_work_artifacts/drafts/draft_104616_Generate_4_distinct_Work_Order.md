# Work Order: WO-144 - Government Structure Refactor

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** `TD-140`, `TD-141`, `TD-142` (God File Decomposition)

## 1. Objective
Decompose the monolithic government entity into a modern Facade/Component structure, following the architectural precedent set by the `Household` agent refactoring. This establishes a clean, extensible foundation for implementing sophisticated policy managers.

## 2. Implementation Plan

### Task A: Create New Module Structure
1.  Create the directory structure for the new `government` module:
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
1.  In `modules/government/dtos.py`, define the core data structures for the module. These will be imported by `api.py`.
    - `TaxBracketDTO`
    - `FiscalPolicyDTO`
    - `MonetaryPolicyDTO`
    - `GovernmentStateDTO`

### Task C: Define Public API and Interfaces
1.  In `modules/government/api.py`, define the public contract for the module:
    - Import all DTOs from `dtos.py`.
    - Define the `IFiscalPolicyManager` protocol.
    - Define the `IMonetaryPolicyManager` protocol.
    - Define the `Government` facade protocol for type hinting purposes.

## 3. Technical Constraints

- **Architectural Alignment**: The new structure MUST mirror the post-refactoring state defined in `design/3_work_artifacts/specs/GOD_FILE_DECOMPOSITION_SPEC.md`. No code should be written against the current, monolithic government entity.
- **DTO Purity**: All data exchange between the `Government` agent and its components, or between the `Government` and other systems (like the `TickScheduler`), MUST use the DTOs defined in `dtos.py`. Raw dictionaries are forbidden.
- **Interface Segregation**: The `api.py` file is the single public entry point. Internal components (`government_agent.py`, `components/*`) should not be imported directly by other modules.

## 4. Success Sign-off Criteria

- **[✅] Code Created**: The new directory structure and all specified files (`api.py`, `dtos.py`, empty component files) are created.
- **[✅] Linting & Type Check**: All new files pass `ruff` and `mypy` checks without errors.
- **[✅] Code Review**: A peer review confirms that the DTOs and Protocol interfaces in `api.py` and `dtos.py` perfectly match the definitions in `design/3_work_artifacts/drafts/draft_103745_Draft_a_comprehensive_Implemen.md`.

---

# Work Order: WO-145 - Progressive Tax System

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** WO-144

## 1. Objective
Implement a progressive tax system as a core component of the government's fiscal policy, serving as an automatic stabilizer for the economy.

## 2. Implementation Plan

### Task A: Implement Fiscal Policy Manager
1.  In `modules/government/components/fiscal_policy_manager.py`, create the `FiscalPolicyManager` class that implements the `IFiscalPolicyManager` protocol.
2.  Implement the `determine_fiscal_stance` method. For the initial implementation, this method will return a static, default `FiscalPolicyDTO` as defined in the spec (e.g., 10%/25%/40% brackets). Dynamic adjustment is a future task.
3.  Implement the `calculate_tax_liability` method based on the pseudo-code provided in the specification. This method will calculate the total tax owed for a given income based on the progressive brackets in the `FiscalPolicyDTO`.

### Task B: Integration with Tax System
1.  The existing `TaxAgency` (or its post-refactoring equivalent) must be updated to use the new `FiscalPolicyManager`.
2.  The `GOVERNMENT_POLICY` phase in the `TickScheduler` must execute before the `TAX_COLLECTION_PHASE` to ensure the correct tax policy is available for the current tick.

## 3. Technical Constraints

- **Statelessness**: The `FiscalPolicyManager` MUST be stateless. All calculations should depend only on the arguments passed to its methods (e.g., `MarketSnapshotDTO`, `FiscalPolicyDTO`, `income`).
- **DTO Purity**: The manager must operate exclusively on DTOs for its inputs and outputs. It should not hold any internal state or directly access database repositories.
- **Unidirectional Data Flow**: The manager receives data and returns a result. It does not call out to other agents or managers directly.

## 4. Success Sign-off Criteria

- **[✅] Unit Tests Passed**: A new test file, `tests/modules/government/components/test_fiscal_policy_manager.py`, is created. It includes tests for `calculate_tax_liability` with multiple income scenarios (e.g., within a single bracket, across multiple brackets, at bracket boundaries) that all pass.
- **[✅] Integration Verified**: An integration test confirms that the `TaxAgency` correctly uses the policy from `FiscalPolicyManager` to calculate and levy taxes.
- **[✅] Code Review**: A peer review confirms the implementation adheres to the stateless and DTO-purity constraints.

---

# Work Order: WO-146 - Monetary Policy & Taylor Rule

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** WO-144

## 1. Objective
Implement a Taylor Rule-based monetary policy to allow the government (acting as a central bank) to manage inflation and employment by adjusting a target interest rate.

## 2. Implementation Plan

### Task A: Implement Monetary Policy Manager
1.  In `modules/government/components/monetary_policy_manager.py`, create the `MonetaryPolicyManager` class that implements the `IMonetaryPolicyManager` protocol.
2.  Implement the `determine_monetary_stance` method. This method will calculate the new `target_interest_rate` based on the Taylor Rule formula and pseudo-code provided in the implementation specification.

### Task B: Integration with Financial Markets
1.  The `target_interest_rate` from the resulting `MonetaryPolicyDTO` must be made available to the financial system.
2.  The new `finance_manager.py` (from `TD-142`) and the `LoanMarket` will use this rate as the base for setting their own interest rates. The `GOVERNMENT_POLICY` phase must run before agents make financial decisions.

## 3. Technical Constraints

- **Statelessness**: The `MonetaryPolicyManager` MUST be stateless. Its calculations must depend solely on the `MarketSnapshotDTO` passed into its methods.
- **DTO Purity**: The manager must receive a `MarketSnapshotDTO` and return a `MonetaryPolicyDTO`. It must not interact directly with other components or repositories.
- **Adherence to Future Architecture**: The integration MUST target the new, decoupled `finance_manager.py` as defined in `GOD_FILE_DECOMPOSITION_SPEC.md`, not the current monolithic `CorporateManager`. Mock implementations must be used for testing until `TD-142` is complete.

## 4. Success Sign-off Criteria

- **[✅] Unit Tests Passed**: A new test file, `tests/modules/government/components/test_monetary_policy_manager.py`, is created. It includes tests verifying the Taylor Rule calculation for various `inflation_gap` and `unemployment_gap` scenarios, all of which must pass.
- **[✅] Integration Verified**: An integration test confirms that the `target_interest_rate` is correctly propagated to and used by the new financing modules (even if they are mocks initially).
- **[✅] Code Review**: A peer review confirms the implementation adheres to the statelessness constraint and correctly implements the Taylor Rule formula.

---

# Work Order: WO-147 - Soft Landing Verification Suite

**Phase:** 28 (Structural Stabilization)
**Priority:** HIGH
**Prerequisite:** WO-145, WO-146

## 1. Objective
Create a new, dedicated verification suite to prove the effectiveness of the fiscal and monetary stabilizers. This script will replace deprecated scenario tests and become the new benchmark for macroeconomic stability.

## 2. Implementation Plan

### Task A: Create Verification Script
1.  Create a new script: `scripts/verify_soft_landing.py`.

### Task B: Implement Baseline Scenario
1.  Add logic to run a 1000-tick simulation with the new stabilizers **disabled**. This should be controlled by a configuration flag that enforces a flat tax and a fixed interest rate.
2.  Record and calculate key metrics: GDP, inflation, unemployment, Gini coefficient, and their volatility (standard deviation).
3.  Count the number and duration of recessions (defined as >= 2 consecutive ticks of negative GDP growth).
4.  Save the aggregated results to `reports/soft_landing_baseline.json`.

### Task C: Implement Stabilizer Scenario
1.  Add logic to run the same 1000-tick simulation with the new stabilizers **enabled**.
2.  Record and calculate the same metrics as the baseline.
3.  Save the aggregated results to `reports/soft_landing_stabilized.json`.

### Task D: Implement Verification and Reporting
1.  Add assertion logic to the script that compares the two scenarios.
2.  The script should generate comparison plots, such as `gdp_volatility.png` and `inflation_stability.png`, to visualize the difference.

## 3. Technical Constraints

- **Test Suite Transition**: This script explicitly marks the deprecation of old scenario tests (e.g., `verify_golden_age.py`). The CI/CD pipeline should be updated to run this new script as the primary macro-level verification.
- **Configurability**: The script must be easily configurable to toggle the stabilizers on or off for the two separate runs.

## 4. Success Sign-off Criteria

- **[✅] Script Execution**: The `scripts/verify_soft_landing.py` script runs to completion without errors for both scenarios.
- **[✅] Artifact Generation**: The script successfully generates all specified output files: `reports/soft_landing_baseline.json`, `reports/soft_landing_stabilized.json`, and the comparison plots.
- **[✅] Verification Pass**: The final assertions within the script pass, confirming that:
    - GDP and Inflation volatility are reduced by at least 25% in the stabilized scenario compared to the baseline.
    - The number of recessionary periods is demonstrably reduced.
