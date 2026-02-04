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

## Technical Debt & Observations
- **Duplicate/Ambiguous Structure**: `modules/government/taxation` already exists. The new spec mandates `modules/government/tax`. This creates potential confusion during the transition period. Future steps must ensure `taxation` is deprecated or merged into `tax`.
- **Any Type Usage**: The new interfaces use `Any` for `firm` and `household` arguments to avoid circular imports. This is a temporary measure (TD-227 resolution). Ideally, specific Protocols (e.g., `IFirm`, `IHousehold`) should be defined in `modules/common/interfaces.py` to replace `Any`.
- **God Class Persistence**: The `Government` class currently still holds all logic. These interfaces are just the first step. The implementation phase (Phase 2) will require careful migration to avoid breaking existing tests that rely on `Government` methods directly.
- **Bug Fix in Legacy Logic**: During extraction, a bug was identified in `Government.reset_tick_flow` where `revenue_this_tick` was reset to `0.0` (float) instead of a dictionary. This has been corrected in `TaxService` to ensure `revenue_this_tick` is always a `Dict[CurrencyCode, float]`.

## Next Steps
- Implement `WelfareService` and `FiscalService` classes.
- Refactor `Government` to use these services.
- Update tests to use the new service boundaries.
