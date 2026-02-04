# Insight: Government Refactor (TD-226)

## Overview
This mission focuses on Phase 1 of the Government Module Decomposition. The goal is to break down the `Government` God Class into smaller, single-responsibility services: Tax, Welfare, and Fiscal.

## Current Progress
- Created `modules/government/tax/api.py` (ITaxService)
- Created `modules/government/welfare/api.py` (IWelfareService)
- Created `modules/government/fiscal/api.py` (IFiscalService)
- Implemented `modules/government/tax/service.py` (TaxService)
  - Encapsulates `TaxationSystem` and `FiscalPolicyManager`.
  - Validated with unit tests in `modules/government/tax/tests/test_service.py`.
- **[NEW] Implemented `modules/government/welfare/service.py` (WelfareService)**
  - Extracted welfare logic (Survival Cost, Unemployment, Stimulus) from `WelfareManager`.
  - Refactored `Government` to use `WelfareService`.
  - Deprecated and removed `WelfareManager`.

## Technical Debt & Observations
- **Duplicate/Ambiguous Structure**: `modules/government/taxation` already exists. The new spec mandates `modules/government/tax`. This creates potential confusion during the transition period. Future steps must ensure `taxation` is deprecated or merged into `tax`.
- **Any Type Usage**: The new interfaces use `Any` for `firm` and `household` arguments to avoid circular imports. This is a temporary measure (TD-227 resolution). Ideally, specific Protocols (e.g., `IFirm`, `IHousehold`) should be defined in `modules/common/interfaces.py` to replace `Any`.
- **God Class Persistence**: The `Government` class currently still holds all logic. These interfaces are just the first step. The implementation phase (Phase 2) will require careful migration to avoid breaking existing tests that rely on `Government` methods directly.
- **Bug Fix in Legacy Logic**: During extraction, a bug was identified in `Government.reset_tick_flow` where `revenue_this_tick` was reset to `0.0` (float) instead of a dictionary. This has been corrected in `TaxService` to ensure `revenue_this_tick` is always a `Dict[CurrencyCode, float]`.
- **[NEW] WelfareManager SRP Violation**: `WelfareManager` contained Wealth Tax logic, which is taxation, not welfare. During extraction, this logic was moved back to `Government` temporarily (inline) because `TaxService` didn't have an explicit API for it and the scope was `WelfareService`. **Action Item**: Move Wealth Tax logic to `TaxService` in the next iteration.
- **[NEW] Service Coupling**: `WelfareService` currently depends on the full `Government` instance to access `finance_system`, `wallet`, and `gdp_history`. This creates a circular dependency (`Government -> WelfareService -> Government`). **Action Item**: Inject specific interfaces (`IFinanceSystem`, `IWallet`) and shared state containers instead of the parent agent.
- **[NEW] Shared State (GDP History)**: `gdp_history` is used by both the Policy Engine (Taylor Rule) and Welfare Service (Stimulus). Currently, `WelfareService` accesses/modifies `Government.gdp_history` directly. This shared mutable state needs a better home (e.g., `EconomicIndicatorsDTO` or a shared `HistoryManager`).

## Next Steps
- Implement `FiscalService` class.
- Move Wealth Tax logic to `TaxService`.
- Refactor `Government` to use `FiscalService`.
- Update tests to use the new service boundaries.

## [2026-02-04] Government Class Refactor (Tax & Welfare Integration)

### Achievements
- Refactored `Government` to use `TaxService` and `WelfareService` via Composition (Facade Pattern).
- Removed direct dependencies on `TaxationSystem` and `FiscalPolicyManager` from `Government`.
- Migrated Wealth Tax calculation logic to `TaxService.calculate_wealth_tax`, cleaning up `Government.run_welfare_check`.
- Maintained backward compatibility for `revenue_this_tick`, `total_collected_tax`, and `tax_revenue` via properties delegating to `TaxService`.
- Fixed a crash risk in `MinistryOfEducation` where it assumed `revenue_this_tick` was a float (it is now strictly `Dict[CurrencyCode, float]`).

### Technical Debt Identified
- **Settlement System Coupling**: `Government` still manually orchestrates tax collection via `settlement_system.transfer` and then calls `tax_service.record_revenue`. Ideally, `TaxService` or a `TaxCollector` component should handle the settlement + recording atomically to prevent drift.
- **Welfare Service Dependency**: `WelfareService` still depends on `Government` instance. This circularity is managed via `TYPE_CHECKING` but remains architecturally unclean.
- **Stimulus Spending Tracking**: `Government.finalize_tick` assumes `stimulus_spending` in `current_tick_stats`, but `WelfareService` aggregates it into `spending_this_tick` without separating it explicitly in a way `Government` can easily read for the snapshot (currently defaults to 0.0 in snapshot).
- **Fiscal Service Pending**: `FiscalService` is defined but not implemented. Fiscal responsibilities (`InfrastructureManager`, Bailouts) are still loosely held by `Government`.

### Insights
- **Type Safety**: The explicit typing in `TaxService` revealed type inconsistencies in legacy code (`MinistryOfEducation`). Strong typing in new services helps catch legacy bugs.
- **State Migration**: Moving state (`revenue_this_tick`, etc.) to services requires careful handling of public properties to avoid breaking consumers like `MinistryOfEducation` or external observers/tests.
