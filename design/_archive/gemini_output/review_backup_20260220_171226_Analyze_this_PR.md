# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 1. 🔍 Summary
This PR implements **Utility-Priority Matching** for Labor Markets, replacing the standard Price-Time priority. Key changes include:
-   **Matching Logic**: Labor orders are now matched based on `Utility = Perception / Price`, where `Perception` is derived from labor skill and education level.
-   **Schema Expansion**: `Household` and `LaborManager` now propagate `education_level` and `market_insight` to the matching engine via `brand_info`.
-   **Cleanup**: Removed the shadowing `simulation/decisions.py` file to resolve import conflicts.
-   **Tests**: Added comprehensive unit tests for the new utility matching logic.

### 2. 🚨 Critical Issues
*None detected.*

### 3. ⚠️ Logic & Spec Gaps
-   **Wage Determination (Bid-Price Rule)**: In `_match_labor_utility`, the transaction price is set to the **Buyer's Bid Price** (`trade_price_pennies = b_wrapper.dto.price_pennies`).
    -   *Implication*: If a Worker asks for $10 and a Firm offers $20, the transaction occurs at $20. This models a "Firm-Set Wage" environment where high offers are binding. This is acceptable but differs from standard "Mid-Point" or "Maker-Taker" pricing in stock markets.
-   **Hardcoded Coefficients**: The utility formula uses a hardcoded multiplier for education: `skill * (1.0 + 0.1 * education)`.
    -   *Risk*: This `0.1` (10% boost per education level) is buried in the engine logic. It should eventually be moved to `economy_params.yaml` for tuning.

### 4. 💡 Suggestions
-   **Refactor `MutableOrder`**: The helper class `MutableOrder` is defined inside the `_match_labor_utility` method. While safe, moving it to the module level (e.g., `_MutableOrderWrapper`) would improve readability and testability.
-   **Config Extraction**: Extract the education weight (`0.1`) to a configuration constant (e.g., `LABOR_EDUCATION_UTILITY_WEIGHT`) to allow for easier balancing of the education return rate without code changes.

### 5. 🧠 Implementation Insight Evaluation
-   **Original Insight**: `communications/insights/phase4-ai-labor-matching.md` matches the implementation accurately. It correctly identifies the formula and the "cv" mechanism (`brand_info`).
-   **Reviewer Evaluation**: The insight is solid. It correctly highlights the architectural shift to Utility-Priority.
    -   *Value*: The "Regression Analysis" section is particularly useful, documenting the `TypeError` fix in `Household.__init__`.
    -   *Addendum*: It would be beneficial to explicitly note the "Bid-Price" clearing rule in future updates to avoiding confusion about wage inflation.

### 6. 📚 Manual Update Proposal (Draft)
I propose recording the hardcoded education weight as a minor technical debt item to ensure it doesn't get lost.

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| **TD-ECON-LABOR-MAGIC** | Economic | **Hardcoded Coeff**: Labor utility uses hardcoded `0.1` multiplier for education. | **Low**: Tuning Friction. | Open |
```

### 7. ✅ Verdict
**APPROVE**

The changes are logically sound, covered by new tests, and the "Insight Report" is properly included. The implementation of Utility-Priority matching adheres to the Phase 4.1 goals. The hardcoding of the education coefficient is a minor maintenance issue, not a blocker.