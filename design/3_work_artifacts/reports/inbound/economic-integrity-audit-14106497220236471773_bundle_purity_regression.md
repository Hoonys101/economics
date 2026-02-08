# Technical Insight Report: Bundle Purity Regression Fix

## 1. Problem Phenomenon

During the execution of `audit_zero_sum.py` and `smoke_test.py`, the simulation failed with an `AttributeError` during the post-sequence phase (analytics aggregation).

**Stack Trace:**
```
File "/app/simulation/orchestration/phases/post_sequence.py", line 104, in execute
    agent_states, transactions, indicators, market_history = self.world_state.analytics_system.aggregate_tick_data(self.world_state)
                                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/simulation/systems/analytics_system.py", line 137, in aggregate_tick_data
    total_labor_income += snap.econ_state.last_labor_income
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'EconStateDTO' object has no attribute 'last_labor_income'
```

Additionally, a reported `NameError` in `Bank` constructor was investigated as per the mission guide.

## 2. Root Cause Analysis

### 2.1 AnalyticsSystem AttributeError
The `AnalyticsSystem` was attempting to access `last_labor_income` and `last_capital_income` from `EconStateDTO` (via `HouseholdSnapshotDTO`). However, an inspection of `modules/household/dtos.py` revealed that `EconStateDTO` defines these fields as:
```python
    # Income Tracking (Transient per tick)
    labor_income_this_tick: float
    capital_income_this_tick: float
```
The mismatch between the consumer (`AnalyticsSystem`) and the contract (`EconStateDTO`) caused the crash. This likely resulted from a rename or refactor in the DTO that was not propagated to the analytics system.

### 2.2 Bank NameError
The mission guide suggested a potential `NameError` due to `config_module` being passed to `LoanManager` instead of `config_manager`.
Investigation of `simulation/bank.py` revealed that the code was already correct:
```python
        # TD-274: Initialize Managers
        self.loan_manager: ILoanManager = LoanManager(config_manager)
        self.deposit_manager: IDepositManager = DepositManager(config_manager)
```
And `LoanManager` in `modules/finance/managers/loan_manager.py` accepts a `config` argument which is compatible with `ConfigManager`.
No actual regression was found in the codebase provided, suggesting the issue might have been fixed in a previous commit or was a false positive in the guide.

## 3. Solution Implementation Details

### 3.1 AnalyticsSystem Fix
Updated `simulation/systems/analytics_system.py` to use the correct DTO field names:
- Replaced `snap.econ_state.last_labor_income` -> `snap.econ_state.labor_income_this_tick`
- Replaced `snap.econ_state.last_capital_income` -> `snap.econ_state.capital_income_this_tick`

### 3.2 Bank Verification
Verified `simulation/bank.py` and confirmed no changes were needed.

## 4. Lessons Learned & Technical Debt

- **DTO Contract Stability**: DTOs serve as the contract between systems. Changes to DTO fields must be strictly audited to ensure all consumers are updated. The `Purity Gate` checks types but might not catch dynamic attribute access if `getattr` or `hasattr` isn't used (though here it was direct access).
- **Automated Regression Testing**: The `smoke_test.py` caught this error immediately. Ensuring these tests run on every PR is crucial.
- **Documentation Accuracy**: The mission guide contained a potential false alarm regarding `Bank`. Keeping task descriptions in sync with the codebase state is important to avoid confusion.

## 5. Verification Results

- `scripts/verify_purity.py`: **Passed** (No architectural violations)
- `scripts/audit_zero_sum.py`: **Passed** (Money Supply Delta: 0.0000)
- `scripts/smoke_test.py`: **Passed**