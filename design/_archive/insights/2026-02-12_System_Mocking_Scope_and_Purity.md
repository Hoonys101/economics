# Insights on Unit Test Failures and Fixes [Mission: fix_unit_tests]

## Technical Debt

### Mocking Mismatch
The `FinanceSystem` relies on `SettlementSystem` as the Single Source of Truth (SSoT) for balances, calling `settlement_system.get_balance(agent_id, currency)`. However, the unit tests mock `Government.wallet.get_balance` instead. This creates a disconnect where the system implementation correctly checks the settlement system, but the test setup fails to propagate the mocked wallet state to the settlement system mock. This indicates a drift between the implementation (using `SettlementSystem`) and the tests (expecting `Government.wallet` to be the source).

### Mock Purity
The extensive use of `MagicMock` without strict typing or `spec` constraints leads to insidious `TypeError` failures like `<` not supported between `MagicMock` and `int`. This happens because unconfigured mock methods return another `MagicMock` by default, which cannot be compared numerically. All methods returning primitive types (int, float, bool) should have explicit `return_value` or `side_effect` configured, or use `spec` to enforce return types if possible (though `MagicMock` spec primarily enforces attribute existence).

### Handler Signature Fragility
`GoodsTransactionHandler` was modified to accept a `slot` keyword argument, but the corresponding unit tests manually mocked the `add_item` method with a fixed signature `(item_id, quantity, transaction_id=None, quality=1.0)`. This lack of flexibility (e.g., missing `**kwargs`) caused tests to fail immediately upon interface changes. Tests should either use `**kwargs` for forward compatibility or be updated alongside interface changes.

## Action Items
1.  Align `FinanceSystem` unit tests to mock `SettlementSystem` behavior consistent with `Government` mock state.
2.  Update `GoodsTransactionHandler` tests to support the new `slot` parameter.
3.  Consider refactoring tests to use a shared `FakeSettlementSystem` instead of raw mocks to reduce setup boilerplate and ensure consistency.
