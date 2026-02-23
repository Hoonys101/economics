# 🐙 Gemini CLI Code Review Report

## 🔍 Summary
This PR implements the **Wave 5 Government AI (Populist)**, introducing a 6-tuple state space (adding Approval & Lobbying), a weighted reward function, and versioned Q-Table persistence. The code is well-structured with clear DTOs (`AIConfigDTO`, `GovernmentStateDTO`). However, a **critical logic flaw** in the learning loop sequence will prevent the AI from learning causal relationships.

## 🚨 Critical Issues
*   **None**. No security credentials or hardcoded paths to external systems were found.

## ⚠️ Logic & Spec Gaps
### 1. The "Self-Looping" Learning Bug
*   **Location**: `simulation/policies/smart_leviathan_policy.py` lines ~43-178 (in `decide` method).
*   **Problem**: You call `self.ai.decide_policy(...)` **before** `self.ai.update_learning(...)`.
    *   `decide_policy()` calculates the *current* state ($S_t$) and immediately updates `self.last_state = S_t`.
    *   Subsequent `update_learning()` uses `self.last_state` (which is now $S_t$) and `current_state` (also $S_t$).
    *   **Result**: The AI learns the transition $Q(S_t, A_t) \rightarrow S_t$, effectively learning that "doing nothing changes nothing" (Identity Mapping), rather than learning the actual consequence of the *previous* action ($S_{t-1} \rightarrow S_t$).
*   **Fix**: The `update_learning` step must consume the `last_state` *before* `decide_policy` overwrites it.

## 💡 Suggestions
### 1. Fix Learning Order
In `simulation/policies/smart_leviathan_policy.py`, move the learning step to the beginning of the `decide` method:

```python
# PROPOSED CHANGE in SmartLeviathanPolicy.decide()

# 1. Learn from the PAST (Reward for action at T-interval)
# This must happen BEFORE deciding the new action overwrites self.last_state
self.ai.update_learning(current_tick, state_dto)

# 2. Observe and Decide (Brain)
# This sets self.last_state = current_state
action = self.ai.decide_policy(current_tick, state_dto)
self.last_action_tick = current_tick

# ... (Rest of Execution Logic) ...

# Remove the update_learning call from the end of the function.
```

### 2. Verify Total Debt Units
*   In `GovernmentAI._get_state`: `total_debt_dollars = state_dto.total_debt / 100.0`.
*   Ensure `state_dto.total_debt` is indeed populated in pennies. In `SmartLeviathanPolicy`, the fallback logic `total_debt = max(0, -total_wealth)` uses `total_wealth`. If `total_wealth` is in pennies, this is correct. Just a reminder to double-check that `total_wealth` hasn't been migrated to dollars in some parts of the system (Legacy vs New).

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: Defined Q-Table versioning, the Reflex vs. Populism conflict, and the need for rolling polling averages.
*   **Reviewer Evaluation**: **High Quality**. The insight correctly identifies the risk of breaking V4 simulations and the philosophical conflict in the `REFLEX_OVERRIDE`. The solution to downgrade the override to a "Constitutional Constraint" is architecturally sound. The "Reward Signal Continuity" point is crucial for reinforcement learning stability.

## 📚 Manual Update Proposal (Draft)
*No manual ledger updates required for this PR, as the insights are well-captured in the mission file.*

## ✅ Verdict
**REQUEST CHANGES**

The **Logic Gap** regarding the order of `decide_policy` and `update_learning` invalidates the reinforcement learning process. This must be fixed to ensure the AI learns from historical cause-and-effect rather than immediate state snapshots.

**Action Required**:
1.  In `SmartLeviathanPolicy.decide`, move `self.ai.update_learning(...)` to be called **before** `self.ai.decide_policy(...)`.
2.  Verify tests still pass (or update `test_learning_flow` if it relied on the specific call order).