# MISSION_SPEC: WO-SPEC-DTO-FINANCE
## Goal
Decouple `CentralBankSystem`, `FinanceSystem`, and `ScenarioVerifier` from `WorldState`.

## Context
Macro-financial systems are the final gatekeepers of M2 integrity.

## Proposed Changes
1. Inject `IMonetaryLedger` and `ISettlementSystem` directly (avoiding `sim.world_state` traversal).
2. Use `MoneySupplyDTO` for macro-level reporting.
3. Isolate `ScenarioVerifier` from engine internals.

## Verification
- Run `pytest tests/unit/test_finance_system.py`.
