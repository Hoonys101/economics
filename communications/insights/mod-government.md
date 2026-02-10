# Technical Insight Report: Government Module Cleanup

**ID:** INSIGHT-MOD-GOV-001
**Date:** 2025-05-27 (Simulated)
**Author:** Jules (AI Agent)
**Scope:** `modules/government/`, `tests/unit/governance/`, `tests/unit/modules/government/`, `tests/unit/test_tax_*.py`

## 1. Problem Phenomenon
During the Unit Test Cleanup Campaign for `mod-government`, the following issues were observed:
- **Dependency Failures:** `pytest` failed initially due to missing `PyYAML`, `joblib`, and `numpy` in the environment.
- **Broken Tests:**
  - `tests/unit/test_tax_collection.py`: Failed because `Government.assets` returns a `float` (default currency balance), but tests accessed it as a dictionary (`gov.assets['USD']`).
  - `tests/unit/test_tax_incidence.py`: Failed due to outdated `Household` and `Firm` initialization signatures (missing `core_config`, `engine`, `config_dto`).
  - `tests/unit/test_tax_incidence.py`: Runtime errors in `TransactionManager` due to missing `escrow_agent` mock.
  - `tests/unit/test_tax_incidence.py`: Runtime `AttributeError: 'Firm' object has no attribute 'hr'` in `simulation/systems/registry.py`, indicating `Registry` was using legacy proxy attributes removed in recent refactors.
  - Assertion Mismatches: Tests assumed a flat 10% tax rate, but the system applied progressive taxation (resulting in ~16.25% effective tax on 100.0 income with survival cost logic), causing value assertion failures (`1090.0` vs `1083.75`).
- **Hardcoded Constants:** Usage of literal `"USD"` strings in `modules/government/tax/tests/test_service.py` and `tests/unit/governance/test_judicial_system.py`.

## 2. Root Cause Analysis
1.  **Refactoring Drift:** Core agents (`Household`, `Firm`) and systems (`Registry`) underwent Orchestrator-Engine refactoring (e.g., moving state to `_econ_state`/`hr_state` and logic to `Engines`), but unit tests and some system components (`Registry`) were not updated to reflect these architectural changes.
2.  **Implicit Logic:** `Government` agent defaults to `TaxService` which utilizes `TAX_BRACKETS` (Progressive Tax) from configuration, overriding the intuitive expectation of `INCOME_TAX_RATE` (which is `0.0` in config) or simple flat tax assumptions in tests.
3.  **Type Inconsistency:** `Government.assets` exposes a `float` (convenience property for default currency), whereas `Household.assets` (in legacy tests/mocks) or expectations were often dictionary-based.

## 3. Solution Implementation Details
1.  **Environment:** Installed required dependencies via `pip`.
2.  **Test Fixes:**
    - Updated `tests/unit/test_tax_collection.py` to assert `gov.assets` as a float.
    - Updated `tests/unit/test_tax_incidence.py`:
        - Implemented correct `Household` and `Firm` factory methods using `AgentCoreConfigDTO` and `IDecisionEngine` mocks.
        - Manually hydrated agent wallets using `deposit()` since `initial_assets` kwarg is no longer directly handled in `__init__` for wallet balance.
        - Mocked `escrow_agent` for `TransactionManager`.
        - Updated assertions to match the actual progressive tax calculation (16.25 deduction on 100.0 income).
3.  **Code Fixes (External Dependency):**
    - Updated `simulation/systems/registry.py` to access `firm.hr_state` and use `firm.hr_engine` instead of the removed `firm.hr` proxy. This was necessary to unblock `test_tax_incidence.py`.
4.  **Cleanup:**
    - Replaced hardcoded `"USD"` with `DEFAULT_CURRENCY` imported from `modules.system.api` in `modules/government/tax/tests/test_service.py` and `tests/unit/governance/test_judicial_system.py`.

## 4. Lessons Learned & Technical Debt
-   **TD-REGISTRY-LEGACY:** `simulation/systems/registry.py` still contains legacy patterns (checking `hasattr(buyer, 'hr')` fallback) and needed patching. It should be fully audited for other legacy attribute accesses.
-   **TD-GOV-ASSETS-TYPE:** `Government.assets` returning `float` while other agents might return dicts or objects creates strict typing friction in tests. A standardized `get_balance(currency)` is preferred.
-   **TD-TAX-CONFIG-CONFUSION:** `INCOME_TAX_RATE` in config is `0.0`, yet the system applies Progressive Tax based on `TAX_BRACKETS`. This "hidden" default behavior makes testing specific rates difficult without explicitly mocking `TaxService` or `FiscalPolicy`.
-   **Test Location:** `modules/government/tax/tests/` exists inside the source tree, while other tests are in `tests/unit/`. These should ideally be consolidated.
