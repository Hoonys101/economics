# Spec: Liquidate LoanMarket Dict-Leak

## 1. Overview
- **Goal**: Resolve `AttributeError` caused by `LoanMarket` methods returning `dict` instead of `LoanInfoDTO` objects.
- **Scope**: `simulation/loan_market.py` and its interaction with `simulation/bank.py`.
- **Target**: Ensure strict `DTO` usage for `LoanInfoDTO` across the Housing/Loan pipeline.

## 2. Problem Analysis
- **Symptom**: `LoanMarket.convert_staged_to_loan` returns a dictionary literal: `{"loan_id": ..., ...}`.
- **Impact**: Downstream consumers (e.g., `HousingMarket` or `Dashboard`) expecting `dto.loan_id` fail with `AttributeError`.
- **Root Cause**:
  1. Legacy implementation of `convert_staged_to_loan` explicitly constructs a `dict`.
  2. Unit tests (`test_loan_market_mortgage.py`) mock `bank.stage_loan` to return a `dict`, reinforcing the bad pattern.
- **Tech Debt**: [TD-DTO-DESYNC-2026] Contract Fracture.

## 3. Proposed Changes

### 3.1. `simulation/loan_market.py`

#### `convert_staged_to_loan`
**Current Logic (Pseudo):**
```python
def convert_staged_to_loan(self, id):
    loan = bank.loans[id]
    return {"loan_id": id, ...}  # Returns Dict
```

**New Logic (Pseudo):**
```python
from modules.finance.api import LoanInfoDTO

def convert_staged_to_loan(self, staged_loan_id: str) -> Optional[LoanInfoDTO]:
    # 1. Validation
    if not hasattr(self.bank, 'loans') or staged_loan_id not in self.bank.loans:
        return None

    # 2. Retrieval (Assuming Bank Internal State Object)
    loan_entity = self.bank.loans[staged_loan_id]

    # 3. DTO Construction
    return LoanInfoDTO(
        loan_id=staged_loan_id,
        borrower_id=loan_entity.borrower_id,
        original_amount=loan_entity.principal,
        outstanding_balance=loan_entity.remaining_balance,
        interest_rate=loan_entity.annual_interest_rate,
        origination_tick=loan_entity.origination_tick,
        due_tick=loan_entity.start_tick + loan_entity.term_ticks,
        lender_id=self.bank.id,
        term_ticks=loan_entity.term_ticks
    )
```

#### `stage_mortgage` & `apply_for_mortgage`
- Update return type hints to `Optional[LoanInfoDTO]`.
- Ensure they propagate the object returned by `convert_staged_to_loan`.

### 3.2. Verification Strategy (Tests)

**Existing Tests (`tests/unit/markets/test_loan_market_mortgage.py`):**
- **Impact**: Will FAIL immediately because mocks return dicts.
- **Action**: Update `mock_bank.stage_loan.return_value` and `mock_bank.loans` entries to use `MagicMock(spec=LoanInfoDTO)` or actual dataclass instances.

**New Test Case (Integration check):**
```python
def test_end_to_end_dto_purity(loan_market, mock_bank):
    # Setup
    mock_bank.loans = {
        "loan_999": MockLoanEntity(borrower_id=1, principal=100.0, ...)
    }

    # Execute
    result = loan_market.convert_staged_to_loan("loan_999")

    # Verify
    assert isinstance(result, LoanInfoDTO)
    assert result.loan_id == "loan_999"
    assert result.original_amount == 100.0
```

## 4. Risk Assessment
- **Breaking Change**: Any code currently relying on `loan['loan_id']` (subscript access) will break.
- **Mitigation**: Search codebase for `apply_for_mortgage` usage. Given this is part of the new `HousingPlanner` pipeline (Phase 32), usage should be limited.
- **Dependency**: Requires `modules.finance.api.LoanInfoDTO` to be strictly defined.

## 5. Mandatory Reporting
- [ ] Create `communications/insights/liquidate-loan-market.md` documenting the fix.
- [ ] Record the transition from `Dict` to `Dataclass` as a resolved Tech Debt item.
