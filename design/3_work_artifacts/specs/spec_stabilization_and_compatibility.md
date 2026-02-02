# Mission Spec: Simulation Stabilization & Compatibility (TD-122-B)

## 1. Objective
Restore system stability and backward compatibility following the Household Agent refactor (TD-162). Ensure that all legacy scripts (like `trace_leak.py`) and existing tests work with the new DTO-based architecture.

## 2. Technical Requirements

### 2.1 Household Compatibility Shims (`simulation/core_agents.py`)
Restore the following properties as "Bridges" to the underlying DTOs. Each MUST have both a Getter and a Setter to maintain compatibility with legacy systems:
- `assets` (intents with `self._econ_state.assets` and `self._assets`)
- `inventory` (sync with `self._econ_state.inventory`)
- `needs` (sync with `self._bio_state.needs`)
- `is_active` (sync with `self._bio_state.is_active`)
- `is_homeless` (sync with `self._econ_state.is_homeless`)
- `is_employed` (sync with `self._econ_state.is_employed`)
- `current_wage` (sync with `self._econ_state.current_wage`)
- `residing_property_id` (sync with `self._econ_state.residing_property_id`)
- `owned_properties` (sync with `self._econ_state.owned_properties`)

### 2.2 Defensive Coding in Managers
- **FiscalPolicyManager**: Update `determine_fiscal_stance` to handle cases where `market_data` contains Mock objects (ensure float conversion for survival cost).

### 2.3 Test Suite Repair (146 Failures)
- Update `tests/unit/` and `tests/integration/` where `Household` is mocked.
- **Pattern**: Instead of just `MagicMock(spec=Household)`, mocks must now initialize `_econ_state`, `_bio_state`, and `_social_state` with appropriate DTO-like nested Mocks/objects.

## 3. Success Criteria
- [ ] `python scripts/trace_leak.py` runs 10 ticks with ZERO leakage and no AttributeErrors.
- [ ] `pytest` passes at least 400+ tests (targeting reduction of the 146 failures).
- [ ] No regressions in `MISSION-ATOMICITY` logic.

## 4. Execution Command
```powershell
.\jules-go.bat MISSION-STABILIZE
```
