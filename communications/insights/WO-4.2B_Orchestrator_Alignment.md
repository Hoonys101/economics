# WO-4.2B: Orchestrator Alignment & Wallet Migration - Insights & Tech Debt

## Insights

1.  **Protocol & Property Inheritance**: Inheriting from a `Protocol` class that defines a `@property` (like `IFinancialEntity.wallet`) can cause `AttributeError: property ... has no setter` if the subclass tries to assign to it in `__init__` without explicitly defining the property or setter. This was observed in `Bank` class. The fix was to implement `@property` explicitly or use internal storage `_wallet` exposed via property.
2.  **Polymorphism Maintenance**: `Government` and `CentralBank` overrode `deposit` and `withdraw` methods from `BaseAgent` (or implied interface) but failed to update the signature to accept the `currency` parameter introduced in Phase 33. This caused `SettlementSystem` to fail silently (returning `None`) because it swallowed the `TypeError`. Consistency in interface implementation is crucial.
3.  **Money Supply Definitions (M0/M2)**:
    -   **M0 (Base Money)**: Should be calculated as the sum of all currency in circulation + bank reserves. In a system where Central Bank assets represent the "negative" source, CB must be excluded from the summation to avoid zero-sum cancellation.
    -   **M2 (Money Supply)**: Must accurately reflect Fractional Reserve Banking. It is defined as `Currency in Circulation (M0 - Reserves) + Bank Deposits`. Simply summing all wallets (including Bank Reserves) and ignoring Deposits underestimates M2 when credit expansion occurs.
4.  **Transaction Processing Phase**: Moving monetary processing to `Phase_MonetaryProcessing` requires careful handling of transaction accumulation. Since `_drain_and_sync_state` clears phase-specific transactions, the monetary ledger must access the accumulated `WorldState.transactions` to capture all relevant events, while being idempotent or careful about double-counting if run multiple times (it runs once per tick).

## Technical Debt

1.  **Bank Inheritance**: `Bank` inherits from `IBankService` (Protocol). While useful for `isinstance` checks, it complicates property implementation. Consider if `Bank` should inherit from an abstract base class instead of a Protocol for shared implementation logic.
2.  **SettlementSystem Error Handling**: `SettlementSystem` uses broad `try-except` blocks that catch `TypeError` (signature mismatch) and treat it as a generic failure, logging it as "Unhandled Fail". This obscures integration issues. It should catch specific exceptions or allow `TypeError` to propagate during development/testing.
3.  **Household Mocking**: Integration tests (`test_m2_integrity.py`) heavily mock `Household`. This requires manual updates to mocks whenever `Household` or its mixins change signature (e.g., adding `currency` to `deposit`). This is brittle. Using a lightweight `TestHousehold` concrete class or factory would be more robust.
4.  **WorldState M2 Calculation**: The `calculate_total_money` implementation logic inside `WorldState` now contains specific logic for `Bank` class detection (`is_bank`). This violates separation of concerns. `ICurrencyHolder` should ideally support `get_money_supply_contribution()` or similar, or `Bank` should have a specific interface for M2 reporting to keep `WorldState` generic.
