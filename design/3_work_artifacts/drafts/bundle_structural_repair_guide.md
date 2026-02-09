# Mission Guide: Structural Architecture Repair (STRUCTURAL-REPAIR-GO)

## 1. Objectives
Fix critical regressions in agent state management and system handlers causing simulation crashes.
- **TD-REG-STRUCT**: Restore missing property accessors on `Household` and `Firm`.
- **TD-REG-CRASH**: Fix `TypeError` in `HREngine` and `AttributeError` in `DemographicManager`.
- **TD-REG-SETTLE**: Resolve `SETTLEMENT_FATAL` in Welfare transfers.

## 2. Reference Context (MUST READ)
- **Primary Report**: [report_20260209_193944_Analyze_the_trace_le.md](file:///c:/coding/economics/reports/temp/report_20260209_193944_Analyze_the_trace_le.md)
- **Crash Logs**: [trace_leak_new.log](file:///c:/coding/economics/trace_leak_new.log)
- **Core Entities**: [core_agents.py](file:///c:/coding/economics/simulation/core_agents.py), [firms.py](file:///c:/coding/economics/simulation/firms.py)

## 3. Implementation Roadmap

### Phase 1: Household Property Restoration
Restore delegate properties in `simulation/core_agents.py` to bridge the gap between DTO-based state and legacy engine access.
- Restore `generation` (delegate to `_bio_state.generation`).
- Restore `talent` (delegate to `_econ_state.talent`).
- Ensure `labor_income_this_tick` and `capital_income_this_tick` setters are correctly updating `_econ_state`.

### Phase 2: Firm Financial Integration
The simulation crashes because `Firm` lacks a `finance` attribute which `financial_handler.py` expects.
- **Option A**: Add `@property def finance(self): return self.finance_engine` to `simulation/firms.py`.
- **Option B**: Update `simulation/systems/handlers/financial_handler.py` to use `agent.finance_engine` or direct state access.
- *Decision*: Restore the `finance` property proxy on `Firm` to maintain interface compatibility with existing handlers.

### Phase 3: Defensive Engine Hardening
Implement robust error handling in performance-critical engines as proposed in the Gemini report.
- **HREngine**: In `process_payroll`, safely handle `None` for `labor_income_this_tick` by defaulting to `0.0`.
- **DemographicManager**: In `process_births`, safely handle parent agents missing the `talent` attribute.

### Phase 4: Welfare Settlement Fix
Resolve `SETTLEMENT_FATAL` where `debit_id` is `None` for `welfare_support_unemployment` transfers.
- Locate the source of the `None` debit ID in `simulation/systems/government_system.py` or wherever welfare is triggered.
- Ensure the Government agent object (id 25) is correctly passed as the payer.

## 4. Verification
Run the following command and ensure no crashes occur within 100 ticks:
```powershell
python scripts/trace_leak.py --ticks 100
```
Check `trace_leak.py` output for "ZERO-SUM AUDIT: PASSED".
