# Fix Mock Integrity Insight Report

| Metadata | Details |
| :--- | :--- |
| **Title** | Hardening Mocks for QE & Debt Logic |
| **Date** | 2026-02-13 |
| **Author** | Jules (AI) |
| **System** | Finance / Test Suite |
| **Status** | Resolved |

## 1. Problem Overview
Recent refactors in the `FinanceSystem` (specifically Quantitative Easing logic) and the removal of legacy state attributes from `Bank` agents caused regressions in unit tests.
- `AttributeError: Mock object has no attribute 'total_debt'`
- `AttributeError: Mock object has no attribute 'sensory_data'`
- `AttributeError: 'Bank' object has no attribute 'assets'`

## 2. Root Cause Analysis
1.  **Logic Evolution vs. Static Mocks**: The `issue_treasury_bonds` method was updated to include QE logic which checks `government.sensory_data.current_gdp` and `government.total_debt`. The existing mocks in `test_sovereign_debt.py` and `test_double_entry.py` were not updated to reflect this new dependency.
2.  **SSoT Migration**: The `Bank` agent's `assets` property was removed in favor of `total_wealth` (to enforce SSoT via `Wallet` or `SettlementSystem`). Tests in `test_bank.py` were still asserting against the deleted `.assets` property.

## 3. Resolution
1.  **Updated `MockGovernment`**:
    - Added `sensory_data` with `current_gdp` initialized.
    - Added initialization of `_total_debt` to ensure robustness.
    - Applied these changes to both `test_sovereign_debt.py` and `test_double_entry.py`.
2.  **Updated `test_bank.py`**:
    - Replaced all usages of `.assets` with `.total_wealth`.

## 4. Technical Debt & Insights
1.  **Mock Fragility**: The need to manually update mocks whenever internal logic changes highlights the fragility of using `MagicMock` with hardcoded attributes.
    - *Insight*: Prefer using "Fake" objects (lightweight implementations) or Factory-created mocks that share a common definition with the real class, rather than ad-hoc `MagicMock` setup in every test file.
2.  **Property vs Attribute**: The `Bank` agent migration from `assets` (property) to `total_wealth` (property) is a good move for clarity, but the lack of a deprecation warning or temporary alias caused immediate test breakage.
    - *Insight*: When removing public APIs (like `assets`), consider a temporary property that logs a warning before removal to ease migration.
3.  **Test Duplication**: `test_sovereign_debt.py` and `test_double_entry.py` have overlapping coverage and mock definitions.
    - *Insight*: Consolidate financial system tests or use a shared `conftest.py` fixture for `MockGovernment` to reduce maintenance burden.

## 5. Next Steps
- Consider introducing a `MockAgentFactory` in `tests/utils/factories.py` that automatically populates standard attributes (`sensory_data`, `wallet`, `total_debt`, `total_wealth`) for all agent types.
- Audit other agent tests for usage of `.assets` which might be broken if `Firm` or `Household` also remove this property.
