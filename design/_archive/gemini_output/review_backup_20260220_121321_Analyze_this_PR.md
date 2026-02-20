# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR refactors unit tests for `FiscalEngine` and `MonetaryEngine` to align with the strictly typed DTO architecture. It replaces loose dictionary usage with proper `FiscalStateDTO`, `MonetaryStateDTO`, and `FiscalDecisionDTO` instantiation, explicitly resolving `AttributeError` failures caused by the recent migration to Dataclasses.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
*None detected.* The changes directly address a specification gap between the test suite (legacy dicts) and the production code (strict DTOs).

## 💡 Suggestions
*   **DTO Factory Usage**: While manual instantiation in tests (`FiscalStateDTO(...)`) is correct for now, consider using `factories.py` or a helper method for complex nested DTOs like `FiscalRequestDTO` in the future to reduce boilerplate and maintenance burden if the DTO schema changes again.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > The current test suite exhibits significant DTO mismatches in the Government and Finance engines. Specifically: `FiscalEngine` and `MonetaryEngine` expect frozen ` @dataclass` instances... but tests... are initializing these inputs as raw dictionaries.
*   **Reviewer Evaluation**:
    The insight accurately identifies the root cause of the test failures (Type mismatch: `dict` vs `Dataclass`). The remediation strategy (Strict DTO Instantiation) is sound and correctly implemented in the PR. This confirms the diagnosis in `ARCH_TESTS.md` regarding "DTO/State Object Transition".

## 📚 Manual Update Proposal (Draft)
*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Draft Content**:
    ```markdown
    ### ID: TD-TEST-DTO-DRIFT
    ### Title: Test Suite DTO Mismatches
    - **Symptom**: `AttributeError` in tests when Engines switch from `dict` access to `dot.notation` (Dataclasses).
    - **Risk**: Test blindness; tests pass false positives or fail noisily during refactors.
    - **Lesson**: Tests must strictly instantiate DTOs (`StateDTO(...)`) rather than using `dict` literals. Use `isinstance` checks for return values.
    ```

## ✅ Verdict
**APPROVE**