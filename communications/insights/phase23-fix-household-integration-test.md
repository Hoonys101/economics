# Insight Report: Fix Household Integration Test

## Architectural Insights
- **DTO Violation in BudgetEngine**: The `BudgetEngine` reads `market_snapshot.goods`, which is not part of the standard `MarketSnapshotDTO` (in `modules/system/api.py`). This implicit dependency relies on dynamic attribute access (`getattr`), which compromises type safety and requires mocks to drift from the DTO contract (`mock_snapshot.goods = {}`).
- **Testing Logic**: Unit/Integration tests for `Household` require explicit state hydration. The `Household` constructor argument `initial_assets_record` is purely statistical and does not hydrate the `Wallet`. Tests must explicitly call `household.deposit(amount)` to enable financial capabilities.
- **BudgetEngine Autonomy**: The `BudgetEngine` autonomously generates survival orders if `NeedsEngine` reports a deficit, regardless of the upstream AI decision. To test specific AI decision flows in isolation, the automatic survival budget must be explicitly disabled via configuration (`survival_budget_allocation=0.0`).

## Test Evidence
```
tests/unit/decisions/test_household_integration_new.py::TestHouseholdIntegrationNew::test_make_decision_integration PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 2 warnings in 0.46s =========================
```
