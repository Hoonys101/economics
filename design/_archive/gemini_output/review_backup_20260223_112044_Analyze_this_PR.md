# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR executes a comprehensive refactor of the `household` module to enforce **DTO Purity** and the **Penny Standard**. Key changes include the introduction of `DurableAssetDTO` to replace loose dictionaries, alignment of `LaborMarket` and `Finance` engines to use `_pennies` integer fields, and the introduction of a backward-compatibility layer in `HouseholdStateAccessMixin` to safely bridge legacy consumers. The refactor also patches `Government` and `Finance` components that relied on outdated DTO structures.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
*   **Hardcoded Magic Number**: In `modules/household/engines/budget.py`, the `_handle_medical_need` method uses a hardcoded `price_estimate = 10000.0` (Line 137). This implicitly assumes a fixed cost for medical services, which may drift from actual market conditions or configuration.
    *   *Risk*: If medical prices spike or deflation occurs, this static estimate could lead to incorrect budgeting behavior.

## 💡 Suggestions
*   **Configurability**: Move `price_estimate` in `budget.py` to `HouseholdConfigDTO` or fetch it dynamically from `market_snapshot` if available (similar to how food prices are handled).
*   **Constant Extraction**: Consider moving `DEFAULT_SURVIVAL_BUDGET_PENNIES` (Line 15) to `modules/household/constants.py` or the central configuration to centralize economic tuning parameters.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: The insight report correctly identifies that the strict DTO enforcement exposed "Deep Couplings" between `Household` state and other modules (`Government`, `Finance`). It highlights that integration tests relying on "Permissive Mocks" failed when the production code became stricter.
*   **Reviewer Evaluation**: The insight is technically sound and valuable. It accurately diagnoses *why* certain integration tests (like `TestFirmManagementLeak`) are failing—not because of logic errors in the refactor, but because the mocks in those tests no longer accurately reflect the strict data structures required by the system. This validates the need for "Mock Hardening" (TD-TEST-DTO-MOCK) previously identified.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
```markdown
### ID: TD-TEST-INT-MOCK-FRAGILITY
- **Title**: Integration Test Mock Fragility (DTO Strictness)
- **Symptom**: Integration tests (e.g., `TestFirmManagementLeak`) fail after DTO refactors because they use permissive mocks that lack new nested structures (e.g., `Government.policy`).
- **Risk**: High maintenance cost for refactors; false negatives in CI.
- **Solution**: Refactor integration tests to use `Golden Fixtures` or strict `DTO Factories` instead of ad-hoc `MagicMock`.
- **Status**: NEW (Household Refactor)
```

## ✅ Verdict
**APPROVE**

The PR significantly improves type safety and financial integrity (Penny Standard) without introducing critical bugs. The legacy compatibility layers ensure a smooth transition. The noted magic number is a minor implementation detail that can be addressed in a follow-up tuning pass.