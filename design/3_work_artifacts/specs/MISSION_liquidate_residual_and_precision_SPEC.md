# Mission Guide: Liquidation of Residual Failures & Market Precision Refactor

## 1. Objectives
- **Liquidate Residual Test Failures**:
    - [ ] **Bailout Legacy**: Replace `executive_salary_freeze` with `executive_bonus_allowed` in `welfare_service.py` to match `BailoutCovenant` DTO.
    - [ ] **Precision Drift**: Refactor pricing logic in `SalesEngine` to use integer pennies and standardized rounding.
    - [ ] **Scaling Mismatches**: Resolve Dollar-vs-Penny mismatches in `FinanceEngine` unit tests.
- **Market Precision Refactor (TD-MKT-FLOAT-MATCH)**:
    - [ ] Refactor `MatchingEngine` to use Integer Math for mid-price and execution.
    - [ ] Implement explicit rounding rules (Round-Down / Remainder-to-Market-Maker) to ensure Zero-Sum integrity.

## 2. Reference Context (MUST READ)
### Core Logic
- [welfare_service.py](../../../modules/government/services/welfare_service.py)
- [sales_engine.py](../../../simulation/components/engines/sales_engine.py)
- [finance_engine.py](../../../simulation/components/engines/finance_engine.py)
- [matching_engine.py](../../../simulation/markets/matching_engine.py)

### Protocols & Contracts
- [finance/api.py](../../../modules/finance/api.py) (BailoutCovenant, LoanInfoDTO)
- [TECH_DEBT_LEDGER.md](../../2_operations/ledgers/TECH_DEBT_LEDGER.md) (TD-MKT-FLOAT-MATCH)

## 3. Implementation Roadmap
### Phase 1: Diagnostic Audit
- Run the full test suite and pinpoint the exact lines causing the ~10 residual failures.
- Trace the `BailoutCovenant` usage across `Government` and `Finance` modules.

### Phase 2: Spec Generation
- Draft a detailed implementation spec for the `MatchingEngine` integer refactor.
- Define a unified `round_to_pennies` policy for all Engines.

### Phase 3: Verification Strategy
- Define success criteria for "Zero-Sum Intelligence": M2 supply delta must be exactly 0.0 after 1000 ticks.

## 4. Verification
- `pytest tests/unit/modules/government/test_welfare_service.py`
- `pytest tests/unit/components/test_finance_engine.py`
- `pytest tests/unit/markets/test_matching_engine.py`
- `pytest tests/integration/test_m2_integrity.py` (if exists)
