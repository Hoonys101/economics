# Mission Guide: Operation 100%: Unit Test Hardening & Mock Strategy

## 1. Objectives
- **Liquidate TD-CM-001**: Fix `ConfigManager` unit tests failing in lean environments.
- **Liquidate TD-TM-001**: Fix `TechnologyManager` unit tests failing due to `MagicMock` vs `int` comparisons.
- **Mock Strategy Harmonization**: Implement "Smarter Mocks" in `conftest.py` or within specific tests to prevent `TypeError` and `AssertionError` when dependencies like `numpy` or `yaml` are mocked.
- **Golden Fixtures Adoption**: Promote the use of `golden_households` and `golden_firms` for state-heavy tests instead of manual `MagicMock` setups.

## 2. Reference Context (MUST READ)
- **Problem Discovery**: `design/_archive/insights/2026-02-11_Test_Completion_And_Debt_Discovery.md`
- **Root Cause Analysis**: `design/_archive/insights/2026-02-11_Mock_Drift_Root_Cause_Analysis.md`
- **Status Ledger**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (TD-CM-001, TD-TM-001, WO-101)

## 3. Implementation Roadmap

### Phase 1: Smart Dependency Mocking
- Update `tests/conftest.py`'s fallback mocks for `numpy` and `yaml`.
- Ensure `mock_numpy.max()` returns a primitive (`0` or length).
- Ensure `mock_numpy.random.rand()` returns a numpy-like array (or list) of floats.
- Ensure `mock_yaml.safe_load()` returns an empty dict `{}` by default instead of a recursive `MagicMock`.

### Phase 2: Unit Test Correction
- **ConfigManager (`tests/unit/modules/common/config_manager/test_config_manager.py`)**:
    - If `yaml` is mocked, ensure the test provides a side-effect or return value that yields the expected configuration dictionary.
    - Avoid `AssertionError: assert <MagicMock ...> == 1`.
- **TechnologyManager (`tests/unit/systems/test_technology_manager.py`)**:
    - Fix `TypeError: '>=' not supported between instances of 'MagicMock' and 'int'`.
    - Specifically, harden `_ensure_capacity` and `_process_diffusion` to handle cases where `numpy` might be a mock, OR (preferred) configure the `numpy` mock in the test's setup to return valid integers for `.shape` and `np.max()`.

### Phase 3: Validation
- Run tests in a "clean" environment (or simulate it by temporarily renaming the real `numpy` and `yaml` in `sys.modules`).
- Ensure 100% pass across ALL environments.

## 4. Verification
- `pytest tests/unit/modules/common/config_manager/test_config_manager.py`
- `pytest tests/unit/systems/test_technology_manager.py`
- Result must be `PASSED` even if `numpy` and `yaml` are missing from the system.
