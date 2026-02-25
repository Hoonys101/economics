--- SOURCE INFO ---
Branch: origin/audit-structural-report-3342853435412465137
Score: 150
File Date: 2026-02-21 17:09:41
Harvested: 2026-02-26 07:08:23
---

# Forensic Audit: Post-Crash Structural Logic Recovery (Phase 21)

## 1. Executive Summary
**Status**: Critical Logic Failure (M2 Leak & Startup Race Conditions)
**Verdict**: The system has stabilized against runtime crashes (Housing Saga), but suffers from severe logical incoherence. The Money Supply (M2) calculation has inverted (Negative M2), indicating a catastrophic accounting failure where debt (overdrafts) masks the existence of liquidity. Additionally, firm creation is failing silently, causing "Ghost" destination errors.

## 2. Detailed Findings

### 2.1. The M2 "Black Hole" (Negative Money Supply)
- **Symptom**: `MONEY_SUPPLY_CHECK` reports negative values, reaching `-99,096,426.00` by Tick 55.
- **Root Cause**: The `calculate_total_money()` function likely sums raw agent balances. In the current implementation, agents (likely Firms in `FIRE_SALE`) are allowed unlimited overdrafts (negative balances). When these negative balances exceed positive deposits, the aggregate "Money Supply" appears negative.
- **Violation**: **Zero-Sum Integrity**. M2 should measure *Liquidity* (Cash + Deposits). A negative balance is a *Liability* (Loan), not "Negative Money". M2 should equal `Sum(max(0, balance_i))`.

### 2.2. Atomic Startup Failure (The "Ghost Firm" Bug)
- **Symptom**: Repeated `SETTLEMENT_FAIL | Engine Error: Destination account does not exist: [120, 123, 124]`.
- **Evidence**: `Tick ? | ERROR | Transaction Record: ... Destination account does not exist: 124`.
- **Root Cause**: Race condition in Firm Lifecycle.
    1. Simulation logic decides to create a Firm.
    2. Capital Injection is attempted *immediately*.
    3. The Firm Agent has not yet been registered in the `Bank` or `WorldState.agents`.
    4. Settlement fails, but the Simulation proceeds, potentially leaving the Investor with debited funds (if not atomic) or the Firm as a "Zombie" with 0 starting capital.

### 2.3. Saga Integrity
- **Symptom**: `SAGA_SKIP | Saga ... missing participant IDs`.
- **Root Cause**: Sagas persist references to agents that may have been garbage collected, failed startup, or died.
- **Risk**: Sagas becoming "Orphaned Processes" that consume compute cycles without effect.

## 3. Phase 22 Structural Fix Specification

### Objective
Restore **M2 Positivity** and **Transactional Atomicity** to ensure the simulation reflects a valid economic state.

### Specification 1: M2 Integrity Patch (`modules/finance/`)
**Requirement**: M2 must never be negative.
- **Logic Change**: Update `WorldState.calculate_total_money()` (or `FinanceSystem`) to distinguish **Deposits** from **Overdrafts**.
- **Formula**: `M2 = Sum(Agent.cash) + Sum(Bank.deposits)`.
- **Implementation**:
  ```python
  # Pseudo-code
  total_m2 = 0
  for agent in agents:
      balance = agent.get_balance()
      if balance > 0:
          total_m2 += balance
      # Negative balances are tracked as 'SystemDebt', not M2 deduction.
  ```

### Specification 2: Atomic Firm Factory (`modules/firm/` & `simulation/`)
**Requirement**: No transaction shall be attempted towards an unregistered agent.
- **New Component**: `FirmFactory` service.
- **Workflow**:
    1. `create_firm()`
    2. `registry.register(firm)`
    3. `bank.open_account(firm.id)` **(BLOCKING)**
    4. `transaction.execute(injection)` **(VERIFIED)**
    5. Return `Firm` only if all steps succeed.

### Specification 3: Transaction Handler Hardening (`modules/economy/`)
**Requirement**: Fail fast on invalid destinations.
- **Logic**: `TransactionEngine` must validate `recipient_id` existence in `Bank` registry *before* attempting processing.
- **Fix**: Convert `Destination account does not exist` from a Runtime Error to a typed `TransactionError` that triggers a clean rollback/abort of the specific operation, rather than a generic engine error.

## 4. Test Plan (Phase 22)

To verify the fixes, the following tests must pass:

1.  **`tests/test_m2_integrity.py`**:
    -   Scenario: Induce massive debt in 50% of agents.
    -   Assertion: `calculate_total_money()` remains positive and constant (barring authorized injection).
2.  **`tests/test_firm_lifecycle.py`**:
    -   Scenario: Rapidly spawn 100 firms.
    -   Assertion: 0 `SETTLEMENT_FAIL` errors regarding "Destination account".
    -   Assertion: All spawned firms have `starting_capital` in their account.

## 5. Regression Analysis (Current State)
- **Existing Tests**: The logs show `SETTLEMENT_FAIL` is currently a caught exception (ERROR log), preventing a crash but corrupting the simulation state.
- **Impact**: The "Crash Fix" (Phase 21) worked by catching errors, but Phase 22 must *prevent* the errors to restore economic validity.

---
*Authorized by: Gemini-CLI (Technical Reporter)*
*Ref: reports/diagnostic_refined.md*