# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🏗️ Audit Pillars Analysis

### 1. Security & Hardcoding
- **Pass**: No secrets or credentials found in the extracted constants.
- **Pass**: Extracted constants (`DEFAULT_MARKET_INSIGHT`, `DEFAULT_LIQUIDATION_PRICE`, etc.) are generic economic parameters, not sensitive data.

### 2. Logic & Integrity
- **Pass**: The extraction of constants maintains the exact values from the original code (e.g., `market_insight` decay `0.001`, boost `0.05`).
- **Pass**: Zero-Sum integrity is preserved; the refactoring is structural.
- **Pass**: Fallback logic for `labor_wage` and `current_price` correctly uses the new constants (`DEFAULT_LABOR_WAGE`, `DEFAULT_PRICE`).

### 3. Configuration & Dependency Purity
- **Warning**: In `modules/firm/api.py`, the new protocols (`ISalesEngine`, `IBrandEngine`, etc.) heavily utilize `Any` for the `state` parameter (e.g., `def post_ask(self, state: Any, ...)`).
  - While this breaks circular dependencies, it weakens the "Protocol Purity" claimed in the insight report. It is acceptable for this transition phase but should be tightened to specific State DTOs in the future.
- **Pass**: `Firm` orchestrator correctly types its engine instances with the new protocols (e.g., `self.sales_engine: ISalesEngine`).

### 4. Knowledge & Manualization
- **Pass**: `communications/insights/firm-decoupling.md` is well-written, covering architectural changes, regression analysis (dependency issues), and test evidence.
- **Observation**: `TECH_DEBT_LEDGER.md` was not updated in the Diff, but `TD-ARCH-FIRM-COUP` is directly addressed by this PR.

### 5. Testing & Hygiene
- **Pass**: Report includes evidence of 925 passing tests.
- **Pass**: The report explains the resolution of `fastapi`/`websockets` environment issues, which gives confidence in the verification process.

---

## 📝 Code Review Report

### 1. 🔍 Summary
- Extracted hardcoded economic values from `simulation/firms.py` into a reusable `modules/firm/constants.py` module.
- Defined explicit protocols (`ISalesEngine`, `IBrandEngine`, `IFinanceEngine`, `IHREngine`) in `modules/firm/api.py` to enforce interface boundaries.
- Updated `Firm` orchestrator to use these constants and protocols, decoupling it from concrete engine implementations.

### 2. 🚨 Critical Issues
*None detected.*

### 3. ⚠️ Logic & Spec Gaps
- **Loose Typing in Protocols**: In `modules/firm/api.py`, methods like `post_ask`, `record_expense`, and `process_payroll` accept `state: Any`. This bypasses static type checking for the state object.
  - *Context*: `def post_ask(self, state: Any, context: SalesPostAskContextDTO) -> Order:`
  - *Recommendation*: Use `TYPE_CHECKING` imports to reference `SalesStateDTO`, `FinanceStateDTO`, etc., to enforce stricter contracts without causing circular imports.

### 4. 💡 Suggestions
- **Tech Debt Update**: Since this PR addresses `TD-ARCH-FIRM-COUP` ("Parent Pointer Pollution") by introducing protocols, consider updating `TECH_DEBT_LEDGER.md` to mark it as "In Progress" or add a reference to this mission.
- **Default Price Safety**: `DEFAULT_PRICE` is set to `1000` (10.00 units). Ensure this fallback is safe for all good types (e.g., cheap raw materials vs expensive electronics) to avoid valuation skew when market data is missing.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: [Jules's Report] "We enforced Protocol Purity by introducing explicit protocols... The new protocols utilize strict Data Transfer Objects (DTOs)..."
- **Reviewer Evaluation**: The insight is accurate and valuable, particularly the section on **Regression Analysis** regarding the missing test dependencies. However, the claim of "Protocol Purity" is slightly overstating the reality given the use of `Any` for state objects. The architectural direction is correct, but the implementation is "Pragmatic Purity" rather than strict purity.

### 6. 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
| TD-ARCH-FIRM-COUP | Architecture | Parent Pointer Pollution | High | In Progress (See firm-decoupling.md) |
```

### 7. ✅ Verdict
**APPROVE**

The PR successfully executes the decoupling of constants and protocols without introducing regressions. The use of `Any` in protocols is a minor technical debt acceptable for this stage of refactoring.