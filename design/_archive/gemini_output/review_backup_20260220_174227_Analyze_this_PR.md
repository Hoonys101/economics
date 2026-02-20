# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 1. 🔍 Summary
Implemented **Phase 4.1 Insight Engine**, introducing a "3-Pillar Learning" system (Experience, Education, Time) for `Household` agents. Key features include **Perceptual Filters** (Market Insight-dependent data distortion) and **Panic Propagation** mechanics. The `HouseholdAI` and `CommerceSystem` were updated to support dynamic insight modulation, and `GovernmentPolicyDTO` now carries macro-prudential signals.

### 2. 🚨 Critical Issues
*   None detected. Security checks (Secrets, URLs) and hardcoding audits passed.

### 3. ⚠️ Logic & Spec Gaps
*   **None**. The implementation closely follows the architectural insights provided.
    *   *Zero-Sum Check*: Insight is a non-monetary metric; its generation/decay does not violate financial integrity.
    *   *Purity Check*: `HouseholdAI` uses `_apply_perceptual_filters` to modify a *copy* of market data, preserving the immutability of the original input DTOs for other agents.

### 4. 💡 Suggestions
*   **Education Consumption**: Currently, `CommerceSystem` consumes *all* available `education_service` in inventory (`household.consume("education_service", edu_amt, ...)`). While compliant with the current spec ("Service Boosting"), future iterations might want to cap this per-tick to prevent "instant genius" spikes if an agent hoards education tokens.
*   **Insight Clamping**: `market_insight` is clamped to `[0.0, 1.0]` in `update_learning` and `consume`. Ensure this range is consistently respected if new modifiers are added later.

### 5. 🧠 Implementation Insight Evaluation

*   **Original Insight**:
    > "We have successfully implemented a robust '3-Pillar Learning' system... 1. Experience (Active Learning)... 2. Education (Service Boosting)... 3. Time (Natural Decay)... Perceptual Filters: High-insight agents see the market 'as it is' (Real-time). Low-insight agents see a distorted reality..."

*   **Reviewer Evaluation**:
    *   **Accuracy**: **High**. The code explicitly implements all three pillars:
        1.  `HouseholdAI.update_learning_v2` now returns `total_td_error`, which flows back to `Household.update_learning` to boost insight (Experience).
        2.  `CommerceSystem` triggers `Household.consume` for `education_service`, applying a direct boost (Education).
        3.  `Household.update_needs` applies a `insight_decay_rate` (Time).
    *   **Architecture**: The **Perceptual Filter** logic in `HouseholdAI` is implemented cleanly, injecting noise/lag into a localized copy of market data based on the agent's insight level. This effectively models information asymmetry.

### 6. 📚 Manual Update Proposal (Draft)
**N/A (Included in PR)**
*   The PR correctly includes updates to `design/1_governance/architecture/ARCH_AI_ENGINE.md`, documenting the "Dynamic Insight Engine (Phase 4.1)".
*   The insight report is correctly filed at `communications/insights/phase4-ai-insight-engine.md`.

### 7. ✅ Verdict
**APPROVE**

The PR is architecturally sound, secure, and fully verified with unit tests. The "Insight Engine" adds significant depth to agent behavior without introducing regression or purity violations.