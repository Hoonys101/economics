# Spec: Workstream C - Markets & Systems Unit Tests

## Objective
Fix unit tests related to market handlers and system services.

## Scope
1.  **tests/unit/markets/**:
    *   Fix `test_housing_transaction_handler.py`.
    *   Fix `test_loan_market.py` and `test_order_book_market.py`.
2.  **tests/unit/systems/**:
    *   Update `test_inheritance_manager.py` and `test_settlement_system.py`.
    *   Repair `test_housing_system.py`.

## Technical Note
Many failures are due to `Agent` mocks lacking `.id` or `._econ_state` attributes. Ensure all setup methods provide these.
