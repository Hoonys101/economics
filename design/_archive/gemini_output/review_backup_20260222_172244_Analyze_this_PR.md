# 🐙 Gemini CLI System Prompt: Git Reviewer

## 📝 Code Review Report

### 🔍 Summary
This PR implements the "Blind Major Choice" mechanism within `SystemEffectsManager`. It introduces logic to randomly assign a specialization (Major) when an agent upgrades to Education Level 1, fetching available majors dynamically from the configuration. It also enforces a "Sunk Cost" rule, preventing agents with existing specializations from switching majors during subsequent upgrades.

### 🚨 Critical Issues
*   None found.

### ⚠️ Logic & Spec Gaps
*   **Uniform Distribution Assumption**: The implementation uses `random.choice(specialized_majors)`, which implies a uniform probability for all majors. If the simulation requires scarcity for certain high-value majors (e.g., `TECHNOLOGY` vs `AGRICULTURE`), this unweighted random selection might cause an oversupply of high-tier talent.
*   **RNG Determinism**: Reliance on the global `random` module (implicit state) instead of a passed-in `RandomState` or seeded generator might complicate deterministic replayability if the global seed is not strictly managed by the `Simulation` engine.

### 💡 Suggestions
*   **Test Location**: Consider moving `tests/unit/systems/test_system_effects_major_choice.py` to `tests/unit/simulation/systems/` to align with the emerging `ARCH_TESTS.md` structure mirroring the source directory.
*   **Future Enhancement**: Support a `weights` key in the `LABOR_MARKET` configuration to allow probability-weighted major assignment (e.g., 50% Agriculture, 10% Technology).

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: *Implemented "Blind Major Choice" ... Random selection from available specialized majors ... Implicitly enforced by the condition `if (current_major == "GENERAL" or current_major is None)`.*
*   **Reviewer Evaluation**: The insight accurately captures the architectural decision to place this logic in `SystemEffectsManager` as a side-effect of the `EDUCATION_UPGRADE`. The identification of the "Sunk Cost" constraint as a state guard is correct. The "Protocol Purity" point regarding separation of concerns (Ministry = Finance/Policy, EffectsManager = State Mutation) is a strong architectural validation.

### 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    (No update required. `TD-CONFIG-HARDCODED-MAJORS` is already marked as RESOLVED (PH4.1) in the provided context, which this PR fulfills.)

### ✅ Verdict
**APPROVE**

The changes are logic-compliant, secure, and include necessary tests. The use of `getattr` for config access provides a safe transition path for the configuration refactor. The insight report is present and accurate.