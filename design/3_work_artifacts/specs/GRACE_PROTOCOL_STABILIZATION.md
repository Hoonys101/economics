# SPEC: The Grace Protocol (Bankruptcy Refinement)

## 1. Overview
Current bankruptcy logic in the simulation is too binary: if a firm or household runs out of cash, it is immediately liquidated. This leads to "accidental" bankruptcies where an entity has valuable inventory or capital but lacks the immediate liquidity to pay a small fee or wage.

The Grace Protocol introduces a multi-stage distress management system to ensure that only truly insolvent entities are removed from the simulation.

## 2. Multi-Stage Distress System

### Stage 1: Liquidity Warning (Cash Crunch)
- **Trigger**: `cash < required_minimum_per_tick` (e.g., predicted wages + maintenance).
- **Action**: 
    - Mark entity with `LiquidityWarning`.
    - Halt non-essential spending (e.g., R&D, Marketing).
    - Trigger `Fire Sale` flag for inventory.

### Stage 2: Distress Mitigation (Rescue)
- **Trigger**: `cash < mandatory_payment` (e.g., maintenance fee about to be charged).
- **Sub-Action A: Fire Sale**
    - The entity must place its inventory on the market at a discount (e.g., 20% below current average price) to raise immediate cash.
- **Sub-Action B: Bridge Loan (Phase 32 Prep)**
    - If the entity has assets (capital/inventory) but no cash, it can apply for a short-term, high-interest bridge loan from the bank.

### Stage 3: Orderly Liquidation (Insolvency)
- **Trigger**: Both Sub-Action A and B fail to raise enough cash, and entity cannot meet its most basic survivability costs for $N$ consecutive ticks.
- **Action**: 
    - Deactivate entity.
    - Transfer all remaining assets to `PublicManager` or distributive through `SettlementSystem`.

## 3. Implementation Details

### CorporateManager / FinanceDepartment Updates
- Add `distress_level` (0: Healthy, 1: Warning, 2: Distress).
- In `update_needs` or `check_bankruptcy`, evaluate liquidation conditions.
- Implement `trigger_fire_sale()`: Forcefully place sell orders for all inventory items at `avg_price * 0.8`.

### AgentLifecycleManager Updates
- Modify `_process_firm_lifecycle` to respect the `distress_level`.
- Only deactivate a firm if `distress_level == 2` AND all mitigation fails.

## 4. Verification
- A firm with 1000 meat inventory and 0 cash should NOT be liquidated.
- It should successfully sell meat at a discount, get cash, and survive.

---

# SPEC: Modern Financial Integrity Tests (TD-165)

## 1. Overview
Update the M2 verification logic to account for Fractional Reserve Banking (`Total_Credit`).

## 2. New Integrity Formula
`M2 = M0 + Total_Credit`

Where:
- `M0` (Base Money): Total cash issued by Central Bank - any burned cash.
- `Total_Credit`: Sum of all outstanding loan principals in the `Bank`.
- `M2` (Money Supply): HH Assets + Firm Assets + Bank Deposits + Gov Assets + CB Assets + Public Treasury.

## 3. Test Cases
- `test_credit_expansion_integrity`: Verify that when a loan is granted, `M2` increases by the loan amount, and the formula `M2 = M0 + Total_Credit` holds.
- `test_credit_contraction_integrity`: Verify that when a loan is repaid or defaulted (and credit destroyed), `M2` decreases and the formula still holds.
- `test_zero_sum_transfers`: Verify that tax payments or wage payments do not change `M2`.

