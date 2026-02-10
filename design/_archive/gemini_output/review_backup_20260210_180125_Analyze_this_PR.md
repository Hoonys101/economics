# 🔍 Summary
This Pull Request primarily refactors the instantiation of core agents like `Firm` and `Household` to use the `AgentCoreConfigDTO`, promoting a cleaner, more structured initialization process. A significant portion of the changes involves updating system and integration tests to align with evolving agent protocols (`IFinancialAgent`, `IInventoryHandler`) and modern state access patterns (e.g., using `wallet.get_balance()` instead of direct `finance.balance` access). An excellent and detailed insight report has been included.

# 🚨 Critical Issues
None found.

# ⚠️ Logic & Spec Gaps
1.  **Leftover Debug Code**: Debug `print` statements have been left in the production code. These should be removed before merging.
    *   `simulation/systems/handlers/goods_handler.py`: `print(f"[DEBUG] GoodsHandler...")`
    *   `simulation/systems/settlement_system.py`: `print(f"[DEBUG] settle_atomic failed...")`

2.  **Missing Test Evidence**: The project guidelines mandate that PRs include evidence of passing tests (e.g., `pytest` logs). This diff does not contain any such evidence, which is a mandatory requirement for approval.

# 💡 Suggestions
*   **Mock Consistency**: In `tests/system/test_engine.py`, the mocked households have their `withdraw`/`deposit` side effects modifying a separate `hh.assets` float, while the primary state is being migrated to `hh._econ_state.assets` as a dictionary. While the test passes, this internal inconsistency can make future debugging difficult. Consider refactoring the mock side effects to directly manipulate the `_econ_state` dictionary to better reflect the behavior of the real objects. This point is already well-articulated in the provided insight report.

# 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    ```markdown
    # Mission Insights: Core Agent & Protocol Restoration

    ## Technical Debt & Insights

    ### 1. Mock fragility in System Tests
    `tests/system/test_engine.py` uses a mix of real objects (`Firm`, `Simulation`) and Mocks (`Household`, `Transaction`). This hybrid approach causes significant friction when protocols change (e.g., `IFinancialAgent` requiring `get_balance`). The mocks often lack the full behavior required by complex systems like `SettlementSystem` (e.g., side effects for `withdraw` working but state not persisting correctly for rollback logic, or method signature mismatches).
    **Recommendation:** Refactor system tests to use lightweight real implementations of `Household` (stubbed engines) instead of pure Mocks where possible, or use a strictly typed `FakeAgent` that fully implements `IAgent` protocols.

    ### 2. Protocol Adherence
    The shift to `IFinancialAgent` (withdraw/deposit with currency) and `IInventoryHandler` is largely complete in code but tests lag behind. The strict enforcement of `currency` in `withdraw` exposed that many mocks were naive.
    **Recommendation:** Add a linting step or a test utility that verifies Mocks against Protocols (`verify_object=True` or custom checker) to catch signature drifts early.

    ### 3. State Access Patterns
    Direct access to attributes like `agent.inventory` (dict) or `agent.finance.balance` persists in tests despite the codebase moving to `agent.get_quantity()` and `agent.wallet.get_balance()`.
    **Action Taken:** Fixed several occurrences in `test_engine.py`, but a global audit of test assertions is recommended.

    ### 4. Settlement System Complexity
    The `settle_atomic` failure in `test_process_transactions_labor_trade` (rollback despite valid conditions) suggests a subtle issue with Mock state interactions or `TaxationSystem` configuration in the test environment. The lack of visibility (swallowed logs in tests) made debugging difficult.
    **Recommendation:** Ensure `mock_logger` in tests is configured to print to stderr on failure, or use `caplog` fixture more effectively.

    ## Protocol Deviations Fixed
    - `Household.__init__`: Updated to use `AgentCoreConfigDTO` and `engine`.
    - `Firm.__init__`: Updated to use `AgentCoreConfigDTO` and `engine`.
    - `MockAgent`: Updated `withdraw`/`deposit` to accept `currency`.
    - `test_api_extensions.py`: Updated to use `_econ_state.assets` structure.
    ```
*   **Reviewer Evaluation**: The insight report is of exceptional quality. It correctly identifies the most significant source of technical debt addressed in this change: the fragility of mocks that are not synchronized with evolving interface protocols. The analysis is precise, the recommendations are actionable (e.g., using `FakeAgent`s, verifying mocks against protocols), and it demonstrates a deep understanding of the architectural challenges. This report perfectly fulfills the requirement for knowledge manualization.

# 📚 Manual Update Proposal
The insights from this mission are valuable for improving our testing standards. They should be consolidated into our central technical debt ledger.

*   **Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`
*   **Update Content**:
    ```markdown
    ---
    
    ## ID: TD-255
    - ** 현상 (Phenomenon) **: System tests using `unittest.mock.Mock` are brittle and frequently break when core interfaces (`Protocol`s) are updated. Mocks often have outdated method signatures or fail to replicate necessary side-effects, leading to high test maintenance friction. (Discovered during `mission_core_agent_restoration`)
    - ** 원인 (Cause) **: Mocks are not automatically verified against the interfaces they are supposed to replicate. Direct patching (`@patch`) and manual mock creation lead to a divergence between the test environment and production code reality.
    - ** 해결 (Solution) **:
        1.  Prioritize using lightweight, real test implementations (`Fake` objects that explicitly implement the protocol) over generic `Mock`s for complex agents.
        2.  Implement a CI step or test utility that verifies mock objects against their corresponding `Protocol` definitions to detect signature drift early.
    - ** 교훈 (Lesson) **: Architectural purity enforced by Protocols must be accompanied by purity in test fixtures to remain effective and prevent technical debt.
    ```

# ✅ Verdict
**REQUEST CHANGES (Hard-Fail)**

While the core code refactoring and the accompanying insight report are excellent, the PR cannot be approved due to two violations of project guidelines:
1.  **Leftover debug `print` statements** in the codebase.
2.  **Missing `pytest` execution logs** to serve as evidence that all tests pass after these significant changes.

Please address these points and resubmit.
