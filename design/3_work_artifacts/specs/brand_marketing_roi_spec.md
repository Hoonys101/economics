# W-1. Spec: Phase 6 - Brand Marketing ROI Optimization

## 1. Goal
기업이 마케팅 예산을 **ROI(투자 대비 수익)**에 기반하여 동적으로 조절하도록 구현합니다.

## 2. Current State Analysis
| 항목 | 현재 상태 | 필요 조치 |
|---|---|---|
| `marketing_budget_rate` | ❌ 없음 (고정 5%) | ✅ 추가 필요 |
| `last_revenue` | ❌ 없음 | ✅ 추가 필요 |
| 마케팅 로직 위치 | `Firm.update_needs` (L589-606) | 로직 수정 필요 |

## 3. Implementation Details

### 3.1 `simulation/firms.py` - Field Additions
```python
# In Firm.__init__ (around line 78)
self.marketing_budget_rate: float = 0.05  # Initial 5%
self.last_revenue: float = 0.0
self.last_marketing_spend: float = 0.0
```

### 3.2 `simulation/firms.py` - Efficiency Logic
Replace fixed 5% logic (L593) with adaptive budgeting:

```python
# In Firm.update_needs, Marketing Section (~L589)
def _adjust_marketing_budget(self):
    """Adjust marketing budget rate based on ROI."""
    delta_spend = self.marketing_budget  # Current tick spend
    if delta_spend <= 0 or self.last_marketing_spend <= 0:
        self.last_revenue = self.revenue_this_turn
        self.last_marketing_spend = self.marketing_budget
        return  # Skip first tick or zero spend
    
    delta_revenue = self.revenue_this_turn - self.last_revenue
    efficiency = delta_revenue / self.last_marketing_spend

    # Decision Rules
    if self.brand_manager.brand_awareness >= 0.9:
        pass  # Maintain (Saturation)
    elif efficiency > 1.5:
        self.marketing_budget_rate = min(0.20, self.marketing_budget_rate * 1.1)
    elif efficiency < 0.8:
        self.marketing_budget_rate = max(0.01, self.marketing_budget_rate * 0.9)

    # Update tracking
    self.last_revenue = self.revenue_this_turn
    self.last_marketing_spend = self.marketing_budget
```

### 3.3 Update Marketing Spend Calculation
```python
# Replace L593: marketing_spend = max(10.0, self.revenue_this_turn * 0.05)
marketing_spend = max(10.0, self.revenue_this_turn * self.marketing_budget_rate)
```

## 4. Config Parameters
```python
# config.py
MARKETING_EFFICIENCY_HIGH_THRESHOLD = 1.5
MARKETING_EFFICIENCY_LOW_THRESHOLD = 0.8
MARKETING_BUDGET_RATE_MIN = 0.01
MARKETING_BUDGET_RATE_MAX = 0.20
BRAND_AWARENESS_SATURATION = 0.9
```

## 5. Verification Plan
**Unit Test**: `tests/test_marketing_roi.py`
1.  `test_budget_increase_on_high_efficiency`: 매출 급증 시 예산 증가.
2.  `test_budget_decrease_on_low_efficiency`: 매출 없이 비용만 쓰면 예산 감소.
3.  `test_budget_stable_on_saturation`: 브랜드 인지도 90% 이상 시 현상 유지.
