# Insights: Refactor HR & Sales Engines

## 1. Technical Debt Discovered
- **`Firm` God Class**: The `Firm` class (in `simulation/firms.py`) is extremely large and handles too many responsibilities (Production, Finance, HR, Sales orchestration, Decision Making, etc.). While moving logic to engines helps, the `Firm` class itself remains a bottleneck for orchestration.
- **Inconsistent Mocking**: Tests use a mix of `MagicMock` and real objects, sometimes causing fragility when signatures change. `test_firm_lifecycle.py` was referenced in the spec but not found; tests were scattered across `tests/simulation/test_firm_refactor.py` and `tests/unit/test_firms.py`.
- **`HREngine` side-effects**: The previous implementation had deep coupling where the engine modified `employee` agents directly. This has been resolved, but other engines (like `FinanceEngine`) should be audited for similar patterns.
- **Implicit Dependencies**: `Firm` relies on `market_context` having specific keys like `fiscal_policy` which are sometimes dictionaries and sometimes objects/mocks in tests. This inconsistency makes it hard to rely on type hints.

## 2. Refactoring Insights
- **DTO Pattern Effectiveness**: Introducing `HRPayrollResultDTO` and `MarketingAdjustmentResultDTO` successfully decoupled the engines from the agent state. This makes the data flow explicit and easier to test.
- **Orchestrator Pattern**: The `Firm` now clearly acts as an orchestrator for Payroll and Marketing, applying the results returned by stateless engines. This improves observability of side-effects (they happen in one place).
- **Testability**: The new engines are purely functional (Input DTO -> Output DTO), making them trivial to unit test without complex mocking of the entire simulation environment.

## 3. Future Recommendations
- **Audit FinanceEngine**: Apply the same pattern to `FinanceEngine`. Currently, it might still have side effects or be too coupled to `FirmState`.
- **Standardize Context DTOs**: Ensure all context DTOs are strictly typed and used consistently across all engines.
- **decompose Firm**: Consider breaking `Firm` into smaller orchestrators or using a composite pattern more aggressively to reduce the size of `firms.py`.
