# Mission Guide: Settlement Kernel Hardening & Saga Decoupling (Track A)

## 1. Objectives
- **TD-253**: Extract `active_sagas` and `process_sagas` from `SettlementSystem` into a new `SagaOrchestrator`.
- **TD-254**: Replace `hasattr` checks with strict adherence to `IFinancialEntity` via a `FinancialEntityAdapter`.
- **TD-258**: Replace manual transaction injections in sagas with calls to a new `MonetaryLedger`.

## 2. Reference Context (MUST READ)
- **Primary Spec**: [spec_settlement_kernel_hardening.md](file:///c:/coding/economics/design/3_work_artifacts/specs/spec_settlement_kernel_hardening.md)
- **Implementation Plan**: [implementation_plan_sec5.md](file:///c:/coding/economics/brain/becf7013-8d5e-43c8-8052-cd658d3936ea/implementation_plan_sec5.md)

## 3. Implementation Roadmap
### Phase 1: Core Interfaces & Ledger
- Create `modules/finance/kernel/api.py` with `ISagaOrchestrator`, `IMonetaryLedger`, and `ISettlementSystem` (refactored).
- Implement `MonetaryLedger` in `modules/finance/kernel/ledger.py`.

### Phase 2: Orchestration Extraction
- Create `modules/finance/sagas/orchestrator.py` and move logic from `SettlementSystem`.
- Update `TickOrchestrator` to call `SagaOrchestrator.process_sagas()`.

### Phase 3: Kernel Cleanup
- Implement `FinancialEntityAdapter` in `modules/finance/kernel/adapters.py`.
- Refactor `SettlementSystem._execute_withdrawal` and `transfer` to use the adapter.
- Remove all saga-related code from `SettlementSystem.py`.

## 4. Verification
- Run `stress_test_validation` scenario.
- Verify that `MonetaryLedger` generates and appends `Transaction` objects for credit expansion/destruction correctly.
- Ensure zero-sum integrity passes via `trace_leak.py`.
