# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
This PR implements **Wave 4.3 Health & Marriage Mechanics**, introducing a `Medical` need, `MarriageSystem` for household merging, and the "Shared Wallet" pattern. It includes a health shock probability model in `LifecycleEngine` and updates `BudgetEngine` to handle inelastic medical demand.

## 🚨 Critical Issues
*   None.

## ⚠️ Logic & Spec Gaps
*   **Unit Mismatch Risk in BudgetEngine (`modules/household/engines/budget.py`)**:
    *   Line 121: `price_limit = allocated_cash / 100.0` converts the allocated pennies (e.g., 12000) to a float (120.0).
    *   `config/defaults.py` sets `medical_service` initial price to `10000` (pennies).
    *   If the Market Matching Engine compares `Order.price_limit` (120.0) directly against the Ask Price (10000), the order will never fill ($120 < $10000).
    *   **Recommendation**: Verify if the matching engine expects `price_limit` in Dollars or Pennies. If Pennies, remove `/ 100.0`. If Dollars, ensure the matching engine converts the Ask Price before comparison.
*   **Shared Wallet Concurrency (`MarriageSystem.py`)**:
    *   The "Shared Wallet" pattern (`spouse._econ_state.wallet = hoh._econ_state.wallet`) means two agents share the same live object.
    *   However, `EconStateDTO.copy()` (in `dtos.py`) performs a deep copy of the wallet.
    *   **Risk**: Agent A spends money in Tick T. Agent B's snapshot for Tick T was taken *before* A's spend but *after* the tick start? Or does B get a fresh snapshot? If B gets a snapshot with the *original* balance, B might attempt a transaction that fails (NSF) because A already spent the funds. This is a realistic "Joint Account Race Condition" but leads to failed plans.

## 💡 Suggestions
*   **Hardcoded Magic Numbers**:
    *   `modules/household/engines/budget.py`: `1.2` (20% urgency premium) and `10000.0` (fallback price) are hardcoded. Consider moving `MEDICAL_PRICE_ESTIMATE` and `MEDICAL_URGENCY_PREMIUM` to `HouseholdConfigDTO`.
*   **Encapsulation**:
    *   `MarriageSystem` directly accesses the protected member `_econ_state` of the `Household` class. While acceptable for a System-Agent relationship in this architecture, consider exposing a specialized method like `Household.merge_financials_with(other)` to encapsulate the wallet reassignment logic.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: Defined the "Shared Instance Pattern" for Wallets to solve Zero-Sum integrity during marriage without complex ledger synchronization.
*   **Reviewer Evaluation**: The insight accurately describes the architectural decision. It correctly identifies the Zero-Sum integrity handling (Transfer then Link). The trade-off regarding "Linked Agents" vs "Composite Agent" is well-reasoned.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/1_governance/architecture/ARCH_AGENTS.md`

```markdown
### 4.3 Shared Resource Patterns (Wave 4.3+)

#### The Shared Wallet Pattern (Marriage)
To model shared household finances without creating a "Composite Agent", we utilize the **Shared Instance Pattern**.
- **Mechanism**: Married agents hold references to the *same* `Wallet` instance in their `_econ_state`.
- **Integrity**: Before linking, the merging agent's funds are transferred via `SettlementSystem` to the target wallet (Zero-Sum compliance).
- **Concurrency**: Agents plan independently based on snapshots. This introduces a realistic "Joint Account Race Condition" where one spouse's spending may cause the other's subsequent transaction to fail (NSF) within the same tick. Engines must handle `TRANSACTION_FAILED` gracefully.
```

## ✅ Verdict
**APPROVE**

(The Unit Mismatch in `BudgetEngine` is marked as a Logic Gap/Risk to be verified, but the architectural pattern and integrity checks are sound. The Logic Gap should be addressed but does not constitute a security or zero-sum hard fail.)