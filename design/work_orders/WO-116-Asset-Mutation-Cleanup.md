# Work Order: WO-116 - Asset Mutation Cleanup

## 1. Context
- **Objective**: Ensure 100% compliance with the `SettlementSystem` for all asset movements.
- **Reference**: `design/manuals/RELIABILITY_LEDGER.md` (Atomicity section)

## 2. Tasks for Jules
1. **Source Code Audit**:
    - Perform a regex search for `_assets +=`, `_assets -=`, `_add_assets`, `_sub_assets`, `self.assets =`, and `agent.assets =`.
2. **Refactoring**:
    - Any direct mutation of `_assets` (except inside `SettlementSystem` or official delegation like `Household._add_assets` which calls `EconComponent`) must be reviewed.
    - If a component or system is directly changing balance, it must be refactored to use the central `SettlementSystem` to ensure the double-entry integrity.
3. **Verification**:
    - Ensure all tests pass.
    - Specifically check that `InheritanceManager`, `LifecycleManager`, and `TransactionProcessor` are using the atomic protocols.

## 3. Reporting Requirement
- List all files refactored.
- Report any "Shadow Logic" found that was bypassing the accounting system.
