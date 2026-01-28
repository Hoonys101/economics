# WO-098-DIAG-B: Market ID Consistency Audit

**Objective**: Verify if buy and sell orders for labor and food are targeting the same market IDs.

**Hypothesis**: 
Firms might be sending orders to `"labor_market"` while households send to `"labor"`, or they target `"goods_market"` instead of `"basic_food"`, causing matching failures.

**Tasks**:
1. **Audit**: Search all `Order(...)` calls in `simulation/decisions/` (Firm and Household engines).
2. **Log Analysis**: Check a sample simulation log to see if orders for the same item are appearing in different `market_id` buckets.
3. **Report**: List all mismatched IDs.
