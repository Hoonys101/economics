# Plan: Connectivity & SSoT Enforcement

1. **Implement `FinancialSentry` and `InventorySentry` in `simulation/systems/settlement_system.py`**
   - Create a `FinancialSentry` class with `_is_active`, `unlock()` and `lock()` class methods.
   - Create an `InventorySentry` class with `_is_active`, `unlock()` and `lock()` class methods.

2. **Update Protocols in `modules/finance/api.py`**
   - Add `SystemicIntegrityError` to be raised when a sentry blocks a change.

3. **Enforce `FinancialSentry` in `modules/finance/wallet/wallet.py`**
   - Add a check at the top of `Wallet.add`, `Wallet.subtract`, and `Wallet.load_balances` that throws `SystemicIntegrityError` if `FinancialSentry._is_active` is False.
   - Wait, `Wallet` may be initialized or loaded. I should also check `__init__` if it mutates `_balances`. Or `FinancialSentry.unlock()` around AgentFactory logic. Actually, we should check `add` and `subtract`. For initialization, we can provide an override or unlock the sentry in `AgentFactory`.

4. **Enforce `InventorySentry` in `modules/agent_framework/components/inventory_component.py`**
   - Update `InventoryComponent.add_item` and `InventoryComponent.remove_item` (and `clear_inventory`) to raise `SystemicIntegrityError` if `InventorySentry._is_active` is False.

5. **Update `DefaultTransferHandler` in `simulation/systems/handlers/transfer_handler.py`**
   - Update the `handle` method. It currently just returns `True`. It should notify `MonetaryLedger` if applicable. Wait, `SettlementSystem` already notifies `MonetaryLedger` when `process_transaction` in the Engine succeeds. Let's look at `SettlementSystem.transfer`.
   - `SettlementSystem.transfer` does:
     ```python
     if self.monetary_ledger:
         is_debit_m2 = self._is_m2_agent(debit_agent)
         is_credit_m2 = self._is_m2_agent(credit_agent)
         # ...
     ```
   - Ah! The MISSION_spec says: *Implement or update the transaction handler for the generic `"transfer"` type to ensure P2P visibility. Intercept `"transfer"` transactions. Notify `MonetaryLedger` of the shift.*
   - Wait, if `SettlementSystem` *already* does this, maybe I just need to move that logic to `DefaultTransferHandler` or ensure it's called? Let me check `DefaultTransferHandler`. The requirement says: *Notify MonetaryLedger of the shift. Verify that if the transfer crosses the M2 boundary, expansion/contraction is recorded.*

6. **Wrap mutations with Sentry locks**
   - Wrap operations in `SettlementSystem` (e.g. `transfer`, `mint_and_distribute`, `transfer_and_destroy`, `execute_multiparty_settlement`, `settle_atomic`) with `FinancialSentry.unlock()` and `.lock()`.
   - Wrap operations in `GoodsTransactionHandler` / `CommerceSystem` (where inventory changes hands) with `InventorySentry.unlock()` and `.lock()`.

7. **Write Unit Tests**
   - Test Sentry Violation: manual increment/decrement of `wallet.add()` and `inventory.add_item()` raises `SystemicIntegrityError`.
   - Test Transfer Visibility: `MonetaryLedger` is updated.

8. **Pre-commit and Output**
   - Run `pytest` and `mypy`. Generate `communications/insights/WO-IMPL-CONNECTIVITY-ENFORCEMENT.md`.
