# TD-073 Firm Refactor: Insights & Lessons Learned

## Phenomenon
The `Firm` class was acting as a "Split Brain" God Class, holding state directly while also delegating behavior to departmental components (`FinanceDepartment`, `HRDepartment`, etc.). This violated the Single Responsibility Principle and made state management ambiguous. Specifically, properties like `firm.assets` were property wrappers around `firm.finance.balance`, causing confusion about the source of truth and leaking implementation details.

## Cause
The initial design used property wrappers to maintain backward compatibility while incrementally introducing components. However, this transition phase persisted too long, leading to a codebase that relied on the facade's convenience properties rather than the authoritative components. This made the `Firm` class bloated and difficult to test in isolation.

## Solution
We executed a comprehensive refactor (V2) to:
1.  **Remove Property Wrappers**: Deleted `assets`, `current_profit`, `revenue_this_turn`, etc., from `Firm`.
2.  **Enforce Composite State**: Implemented `FirmStateDTO` as a composite of `FinanceStateDTO`, `ProductionStateDTO`, `SalesStateDTO`, and `HRStateDTO`.
3.  **Refactor Decision Logic**: Decomposed `_execute_internal_order` by moving logic into `ProductionDepartment.invest_in_automation`, `HRDepartment.fire_employee`, etc.
4.  **Update Call Sites**: Systematically replaced `firm.assets` with `firm.finance.balance` across the simulation engine and tests.
5.  **Polymorphism Handling**: Updated `SettlementSystem` to inspect `agent.finance.balance` before falling back to `agent.assets`, ensuring compatibility with the new `Firm` structure while maintaining `IFinancialEntity` protocol support for other agents.

## Lesson Learned
*   **Rip the Band-Aid**: Transitional wrappers are useful but dangerous if not deprecated and removed quickly. They encourage technical debt accumulation.
*   **Composite DTOs**: structuring DTOs to mirror the component architecture (Composite Pattern) significantly improves clarity and prevents data leakage between logical boundaries.
*   **Test Brittleness**: Heavy reliance on mocks in unit tests (`Mock(spec=Firm)`) made the refactor painful, as every mock had to be updated to reflect the new internal structure. Future tests should prefer using DTOs or real component instances where possible, or factory helpers that abstract the mock structure.
