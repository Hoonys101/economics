# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 🔍 Summary
This PR implements a comprehensive migration to **Integer-based Pricing (`price_pennies`)** across the entire simulation to enforce Financial Integrity (Zero-Sum). It standardizes `Order` object creation in all decision engines (Household, Firm, Government, System) to include strict integer values, resolving widespread `TypeError`s identified in post-merge testing.

### 🚨 Critical Issues
*   None. No security violations or hardcoded secrets detected.

### ⚠️ Logic & Spec Gaps
1.  **Price/Pennies Desync in Phase 1 (Deflationary Logic)**:
    *   **File**: `simulation/orchestration/phases/decision.py` (approx line 150)
    *   **Issue**: The code `order = replace(order, price_limit=new_price)` updates the float limit but **fails to update `price_pennies`**.
    *   **Impact**: The `MatchingEngine` (which now prioritizes `price_pennies` for sorting and execution) will ignore this deflationary adjustment, executing the trade at the original, higher price. This creates a functional regression for `DEFLATIONARY_PRESSURE_MULTIPLIER`.
    *   **Fix**: Update to `order = replace(order, price_limit=new_price, price_pennies=int(new_price * 100))`.

2.  **Ad-Hoc Class Definition in Engine**:
    *   **File**: `modules/household/engines/budget.py`
    *   **Issue**: A local class `StateWrapper` is defined inside `_plan_housing`.
    *   **Impact**: This suggests an interface mismatch between `EconStateDTO` and what `HousingPlanner` expects. While not a runtime error, it creates maintenance debt. Ideally, `HousingPlanner` should accept `EconStateDTO` directly or a standard adapter should be used.

### 💡 Suggestions
1.  **Centralize Order Factory**: The widespread repetition of `price_pennies=int(price * 100)` logic (seen in ~20 files) is prone to errors (as seen in `Phase1_Decision`). Consider adding a helper method `Order.create_from_float(...)` or similar factory to handle the conversion and sync consistently.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: The user correctly identified that strict DTO typing (`CanonicalOrderDTO`) clashed with legacy alias usage (`Order`), causing `TypeError`. The insight regarding `RealEstateUnit.estimated_value` being treated as float vs int is also crucial.
*   **Reviewer Evaluation**: The insight is accurate and valuable. The "Integer Migration Semantic Drift" observation is particularly important for future audits. The solution strategy (mass refactoring) was necessary.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md`
*   **Draft Content**:
```markdown
### 4. Order Generation Standard (The Penny Sync Rule)
- **Synchronization**: Any logic that generates or modifies a market `Order` MUST ensure that `price_limit` (float) and `price_pennies` (int) are synchronized.
- **Priority**: The `MatchingEngine` treats `price_pennies` as the Single Source of Truth (SSoT) for sorting and execution. Modifying `price_limit` without updating `price_pennies` results in "Ghost Logic" where the change is visible in logs but ignored by the market.
- **Pattern**:
  ```python
  # CORRECT
  new_pennies = int(new_float_price * 100)
  order = replace(order, price_limit=new_float_price, price_pennies=new_pennies)
  ```
```

### ✅ Verdict
**REQUEST CHANGES**

**Reason**: The logic gap in `simulation/orchestration/phases/decision.py` regarding `price_pennies` synchronization is a functional regression that undermines the integrity of the deflationary pressure mechanic. This must be fixed to ensure the `MatchingEngine` respects the adjusted prices. Other changes are excellent and strictly adhere to the new integer standard.