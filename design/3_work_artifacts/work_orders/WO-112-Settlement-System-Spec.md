# Work Order: WO-112 - Settlement System & Economic Purity

**Phase:** Phase 24 (Engine Repair)
**Priority:** CRITICAL
**Prerequisite:** AUDIT-ECONOMIC-V2 (Completed)

## 1. Problem Statement
The current simulation allows direct modification of agent assets (`agent.assets += ...`), leading to "Shadow Economy" activities that bypass logging and audit trails. Additionally, floating-point residuals during asset distribution (e.g., inheritance) evaporate from the system, violating the zero-sum principle and causing systemic deflation.

## 2. Objective
Implement a centralized, atomic `SettlementSystem` to handle all asset movements, enforce the privacy of agent asset state, and resolve residual evaporation.

## 3. Target Metrics
| Metric | Current | Target |
|---|---|---|
| Direct Asset Mutations (`assets +=`) | 40+ | 0 |
| Zero-sum Violations (Residuals) | Detected | 0 |
| Atomic Transaction Success Rate | N/A | 100% |

## 4. Implementation Plan

### Track A: Foundation (`simulation/finance/`)
1.  **API Definition**: Create `simulation/finance/api.py` with `IFinancialEntity` (Protocol) and `ISettlementSystem` (Interface) as per spec.
2.  **SettlementSystem Implementation**: Create `simulation/systems/settlement_system.py`. Implement `transfer` with debit/credit atomicity and comprehensive logging.
3.  **BaseAgent Refactor**: 
    - Rename `assets` to `_assets` in `BaseAgent`.
    - Provide `@property assets` (Read-only).
    - Implement `_add_assets` and `_sub_assets` (Protected).

### Track B: Integration & Refactoring
1.  **TransactionProcessor**: Replace all direct asset modifications with `settlement_system.transfer()` calls. Ensure tax collection also routes through this system.
2.  **InheritanceManager**: Implement "Residual Catch-all" logic. Calculate `remainder = total_cash - total_distributed` and transfer it to the government or reflux system.
3.  **Government & Bank**: Refactor all spending (`provide_household_support`, `invest_infrastructure`) and reserve updates to use the new system.

### Track C: Cleanup & Verification
1.  **Global Audit**: Grep for any remaining `assets +=` or `assets -=` and replace them.
2.  **Zero-Sum Verification**: Create or update `scripts/verify_zero_sum.py` to prove that total money supply is conserved across transfers and deaths.
3.  **Legacy Compatibility**: If any system cannot be moved immediately, register it in `TECH_DEBT_LEDGER.md`.

## 5. Verification
- Run `pytest tests/` (Expect fix-up tasks for existing tests).
- Run `python scripts/verify_zero_sum.py`.
- Verify logs for `TRANSFER` and `INSUFFICIENT_FUNDS` tags.

## 6. Jules Assignment
| Track | Task | Files |
|---|---|---|
| Track A | Core Infrastructure | `simulation/finance/api.py`, `simulation/systems/settlement_system.py`, `simulation/base_agent.py` |
| Track B | Major System Refactor | `simulation/systems/transaction_processor.py`, `simulation/systems/inheritance_manager.py`, `simulation/agents/government.py`, `simulation/bank.py` |
| Track C | Integrity Proof | `scripts/verify_zero_sum.py`, `design/TECH_DEBT_LEDGER.md` |

**Mandatory Reporting**: Record all implementation insights in `communications/insights/WO-112-settlement-insights.md`.
