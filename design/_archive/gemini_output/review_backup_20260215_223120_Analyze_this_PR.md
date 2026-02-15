# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**.
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 📝 Code Review Report

### 1. 🔍 Summary
This PR executes a major refactoring to migrate financial values from `float` (dollars) to `int` (pennies) across DTOs, Engines, and the `SettlementSystem`. It also hardens the `IBank` protocol with stricter type checking (`@runtime_checkable`).

### 2. 🚨 Critical Issues
*   **None**. No security credentials or critical hardcoded paths found.

### 3. ⚠️ Logic & Spec Gaps
*   **Potential 100x Cost Inflation Bug (`simulation/firms.py`)**:
    *   Line 1017: `unit_cost_estimate=int(self.finance_engine.get_estimated_unit_cost(self.finance_state, item_id, self.config) * 100)`
    *   **Context**: `FinanceState` fields like `expenses_this_tick` have been migrated to `int` (pennies). Assuming `get_estimated_unit_cost` (which is not in the diff) calculates cost based on these state variables, it now returns **pennies** (not dollars as before).
    *   **Issue**: Multiplying the result (pennies) by 100 treats the value as if it were still dollars, resulting in a value that is **100x larger than intended**.
    *   **Recommendation**: Remove the `* 100` multiplier if the engine now returns pennies. Verify the return unit of `get_estimated_unit_cost`.

### 4. 💡 Suggestions
*   **Magic Number**: `modules/firm/engines/pricing_engine.py` uses `1000` (10.00 pennies) as a default price fallback. Consider moving this to `FirmConfigDTO` or a constant `DEFAULT_FALLBACK_PRICE_PENNIES`.
*   **Unit Consistency**: `modules/firm/engines/pricing_engine.py` keeps `shadow_price` as `float`. While acceptable for internal analysis, ensure this doesn't leak into any transactional logic later.

### 5. 🧠 Implementation Insight Evaluation
*   **Original Insight**: `communications/insights/fix-dto-integrity.md` correctly captures the migration scope (Float -> Int) and the Protocol Purity updates.
*   **Reviewer Evaluation**: The insight is accurate and well-structured. It correctly identifies the "Zero-Sum Integrity" mandate as the driver. The "Test Evidence" section is robust.

### 6. 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md` (or `ECONOMIC_INSIGHTS.md` if available)
*   **Draft Content**:
```markdown
## [2026-02-15] DTO Integer Migration & Protocol Hardening
- **Context**: Migrated core financial DTOs and Engines from `float` (dollars) to `int` (pennies) to enforce Zero-Sum integrity.
- **Change**: Updated `Transaction`, `Share`, `RealEstateUnit`, and associated Engine DTOs. Refactored `SettlementSystem` to use `IBank` protocol with `isinstance` checks instead of `hasattr`.
- **Impact**: eliminated floating-point drift in financial transactions.
- **Verification**: `tests/unit/modules/finance/test_system.py` and `test_engines.py` passed.
- **Lesson**: When migrating units (Dollars -> Pennies), derived calculations in Orchestrators (like `Firm.py`) often retain legacy conversion logic (`* 100`), leading to magnitude errors. Always audit call sites for unit conversion redundancy.
```

### 7. ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

The logic in `simulation/firms.py` regarding `unit_cost_estimate` appears to introduce a 100x calculation error due to double-conversion (Pennies * 100). This must be verified and fixed before merging. The rest of the PR is solid.