# Mission Insight: Fix Leak and Arithmetic Errors

## Technical Debt Addressed

1.  **Multi-Currency Support in Financial Calls**:
    *   Updated `IFinancialEntity.deposit` and `withdraw` calls in `SettlementSystem` and `TransactionManager` to explicitly pass `currency=DEFAULT_CURRENCY`.
    *   This ensures that future multi-currency features won't silently default to USD without explicit intent.
    *   Updated `CentralBank` internal asset management to respect currency arguments.

2.  **Arithmetic Safety with Dictionaries**:
    *   Fixed `ProductionDepartment` and `SalesDepartment` where `Dict[CurrencyCode, float]` (e.g., `balance`, `revenue_this_turn`) was being treated as `float`.
    *   This prevents runtime crashes (`AttributeError: 'float' object has no attribute 'get'` or `TypeError`).

3.  **Trace Leak Verification**:
    *   Verified `trace_leak.py` passes with `0.0000` leak.
    *   Ensured that Mock agents in tests align with the system's explicit currency usage.

## Insights

*   **Type Safety Risks**: The transition from `float` assets/revenue to `Dict` requires careful auditing of all arithmetic operations. `mypy` or similar static analysis would catch these, but runtime checks or strict DTO typing is crucial.
*   **Explicit vs Implicit**: Explicitly passing `currency` makes the code more verbose but significantly safer for a multi-currency simulation. Implicit defaults hide assumptions that break when new currencies are introduced.
*   **Test Alignment**: Unit tests must mirror the production architecture. `test_marketing_roi.py` was failing because it mocked data as `float` while the system now enforces `Dict`. Tests should be updated alongside refactors.
