# Work Order: Phase 6 - Brand Marketing ROI Optimization

## 🎯 Objective
Implement adaptive marketing budgeting so Firms adjust their marketing spend based on ROI (Return on Investment).

## 📂 Reference
- Spec: `design/specs/brand_marketing_roi_spec.md` (Read this first!)

## 🛠️ Tasks

### Task A: Add Required Fields to Firm
File: `simulation/firms.py`
1.  In `Firm.__init__` (around line 78), add:
    ```python
    self.marketing_budget_rate: float = 0.05  # Initial 5%
    self.last_revenue: float = 0.0
    self.last_marketing_spend: float = 0.0
    ```

### Task B: Add Config Parameters
File: `config.py`
```python
MARKETING_EFFICIENCY_HIGH_THRESHOLD = 1.5
MARKETING_EFFICIENCY_LOW_THRESHOLD = 0.8
MARKETING_BUDGET_RATE_MIN = 0.01
MARKETING_BUDGET_RATE_MAX = 0.20
BRAND_AWARENESS_SATURATION = 0.9
```

### Task C: Implement Adaptive Budgeting Logic
File: `simulation/firms.py` (in `update_needs` method, around L589-606)
1.  Replace fixed 5% logic with dynamic `marketing_budget_rate`.
2.  Add `_adjust_marketing_budget()` method to calculate efficiency and adjust rate.
3.  Call `_adjust_marketing_budget()` AFTER marketing spend is applied.

**Efficiency Formula:**
```python
efficiency = delta_revenue / last_marketing_spend
```

**Decision Rules:**
- `efficiency > 1.5`: Increase rate by 10% (max 20%)
- `efficiency < 0.8`: Decrease rate by 10% (min 1%)
- `brand_awareness >= 0.9`: Maintain (saturation)

### Task D: Unit Tests
Create `tests/test_marketing_roi.py`:
1.  `test_budget_increase_on_high_efficiency`: Revenue up → budget rate up.
2.  `test_budget_decrease_on_low_efficiency`: No revenue + spend → budget rate down.
3.  `test_budget_stable_on_saturation`: High awareness → rate unchanged.

## 🚀 Deliverables
- Modified `simulation/firms.py`
- Modified `config.py`
- New `tests/test_marketing_roi.py`
- Run unit tests and report results.
