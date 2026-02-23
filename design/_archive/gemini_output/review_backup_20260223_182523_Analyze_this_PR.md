# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🏗️ Audit Pillars

### 1. Security & Hardcoding
*   **CRITICAL**: `simulation/systems/transaction_processor.py` contains a hardcoded magic number `999999` in `_handle_public_manager`.
*   **CRITICAL**: `modules/government/political/orchestrator.py` contains a hardcoded ID `1` in `valid_payees`.
*   These magic numbers obscure intent and create maintenance hazards. They must be replaced with named constants (e.g., from `modules.system.constants`).

### 2. Logic & Integrity
*   **Resurrection Hack**: The modification of `context.agents` in `EscheatmentHandler` is a clever but dangerous workaround. It effectively modifies global state during a transaction context. While the `finally` block ensures cleanup, this pattern implies `SettlementSystem` is too coupled to the live agent registry.
*   **SkipTransactionError**: The introduction of `SkipTransactionError` significantly improves robustness against "Zombie Agent" crashes. This aligns well with the "Best Effort" processing philosophy for batch operations.

### 3. Config & Dependency Purity
*   **FirmFactory Injection**: Updating `FirmManagement` to inject `engine` into `FirmFactory` resolves a critical `STARTUP_FATAL` error and correctly implements Dependency Injection.

### 4. Knowledge & Manualization
*   **Insight Report**: `communications/insights/MISSION_wave5_runtime_stabilization.md` is present and accurately documents the "Resurrection Hack" and the "Strictness vs Reality" architectural conflict.

### 5. Testing & Hygiene
*   **Test Alignment**: Tests in `tests/modules/finance/transaction/test_engine.py` and `tests/unit/test_transaction_engine.py` were correctly updated to reflect the new `SkipTransactionError` behavior.

---

## 📝 Code Review Report

### 🔍 Summary
This PR implements runtime stabilization fixes for Wave 5. It introduces `SkipTransactionError` to handle inactive agents gracefully in batch transactions, implements a context-injection workaround ("Resurrection Hack") for escheating dead agents, and fixes a Dependency Injection missing argument in `FirmFactory`.

### 🚨 Critical Issues
*   `modules/government/political/orchestrator.py`: **Hardcoded ID `1`**.
    ```python
    valid_payees = [ID_PUBLIC_MANAGER, ID_GOVERNMENT, "GOVERNMENT_TREASURY", 1]
    ```
    Is `1` the System Admin? Use a named constant.
*   `simulation/systems/transaction_processor.py`: **Hardcoded Magic Number `999999`**.
    ```python
    or tx.seller_id == 999999
    ```
    This looks like a debug value or a legacy ID for the Public Manager. Consolidate to `ID_PUBLIC_MANAGER` or add a named constant.

### ⚠️ Logic & Spec Gaps
*   **EscheatmentHandler Side-Effect**: Modifying `context.agents` (even temporarily) is risky in a concurrent environment (though this sim is likely single-threaded). Ensure this doesn't mask genuine "Missing Agent" bugs elsewhere.

### 💡 Suggestions
*   **Consolidate ID Checks**: In `TransactionProcessor`, instead of checking 4 different variations of Public Manager IDs inline, create a helper `is_public_entity(agent_id)` in `modules.system.constants` or a relevant service.

### 🧠 Implementation Insight Evaluation
*   **Original Insight**: *We implemented a temporary context injection in `EscheatmentHandler` to re-introduce the dying agent into the `context.agents` map... preserving Zero-Sum integrity before the agent is finalized.*
*   **Reviewer Evaluation**: The insight accurately captures the "Strictness vs. Lifecycle" conflict. The `SettlementSystem` demanding an agent exist in the live registry vs. the `EscheatmentHandler` trying to clean up a dead agent is a classic lifecycle race condition. This is a high-value architectural finding.

### 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/TECH_DEBT_LEDGER.md`

```markdown
## [2026-02-23] Settlement Lifecycle Strictness
*   **Status**: Active / Workaround Applied
*   **Component**: `SettlementSystem` / `EscheatmentHandler`
*   **Phenomenon**: `SettlementSystem` throws `InvalidAccountError` if an agent is not in the live registry. However, `EscheatmentHandler` needs to transfer assets *from* an agent that is already flagged as inactive/removed.
*   **Current Hack**: "Resurrection Hack" in `EscheatmentHandler` temporarily re-injects the dead agent into `TransactionContext.agents` during the atomic settlement call.
*   **Risk**: Modifying context state inside a handler is anti-pattern and assumes single-threaded execution.
*   **Resolution Plan**: Update `SettlementSystem` to accept a `allow_inactive=True` flag or checking the `inactive_agents` registry fallback natively.
```

### ✅ Verdict
**REQUEST CHANGES**

Please replace the hardcoded IDs (`1`, `999999`) with named constants. The logic changes are solid and the tests are aligned.