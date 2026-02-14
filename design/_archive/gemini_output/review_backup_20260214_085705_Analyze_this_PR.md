# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR fixes a `TypeError` in `test_public_manager_compliance.py` caused by a mismatch between the `MarketSignalDTO` definition and its usage in test fixtures. Specifically, it initializes the missing `total_bid_quantity` and `total_ask_quantity` fields, ensuring the test aligns with the evolved DTO schema.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   None. The fix directly addresses the described regression.

## 💡 Suggestions
*   **Centralized Test Factories**: As noted in previous insights (and hinted at here), manually updating DTO instantiations across scattered unit tests is prone to "Shotgun Surgery" anti-patterns. Consider creating a `tests/factories.py` or similar to centralize DTO creation with sensible defaults, so future schema additions only need to be updated in one place.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > The `MarketSignalDTO` is a frozen dataclass used for cross-boundary data transfer... It was updated to include `total_bid_quantity` and `total_ask_quantity`... However, the test `tests/unit/modules/system/execution/test_public_manager_compliance.py` was instantiating `MarketSignalDTO` without these required fields... This highlights the importance of keeping test data fixtures in sync with DTO schema changes.
*   **Reviewer Evaluation**: The insight accurately identifies the root cause (schema evolution vs. static test fixtures). It correctly links this to the "DTO Purity" guardrail. The evaluation is sound.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### [2026-02-14] Test Fixture Desynchronization (DTO Evolution)
    *   **Context**: `MarketSignalDTO` added `total_bid_quantity`/`total_ask_quantity` fields.
    *   **Issue**: `test_public_manager_compliance.py` failed because it manually instantiated the DTO without new fields.
    *   **Resolution**: Manually updated test fixture with default `0.0` values.
    *   **Lesson**: Evolution of shared DTOs breaks decentralized test fixtures.
    *   **Action Item**: Implement centralized DTO Factories (e.g., `ModelFactory`) for tests to encapsulate default values and reduce maintenance burden on schema changes.
    ```

## ✅ Verdict
**APPROVE**

The changes are minimal, safe, and correct. The insight is properly recorded in the PR. The test evidence confirms the fix.