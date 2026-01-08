# Work Order: WO-025 Materiality & Durables

**Phase**: 15 (Post-Banking)
**Objective**: Introduce durability, quality, and depreciation to Goods, creating "Business Cycles" and "Quality Competition".

---

## 1. Core Concepts

### A. Materiality (The Object Persistence)
*   **Commodities (Food/Service)**: Consumed instantly. $Utility = Qty \times Quality$.
*   **Durables (Consumer Goods)**: Persistent assets. They provide utility *over time* until they break.
    *   $Utility_{tick} = \sum (ActiveItem.Quality \times UsageRate)$

### B. The Quality Ladder
*   Product Quality is no longer fixed (1.0).
*   **Formula**: $Quality = 1.0 + \ln(\text{Avg Labor Skill}) \times \text{Tech Multiplier}$
*   High-skill firms produce high-quality goods.
*   Wealthy households prefer high-quality goods (Higher Utility/Space).

---

## 2. Implementation Specifications

### A. Configuration (`config.py`)
Update `GOODS` dictionary:
```python
"consumer_goods": {
    "sector": "GOODS",
    "is_durable": True,
    "base_lifespan": 50,  # Ticks (e.g., 2 months)
    "quality_sensitivity": 0.5, # How much skill affects quality
    ...
}
```

### B. Firm Logic (`simulation/firms.py`)
**Method**: `produce()`
1.  Calculate `avg_skill`: Average `labor_skill` of current employees.
2.  Calculate `product_quality`: Use the formula above.
3.  **Inventory Storage**:
    *   *Challenge*: Storing individual items in Firm Inventory is expensive.
    *   *Simplification*: Firms store `(quantity, quality_level)`. Since a firm usually produces consistent quality in a tick, update the firm's "Current Product Quality" attribute.
    *   When selling, stamp the transaction with `quality`.

### C. Household Logic (`simulation/core_agents.py`)
**Attribute**: `self.durable_assets = []` (List of dictionaries: `{'item_id': str, 'quality': float, 'remaining_life': int}`)

**Method**: `consume(item_id, quantity, transaction_quality)`
*   If `is_durable`:
    *   Do NOT destroy.
    *   Add to `self.durable_assets`: `{'item_id': item_id, 'quality': transaction_quality, 'remaining_life': MAX_LIFE}`.
    *   *Saturation Logic*: Implement "Utility Saturation" per `design/specs/utility_maximization_spec.md`.
    *   If Household already has functioning asset, Marginal Utility drops near zero.

**Method**: `update_needs()`
*   Iterate `self.durable_assets`:
    *   `utility = asset['quality']` (1 item = 1 unit of utility * quality).
    *   `self.needs['quality'] -= utility` (Satisfy need).
    *   `asset['remaining_life'] -= 1` (Depreciation).
*   **Cleanup**: Remove items where `remaining_life <= 0`.
    *   *Event*: "Household X's Goods broke!" (Triggers Demand).

### D. Market Logic
*   **Price**: Price should correlate with Quality.
*   *MVP*: Households judge value by `Price / Quality`. High quality justifies higher price.

---

## 3. Verification & Success Criteria

### Script: `scripts/verify_durables.py`
1.  **Run Simulation**: 500 Ticks.
2.  **Observe Demand**:
    *   Tick 0-10: Huge spike (Initial Stocking).
    *   Tick 11-49: Near Zero Demand (Saturation).
    *   Tick 50: Spike (Replacement Cycle).
3.  **Observe Quality**:
    *   Check if Households with high `labor_skill` (High Income) end up owning Higher Quality assets.

---

## 4. Execution Steps

1.  Update `config.py` (Add `is_durable`, `lifespan`).
2.  Update `Firm.produce` (Quality Calculation).
3.  Update `Household.consume` & `Household.update_needs` (Asset Logic).
4.  Run Verification.
