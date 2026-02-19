# 🐙 Gemini CLI System Prompt: Git Reviewer

## 🔍 Summary
Implemented **Agent Lifecycle Atomicity** by ensuring all market orders are cancelled *before* an agent enters the liquidation phase. This prevents "zombie trading" where a dead agent's orders could still match. Also verified `StockMarket` compliance with `IMarket` and added strict `spec=IMarket` tests.

## 🚨 Critical Issues
*None detected.*

## ⚠️ Logic & Spec Gaps
**1. Loose ID Comparison in `OrderBookMarket`**
*   **Location**: `simulation/markets/order_book_market.py` lines 188+ (`cancel_orders`)
*   **Issue**: The comparison `o.agent_id != agent_id` relies on strict type equality. In Python, `123 != "123"` is `True`, meaning if an integer ID is passed but orders utilize string IDs (or vice versa), the orders will **fail to cancel** (they will be kept).
*   **Contrast**: `StockMarket.cancel_orders` correctly handles this via `str(m.order.agent_id) != str(agent_id)`.
*   **Recommendation**: Adopt the robust string-conversion comparison from `StockMarket` into `OrderBookMarket` to ensure safety against mixed ID types.

## 💡 Suggestions
*   **Standardize Comparison**: Extract the ID matching logic into a helper or ensure `CanonicalOrderDTO` enforces a strict ID type (e.g., always `str`) upon instantiation to avoid this class of bugs entirely.

## 🧠 Implementation Insight Evaluation
*   **Original Insight**: *"`IMarket` has evolved from a purely read-only snapshot interface to include `cancel_orders`... Order cancellation is now the first step in the liquidation process..."*
*   **Reviewer Evaluation**: **High Value**. The insight correctly identifies a shift in the `IMarket` contract. Previously, markets were largely passive recipients of orders. Granting the `DeathSystem` privileged access to `cancel_orders` is a necessary breach of the "Markets are black boxes" abstraction to ensure system integrity. This justifies the protocol change.

## 📚 Manual Update Proposal (Draft)
**Target File**: `design/1_governance/architecture/standards/LIFECYCLE_HYGIENE.md`

```markdown
### 3. Lifecycle Atomicity & Cleanup
- **Liquidation Sequence**: When an agent is marked for death/liquidation, the system MUST ensure no further interactions occur with the outside world.
  1.  **Scrub Orders**: Call `market.cancel_orders(agent_id)` on ALL markets. This prevents "Zombie Trades" (matching after death).
  2.  **Liquidate Assets**: Convert inventory/assets to liquid currency.
  3.  **Transfer Balance**: Move funds to the appropriate sink (e.g., Treasury, Inheritor).
  4.  **Deactivate**: Finally, set `is_active = False`.
- **Pre-Liquidation Lock**: Logic relies on step 1 (Scrubbing) finishing completely before step 2 begins.
```

## ✅ Verdict
**APPROVE**

*The logic gap regarding ID types in `OrderBookMarket` should be addressed, but the overall architectural change to `DeathSystem` and `IMarket` is sound and well-tested with `spec` checks.*