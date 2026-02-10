# Code Review Report

## 🔍 Summary
This Pull Request primarily addresses the cleanup and refactoring of unit tests for `mod-agents` (`Firm`, `Household`, `Bank`, `Government`) following recent core architectural changes. The changes fix broken tests by adapting to new DTOs and API signatures, correct a profit calculation bug in `Firm`, and remove hardcoded values, significantly improving test reliability and code integrity.

## 🚨 Critical Issues
None. This submission correctly identifies and resolves existing issues. No new security vulnerabilities or critical logic flaws were introduced.

## ⚠️ Logic & Spec Gaps
None. The identified logic gaps were not in the production code's intent but in the test implementations, which have now been corrected.
- **`tests/unit/agents/test_government.py`**: The previous mock for `issue_treasury_bonds` only returned a value without simulating the state change (the government receiving the cash). The new `side_effect` correctly updates the government's wallet, allowing subsequent logic to pass as intended. This fixes a flawed test.
- **`simulation/firms.py`**: The fix in `record_revenue` to also update `current_profit` resolves a bug where firm profit was not being correctly tallied within a tick. This enhances the Zero-Sum integrity of the simulation.

## 💡 Suggestions
The quality of this submission is high. The proactive refactoring of tests to align with new architectural patterns (`AgentCoreConfigDTO`) is commendable. Continue this practice to prevent test suite decay.

## 🧠 Implementation Insight Evaluation
- **Original Insight**:
  ```markdown
  # Technical Insight: Mod-Agents Cleanup

  ## 1. Problem Phenomenon
  During the Unit Test Cleanup Campaign for `mod-agents`, several test failures were observed due to recent architectural refactoring in `Core Agents` (`Firm`, `Household`, `Bank`, `Government`).

  ### Symptoms
  - **`test_firm_profit.py`**: `TypeError: Firm.__init__() got an unexpected keyword argument 'id'`.
  - **`test_household_refactor.py`**: `TypeError: Household.__init__() missing 2 required positional arguments`.
  - **`test_bank.py`**: ID type mismatches (`str` vs `int`) causing `payment_callback` failures and missing interest transactions.
  - **`test_bank_decomposition.py`**: Invalid usage of `get_balance` for customer lookups and ID type mismatches.
  - **`agents/test_government.py`**: `AttributeError: ... does not have the attribute 'WelfareService'`, and logic failure in deficit spending tests due to missing side effects in mocks.

  ## 2. Root Cause Analysis
  1.  **Orchestrator-Engine Refactor**: `Firm` and `Household` constructors were updated to accept `AgentCoreConfigDTO` and Engines, but unit tests were using legacy arguments (e.g., passing `id` directly).
  2.  **ID Typing Discrepancy**: The codebase is migrating to strict `int` based `AgentID`, but older tests were casting IDs to `str` or mixing types, causing dictionary lookups to fail.
  3.  **Renamed Services**: `WelfareService` was renamed/refactored to `WelfareManager`, but `test_government.py` was still trying to patch the old name.
  4.  **Mock Logic Gaps**: Mocks for `issue_treasury_bonds` returned values but didn't simulate the state change (wallet update) required for subsequent logic checks in `Government`.
  5.  **Hardcoded Constants**: Tests contained hardcoded "USD" strings instead of using `DEFAULT_CURRENCY`.

  ## 3. Solution Implementation Details
  1.  **Updated Test Fixtures**: Refactored `mock_firm` and `Household` initialization in tests to use `AgentCoreConfigDTO` and `create_firm_config_dto` factory.
  2.  **Strict ID Typing**: Updated `test_bank.py` and `test_bank_decomposition.py` to use `int` for `borrower_id` consistently.
  3.  **Corrected API Usage**: Updated `test_bank_decomposition.py` to use `get_customer_balance` instead of `get_balance`.
  4.  **Patched Correct Classes**: Updated `test_government.py` to patch `WelfareManager`.
  5.  **Enhanced Mocks**: Added `side_effect` to `mock_finance.issue_treasury_bonds` to update government wallet, ensuring `provide_household_support` logic proceeds correctly.
  6.  **Removed Hardcoding**: Replaced `"USD"` with `DEFAULT_CURRENCY`.

  ## 4. Lessons Learned & Technical Debt
  - **Lesson**: When refactoring constructors or core APIs, updating unit tests immediately is crucial to avoid "rot".
  - **Lesson**: Mocks should simulate side effects (state changes) if the code under test relies on those changes, not just return values.
  - **Debt**: `Firm.record_revenue` did not update `current_profit` in `FinanceState`, which was fixed, but indicates a need for better synchronization or encapsulation between `Firm` (Orchestrator) and `FinanceEngine` (Logic).
  - **Debt**: `FinanceEngine` relies on `mock` objects in tests which iterate over them causing TypeErrors if not properly configured (return_value=[]).
  ```
- **Reviewer Evaluation**: The insight report is exemplary. It correctly identifies the root causes of the test failures, clearly linking them to specific architectural changes. The analysis of "Mock Logic Gaps" is particularly valuable, as it highlights a common testing pitfall. The "Lessons Learned" and "Technical Debt" sections demonstrate a deep understanding of the code and its underlying architectural principles. This is a model for how technical insights should be documented.

## 📚 Manual Update Proposal
The lesson regarding mock `side_effect` is a crucial piece of knowledge for maintaining a robust test suite. I propose adding it to the project's technical debt ledger.

- **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
- **Update Content**:
  ```markdown
  ---
  id: TD-XXX
  title: "Test Fragility due to State-Agnostic Mocks"
  status: "Identified"
  date: "2026-02-10"
  reporter: "Gemini"
  tags: ["testing", "mocking", "state-management"]
  ---

  ### 현상 (Phenomenon)
  - `agents/test_government.py`의 `test_deficit_spending_allowed_within_limit` 테스트에서 `mock_finance.issue_treasury_bonds`가 반환값만 있고 정부의 자산(wallet) 상태를 변경하지 않아, 이후 로직이 실패하는 문제가 발생했습니다.

  ### 원인 (Root Cause)
  - 테스트 대상 코드가 의존하는 객체(Dependency)의 상태 변화(Side Effect)에 영향을 받는 경우, `mock.return_value`만으로는 충분하지 않습니다. Mock이 단순히 값을 반환할 뿐, 실제 객체처럼 상태를 변경시키지 않으면 테스트는 현실과 다른 시나리오로 진행됩니다.

  ### 해결 (Solution)
  - `mock.side_effect`를 사용하여 함수를 연결하고, 해당 함수 내에서 목 객체나 테스트 대상 객체의 상태를 직접 변경하도록 구현했습니다. 이를 통해 Mock이 상태 변화를 올바르게 시뮬레이션하도록 수정했습니다.

  ### 교훈 (Lesson Learned)
  - **Mocks Must Simulate State**: 테스트 중인 코드가 의존성의 상태 변화에 의존하는 경우, Mock은 `return_value`를 넘어 `side_effect`를 통해 해당 상태 변화를 충실히 시뮬레이션해야 합니다. 그렇지 않으면 테스트는 거짓 양성(false-positive)을 통과하거나, 이 경우처럼 거짓 음성(false-negative)으로 실패할 수 있습니다.
  ```

## ✅ Verdict
**APPROVE**
