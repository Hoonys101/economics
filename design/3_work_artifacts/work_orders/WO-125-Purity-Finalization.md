# Work Order: -Finalization

**Phase:** The Great Reset (Finalization)
**Objective:** Finalize the "Economic Purity" reforms by removing all remaining legacy asset mutation paths and enforcing the Purity Gate.
**Assignee:** Jules (Implementation Agent)

## 1. Context
The "Economic Purity" initiative (, ) aimed to centralize all asset mutations into the `SettlementSystem` and enforce DTO-only decision contexts.
Recent audits (TD-101, TD-117) indicate that while the core architecture is in place, legacy fallbacks and commented-out fields remain, posing a "Structural Risk" of regression.
We must now perform the final cleanup to liquidate these debts.

## 2. Tasks

### Task A: Enforce SettlementSystem (TD-101)
**Location:** `simulation/systems/transaction_processor.py`
**Goal:** Remove the legacy fallback `else` blocks that allowed direct `withdraw/deposit`.
**Action:**
1. In `TransactionProcessor.execute`:
 - Verify that `state.settlement_system` is available. Raise `RuntimeError` if it is missing (it should be mandatory now).
 - Remove all `if settlement: ... else: ...` blocks.
 - Replace them with unconditional `settlement.transfer(...)` calls.
 - If `settlement.transfer` fails, the transaction is skipped (no manual fallback).

### Task B: Finalize Purity Gate (TD-117)
**Location:** `simulation/dtos/api.py`
**Goal:** Permanently remove the deprecated fields to prevent regression.
**Action:**
1. In `DecisionContext` class:
 - Delete the commented-out lines:
 ```python
 # household: Optional["Household"] = None
 # firm: Optional["Firm"] = None
 ```
 - Ensure `state` and `config` are the *only* way to access agent data.

### Task C: Verify and Clean Rules
**Location:** `simulation/decisions/rule_based_household_engine.py` (and usage sites)
**Goal:** Ensure no `self.household` references remain (Audit).
**Action:**
1. Scan for any usage of `context.household` or `context.firm` in rule-based engines.
2. (Already verified by `verify_purity_gate.py` which passes strict check locally, but ensure static analysis matches).
3. Remove any "Note: Wage modifier..." comments if they are no longer relevant or confusing.

### Task D: Verification
**Action:**
1. Run `tests/test_transaction_processor.py` (ensure it mocks SettlementSystem correctly).
2. Run `tests/test_household_decision_engine_new.py`.
3. Run `scripts/verify_purity_gate.py`.

## 3. Definition of Done
1. `TransactionProcessor` has NO calls to `.withdraw()` or `.deposit()` on agents.
2. `DecisionContext` definition in `api.py` has NO legacy strings/comments referring to agent instances.
3. All tests pass.
4. Tech Debts TD-101 and TD-117 can be marked RESOLVED in `TECH_DEBT_LEDGER.md`.
