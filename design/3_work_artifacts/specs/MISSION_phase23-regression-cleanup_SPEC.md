# MISSION Spec: Phase 23 Regression Cleanup (Operation Zero Failure)

## 1. Overview
The merger of Phase 23 P1, P2, and P3 missions has introduced 8 logical failures and attribute mismatches in the test suite. This mission's goal is to restore a 100% test pass rate by aligning test mocks and logic with the updated v3.0 Architecture (Government singleton, Penny Standard).

## 2. Target Regressions

### 2.1. Government Architecture Mismatch
- **Symptoms**: `AttributeError: Mock object has no attribute 'primary_government'`
- **Affected Files**: `tests/modules/governance/test_system_command_processor.py`
- **Root Cause**: The transition from `Simulation.governments` (list) and `Simulation.primary_government` to a direct `Simulation.government` (singleton) was not fully reflected in all governance test mocks.
- **Action**: Update all mocks in the affected test files to use `.government` and ensure they satisfy the `IGovernment` protocol.

### 2.2. M&A Manager Type Conflicts
- **Symptoms**: `TypeError: '<' not supported between instances of 'float' and 'MagicMock'`
- **Affected Files**: `simulation/systems/ma_manager.py:86`, `tests/system/test_phase29_depression.py`
- **Root Cause**: In `ma_manager.py`, `intrinsic_value_pennies` is now derived from `firm.finance_state.valuation_pennies`. If a firm mock in the depression scenario returns a `MagicMock` for this attribute, the comparison with `market_cap_pennies` (float/int) fails.
- **Action**: Ensure all firm mocks in the affected tests provide a valid `int` for `finance_state.valuation_pennies`.

### 2.3. Logical Inconsistencies
- **Symptoms**: `AssertionError: assert 2 == 1`
- **Affected Files**: `tests/integration/scenarios/diagnosis/test_agent_decision.py`
- **Root Cause**: Likely a change in decision-making frequency or state application order following the SEO (Stateless Engine & Orchestrator) refactor.
- **Action**: Debug the decision output of the refactored Firm agent and ensure the test expectations align with the new 3-phase pipeline.

### 2.4. Audit Integrity
- **Symptoms**: `assert False` in `test_audit_total_m2_logic`
- **Affected Files**: `tests/unit/simulation/systems/test_audit_total_m2.py`
- **Root Cause**: The `SettlementSystem` audit logic was tightened to use exact integer pennies. Floating point drifts in mocks are no longer tolerated.
- **Action**: Update the test fixtures to use exact integer pennies and correct the audit threshold expectations.

## 3. Mandatory Verification
As per the hardened `mission_protocol.py`:
1. **Regression Analysis**: You MUST include an analysis section in your insight report explaining the root cause of each regression you fixed.
2. **Total Test Pass**: You MUST provide proof that `pytest tests/` returns 100% Green.
3. **No Legacy Breaks**: You MUST NOT revert any Phase 23 architectural changes to fix the tests. Correct the tests to match the architecture.

## 4. Context Files
- `simulation/systems/ma_manager.py`
- `simulation/world_state.py`
- `tests/modules/governance/test_system_command_processor.py`
- `tests/system/test_phase29_depression.py`
- `tests/unit/simulation/systems/test_audit_total_m2.py`
