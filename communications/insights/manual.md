# Manual Fix Insight Report

## Architectural Insights
The `MarketSnapshotDTO` in `modules/system/api.py` enforces a required `market_data` dictionary argument. This field is positioned before optional market-specific snapshots (housing, loan, labor).
The unit tests in `tests/unit/modules/household/test_decision_unit.py` were instantiating `MarketSnapshotDTO` without this argument, causing `TypeError`.
This highlights a mismatch where DTO definitions evolved but dependent tests were not updated.
The fix applied was to inject an empty dictionary `market_data={}` in the test instantiations. This adheres to the DTO contract while acknowledging that the specific tests (`test_orchestrate_housing_buy`, `test_shadow_wage_update`) do not currently rely on the contents of `market_data`.
Future work should ensure that if `market_data` becomes critical for decision logic, these tests are updated with meaningful mock data.

## Test Evidence
```
tests/unit/modules/household/test_decision_unit.py::TestDecisionUnit::test_orchestrate_housing_buy PASSED [ 50%]
tests/unit/modules/household/test_decision_unit.py::TestDecisionUnit::test_shadow_wage_update PASSED [100%]

=============================== warnings summary ===============================
../home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 0.19s =========================
```
