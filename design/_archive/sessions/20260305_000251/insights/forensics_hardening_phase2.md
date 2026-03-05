# Forensics Hardening Phase 2 Insight Report

## Architectural Insights

### Technical Debt Identified

1.  **DTO Inconsistency**:
    -   `LoanApplicationDTO` is defined as a `TypedDict` in `modules/finance/dtos.py` but as a `@dataclass` in `modules/finance/engine_api.py`. They have different fields.
    -   `LoanDTO` is a `TypedDict` in `modules/finance/dtos.py` but `LoanStateDTO` is a `@dataclass` in `modules/finance/engine_api.py` with slight differences.
    -   `TransactionContext` is a `TypedDict` in `simulation/dtos/transactions.py` but a `@dataclass` in `simulation/systems/api.py`.

2.  **Corporate Tax Calculation Bug**:
    -   In `modules/government/taxation/system.py`, `generate_corporate_tax_intents` multiplies the already-pennies `tax_amount` by 100, effectively inflating tax by 100x. This is a critical zero-sum integrity violation (magic money creation/destruction leak).

3.  **Use of `TypedDict` for Cross-Boundary Data**:
    -   `modules/finance/dtos.py` uses `TypedDict` extensively, which violates the mandate "DTO Purity: Use typed DTOs/Dataclasses for cross-boundary data. Avoid raw dicts."

### Architectural Decisions

1.  **Unify DTOs**:
    -   Promote `@dataclass` versions as the canonical DTOs.
    -   Move `TransactionContext` to `simulation/dtos/transactions.py` (as dataclass).
    -   Convert `modules/finance/dtos.py` contents to `@dataclass`.
    -   Update `modules/finance/engine_api.py` to import from `modules/finance/dtos.py`.

2.  **Fix Zero-Sum Integrity**:
    -   Remove the 100x multiplier in corporate tax calculation.

## Regression Analysis

(To be filled after implementation)

## Test Evidence

(To be filled after implementation)

## Test Evidence

All relevant tests passed (26/26):
- `tests/finance/test_settlement_fx_swap.py`: Verified FXMatchDTO dataclass usage.
- `tests/finance/test_protocol_integrity.py`: Verified settlement system integrity.
- `tests/forensics/test_bond_liquidity.py`: Verified bond liquidity checks.
- `tests/forensics/test_escheatment_crash.py`: Verified escheatment handler stability.
- `tests/forensics/test_ghost_account.py`: Verified dynamic agent resolution.
- `tests/forensics/test_saga_integrity.py`: Verified saga orchestrator DTO validation.

Specific Regression Test for Corporate Tax Bug:
- Created and ran `tests/modules/government/taxation/test_corporate_tax_bug.py` which confirmed the fix (100 pennies vs 10000 pennies).
