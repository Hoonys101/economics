# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR implements the **Brain Scan (What-If Analysis)** capability for the `Firm` agent, a critical feature for "Stateless Engine Orchestration" (SEO). It introduces the `IBrainScanReady` protocol and a pure `brain_scan` method in `Firm` that orchestrates engines with injected context (`config_override`, `market_snapshot_override`) without side effects.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   **Legacy Order Handling**: The `brain_scan` method currently skips legacy decision logic unless mocked (`if "decision_engine" in context.mock_responses`). Ensure this doesn't lead to "Blind Spots" where the brain scan result diverges significantly from reality for firms still heavily reliant on legacy logic.

## 💡 Suggestions
*   **Test Hygiene (DTOs)**: In `tests/test_firm_brain_scan.py`, `MagicMock` is used for DTOs (e.g., `mock_budget = MagicMock()`).
    *   **Guidance**: Per `TESTING_STABILITY.md`, avoid mocking DTOs. DTOs are simple data containers; instantiate them directly (e.g., `BudgetPlanDTO(labor_budget_pennies=10000, ...)`) or use a Factory. This catches type errors (e.g., typo in field name) that a permissive `MagicMock` would hide.
*   **Refactoring**: The override application in `brain_scan` is repetitive (`if context.config_override:`). Consider moving this logic to a helper method `_apply_context_overrides(context)` to keep the orchestrator clean.

## 🧠 Implementation Insight Evaluation

*   **Original Insight**: *When using `MagicMock(spec=Dataclass)`, if the dataclass has fields without default values, they do not appear in `dir(Dataclass)`. Consequently, `MagicMock` raises an `AttributeError`... Solution: Use a permissive `MagicMock()`.*
*   **Reviewer Evaluation**: The observation regarding `dir(Dataclass)` and `MagicMock` is technically accurate and a common friction point. However, the proposed solution (permissive mocks) contradicts strict testing standards (`TESTING_STABILITY.md`). **Better Solution**: Do not mock DTOs at all. Instantiate the real Data Class. If the DTO is complex, use a Factory (e.g., `DietFactory` patterns). This ensures tests break if the DTO schema changes, maintaining "Type Safety".

## 📚 Manual Update Proposal (Draft)

*   **Target File**: `design/1_governance/architecture/ARCH_AGENTS.md`
*   **Draft Content**:
    ```markdown
    ### 4.3 Advanced Capability: Brain Scan (What-If Analysis)
    The Stateless Engine architecture enables a "Brain Scan" capability (`IBrainScanReady`), allowing agents to simulate decision cycles purely in memory.

    - **Mechanism**:
      1. **Snapshot Injection**: Accepts `MarketSnapshotDTO` and `ConfigDTO` overrides.
      2. **Pure Execution**: Calls the same Stateless Engines used in production (`plan_budget`, `decide_workforce`).
      3. **Result Aggregation**: Returns an `IntentDTO` payload without executing side effects (no `settlement.transfer` or `market.place_order`).
    - **Use Case**:
      - **Counterfactuals**: "What if wages rose 10%?"
      - **Optimization**: Running 100 variations of pricing strategy in a single tick.
      - **Debugging**: Inspecting agent logic logic without pausing the simulation.
    ```

## ✅ Verdict
**APPROVE**

The implementation solidly demonstrates the value of the SEO pattern. The `brain_scan` method provides a safe, side-effect-free way to query agent logic. The test hygiene issue regarding DTO mocking is noted as a suggestion for future cleanup but does not block this feature.