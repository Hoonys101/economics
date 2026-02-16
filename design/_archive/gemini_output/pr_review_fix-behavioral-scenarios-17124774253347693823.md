🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_fix-behavioral-scenarios-17124774253347693823.txt
📖 Attached context: design\1_governance\architecture\ARCH_TESTS.md
📖 Attached context: design\1_governance\architecture\standards\TESTING_STABILITY.md
🚀 [GeminiWorker] Running task with manual: git-review.md

📝 [Review Report]
============================================================
# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR addresses unit vs. float type mismatches in test configurations. It aligns `survival_bid_premium` to an integer (`1`) in `test_animal_spirits_phase2.py` and patches `CHILD_MONTHLY_COST` in `test_wo048_breeding.py` to support legacy "Dollar-based" test logic against "Penny-based" production configuration.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
*   **Currency Unit Consistency (`tests/integration/test_wo048_breeding.py`, Line 90)**:
    *   The test patches `CHILD_MONTHLY_COST` to `500.0` (Float/Dollars) while the insight admits the production standard is `50000` (Int/Pennies).
    *   While this fixes the immediate test failure, it creates a "Schrödinger's Config" where the codebase operates on different currency scales during testing vs. production. This increases the risk of floating-point errors masking integer logic bugs.
*   **Type Hygiene (`tests/unit/decisions/test_animal_spirits_phase2.py`, Line 57)**:
    *   The assertion `assert orders[0].price == 11.0` uses a float. If `survival_bid_premium` is now strictly an integer (`1`), and the base price was presumably `10` (or `10.0`), the system should ideally be asserting against integer pennies (`11`) to strictly enforce the "Penny Architecture".

## 💡 Suggestions
*   **Refactor Integration Test**: Instead of patching `CHILD_MONTHLY_COST` to `500.0`, update the `test_wo048_breeding.py` test data to use Penny-based values (e.g., wage = 2500, cost = 50000) to match the production environment. This ensures the test validates the actual production arithmetic.
*   **Clarify Premium Logic**: The change from `10.0 * 1.1` (10% premium) to `10.0 + 1.0` (flat premium) in `test_animal_spirits_phase2.py` changes the economic logic from relative to absolute. Ensure this behavior change is intentional and not just a type fix.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > "The `tests/integration/test_wo048_breeding.py` test suite uses "Dollar" based values... while the production configuration... has migrated to "Penny" values... Resolution: Patched `CHILD_MONTHLY_COST`... to restore the intended economic dynamics for the test scenario."
*   **Reviewer Evaluation**:
    *   The insight accurately identifies the root cause (Unit Mismatch).
    *   It correctly identifies the resolution as a workaround (Patching) rather than a full refactor.
    *   **Value**: High. It documents a specific area of Technical Debt (Legacy Dollar Tests) that needs to be addressed in the `ARCH_TESTS.md` cleanup campaign.

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### Test Suite Currency Mismatch
    - **Date**: 2026-02-16
    - **Mission**: fix-behavioral-scenarios
    - **Description**: Integration tests (e.g., `tests/integration/test_wo048_breeding.py`) rely on legacy "Dollar" unit values (float), requiring ad-hoc config patching to `500.0` to function against the "Penny" (integer) based production system.
    - **Impact**: Risk of floating-point precision errors in tests masking integer arithmetic bugs in production.
    - **Action Item**: Refactor `test_wo048_breeding.py` and similar integration tests to use `Penny` integer values (x100 scale) for wages and costs.
    ```

## ✅ Verdict
**APPROVE**

The PR fixes the immediate crash and provides honest documentation of the underlying unit mismatch. While the "Dollar patching" in tests is technical debt, it is explicitly acknowledged in the insights, satisfying the audit requirements.
============================================================
✅ Review Saved: C:\coding\economics\design\_archive\gemini_output\review_backup_20260216_220849_Analyze_this_PR.md
