modules/finance/api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable

from modules.system.api import CurrencyCode, AgentID

@dataclass(frozen=True)
class BorrowerProfileDTO:
    """
    Standardized Data Transfer Object for Borrower Risk Assessment.
    TD-DTO-DESYNC-2026: Fixed signature desynchronization.
    """
    borrower_id: str
    gross_income: float
    existing_debt_payments: float
    collateral_value: float
    existing_assets: float
    # Optional fields for enhanced risk scoring (Future-proofing)
    credit_score: Optional[float] = None
    industry_sector: Optional[str] = None
    consecutive_loss_ticks: int = 0

@dataclass(frozen=True)
class LoanInfoDTO:
    """
    Represents the details of an active or proposed loan.
    """
    loan_id: str
    borrower_id: str
    lender_id: str
    original_amount: float
    remaining_principal: float
    interest_rate: float
    term_ticks: int
    start_tick: int
    # Status tracking
    status: str = "PENDING"  # PENDING, ACTIVE, DEFAULTED, CLOSED
    covenants: Optional[Any] = None

@dataclass(frozen=True)
class GrantBailoutCommand:
    """
    Command to grant a bailout loan to a distressed entity.
    """
    firm_id: AgentID
    amount: float
    interest_rate: float
    covenants: BailoutCovenant

@dataclass(frozen=True)
class BailoutCovenant:
    """
    Restrictions applied to a bailout loan.
    """
    dividends_allowed: bool = False
    executive_bonus_allowed: bool = False
    min_employment_level: Optional[int] = None

@runtime_checkable
class IFinancialAgent(Protocol):
    """
    Protocol for agents participating in the financial system.
    """
    id: AgentID
    
    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> float:
        ...

    def get_total_debt(self) -> float:
        ...

```

design/3_work_artifacts/specs/liquidate_dto_contracts_spec.md
```markdown
# Spec: Liquidate DTO Contract Desyncs (TD-DTO-DESYNC-2026)

## 1. Overview
This specification addresses the Critical Technical Debt **TD-DTO-DESYNC-2026**. The transition to frozen Dataclasses for DTOs has caused widespread regressions in the Finance and Corporate Logic modules. Specifically, `BorrowerProfileDTO` constructor signatures do not match their call sites, and legacy tests/logic are attempting to subscript (`obj['key']`) objects that are now Dataclasses (`obj.key`).

## 2. Scope
- **Target Module**: `modules/finance/` and `simulation/decisions/firm/`
- **Affected Tests**: ~700 tests (specifically `tests/unit/finance/` and `tests/unit/corporate/`)
- **Key Artifacts**:
    - `BorrowerProfileDTO` (Signature Alignment)
    - `LoanInfoDTO` (Access Pattern Standardization)
    - `FinancialStrategy` (Update Instantiation)

## 3. API & Data Structures

### 3.1. `BorrowerProfileDTO` (Refined)
Defined in `modules/finance/api.py`. Must be a `frozen=True` dataclass.

```python
@dataclass(frozen=True)
class BorrowerProfileDTO:
    borrower_id: str
    gross_income: float
    existing_debt_payments: float
    collateral_value: float
    existing_assets: float
    credit_score: Optional[float] = None
    industry_sector: Optional[str] = None
    consecutive_loss_ticks: int = 0
```

### 3.2. `LoanInfoDTO` (Refined)
Legacy code treating this as a dictionary must be refactored to use dot notation.

```python
@dataclass(frozen=True)
class LoanInfoDTO:
    loan_id: str
    borrower_id: str
    lender_id: str
    original_amount: float
    remaining_principal: float
    # ... (see api.py)
```

## 4. Implementation Plan

### 4.1. Code Refactoring (`FinancialStrategy`)
File: `simulation/decisions/firm/financial_strategy.py`
- **Action**: Verify `BorrowerProfileDTO` instantiation in `_manage_debt` matches the new signature.
- **Correction**: Ensure no legacy keys are passed. The current snippet looks correct *if* the DTO matches. The spec enforces the DTO to match this usage.

### 4.2. Test Suite Refactoring (`Mass Replace`)
File: `tests/unit/finance/*.py` & `tests/unit/corporate/*.py`
- **Action**: Replace all occurrences of `loan['field']` with `loan.field`.
- **Target**: `test_finance_system_refactor.py`, `test_financial_strategy.py`.
- **Regex Strategy**: `s/loan\['(\w+)'\]/loan.\1/g`

## 5. Risk Analysis & Audit

### 5.1. Impact Analysis
- **High Risk**: Modifying `BorrowerProfileDTO` might break `LoanRiskEngine` if it expects different fields.
    - **Mitigation**: Grep `LoanRiskEngine` usage to ensure it consumes the new attributes correctly.
- **Test Fragility**: Mocks in `conftest.py` might be returning dicts instead of DTOs.
    - **Mitigation**: Update `conftest.py` fixtures to return instances of the new Dataclasses.

### 5.2. Mandatory Reporting
> **[Instruction]**
> Upon completion of the analysis and before/during implementation, you MUST record all findings, debt resolutions, and potential side-effects in:
> `communications/insights/liquidate-dto-contracts.md`
>
> This report is a **Hard Requirement** for PR approval.

## 6. Verification Plan

### 6.1. Verification Test Case
Create a specific verification test to ensure the contract holds.

```python
def test_borrower_profile_contract_integrity():
    from modules.finance.api import BorrowerProfileDTO
    
    # Happy Path: Exact Match with FinancialStrategy usage
    dto = BorrowerProfileDTO(
        borrower_id="FIRM-001",
        gross_income=1000.0,
        existing_debt_payments=50.0,
        collateral_value=0.0,
        existing_assets=500.0
    )
    assert dto.borrower_id == "FIRM-001"
    
    # Contract Check: Immutability
    try:
        dto.gross_income = 2000.0
        assert False, "DTO should be frozen"
    except (FrozenInstanceError, AttributeError):
        pass
```

### 6.2. Integration Check
Run `pytest tests/unit/finance/test_finance_system_refactor.py` and ensure the `test_grant_bailout_loan_deprecated` passes with dot notation assertions.
```