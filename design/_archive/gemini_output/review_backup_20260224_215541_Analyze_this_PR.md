# 🐙 Gemini CLI System Prompt: Git Reviewer

> **Worker Identity**: You are a **Gemini-CLI Subordinate Worker** (Lead Code Reviewer & Security Auditor).
> **Mission Authority**: You operate under the strict orchestration of **Antigravity (The Architect)**. 
> **Operational Protocol**: You are a content generator. You cannot execute code or modify the filesystem. Your output is a "Code Review Report" for human/Antigravity review.

---

## 🏗️ Audit Pillars Analysis

### 1. Security & Hardcoding
- **Passed**: No API keys or external secrets found.
- **Note**: Constants like `DESPERATION_THRESHOLD_TICKS = 20` and `0.9` wage filter are logic-specific and acceptable for this implementation phase.

### 2. Logic & Integrity
- **Passed**: "Labor Thaw" mechanisms (Desperation Decay, Talent Signal, Liquidity Check) are implemented consistently across DTOs, Engines, and Systems.
- **Liquidity Guard**: The check `current_cash >= projected_cost` in `Firm` prevents "hiring into bankruptcy" loops, a critical stability fix.
- **Desperation Decay**: The decay rate (5% per tick after 20 ticks) is aggressive but aligns with the "Thaw" objective to force market clearing.
- **Zero-Sum**: No money is created; matching scores are abstract multipliers.

### 3. Configuration & Dependency Purity
- **Passed**: `BudgetEngine` remains stateless, modifying the passed `EconStateDTO` in place. `Firm` correctly delegates balance checks to `FinancialComponent`.

### 4. Knowledge & Manualization
- **Passed**: `communications/insights/WO-IMPL-LABOR-MARKET-THAW.md` is well-structured and covers architectural decisions and test evidence.
- **Evaluation**: The insight correctly identifies the "Adapter Bottleneck" resolved by passing `talent_score` via `CanonicalOrderDTO.metadata`.

### 5. Testing & Hygiene
- **Passed**: `tests/unit/test_labor_thaw.py` covers the new logic. Existing system tests pass.

---

## 📝 Code Review Report

### 🔍 Summary
Implements **Labor Market Thaw** mechanics (Phase 4.2) to unblock matching stagnation. Key features include **Desperation Wage Decay** (Households lower ask price over time), **Talent Signaling** (Higher talent boosts match score), and **Firm Liquidity Checks** (Prevents hiring if cash < 1st wage payment).

### 🚨 Critical Issues
*None detected.*

### ⚠️ Logic & Spec Gaps
*None detected.*

### 💡 Suggestions
*   **Magic Number**: In `modules/labor/system.py`, the relaxed wage filter `if base_score < 0.9:` is hardcoded. Consider moving this `0.9` to a configurable constant (e.g., `LaborConfigDTO.wage_match_tolerance`) in a future refactor to allow dynamic tuning without code changes.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: "Adapter Bottleneck Navigated... talent attribute... marshaled through CanonicalOrderDTO.metadata... via the updated LaborMatchDTO."
*   **Reviewer Evaluation**: **Valid & Critical**. The reviewer notes that `LaborMarket.place_order` was updated to check `order_dto.metadata` (previously only checked `brand_info` for Households). This was a necessary fix to allow the `RuleBasedHouseholdDecisionEngine` (which writes to `metadata`) to successfully transmit the `talent_score`. Without this change, the talent signal would have been lost during DTO conversion.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`
*   **Draft Content**:
    ```markdown
    ## [Phase 4.2] Labor Market Thaw & Desperation Mechanics
    **Date**: 2026-02-24
    **Mission**: WO-IMPL-LABOR-MARKET-THAW
    
    ### Mechanisms Implemented
    1.  **Desperation Decay**: Households now track `unemployment_duration`. After 20 ticks, the `shadow_reservation_wage` decays by 5% per tick, overriding the minimum wage config (floor: 1 penny). This forces eventual market clearing.
    2.  **Talent Signal**: `LaborMarket` matching now includes a multiplier based on `talent_score` (1.0 + (talent-1.0)*0.5), allowing high-talent agents to win bids even at slightly higher wages.
    3.  **Liquidity Guard**: Firms now perform a "Pre-flight Liquidity Check" before placing job offers. If `cash < wage * quantity`, the hiring order is aborted to prevent immediate insolvency.
    ```

### ✅ Verdict
**APPROVE**