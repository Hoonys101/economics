# Technical Specification: Corrective Actions for Regressions in Bank and Analytics Systems

## 1. Overview

A pre-flight audit has identified two critical regressions that compromise simulation integrity.
1.  A `NameError` during `Bank` initialization, causing a fatal crash.
2.  A latent `AttributeError` in `AnalyticsSystem` due to a data contract violation with `EconStateDTO`, which will cause data persistence to fail.

This specification outlines the precise, minimal changes required to correct these defects and restore system stability.

---

## 2. Task Breakdown

### Task 2.1: Correct Dependency Injection in `Bank` Constructor

- **File**: `simulation/bank.py`
- **Analysis**: The `Bank` class constructor receives a `config_manager` instance but fails to pass it to its subordinate `LoanManager`. It attempts to use an undefined variable, `config_module`, resulting in a `NameError`. This violates the dependency injection contract where a parent container is responsible for correctly provisioning its children.
- **Action**: Modify the `LoanManager` instantiation to use the correct `config_manager` variable.

#### Code Modification:
```python
# File: simulation/bank.py

# ...
class Bank(IBankService, ICurrencyHolder, IFinancialEntity):
    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager,
                 # ...
                 ):
        # ...
        self.config_manager = config_manager
        # ...

        # TD-274: Initialize Managers
        # BEFORE
        # self.loan_manager: ILoanManager = LoanManager(config_module)

        # AFTER
        self.loan_manager: ILoanManager = LoanManager(config_manager)

        self.deposit_manager: IDepositManager = DepositManager(config_manager)
        # ...
```

---

### Task 2.2: Enforce DTO Schema Adherence in `AnalyticsSystem`

- **File**: `simulation/systems/analytics_system.py`
- **Analysis**: The `AnalyticsSystem` violates the DTO data contract by attempting to access `snap.econ_state.last_labor_income` and `snap.econ_state.last_capital_income`. The authoritative schema for `EconStateDTO` (defined in `modules/household/dtos.py`) specifies these fields as `labor_income_this_tick` and `capital_income_this_tick`. This mismatch guarantees a runtime `AttributeError`.
- **Action**: Update the aggregation logic to reference the correct field names as defined in the `EconStateDTO` contract.

#### Code Modification:
```python
# File: simulation/systems/analytics_system.py

# ...
class AnalyticsSystem:
    def aggregate_tick_data(self, world_state: "WorldState"):
        # ...
            total_labor_income = 0.0
            total_capital_income = 0.0

            for h in world_state.households:
                # Access via snapshot for purity
                if hasattr(h, 'create_snapshot_dto'):
                    snap = h.create_snapshot_dto()
                    # BEFORE
                    # total_labor_income += snap.econ_state.last_labor_income
                    # total_capital_income += snap.econ_state.last_capital_income

                    # AFTER
                    total_labor_income += snap.econ_state.labor_income_this_tick
                    total_capital_income += snap.econ_state.capital_income_this_tick
        # ...
```

---

## 3. Verification Plan

- **Unit Test (Bank)**: A test case must be implemented to verify that `Bank.__init__` correctly instantiates `LoanManager` and that the `config_manager` object received by `LoanManager` is the *same instance* passed to the `Bank`.
- **Unit Test (AnalyticsSystem)**: A test case must be implemented for `AnalyticsSystem.aggregate_tick_data`. It will use a mock `WorldState` containing a `Household` agent with a pre-populated `HouseholdSnapshotDTO`. The test must assert that the `total_labor_income` and `total_capital_income` are correctly summed from the `labor_income_this_tick` and `capital_income_this_tick` fields.
- **Integration Test**: The `scripts/audit_zero_sum.py` simulation script must execute to completion without runtime errors, confirming the `NameError` is resolved.

---

## 4. 🚨 Risk & Impact Audit

- **Risk Level**: Low. The changes are highly targeted and address simple logical errors (typo, incorrect field name).
- **Impact**:
  - **Positive**: Resolves a fatal simulation crash and a guaranteed data persistence failure. Restores core banking and analytics functionality.
  - **Negative**: None. These fixes have no known downstream negative impacts.
- **Architectural Finding**: The existence of these regressions highlights a gap in automated testing for object construction and DTO-based data aggregation. The verification plan is designed to begin closing this gap.

---

## 5. 🚨 Mandatory Reporting Verification

- **Status**: Complete.
- **Report Filed**: `communications/insights/INS-20260208-Test-Coverage-Gaps.md`
- **Summary**: An insight report has been logged detailing the failure of existing tests to catch basic dependency injection and data contract violations. The report recommends a review of testing strategy to include more robust checks for component initialization and DTO schema adherence across all modules.
