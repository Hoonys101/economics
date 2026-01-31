# WORK ORDER: WO-165 - Modern Financial Integrity Tests

## 1. Context
The existing M2 verification tests are based on an old M0-only economy. With Fractional Reserve Banking implemented, we need a test suite that validates the integrity of the money supply considering credit creation.

## 2. Technical Requirements

### A. New Test Module (`tests/finance/test_m2_integrity.py`)
- Create a test that initializes a `WorldState` with a `Bank`, `Government`, and `CentralBank`.
- Implement `test_credit_expansion`:
    - Grant a loan of 500.
    - Assert that `WorldState.calculate_total_money()` (M2) has increased by 500.
    - Assert that `M2 == M0 + Total_Credit` holds.
- Implement `test_credit_destruction`:
    - Repay a loan or simulate default.
    - Assert that `M2` decreases correctly and the formula remains balanced.
- Implement `test_settlement_purity`:
    - Use `SettlementSystem` to transfer 100 between agents.
    - Assert that `M2` remains unchanged.

### B. Baseline Money Tracking
- Ensure `WorldState` properly tracks `M0` (Base Money). This might require adding a `total_base_money` field to `CentralBank` or `WorldState`.

## 3. Success Criteria
- 100% Pass rate on `tests/finance/test_m2_integrity.py`.
- No regression in existing `test_phase20_integration.py`.
