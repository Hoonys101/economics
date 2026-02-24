# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🔍 Summary
This PR addresses two critical macro-economic instability drivers: **Hyperinflation** caused by incorrect OMO dimensionality (interpreting penny amounts as bond quantities) and **Premature Firm Liquidation** where solvent firms were killed by the "Zombie Timer". It introduces a "Solvency-First" lifecycle check and a strict `amount // par_value` calculation for bond operations. Additionally, it enforces DTO attribute access in `CentralBankSystem` and expands test coverage to verify these logic repairs.

---

## 🚨 Critical Issues
*   None found. Security and Hardcoding checks passed.

---

## ⚠️ Logic & Spec Gaps
*   **None identified.** The logic changes (`current_assets > threshold` check and `quantity` calculation) directly address the stated architectural insights. The move to DTO dot-notation access (`instruction.target_amount`) is a positive step for type safety, provided all callers (orchestrators) have been updated to pass DTO objects instead of dicts. The included tests suggest this is the case.

---

## 💡 Suggestions
*   **Test Organization**: `test_omo_quantity_calculation` is currently located inside `tests/test_firm_survival.py`. While acceptable for a hotfix, it functionally belongs in `tests/integration/test_omo_system.py` or a dedicated unit test for `CentralBankSystem`. Consider moving it in a future refactor for better discoverability.

---

## 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > **Solvency-First Lifecycle**: The `AgingSystem` was refactored to prioritize Solvency (Assets > 0) over the "Zombie Timer" (Consecutive Losses). This prevents "Institutional Suicide" where solvent firms were killed prematurely.
    > **Dimensional Correction in OMO**: The `CentralBankSystem` previously calculated OMO quantity as `amount`, leading to hyperinflation (assuming Price=1). The fix introduces `quantity = amount // par_value` (where par_value=10000 pennies), ensuring correct monetary injection scaling.

*   **Reviewer Evaluation**:
    *   **High Value**: The "Dimensional Correction" insight is crucial. Confusing *Nominal Value* (pennies) with *Quantity* (units) is a classic financial engineering error that was correctly identified and fixed.
    *   **Strategic Shift**: The "Solvency-First" approach shifts the simulation from a pure rule-based termination to a more asset-centric survival model, which should allow for more realistic "turnaround" scenarios for firms.
    *   **Accurate**: The insights accurately reflect the code changes in `aging_system.py` and `central_bank_system.py`.

---

## 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` (or create if missing)

```markdown
## [2026-02-24] Macro-Economic Stabilization (WO-FINAL-MACRO-REPAIR)

### 1. Dimensionality Correction (OMO)
- **Problem**: The Central Bank interpreted OMO targets (e.g., "Buy 1M pennies") as bond quantities (e.g., "Buy 1M bonds"), triggering massive hyperinflation (10,000x multiplier effect).
- **Fix**: Enforced dimensional analysis. `Quantity = Target_Amount_Pennies // Bond_Par_Value_Pennies`.
- **Lesson**: Financial engines must explicitly distinguish between `MonetaryAmount` (Currency) and `UnitQuantity` (Assets).

### 2. Solvency-First Lifecycle
- **Problem**: Firms with massive cash reserves were being liquidated simply because they had consecutive losses (Zombie Timer), acting like a rigid "expiration date" regardless of financial health.
- **Fix**: Introduced `Solvency Bypass`. If `Assets > Closure_Threshold`, the Zombie Timer is ignored.
- **Principle**: "Cash is King." A firm should only die when it cannot pay its debts (Insolvency) or runs out of capital, not just because it is currently unprofitable.
```

---

## ✅ Verdict
**APPROVE**

The PR effectively resolves critical economic simulation bugs with sound logic and comprehensive testing. The 100% test pass rate on a large suite (1054 tests) provides high confidence.