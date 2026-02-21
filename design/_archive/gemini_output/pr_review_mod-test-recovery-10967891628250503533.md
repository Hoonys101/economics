🕵️  Reviewing Code with instruction: 'Analyze this PR.'...
📖 Attached context: C:\coding\economics\design\_archive\gemini_output\pr_diff_mod-test-recovery-10967891628250503533.txt
📖 Attached context: design\1_governance\architecture\standards\TESTING_STABILITY.md
📖 Attached context: design\1_governance\architecture\standards\LIFECYCLE_HYGIENE.md
📖 Attached context: design\1_governance\architecture\standards\FINANCIAL_INTEGRITY.md
📖 Attached context: design\1_governance\architecture\standards\INDEX.md
📖 Attached context: design\1_governance\architecture\ARCH_SEQUENCING.md
📖 Attached context: design\1_governance\architecture\ARCH_TESTS.md
📖 Attached context: design\2_operations\ledgers\TECH_DEBT_LEDGER.md
📖 Attached context: modules\system\api.py
📖 Attached context: simulation\dtos\api.py
🚀 [GeminiWorker] Running task with manual: git-review.md

📝 [Review Report]
============================================================
# 🐙 Gemini CLI Code Review Report

## 🔍 Summary
This PR addresses critical test suite instability in restricted environments by implementing a "Mock-if-Missing" strategy for heavy dependencies (`fastapi`, `pydantic`, `websockets`). Simultaneously, it fixes a **Financial Integrity regression** in `DebtStatusDTO`, enforcing the Penny Standard (Integer arithmetic) in `Bank.get_debt_status`.

## 🚨 Critical Issues
*   None found. Security and "Zero-Sum" checks passed.

## ⚠️ Logic & Spec Gaps
*   **None**. The `int()` casting in `simulation/bank.py` correctly aligns with `FINANCIAL_INTEGRITY.md`.

## 💡 Suggestions
*   **Repetitive Mock Checks**: The logic to check if a module is mocked (`isinstance(websockets, MagicMock) ...`) is repeated across multiple test files. Consider centralizing this into a helper (e.g., `tests.utils.is_mocked(module)`) to reduce boilerplate and maintenance burden.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: *"The codebase had drifted from the strict Protocol definition... `Bank.get_debt_status` was instantiating `DebtStatusDTO` with legacy fields... Resolution: The `Bank` class... were updated to strictly adhere to the `DebtStatusDTO` dataclass signature... reinforces the 'Zero-Sum Integrity' guardrail."*
*   **Reviewer Evaluation**: **Excellent**. The insight correctly identifies a high-priority regression (Float vs Int in financial DTOs) that would have caused silent calculation errors. The connection between the "Mock-if-Missing" strategy and the ability to run the test suite in the sandbox is also well-articulated. This is a high-value fix for both stability and correctness.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/1_governance/architecture/standards/TESTING_STABILITY.md`

```markdown
### 7. Soft Dependency Strategy (The "Run Anywhere" Rule)
- **Mock-if-Missing**: The test suite MUST run in environments where optional heavy dependencies (e.g., `fastapi`, `uvicorn`, `websockets`, `pydantic`) are not installed.
- **Conditional Skips**: Tests relying on these libraries MUST use conditional skips or `conftest.py` injection to gracefully degrade.
- **Implementation**:
  ```python
  # conftest.py pattern
  try:
      import fastapi
  except ImportError:
      fastapi = MagicMock()
      sys.modules["fastapi"] = fastapi
  ```
```

## ✅ Verdict
**APPROVE**

The PR successfully stabilizes the test suite and enforces the Penny Standard in the Bank module. The accompanying insight report is comprehensive and accurate.
============================================================
✅ Review Saved: C:\coding\economics\design\_archive\gemini_output\review_backup_20260221_183325_Analyze_this_PR.md
