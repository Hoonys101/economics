# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ Audit Pillars Analysis

### 1. 🛡️ Security & Hardcoding
- **Pass**: No API keys, secrets, or external URLs were detected in the diff.
- **Pass**: Path references appear to be relative/internal.

### 2. 🧠 Logic & Integrity
- **Zero-Sum Integrity**: The refactoring in `LaborMarket.match_market` correctly calculates surplus using integer arithmetic (`surplus = offer.offer_wage_pennies - seeker.reservation_wage_pennies`).
  - **Note**: The sharing logic `int(seeker.reservation_wage_pennies + (surplus * bargaining_power))` effectively floors the result. If `surplus` is odd and `bargaining_power` is 0.5, 0.5 pennies are implicitly retained by the paying side (Firm) via the price mechanism. This is a known acceptable behavior (Trade-off for Integer Safety) per `TD-MARKET-FLOAT-TRUNC`.
- **Spec Compliance**: The `JobOfferDTO` and `JobSeekerDTO` updates align perfectly with the "Integer Pennies" mandate (Phase 4.1).
- **Migration Safety**: The adapter logic in `place_order` and the `Transaction` creation correctly maps `_pennies` fields to legacy `price` (float) fields while prioritizing `total_pennies` as the SSoT.

### 3. 🏗️ Configuration & Dependency Purity
- **Pass**: `FiscalPolicyDTO` introduced in `modules/government/dtos.py` is a standard dataclass, resolving the `ImportError` mentioned in the insight.
- **Pass**: `LaborMarket` implementation remains stateless regarding agent instances, operating purely on DTOs.

### 4. 📚 Knowledge & Manualization
- **Pass**: `communications/insights/MISSION_labor_api_dto.md` is present and follows the required template.
- **Content**: The insight correctly identifies the DTO mismatch type error and documents the migration to integer pennies. Test evidence is sufficient.

### 5. 🧪 Testing & Hygiene
- **Pass**: Unit tests in `tests/unit/modules/labor/test_bargaining.py` and `tests/unit/test_labor_market_system.py` were actively updated to use `_pennies` fields and `IndustryDomain` enum, preventing regression.
- **Evidence**: `pytest` output confirms 10 passing tests.

---

## 📝 Code Review Report

### 1. 🔍 Summary
- Refactored `LaborMarket` matching logic and `JobOfferDTO`/`JobSeekerDTO` to strictly use integer pennies (`offer_wage_pennies`), resolving float precision mismatches.
- Restored `FiscalPolicyDTO` in `modules/government/dtos.py` to fix critical import errors in the Government module.
- Updated unit tests to enforce `IndustryDomain` enum usage and validate the new penny-based bargaining arithmetic.

### 2. 🚨 Critical Issues
*   None detected.

### 3. ⚠️ Logic & Spec Gaps
*   None detected.

### 4. 💡 Suggestions
*   **Surplus Floor Bias**: In `LaborMarket.match_market`, `int(seeker.reservation_wage_pennies + (surplus * 0.5))` truncates the worker's share if the surplus is odd. While this ensures integer safety, be aware that it creates a systemic micro-bias (0.5 pennies) in favor of the employer (who pays the `matched_wage`). This is acceptable for now but might need a "Banker's Rounding" utility in the future if surplus splits become more complex.

### 5. 🧠 Implementation Insight Evaluation
- **Original Insight**: "Identified a critical mismatch between `JobOfferDTO` and `JobSeekerDTO` definitions... and their usage in `modules/labor/system.py`... Refactored `LaborMarket` implementation to strictly use penny-based arithmetic..."
- **Reviewer Evaluation**: The insight is accurate and valuable. It correctly diagnoses a dangerous drift between API contracts (DTOs) and implementation usage (Legacy floats). The fix solidifies the "Integer Pennies" standard in the Labor domain.

### 6. 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
```markdown
| **TD-WAVE3-DTO-SWAP** | DTO | **IndustryDomain Shift**: Replace `major` with `IndustryDomain` enum. | **Medium**: Structure. | **RESOLVED (PH4.1)** |
```

### 7. ✅ Verdict
**APPROVE**