# WORK ORDER: WO-167 - The Grace Protocol (Bankruptcy Stabilization)

## 1. Context
Current bankruptcy logic is too aggressive, leading to premature liquidation of entities that have non-cash assets. We need to implement a "Grace Protocol" to allow entities to recover via asset liquidation or bridge loans.

## 2. Technical Requirements

### A. FinanceDepartment (`simulation/components/finance_department.py`)
- Add `is_distressed: bool` flag.
- Implement `trigger_emergency_liquidation()`:
    - This method should identify all items in `firm.inventory`.
    - It should generate `Order` objects (sell orders) with a price set to `market_avg_price * 0.8`.
    - These orders should be marked with a priority or immediately sent to the relevant markets.
- In `check_bankruptcy()`, instead of just incrementing `consecutive_loss_turns`, evaluate if the firm is in a "Cash Crunch" (Cash < 0 or Cash < 10% of expected expenses).

### B. AgentLifecycleManager (`simulation/systems/lifecycle_manager.py`)
- Modify `_process_firm_lifecycle`:
    - If a firm has 0 cash but `inventory_value > 0`, do NOT set `is_active = False`.
    - Instead, call `firm.finance.trigger_emergency_liquidation()`.
    - Set a `distress_tick_counter`. Only liquidate if `distress_tick_counter > 5` and cash is still 0.

### C. Household Scaling
- Apply similar logic to `Household` if they are in debt or cannot afford food but have assets (durable goods or stocks to sell).

## 3. Success Criteria
- A firm with 0 cash but high inventory value is not liquidated.
- The firm places sell orders and survived once a sale is made.
- `trace_leak.py` confirms no money is lost during this process.
