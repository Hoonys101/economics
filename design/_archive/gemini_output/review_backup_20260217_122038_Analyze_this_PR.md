# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR refactors the `HousingTransactionHandler` to use a **Saga pattern** for atomic settlement and introduces the `HousingTransactionContextDTO` to decouple logic from the monolithic simulation state. It also formalizes `Firm` inventory management using a facade pattern over `InventoryComponent` and explicitly defines the `IHousingTransactionParticipant` protocol.

## 🚨 Critical Issues
*   None found.

## ⚠️ Logic & Spec Gaps
*   **Direct State Mutation**: The handler directly modifies `buyer.residing_property_id` and `unit.owner_id`. While this is standard for current TransactionHandlers, it technically violates the "Stateless Engine" purity goal. Ensure `HousingTransactionContextDTO` holds references to mutable entities explicitly to signal this side-effect capability.

## 💡 Suggestions
*   **Config Proxy**: `mortgage_rate = getattr(context.config_module, ...)` is safe but repetitive. Consider wrapping `config_module` in a typed helper (e.g., `MarketConfigAdapter`) to provide auto-completion and type safety for these lookups.
*   **Transaction Queue Visibility**: The `context.transaction_queue.append(...)` pattern relies on the caller passing a mutable list. Ensure this list is processed by the main `TransactionProcessor` in the same tick to effectuate the side-effects (Credit Creation/Destruction).

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: `Protocol Drift in Housing Market` and `Firm Inventory Logic Separation` identified in `communications/insights/liquidate-regressions.md`.
*   **Reviewer Evaluation**: The insight correctly identifies the risk of "God Classes" (`Firm`) and "Implicit Protocols" (`hasattr` checks). The move to explicit `InventoryComponent` and `IHousingTransactionParticipant` is a high-value architectural improvement that reduces coupling and runtime errors.

## 📚 Manual Update Proposal (Draft)

**Target File**: `design/2_operations/ledgers/TECH_DEBT_HISTORY.md` (or equivalent archive)

```markdown
### ID: TD-ARCH-HOUSING-PROTOCOL
### Title: Housing Protocol & Inventory Facade Standardization
- **Date**: 2026-02-17
- **Symptom**: Housing handlers relied on implicit `hasattr` checks for wages/assets, and `Firm` class was a monolith managing raw inventory dicts.
- **Resolution**: Introduced `IHousingTransactionParticipant` protocol and `HousingTransactionContextDTO`. Refactored Firm to use `InventoryComponent` with strict slot management (MAIN/INPUT).
- **Commit**: (Current PR)
```

## ✅ Verdict
**APPROVE**