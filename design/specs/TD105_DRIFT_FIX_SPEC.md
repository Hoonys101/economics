# Specification: TD-105 Money Drift Hotfix

## 1. Overview
This document specifies the required changes to resolve the positive money drift (TD-105) originating from the `Government.invest_infrastructure` method. The core problem is that funds are credited to the `EconomicRefluxSystem` without a corresponding, guaranteed debit from the `Government`'s assets, violating the zero-sum principle for internal transfers.

The fix will be narrowly targeted to the identified method, ensuring the transaction becomes verifiably zero-sum while adhering to the project's architectural constraints.

## 2. Risk Analysis & Constraints
This solution is designed in accordance with the findings of the `TD105_DRIFT_FORENSICS.md` report and the automated pre-flight audit.

-   **Primary Constraint**: The implementation **must** continue to use the `SettlementSystem.transfer()` method for executing the transfer, as per the work order requirements.
-   **Identified Risk**: The `SettlementSystem.transfer()` method is considered untrusted and is the likely source of the bug, as it may not be performing the debit action correctly.
-   **Mitigation Strategy**: To resolve the zero-sum violation without modifying the `SettlementSystem` directly, the fix will consist of an explicit, manual debit on the `Government` agent's assets immediately following a successful transfer call. This ensures a debit is paired with every successful credit, correcting the system-level balance.

## 3. Proposed Solution

The change is confined to the `invest_infrastructure` method within the `simulation/agents/government.py` file.

### 3.1. Target File
`simulation/agents/government.py`

### 3.2. Target Method
`invest_infrastructure(self, current_tick: int, reflux_system: Any = None) -> Tuple[bool, List[Transaction]]`

### 3.3. Implementation Change

The logic for financing the investment (checking assets and issuing bonds) will remain unchanged. The modification will apply only to the execution of the transfer to the `reflux_system`.

**BEFORE (Current Flawed Logic):**
```python
        # ... (financing logic) ...

        if not self.settlement_system or not reflux_system:
             # ... (error handling) ...
             return False, []

        transfer_success = self.settlement_system.transfer(
             self,
             reflux_system,
             effective_cost,
             "Infrastructure Investment (Direct)"
        )

        if not transfer_success:
             logger.error(f"INFRASTRUCTURE_FAIL | Settlement transfer failed.")
             return False, []

        self.expenditure_this_tick += effective_cost
        self.infrastructure_level += 1

        # ... (logging) ...
        return True, transactions
```

**AFTER (Proposed Zero-Sum Logic):**
```python
        # ... (financing logic) ...

        if not self.settlement_system or not reflux_system:
             # ... (error handling) ...
             return False, []

        # [FIX] Execute the transfer, which is assumed to only perform the CREDIT action reliably.
        transfer_success = self.settlement_system.transfer(
             self,
             reflux_system,
             effective_cost,
             "Infrastructure Investment (Direct)"
        )

        if not transfer_success:
             logger.error(f"INFRASTRUCTURE_FAIL | Settlement transfer to RefluxSystem failed.")
             # If transfer fails, no debit occurs. Money balance is preserved.
             return False, []

        # [FIX] Perform the corresponding DEBIT manually to ensure a zero-sum transaction.
        # This corrects the drift by guaranteeing the sender's assets are reduced.
        try:
            self.withdraw(effective_cost)
        except InsufficientFundsError as e:
            logger.critical(
                f"GOVERNMENT_INCOHERENCE | Post-transfer debit failed for infra investment! "
                f"Assets were available pre-transfer but not post-transfer. This indicates a critical bug. "
                f"Error: {e}",
                extra={"tick": current_tick, "agent_id": self.id}
            )
            # This scenario should not happen if financing is correct, but is a safety check.
            # We do not return here, as the money has already been credited to Reflux.
            # The critical log is the indicator of a new, severe problem.

        self.expenditure_this_tick += effective_cost
        self.infrastructure_level += 1

        # ... (logging) ...
        return True, transactions
```
**Note:** The `withdraw` method (which raises `InsufficientFundsError`) should be used instead of a direct `_sub_assets` call to ensure proper validation and error handling is respected.

## 4. Verification Plan

A new, dedicated test case **must** be created to validate the zero-sum property of this specific transaction. This test is critical to prevent regressions.

-   **Test File**: `tests/test_government_finance.py` (or a new appropriate file)
-   **Test Name**: `test_invest_infrastructure_is_zero_sum`
-   **Test Logic**:
    1.  Initialize a `Government` agent and a mock `EconomicRefluxSystem` agent. Both must implement the `IFinancialEntity` interface (`assets`, `deposit`, `withdraw`).
    2.  Set initial assets for both agents (e.g., `government.assets = 10000`, `reflux.assets = 0`).
    3.  Mock the `finance_system` and `settlement_system`. The `settlement_system.transfer` mock should return `True` and call `deposit` on the receiving agent (`reflux_system`).
    4.  Record the total assets before the operation: `total_assets_before = government.assets + reflux.assets`.
    5.  Execute `government.invest_infrastructure(current_tick=1, reflux_system=reflux)`.
    6.  Record the total assets after the operation: `total_assets_after = government.assets + reflux.assets`.
    7.  **Assert `total_assets_after == total_assets_before`**.
    8.  Assert that `government.assets` has decreased and `reflux.assets` has increased by the investment cost.

## 5. Deprecation Notice & Future Work
The architectural root cause is the use of two conflicting patterns for value transfer. The direct `SettlementSystem.transfer` call is fragile and error-prone.

-   **Recommendation**: This hotfix is a temporary mitigation. The long-term solution is to refactor all instances of direct `SettlementSystem.transfer` to use the more robust pattern of generating a `Transaction` object to be processed by the central `TransactionProcessor`.
-   **Action Item**: A new technical debt ticket should be created to identify and refactor other instances of this pattern, particularly within `simulation/components/finance_department.py` (`invest_in_automation`, `invest_in_rd`, `invest_in_capex`), to use the standard `Transaction` generation pattern.
