# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR implements **Reporting DTO Penny-Hardening** by migrating key financial metrics and configuration thresholds from `float` (dollars) to `int` (pennies). This eliminates floating-point drift in aggregate statistics (GDP, Total Consumption) and enforces the "Penny Standard" across the reporting layer, ensuring strict zero-sum alignment with the core ledger.

## 🚨 Critical Issues
*   None identified.

## ⚠️ Logic & Spec Gaps
*   None identified. The changes adhere strictly to the [FINANCIAL_INTEGRITY.md](../design/1_governance/architecture/standards/FINANCIAL_INTEGRITY.md) standard.

## 💡 Suggestions
*   **Future Refactoring**: The `is_food` logic in `Household.add_consumption_expenditure` relies on string matching ("food" in `item_id`) or a dictionary lookup. Consider moving this classification logic to a dedicated `GoodsClassifier` service to avoid scattering string literals across agents.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**:
    > The migration of Reporting DTOs from `float` (dollars) to `int` (pennies) eliminates floating-point precision errors in financial reporting. ... A new `IConsumptionTracker` protocol ... decouples the "act of consuming" (quantity reduction) from the "act of spending" (value transfer).
*   **Reviewer Evaluation**:
    The insight accurately captures the architectural shift. Decoupling *expenditure tracking* (financial event) from *consumption* (biological event) is a crucial distinction that prevents "Ghost GDP" (where consumption happens without spending, or vice versa, distorting metrics). The note on "Protocol Purity" is also well-founded, as it reduces dependency on concrete `Household` classes in transaction handlers.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/2_operations/ledgers/ECONOMIC_INSIGHTS.md`

```markdown
### [2026-02-19] Reporting DTO Penny-Hardening
*   **Context**: Floating-point aggregation of individual agent expenditures resulted in minor deviations from the System Ledger's totals (GDP drift).
*   **Change**: Converted `EconomicIndicatorData` and `HouseholdConfigDTO` thresholds to integer pennies.
*   **Pattern Introduced**: `IConsumptionTracker` and `IIncomeTracker` protocols. Transaction Handlers now "fire-and-forget" statistical updates to agents via these protocols, ensuring that *spending* is recorded exactly when *settlement* occurs.
*   **Impact**: 'Total Consumption' metric is now mathematically guaranteed to equal the sum of 'Settled Transactions', enforcing Zero-Sum integrity in the dashboard.
```

## ✅ Verdict
**APPROVE**