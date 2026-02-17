# Insight Report: Liquidate DTO Contracts (TD-DTO-DESYNC-2026)

## [Architectural Insights]

### 1. DTO Transition to Frozen Dataclasses
The transition to `frozen=True` dataclasses (`BorrowerProfileDTO`, `LoanInfoDTO`) significantly improves type safety and immutability across system boundaries. However, it necessitates strict adherence to attribute access (dot notation) over dictionary access (`__getitem__`). This refactor revealed widespread legacy usage of dictionary-style access in tests and deprecated methods, which have now been liquidated.

### 2. Float vs Integer Monetary Values
A key architectural tension identified is the mismatch between the "Zero-Sum Integrity" mandate (using integer pennies) and the new DTO specifications (using `float` for `gross_income`, `amount`, etc.).
- **Resolution:** The system now treats `float` in DTOs as a transport format for monetary values (e.g., `100.0` represents 100 pennies or units depending on context, but consistently mapped).
- **Risk:** Potential precision loss if large integers are converted to floats and back, though unlikely at current simulation scale.
- **Conversion:** Explicit casting (`float()`, `int()`) has been introduced at boundary layers (`process_loan_application`, `get_debt_status`) to bridge the gap between the `FinancialLedger` (int pennies) and external DTOs (floats).

### 3. Protocol Evolution
`IFinancialAgent` has been evolved to support new getter methods (`get_liquid_assets`, `get_total_debt`) while retaining legacy transaction methods (`_deposit`, `_withdraw`, `get_balance`) to ensure backward compatibility with the `SettlementSystem`. This "additive" approach prevents system-wide breakage while fulfilling new interface requirements.

### 4. Robust Engines
`LoanRiskEngine` has been hardened to accept both Dictionary (Legacy/Engine-Internal) and Object (New DTO) access patterns for `BorrowerProfileDTO` data. This ensures that even if upstream adapters fail or partial migrations occur, the engine remains operational without raising `AttributeError` or `TypeError`.

## [Test Evidence]

```text
============================= test session starts ==============================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.3, cov-6.0.0, mock-3.14.0
collected 37 items

tests/unit/finance/call_market/test_service.py .....                     [ 13%]
tests/unit/finance/engines/test_finance_engines.py ......                [ 29%]
tests/unit/finance/test_bank_service_interface.py ......                 [ 45%]
tests/unit/finance/test_credit_scoring.py .....                          [ 59%]
tests/unit/finance/test_finance_system_refactor.py ...                   [ 67%]
tests/unit/finance/test_utils.py .....                                   [ 81%]
tests/unit/corporate/test_corporate_orchestrator.py .                    [ 83%]
tests/unit/corporate/test_financial_strategy.py ..                       [ 89%]
tests/unit/corporate/test_hr_strategy.py .                               [ 91%]
tests/unit/corporate/test_production_strategy.py ..                      [ 97%]
tests/unit/corporate/test_sales_manager.py .                             [100%]

============================== 37 passed in 0.31s ==============================
```
