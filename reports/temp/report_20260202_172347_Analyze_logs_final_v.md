# Test & Integrity Analysis Report

## Executive Summary
The system has a critical money integrity leak of approximately 8,000 units per tick, likely originating from un- or under-funded government spending that is not tracked as authorized money creation. Additionally, 15 integration tests are failing, primarily due to outdated test setups and contract mismatches with refactored code, which obscure other potential logic flaws.

## Detailed Analysis

### 1. Money Leak (8,000 units)
- **Status**: ❌ Unresolved
- **Evidence**: `scripts/trace_leak.py` detects a consistent leak where the `Actual Delta` in total money supply exceeds the `Authorized Delta` (from credit creation) by ~8,000 units.
- **Diagnosis**: The `trace_leak.py` script accounts for the 5,000 unit loan it manually creates, but fails to account for other fiscal activities that occur during `sim.run_tick()`. Test logs for `test_fiscal_integrity.py` and `test_phase29_depression.py` show the government initiating infrastructure spending. It's highly probable the government is spending money without sufficient funds, and the settlement system is not preventing this, leading to untracked money creation. The "housing fix" addressed a specific manifestation of this, but not the root cause in the government/settlement modules.

### 2. Test Failures (15)
- **Status**: ❌ 15 Failing Tests
- **Evidence**: `logs/final_verification_tests.log`
- **Notes**: The failures have been grouped into categories to guide remediation. Many are not logic bugs but rather indicate that tests have not been updated to reflect recent code refactoring, especially around class constructors and DTOs.

## Failure Categorization

| Category | # | Description | Test Case Examples |
| :--- | :-: | :--- | :--- |
| **A. Mocking & Test Setup Issues** | 8 | Tests are broken due to outdated mocks, incorrect test data, or changes in class constructors (`__init__`). These are the highest priority as they create noise and hide real bugs. | `test_bank_deposit_balance`, `test_infrastructure_investment`, `test_process_omo_purchase_transaction`, `test_bootstrapper_injection` |
| **B. DTO/Interface Mismatches** | 2 | Core components (Engines) are being called with outdated Data Transfer Objects (DTOs) or function signatures, causing `TypeError`s at the interface level. | `test_standalone_firm_engine_uses_dto`, `test_household_engine_uses_dto` |
| **C. Core Logic & Behavior Bugs** | 3 | These appear to be genuine bugs in economic logic, such as incorrect calculations or unmet assertions. | `test_indicator_aggregation`, `test_collect_tax_legacy`, `test_scenario_b_high_income` |
| **D. Missing Attribute** | 1 | A class is missing an attribute that the test expects, indicating an incomplete refactor. | `test_household_attributes_initialization` (`gender`) |
| **E. Systemic Integration Failure** | 1 | A complex system-level test is failing due to a `TypeError` deep in the simulation run, pointing to faulty data flow between major components. | `test_depression_scenario_triggers` |

## Action Plan for Jules

Your primary goal is to restore the integrity of the test suite and then assist in plugging the money leak.

**Phase 1: Stabilize the Test Suite (Fix Mocking & Interface Errors)**

1.  **Target: Category A (Mocking & Test Setup)**
    *   **Task**: For each of the 8 failures in this category, read the `TypeError` or `AttributeError` and update the test to correctly instantiate the class or configure the mock.
    *   **Example (`test_bank_deposit_balance`)**: The error `Bank.__init__() missing 1 required positional argument: 'config_manager'` means you must provide a `config_manager` mock when creating the `Bank` object in the test.
    *   **Example (`test_process_omo_purchase_transaction`)**: The error `'MockAgent' object has no attribute '_econ_state'` means your `MockAgent` needs to have an `_econ_state` attribute, likely a `Mock` itself.

2.  **Target: Category B (DTO/Interface Mismatches)**
    *   **Task**: Fix the DTO-related failures.
    *   For `test_standalone_firm_engine_uses_dto`, find the definition of `FirmStateDTO` and update the test to initialize it with the correct keyword arguments. The error indicates `assets` is no longer a valid argument.
    *   For `test_household_engine_uses_dto`, the error `'>' not supported between instances of 'MagicMock' and 'MagicMock'` means you must configure the return values for `market_avg_wage` and `household.current_wage` on your mocks so they return numbers.

3.  **Target: Category D (Missing Attribute)**
    *   **Task**: Address the missing `gender` attribute in `test_household_attributes_initialization`. You will need to modify the `Household` class to include this attribute in its `__init__` method.

**Phase 2: Isolate and Fix Logic Bugs**

Once the test suite is stable, the remaining failures are more likely to be genuine logic bugs.

4.  **Target: Category C (Core Logic)**
    *   **Task**: Investigate `test_indicator_aggregation`. The metric `total_consumption` is `0.0` when it should be `10.0`. Trace the `indicator_pipeline` to see why consumption events are not being aggregated.
    *   **Task**: Investigate `test_collect_tax_legacy`. The test asserts a mock was called but it wasn't. Find where the call to `government.tax_agency.collect_tax` *should* be happening and why it's being skipped.

5.  **Target: The Money Leak**
    *   **Task**: Modify `scripts/trace_leak.py`. The `authorized_delta` calculation is incomplete. It needs to account for fiscal spending. After `sim.run_tick()`, query the simulation state for any government spending that occurred during the tick (e.g., from `infrastructure_manager`) and add it to `authorized_delta`.
    *   **Hypothesis**: If you correctly account for this spending, the `leak` value should drop to near zero. If it does not, the problem is more severe, likely in the `SettlementSystem` itself.
