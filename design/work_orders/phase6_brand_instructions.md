# Work Order: Phase 6 - The Brand Economy Implementation

**To**: Jules (Implementation Specialist)
**From**: Antigravity (Chief Architect)
**Reference**: [W-1 Spec: Brand Economy](../specs/phase6_brand_economy_spec.md)

## Context
We are upgrading the simulation from a pure Price/Quantity model to a **Brand/Quality** model. Consumers will now select products based on a Utility Score that includes Price, Perceived Quality, Brand Awareness, and Loyalty.

## Mission
Implement the "Brand Economy" mechanics as defined in the referenced W-1 Specification.

## Step-by-Step Instructions

### 1. Core Logic & Config
- [ ] **`config.py`**: Add the constants from Section 2.1 of the Spec (MARKETING_DECAY_RATE, etc.).
- [ ] **`simulation/brands/brand_manager.py`**: Create this new class. Implement `update()` with Adstock and S-Curve logic.
- [ ] **Test**: Create `tests/test_brand_manager.py` and verify that adstock decays and awareness is sigmoid.

### 2. Agent Updates
- [ ] **`Firm` (`simulation/firms.py`)**:
    - Instantiate `self.brand_manager`.
    - Add `marketing_budget` to `decision_engine` output handling (requires Action Space update later, for now just a placeholder or random/rule-based).
    - In `produce()`, ensure `quality` is defined (use `productivity_factor / 10.0` as V1).
- [ ] **`Household` (`simulation/core_agents.py`)**:
    - Add `self.brand_loyalty: Dict[int, float]` (Default 1.0).
    - Add `self.quality_preference: float` (0.0~1.0, derived from Personality).

### 3. Market Logic (The Big Change)
- [ ] **`Order` (`simulation/models.py`)**: Add `target_agent_id: Optional[int]`.
- [ ] **`OrderBookMarket` (`simulation/markets/order_book_market.py`)**:
    - Modify `match_orders` to PRIORITIZE `BuyOrder` with `target_agent_id`.
    - If `target_agent_id` matches a `SellOrder.agent_id`, execute immediately.
    - Only then run the normal matching for generic orders.
- [ ] **`Household.make_decision`**:
    - Instead of just `buy(best_price)`, implement `choose_best_seller()` using the **Utility Function** in the Spec.
    - Generate specific `BuyOrder(target_agent_id=winner_id)`.

### 4. AI Reward Integration
- [ ] **`AIDrivenFirmDecisionEngine`**:
    - Modify `calculate_reward`.
    - Add `(delta_brand_awareness * VALUATION_MULTIPLIER)` to the reward.
    - This ensures AI learns to spend money on marketing.

## Constraints
- **Do NOT break verification**: `scripts/verify_phase4.py` must still pass (backward compatibility).
- **Type Hinting**: Maintain strict Python type hints.

## Deliverable
- A working `verify_brand_economy.py` script (I will trust you to create this) showing:
    1.  Firms spending on Marketing.
    2.  Brand Awareness Rising.
    3.  Households buying from Higher Priced but High Brand firms (Deviation from cheapest price).
