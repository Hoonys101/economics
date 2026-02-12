# Mission Guide: Finance Engine Purity & QE Restoration

## 1. Objectives
- **Restore QE Logic (TD-QE-MISSING)**: Fix the desync in `issue_treasury_bonds` where Central Bank purchase logic was either missing or failing verification.
- **Enforce Engine Purity (TD-FIN-001)**: Refactor `DebtServicingEngine` and `LoanBookingEngine` to follow the `State_In -> State_Out` pattern, avoiding in-place mutation of the `FinancialLedgerDTO`.

## 2. Implementation Roadmap

### Phase 1: Engine Purity (Functional Pattern)
- **Location**: `modules/finance/engines/`
- **Task**: Modify `grant_loan` and `service_all_debt` to:
    1. Create a deep copy of the `FinancialLedgerDTO`.
    2. Perform operations on the copy.
    3. Return the copy in `EngineOutputDTO`.
- **Constraint**: Ensure `Transaction` objects generated remain consistent with the new state.

### Phase 2: QE Restoration & SEO Alignment
- **Location**: `modules/finance/system.py`
- **Task**: 
    1. Update `issue_treasury_bonds` to use the refactored SEO pattern (receiving necessary macro stats as DTOs).
    2. Verify the `debt_to_gdp` trigger.
    3. Fix the `xfail` in `tests/modules/finance/test_qe_bond_issuance.py`.
    4. Ensure `central_bank.id` is correctly recorded as the owner when QE is active.

## 3. Reference Context (MUST READ)
- `modules/finance/engines/debt_servicing_engine.py`
- `modules/finance/engines/loan_booking_engine.py`
- `modules/finance/system.py`
- `tests/modules/finance/test_qe_bond_issuance.py` (Source of Truth for the failure)

## 4. Verification
- `pytest tests/modules/finance/engines/test_loan_engines.py`
- `pytest tests/modules/finance/test_qe_bond_issuance.py` (Remove xfail and verify PASS)
- Zero-sum integrity must be maintained.
