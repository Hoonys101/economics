# AUDIT-S3-2A-SSOT-BYPASS: SSoT Integrity Audit (Direct Mutation Search)

## 1. [Architectural Insights]

This audit investigates instances where modules bypass the `SettlementSystem` or `IInventoryHandler` to directly mutate agent state (`cash`, `inventory`, `assets`).

### 1.1 Financial SSoT (Wallet)
The `Wallet` class implemented in `modules/finance/wallet/wallet.py` correctly enforces the `FinancialSentry` protocol. Any attempt to call `wallet.add()` or `wallet.subtract()` without an active `FinancialSentry.unlocked()` context results in a `SystemicIntegrityError`.

**Identified Bypasses & Risks:**
- **Authorized Bypasses (Government)**: The `Government` agent (`simulation/agents/government.py`) explicitly imports `FinancialSentry` and uses the `unlocked()` context in `_internal_add_assets` and `_internal_sub_assets` to mutate its own wallet. While this avoids a runtime crash, it bypasses the `SettlementSystem.transfer` protocol and the associated logging/ledgering.
- **Legacy Dead Code (Household)**: `HouseholdFinancialsMixin` (`modules/household/mixins/_financials.py`) contains direct calls to `wallet.add()` without a sentry. These methods (`_internal_add_assets`, `adjust_assets`) will throw `SystemicIntegrityError` if executed, indicating they are either dead code or logic waiting to fail.
- **Bank Ledger Desync**: The `Bank` agent directly modifies `bank_state.deposits` in `deposit_from_customer`. While this isn't a "Wallet" mutation for the bank itself, it mutates the **Liability Ledger** without going through a central settlement authority.

### 1.2 Inventory SSoT (Direct Dict Mutation)
Unlike the `Wallet`, agent `inventory` is currently implemented as a raw `Dict[str, float]` in `EconStateDTO`. This provides **ZERO** protection against direct mutation.

**Identified Violations:**
- **ConsumptionManager Bypass**: `ConsumptionManager.consume` (`modules/household/consumption_manager.py`) directly performs dictionary subtraction on `inventory`. This happens outside any `IInventoryHandler` implementation, rendering the `InventorySentry` purely symbolic for these calls.
- **Household Mixin Bypass**: `HouseholdFinancialsMixin.modify_inventory` directly modifies the dictionary.
- **Agent Initialization**: `Household.load_state` uses `InventorySentry.unlocked()` to clear and update inventory, which is the intended pattern for "system-level" operations, but highlights the lack of a proper "Inventory Holder" abstraction that can own its own guard.

## 2. [Regression Analysis]

No existing tests were broken because this audit is read-only. However, fixing the identified violations will require:
1.  **Inventory Holder Wrapper**: Replacing `Dict[str, float]` with an `Inventory` class that enforces `InventorySentry` similarly to `Wallet`.
2.  **Removal of Direct Sentry Access**: Prohibiting agents (like `Government`) from importing `FinancialSentry` directly. They should use `SettlementSystem` for all monetary adjustments.

## 3. [Test Evidence]

This mission is an audit. Verification of the "Zero-Sum" and "SSoT" principles is performed via manual code inspection.

```python
# SUCCESS: FinancialSentry enforcement verified in Wallet.py
if not FinancialSentry._is_active:
    raise SystemicIntegrityError("Direct mutation of wallet balance is FORBIDDEN. Use SettlementSystem.")
```

### Recommendation Matrix
| File | Violation Type | Hardening Point |
| :--- | :--- | :--- |
| `modules/household/mixins/_financials.py` | Potential Runtime Crash | Remove `_internal_add_assets`; use `SettlementSystem.transfer` with a 'SYSTEM' source. |
| `simulation/agents/government.py` | Protocol Bypass | Replace `FinancialSentry.unlocked()` with formalized escheatment/funding calls via `SettlementSystem`. |
| `modules/household/consumption_manager.py` | Inventory Bypass | Refactor to use an `IInventoryHandler` method instead of direct dict access. |
| `modules/household/dtos.py` | Definition Gap | Wrap `inventory: Dict` in a primitive that supports Sentry checks. |
