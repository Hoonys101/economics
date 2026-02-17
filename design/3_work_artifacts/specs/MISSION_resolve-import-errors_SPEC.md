# Mission Guide: Post-Merge Import Stabilization

## 1. Objectives
- Resolve all broken imports and file path errors introduced by the double-merge of `market-precision-refactor` and `protocol-lockdown`.
- Specifically fix the "Module not found" or "File not found" errors in the test suite.
- Re-align any DTO imports that were affected by the path changes in `modules/finance/transaction/api.py` vs `modules/finance/api.py`.

## 2. Reference Context (MUST READ)
- **Problem**: Recent merge standardized on `total_pennies` and strictly enforced `@runtime_checkable` protocols.
- **Conflict Point**: `OrderBookMarket` and `TransactionProcessor` might have conflicting import paths for the updated `Transaction` model if they moved.
- **Test Locations**: 
    - [test_precision_matching.py](file:///c:/coding/economics/tests/market/test_precision_matching.py) (Verify actual location)
    - [test_omo_system.py](file:///c:/coding/economics/tests/integration/test_omo_system.py)

## 3. Implementation Roadmap
### Phase 1: Audit
- Run `pytest` to identify every single `ImportError` or `ModuleNotFoundError`.
### Phase 2: Fix
- Update `import` statements in source and test files.
- Ensure `Transaction` is imported from `simulation.models` and not a stale path.
- Fix any `total_pennies` vs `amount_pennies` naming mismatches if they missed my manual merge.

## 4. Verification
- `pytest -rfE --tb=short tests/unit/test_transaction_engine.py tests/unit/test_market_adapter.py tests/integration/test_omo_system.py tests/market/test_precision_matching.py`
