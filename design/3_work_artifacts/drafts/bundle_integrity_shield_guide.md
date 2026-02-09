# Integrated Mission Guide: Phase 12 - integrity Shield

## 1. Objectives
Restore system stability and diagnostic integrity by fixing 15 critical regressions identified during the Orchestrator-Engine refactor.

## 2. Reference Context (MUST READ)
- **Failure Audit Report**: [report_20260209_174243_Fail_logs_unit_test.md](file:///c:/coding/economics/reports/temp/report_20260209_174243_Fail_logs_unit_test.md)
- **Architecture SSoT**: `design/1_governance/architecture/ARCH_AGENT_ORCHESTRATOR.md` (If exists, else rely on `simulation/firms.py` and `simulation/core_agents.py` patterns).

## 3. Implementation Roadmap

### Phase 1: Collective Errors & Imports (High Priority)
1. **Remove Dead Weight**: Delete `tests/unit/test_base_agent.py`. `BaseAgent` no longer exists.
2. **Restore Household API**: In `modules/household/api.py`, re-define the following protocols/DTOs that were lost during decomposition:
   - `IConsumptionManager`, `IDecisionUnit`, `IEconComponent`, `OrchestrationContextDTO`.
   - Ensure they align with their current usage in `simulation/core_agents.py` and unit tests.
3. **Fix DTO Path**: In `tests/unit/modules/government/test_adaptive_gov_brain.py`, fix the import for `GovernmentStateDTO`.
4. **Liquidation API**: In `modules/simulation/api.py` (or relevant), define `IShareholderRegistry`.

### Phase 2: API Alignment (Mass Update)
5. **Transfer Signature**: Update all `settlement_system.transfer` calls in:
   - `tests/unit/systems/handlers/test_housing_handler.py`
   - `tests/unit/systems/test_housing_system.py`
   - Include `currency='USD'` to match the new `ITransferSystem` protocol.
6. **Commerce API**:
   - `test_commerce_system.py`: Update `execute_consumption_and_leisure` -> `finalize_consumption_and_leisure`.
   - Fix `reflux_system` injection in `test_fast_track_consumption_if_needed`.
7. **Event System**:
   - In `tests/unit/systems/test_event_system.py`, add `config` as a positional argument to `execute_scheduled_events`.

### Phase 3: Runtime & Logic Fixes
8. **Production Engine Crash**:
   - In `simulation/components/engines/production_engine.py`, fix `execute_rd_outcome` to handle `None` for `labor_skill`.
   - Use `sum(emp.labor_skill or 0.0 for emp in hr_state.employees)`.
9. **Ministry of Education**:
   - In `test_ministry_of_education.py`, ensure `x._econ_state.wallet.get_balance.return_value` is set to a float to allow sorting.
   - Replace `_sub_assets` checks with `settlement_system.transfer` verification.
10. **Firm Management**:
    - Restore `transfer` logic in `FirmManagementSystem.spawn_firm`.
    - Add `RuntimeError` guard if `settlement_system` is missing.
11. **Housing Handler**:
    - Fix `handle` to return `False` when `final_settlement` fails in `test_handle_payment_failure`.

## 4. Verification
- **All Systems**: `python -m pytest tests/unit/systems`
- **Stability**: `python scripts/trace_leak.py --ticks 1`
- **Stress**: `python scripts/trace_leak.py --ticks 100`

> [!IMPORTANT]
> Do not use legacy `_sub_assets` or `_add_assets` methods. Always use the `SettlementSystem` via the simulation state.
