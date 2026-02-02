# Insight: Housing Money Leak and Test Repair

## Phenomenon
A critical monetary leak of 8,000.00 was identified in housing purchases, where the money supply increased unexpectedly. Additionally, 4 unit tests in `test_housing_handler.py` were failing.

## Cause
1.  **Money Leak**: The `HousingTransactionHandler` executed a transfer of loan proceeds from the **Buyer** to the **Escrow Agent**. However, `Bank.grant_loan` had already created a **new deposit** for the Buyer (Money Creation). This resulted in the Buyer having the funds (which were then transferred), effectively keeping the system in a state where new money was created but the transaction flow implied a transfer of existing funds (or the expectation was money neutrality in the test context). The requirement was for the transfer to originate from the **Bank** (Reserves), implying the loan should be funded by the Bank's assets directly for this transaction type, or at least the Buyer shouldn't hold the deposit.
2.  **Test Failures**:
    *   `test_housing_handler.py` contained outdated logic that did not account for the `EscrowAgent`.
    *   Mocks for `Household` were failing `isinstance` checks or property access (`buyer.assets`) because `spec=Household` does not automatically configure properties returning values, leading to `TypeError` when comparing Mocks with floats.
    *   `MagicMock` of `config_module` returned Mocks for nested dictionaries (`housing`), causing calculation of `down_payment` to result in a Mock object.

## Solution
1.  **Refactored `HousingTransactionHandler`**:
    *   Implemented a "Neutralization" step: Immediately after `grant_loan` creates a deposit for the Buyer, `context.bank.withdraw_for_customer` is called to remove it.
    *   Changed the disbursement transfer to originate from `context.bank` (Reserves) to `EscrowAgent`.
    *   Updated compensation logic: If disbursement fails, `terminate_loan` is used (since the deposit is already gone, `void_loan` would fail). If final settlement fails, funds are returned to Bank (Loan Principal) and Buyer (Down Payment) separately.

2.  **Repaired Unit Tests**:
    *   Updated `tests/unit/systems/handlers/test_housing_handler.py` and `tests/unit/markets/test_housing_transaction_handler.py`.
    *   Configured `Household` mocks using `PropertyMock` for `assets` to support property access on the mock.
    *   Explicitly set `self.state.config_module.housing` dictionary to ensure `get()` returns values, not Mocks.
    *   Updated assertions to verify the new `withdraw` -> `transfer(Bank, Escrow)` flow.

## Lesson Learned
*   **Mocking Properties**: When mocking complex domain objects like `Household` that use `@property` to delegate state, standard `MagicMock(spec=Class)` is insufficient for property access. `type(mock).prop = PropertyMock(...)` is required.
*   **Mocking Configs**: Always explicitly set dictionary attributes on config mocks (e.g., `config.housing = {}`) if the code uses `getattr(config, "housing", {}).get(...)`, otherwise nested `get` calls return Mocks, causing subtle type errors.
*   **Financial Atomicity**: In a fractional reserve system, "Loan" = "New Deposit". If a transaction requires "Bank -> Seller" payment semantics, the intermediate "New Deposit" for the borrower must be explicitly handled (neutralized) to avoid double-counting or leakage if the simulation tracks broad money.
