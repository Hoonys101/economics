# Mission Phase 5 Interfaces Insights

## Technical Debt

### Missing Dependency: `modules.government.treasury`
The `modules/finance/central_bank/api.py` module defines a forward reference to `modules.government.treasury.api.ITreasuryService` and `BondDTO` within a `TYPE_CHECKING` block.
However, `modules/government/treasury` does not currently exist. This will cause static type checkers (mypy) to fail, although runtime execution remains safe due to the guard.
**Action Required:** Create `modules/government/treasury` package and define `ITreasuryService` and `BondDTO`.

### Duplicate Interface: `ICentralBank`
An `ICentralBank` interface already exists in `modules/finance/api.py`. The new `modules/finance/central_bank/api.py` introduces a new `ICentralBank` protocol specific to Phase 5 requirements.
This creates ambiguity and potential conflict.
**Action Required:** Deprecate `ICentralBank` in `modules/finance/api.py` and migrate usages to the new definition, or consolidate them.

## Insights
- The separation of `CallMarket` and `CentralBank` into distinct sub-modules improves modularity compared to the monolithic `modules/finance/api.py`.
- The use of `Protocol` for interfaces allows for structural typing, facilitating mocking and testing.
