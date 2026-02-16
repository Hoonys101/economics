# Code Review Report: Liquidate DTO Contracts

## 🔍 Summary
Synchronizes `BorrowerProfileDTO`, `LoanInfoDTO`, and `Bailout` related DTOs to use `float` types, resolving the signature desynchronization. Implements a robust "Dual-Access" pattern in `LoanRiskEngine` to handle both legacy dictionaries and new DTO objects, and updates `Bank` and `FinanceSystem` to bridge integer-based ledgers with the new float-based DTOs.

## 🚨 Critical Issues
*   None identified.

## ⚠️ Logic & Spec Gaps
*   **Migration Heuristic Edge Case**: In `modules/finance/engines/loan_risk_engine.py`, the logic `if income == 0.0: income = float(get_field("income", 0.0))` uses `0.0` as a sentinel value to trigger a fallback lookup. While practical for migration, this theoretically prevents an agent with a legitimate `gross_income` of `0` from being processed correctly if they *also* have a legacy `income` field with a non-zero garbage value. Given this is a risk engine, it's acceptable, but noted.

## 💡 Suggestions
*   **Cleanup Marker**: The `safe_float` helper in `simulation/bank.py` and `get_field` in `loan_risk_engine.py` are clear defensive coding patterns for migration. It is recommended to annotate these with `# TODO: Remove after full DTO migration` to prevent them from becoming permanent technical debt.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: *"A key architectural tension identified is the mismatch between the "Zero-Sum Integrity" mandate (using integer pennies) and the new DTO specifications (using `float`)... The system now treats `float` in DTOs as a transport format for monetary values."*
*   **Reviewer Evaluation**: **Valid & Critical**. The distinction that `float`s in DTOs represent *Pennies* (e.g., `100.0` = 100 pennies) rather than *Dollars* (`1.00`) is a crucial architectural decision. This prevents the "Floating Point Dust" issue where `0.33` dollars becomes infinite fractions. The casting strategy at the boundary (`int(float_pennies)`) is the correct approach to maintain ledger integrity.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-DTO-DESYNC-2026** | DTO/API | **Contract Fracture**: `BorrowerProfileDTO` desync across Firm logic & 700+ tests following Dataclass migration. | **Critical**: System Integrity. | **Liquidated** |
```

## ✅ Verdict
**APPROVE**