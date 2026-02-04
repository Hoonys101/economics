# Mission Phase 5 Interfaces Insights

## Technical Debt

### Missing Dependency: `modules.government.treasury`
The `modules/finance/central_bank/api.py` module defines a forward reference to `modules.government.treasury.api.ITreasuryService` and `BondDTO` within a `TYPE_CHECKING` block.
**Resolution:** A skeleton `modules/government/treasury/api.py` has been created with `ITreasuryService` and `BondDTO` definitions to satisfy static analysis.

### Duplicate Interface: `ICentralBank` and `BondDTO`
- **ICentralBank:** An `ICentralBank` interface already exists in `modules/finance/api.py`. The new `modules/finance/central_bank/api.py` introduces a new `ICentralBank` protocol specific to Phase 5 requirements.
- **BondDTO:** Defined in both `modules/finance/api.py` and `modules/government/treasury/api.py`.

## Migration Plan for ICentralBank and BondDTO

To resolve the architectural conflicts and ambiguity, the following migration plan is proposed:

1.  **Phase 5 Implementation:**
    - Develop the new `CentralBank` implementation using `modules/finance/central_bank/api.py`.
    - Develop the new `TreasuryService` using `modules/government/treasury/api.py`.

2.  **Deprecation of Legacy Interfaces:**
    - Add `@deprecated` decorators (or comments) to `ICentralBank` and `BondDTO` in `modules/finance/api.py`.
    - Identify all usages of legacy `ICentralBank` (mostly in `modules/finance/api.py` dependent code) and `BondDTO`.

3.  **Refactoring & Consolidation:**
    - Update `modules/finance/api.py` to import `BondDTO` from `modules/government/treasury/api.py` instead of redefining it.
    - Update agents/components using the old `ICentralBank` to use the new interface. This may require adapter patterns if the new interface is not a superset of the old one.
    - Once all references are migrated, remove the legacy definitions from `modules/finance/api.py`.

4.  **Timeline:**
    - Steps 1 is part of the current Phase 5 build.
    - Steps 2-3 should be executed as a dedicated "Refactor" task immediately following the completion of the Phase 5 core logic, before Phase 6.

## Insights
- The separation of `CallMarket` and `CentralBank` into distinct sub-modules improves modularity compared to the monolithic `modules/finance/api.py`.
- The use of `Protocol` for interfaces allows for structural typing, facilitating mocking and testing.
