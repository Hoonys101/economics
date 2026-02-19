# Insight Report: Matching Engine Integer Math Hardening
## Executive Summary
This report details the successful hardening of the simulation's financial integrity by enforcing integer math (pennies) across key systems. The primary goal was to eliminate floating-point drift and ensure zero-sum correctness in transaction processing.

## Architectural Insights
1.  **Dual-Precision Model**:
    *   We adopted a "Dual-Precision" model where `Transaction.total_pennies` (int) serves as the Single Source of Truth (SSoT) for financial settlement.
    *   `Transaction.price` (float) is retained for backward compatibility with UI and legacy agents but is treated as a derived or display value.

2.  **Explicit Rounding**:
    *   `CommerceSystem` and `TransactionProcessor` were refactored to use `round_to_pennies(price * quantity * 100)` instead of simple integer casting. This prevents truncation errors (e.g., $0.29 * 100 -> 28.99... -> 28) and ensures accurate financial accounting.

3.  **Handler Hardening**:
    *   `GoodsTransactionHandler`, `LaborTransactionHandler`, and `HousingTransactionHandler` were updated to prioritize `total_pennies` if present.
    *   Fallback logic was improved to explicitly interpret legacy float prices as dollars and convert them to pennies using robust rounding.

4.  **Saga Integrity**:
    *   `HousingTransactionSagaHandler` was updated to explicitly set `total_pennies` and correct dollar-based prices in manual `Transaction` creations, ensuring consistency with the new standard.

## Test Evidence
The following tests confirm the correctness of the implementation:

```
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_order_book_matching_integer_math PASSED [ 16%]
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_stock_matching_mid_price_rounding PASSED [ 33%]
tests/market/test_matching_engine_hardening.py::TestMatchingEngineHardening::test_small_quantity_zero_pennies PASSED [ 50%]
tests/unit/test_goods_handler_precision.py::TestGoodsHandlerPrecision::test_legacy_price_handling PASSED [ 66%]
tests/unit/test_transaction_integrity.py::TestTransactionIntegrity::test_commerce_system_transaction_total_pennies PASSED [ 83%]
tests/unit/test_transaction_integrity.py::TestTransactionIntegrity::test_settlement_system_record_total_pennies PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 6 passed, 2 warnings in 0.35s =========================
```
