# Mission Guide: Restoration of Phase 9.2 Architectural Integrity

## 1. Objectives
- Resolve `NameError` in `Bank` constructor (TD-274 regression).
- Resolve `AttributeError` in `AnalyticsSystem` data aggregation (DTO contract violation).
- Restore stability for zero-sum audit and smoke tests.

## 2. Technical Specifications (Reference: draft_193531)

### 2.1 Bank Initialization Fix
- **File**: `simulation/bank.py`
- **Logic**: The constructor receives `config_manager` but currently passes an undefined `config_module` to `LoanManager` and `DepositManager`.
- **Target**: Change `LoanManager(config_module)` -> `LoanManager(config_manager)`.

### 2.2 AnalyticsSystem DTO Alignment
- **File**: `simulation/systems/analytics_system.py`
- **Logic**: Transition from ad-hoc attribute probing to strict DTO access.
- **Contract**: Use `labor_income_this_tick` and `capital_income_this_tick` as defined in `EconStateDTO`.

## 3. Implementation Roadmap

### Phase 1: Logic Correction
1. Modify `simulation/bank.py:__init__` to pass the injected `config_manager`.
2. Modify `simulation/systems/analytics_system.py:aggregate_tick_data` to use correct DTO field names.

### Phase 2: Internal Verification
1. Run `python scripts/verify_purity.py` to ensure no architectural violations.
2. Run `python scripts/audit_zero_sum.py` to verify simulation startup and flow.
3. Run `python scripts/smoke_test.py`.

## 4. Success Criteria
- [ ] No `NameError` on simulation startup.
- [ ] No `AttributeError` during tick aggregation.
- [ ] `audit_zero_sum.py` completes with 0% leak.
- [ ] Purity gate passes (0 violations).
