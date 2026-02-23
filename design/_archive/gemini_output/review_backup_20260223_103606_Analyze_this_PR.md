# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**.
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ Code Review Report

### 🔍 Summary
This PR implements a comprehensive realignment of the Finance Module APIs and DTOs, strictly enforcing the **Penny Standard (Integer Arithmetic)** across the core financial domains (`FinanceSystem`, `Bank`, `Government`, `Taxation`). It consolidates scattered data structures into `modules/finance/dtos.py` and removes legacy floating-point reliance in critical paths (e.g., `LoanRiskEngine`, `TaxService`). Compatibility layers (properties returning floats) are added to `LoanDTO` to ease migration.

### 🚨 Critical Issues
*   None found. The migration to integer math (`round_to_pennies`) appears robust and safe.

### ⚠️ Logic & Spec Gaps
*   **Encapsulation Risk in `FinanceSystem`**: 
    In `modules/finance/system.py`, the `request_loan` method appears to return `loan_state` directly from the ledger:
    ```python
    # loan_state is already LoanDTO (LoanStateDTO alias)
    return loan_state, result.generated_transactions
    ```
    Since `LoanDTO` is not explicitly marked `frozen=True` in the diff (default is mutable), and `LoanStateDTO` is an alias to it, returning the ledger object directly exposes the Bank's internal state to modification by the caller (e.g., `Household` agent).
    *   **Mitigation**: Ensure `LoanDTO` is `frozen=True` or return `copy.deepcopy(loan_state)`.

### 💡 Suggestions
*   **Encapsulation**: Decorate `LoanDTO` with `@dataclass(frozen=True)` in `modules/finance/dtos.py` to prevent accidental mutation of the ledger state via returned references.
*   **Legacy Housing DTOs**: `MortgageApprovalDTO` (in `modules/housing/dtos.py` and `modules/market/housing_planner_api.py`) still uses `float` for `approved_principal`. While `LoanMarket` handles the conversion correctly, plan to migrate these DTOs to `int` pennies in the next wave (Wave 2) for full consistency.
*   **Market Data Assumption**: `TaxationSystem` correctly assumes market data prices are in float dollars and converts them. Ensure `OrderBookMarket` telemetry continues to provide float prices in `market_stats` to maintain this contract.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: The user provided `communications/insights/MISSION_finance_api_dto.md` highlighting DTO consolidation, Integer Pennies Standard, and successful regression testing.
*   **Reviewer Evaluation**: The insight accurately reflects the changes. The "Test Evidence" section is particularly valuable, confirming that the drastic type changes didn't break existing logic (`BOND_ISSUANCE_WARNING`, `BAILOUT_DENIED` logs show logic is working). The note on "Import Errors" shows good diligence in regression fixing.

### 📚 Manual Update Proposal (Draft)
**Target File**: `design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md`

**Draft Content**:
```markdown
### 4. Data Transfer Objects (DTOs)
- **Unified Definition**: All financial DTOs (`LoanDTO`, `BondDTO`, `DepositDTO`) are defined in `modules/finance/dtos.py`.
- **Immutability**: DTOs returned by Systems (e.g., `FinanceSystem`, `BankService`) MUST be treated as immutable. Where possible, use `@dataclass(frozen=True)`.
- **Penny Fields**: All monetary fields in DTOs MUST be suffixed with `_pennies` (e.g., `principal_pennies`) or clearly documented as integer pennies.
- **Legacy Compatibility**: Computed properties returning `float` (e.g., `original_amount`) are permitted for backward compatibility but must not be used for ledger arithmetic.
```

### ✅ Verdict
**APPROVE**

The PR successfully executes the "Integer Penny" migration and DTO consolidation without introducing security vulnerabilities or obvious logic errors. The logic gaps identified (DTO mutability) are architectural improvements for the next iteration rather than blocking flaws, given the current cooperative agent environment. The inclusion of the Insight Report and `TECH_DEBT_LEDGER.md` updates is compliant with protocol.