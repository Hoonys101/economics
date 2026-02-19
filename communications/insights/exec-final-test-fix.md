# Execution Insight: Government.py DTO Instantiation Fix

## Architectural Insights
1. **DTO Instantiation Regression**: The regression was caused by `Government.provide_firm_bailout` passing a raw dictionary instead of a `MarketSnapshotDTO` dataclass to `FiscalEngine.decide`. The engine expects a dataclass to access `.market_data` attributes, causing an `AttributeError`.
2. **Protocol Definition Mismatch**: `IFiscalEngine` in `modules/government/engines/api.py` was importing `MarketSnapshotDTO` from `modules.finance.engines.api` (which is a `TypedDict`), while the implementation `FiscalEngine` uses `modules.system.api` (which is a `dataclass`). This was harmonized by updating `modules/government/engines/api.py` to import from `modules.system.api`, enforcing the dataclass contract.
3. **Implicit Dependencies**: The system relies on duck-typing in some areas, but mixing TypedDicts and Dataclasses for the same concept (`MarketSnapshotDTO`) across modules (`finance` vs `system`) creates fragility. Future refactoring should consider unifying these or enforcing strict type boundaries.

## Test Evidence

### Reproduction Test (Fix Verification)
```
tests/reproduce_issue.py::test_provide_firm_bailout_crash
-------------------------------- live log call ---------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 10000})
PASSED                                                                   [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 1 passed, 2 warnings in 0.20s =========================
```

### Existing Tests (Regression Check)
```
tests/unit/agents/test_government.py::test_calculate_income_tax_delegation
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 16%]
tests/unit/agents/test_government.py::test_calculate_corporate_tax_delegation
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 33%]
tests/unit/agents/test_government.py::test_collect_tax_removed
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 50%]
tests/unit/agents/test_government.py::test_run_public_education_delegation
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 66%]
tests/unit/agents/test_government.py::test_deficit_spending_allowed_within_limit
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
PASSED                                                                   [ 83%]
tests/unit/agents/test_government.py::test_deficit_spending_blocked_if_bond_fails
-------------------------------- live log setup --------------------------------
INFO     simulation.agents.government:government.py:163 Government 1 initialized with assets: defaultdict(<class 'int'>, {'USD': 100000})
-------------------------------- live log call ---------------------------------
WARNING  simulation.agents.government:government.py:465 WELFARE_FAILED | Insufficient funds even after bond issuance attempt. Needed: 50000, Has: 10000
PASSED                                                                   [100%]

=============================== warnings summary ===============================
../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428
  /home/jules/.local/share/pipx/venvs/pytest/lib/python3.12/site-packages/_pytest/config/__init__.py:1428: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 6 passed, 2 warnings in 0.31s =========================
```
