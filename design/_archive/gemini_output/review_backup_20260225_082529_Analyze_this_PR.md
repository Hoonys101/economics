# 🐙 Gemini CLI System Prompt: Git Reviewer Report

## 🔍 Summary
This PR successfully introduces the `EstateRegistry` (Graveyard pattern) to cleanly handle agents in the "Limbo" phase (after death/bankruptcy but before final escheatment). This elegant solution removes the fragile "Resurrection Hack" in the `EscheatmentHandler`. Additionally, it updates `WorldState.calculate_total_money` to prevent M2 leaks by including the estate, and fixes `test_m2_integrity.py` assertions to align with the Penny Standard.

## 🚨 Critical Issues
None. No security violations, hardcoded paths, or zero-sum leaks were detected. The transition to `EstateRegistry` actively prevents money leaks during agent death.

## ⚠️ Logic & Spec Gaps
- **Agent Registry Iteration**: `AgentRegistry.get_all_agents()` and `get_all_financial_agents()` do not include agents from the `EstateRegistry`. While this is structurally correct (dead agents shouldn't participate in markets or general logic), developers must be aware that global audits or balance aggregations relying on `get_all_agents()` will miss estate funds. `WorldState.calculate_total_money` was correctly explicitly updated to account for this, which is good.

## 💡 Suggestions
- **Type Coercion in Registry**: In `EstateRegistry.get_agent`, there is logic for string-to-int fallback (`isinstance(agent_id, str) and agent_id.isdigit()`). While this matches legacy `AgentRegistry` behavior, standardizing `AgentID` globally (e.g., strict typing as `int` via the `AgentID` NewType) would remove the need for ad-hoc type casting and improve type safety.

## 🧠 Implementation Insight Evaluation
- **Original Insight**: 
  > **The "Limbo" Problem in Double-Entry Accounting**
  > In a strict zero-sum simulation, an entity cannot simply "cease to exist" if it holds assets or liabilities. Previously, `DeathSystem` deleted agents from the registry immediately upon liquidation. However, asynchronous processes (like `EscheatmentHandler` transferring remaining assets to the government) would fail because the agent no longer existed in the registry, leading to `KeyError` or requiring fragile "Resurrection Hacks" (temporarily re-injecting the agent).
  > **The Solution: Estate Registry**
  > We introduced `simulation/registries/estate_registry.py` and the `IEstateRegistry` protocol. This creates a formal "Graveyard" state. [...]
- **Reviewer Evaluation**: Excellent insight. Identifying the "Limbo" state in double-entry systems is a mature architectural observation. Moving away from the "Resurrection Hack" to a formalized `EstateRegistry` properly respects the agent lifecycle pipeline and Zero-Sum integrity constraints. The accompanying documentation regarding the Penny Standard test regression perfectly captures technical debt resolution.

## 📚 Manual Update Proposal (Draft)
- **Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md` (or `TECH_DEBT_LEDGER.md` if preferred)
- **Draft Content**:
```markdown
### Estate Registry Pattern for Agent Liquidation
- **Phenomenon**: Asynchronous final settlement processes (like Escheatment) were failing with `KeyError`s because liquidated agents were instantly deleted from the `AgentRegistry`. Previous workarounds involved "resurrecting" agents temporarily.
- **Cause**: In a strict Zero-Sum double-entry system, an entity cannot "cease to exist" while it still holds residual assets or liabilities waiting to be cleared.
- **Solution / Architectural Standard**: Introduced `EstateRegistry` (The Graveyard). Agents transition: `Active` -> `Estate` -> `Deleted`. `AgentRegistry.get_agent(id)` implements a transparent Fallback Pattern, checking the `EstateRegistry` if an active agent isn't found. This allows the `SettlementSystem` to resolve accounts for deceased agents without polluting the active simulation pool. **Crucial Rule**: Global monetary audits (like M2 calculation) must explicitly iterate over both the active registry and the `EstateRegistry` to prevent temporary money supply leaks.
```

## ✅ Verdict
**APPROVE**