# Wave 2.1: Firm Architecture Overhaul - Insight Report

## 1. Architectural Insights

### Technical Debt Identified
1.  **Penny/Dollar Ambiguity**: The `Firm` and its engines (`SalesEngine`, `HREngine`, `FinanceEngine`) suffered from inconsistent handling of monetary values. `Transaction.price` was treated as both pennies and dollars in different contexts, and `total_pennies` was sometimes calculated by multiplying pennies by 100, leading to massive inflation bugs (100x cost).
2.  **Legacy Logic Leaks**: `Firm` still contained some legacy logic for order generation that bypassed the new Engine architecture.
3.  **Protocol Violations**: Engines were not explicitly implementing their `@runtime_checkable` protocols, relying on duck typing which is fragile.

### Architectural Decisions
1.  **Strict Penny Arithmetic**: All internal calculations and DTO fields (e.g., `SalesPostAskContextDTO.price_pennies`) now strictly use integer pennies.
2.  **Explicit Display Values**: `Transaction.price` (float) is now consistently set to `total_pennies / 100.0` for display/logging purposes, while `total_pennies` (int) remains the Source of Truth (SSoT) for settlement.
3.  **DTO Purity**: Context DTOs are updated to reflect the penny-first architecture (e.g., renaming `price` to `price_pennies`).
4.  **Protocol Implementation**: All engines now explicitly inherit from their respective Protocols (`ISalesEngine`, `IHREngine`, `IFinanceEngine`, `IProductionEngine`).

## 2. Regression Analysis

### Broken Tests
- `tests/unit/components/test_engines.py`: `test_post_ask` failed because `SalesPostAskContextDTO` changed signature (renamed `price` to `price_pennies`).
- `tests/unit/test_firms.py`: `test_post_ask` failed because `Firm.post_ask` logic changed to expect pennies or convert float-dollars to pennies correctly.

### Fix Strategy
- Updated tests to use `price_pennies` in DTO construction.
- Updated `Firm.post_ask` to handle both `float` (dollars) and `int` (pennies) inputs to support legacy test calls while enforcing penny logic internally.
- Restored `TestProductionEngine` which was accidentally deleted during verification updates.

## 3. Test Evidence

### Verification Script (`verify_firm_architecture.py`)
```
verify_firm_architecture.py::test_sales_engine_post_ask_fix PASSED       [ 50%]
verify_firm_architecture.py::test_sales_engine_marketing_fix PASSED      [100%]
```

### Unit Tests
```
tests/unit/components/test_engines.py::TestHREngine::test_create_fire_transaction PASSED [  7%]
tests/unit/components/test_engines.py::TestHREngine::test_process_payroll PASSED [ 14%]
tests/unit/components/test_engines.py::TestSalesEngine::test_post_ask PASSED [ 21%]
tests/unit/components/test_engines.py::TestSalesEngine::test_generate_marketing_transaction PASSED [ 28%]
tests/unit/components/test_engines.py::TestFinanceEngine::test_generate_financial_transactions PASSED [ 35%]
tests/unit/components/test_engines.py::TestProductionEngine::test_produce_depreciation PASSED [ 42%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_no_liabilities PASSED [ 50%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_liabilities PASSED [ 57%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_with_treasury_shares PASSED [ 64%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_negative_net_assets PASSED [ 71%]
tests/unit/test_firms.py::TestFirmBookValue::test_book_value_zero_shares PASSED [ 78%]
tests/unit/test_firms.py::TestFirmProduction::test_produce PASSED        [ 85%]
tests/unit/test_firms.py::TestFirmSales::test_post_ask PASSED            [ 92%]
tests/unit/test_firms.py::TestFirmSales::test_adjust_marketing_budget_increase PASSED [100%]
```
