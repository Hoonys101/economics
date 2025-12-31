# [Phase 3] Dashboard Full-Stack Refinement - Work Order

**목표**: 백엔드 데이터 가공과 프론트엔드 시각화를 병행하여 Phase 5 실험 데이터를 대시보드에 통합.

## 1. API Contract (JSON 규격 확정)
Jules는 아래 구조를 준수하여 데이터를 생성하고, 프론트엔드는 이를 바탕으로 렌더링을 수행한다.

```json
{
  "society_tab": {
    "population": 1000,
    "avg_age": 45.2,
    "time_allocation": {
      "work": ..., "parenting": ..., "self_dev": ..., "entertainment": ..., "idle": ...
    },
    "avg_leisure_hours": 14.5
  },
  "government_tab": {
    "budget_balance": -500.0,
    "current_avg_tax_rate": 0.35,
    "tax_revenue_breakdown": {
      "income_tax": ..., "corporate_tax": ..., "wealth_tax": ..., "consumption_tax": ...
    },
    "welfare_spending": 3000.0
  }
}
```

## 2. Backend Tasks (Aggregator)
- **DTO (dtos.py)**: 위 JSON 구조에 맞춰 `SocietyTabDataDTO`, `GovernmentTabDataDTO` 필드 추가.
- **Logic (snapshot_viewmodel.py)**:
    - 가계 에이전트들의 `leisure_type`별 시간 합계를 집계(GROUP BY).
    - 정부 에이전트의 세금 기록을 세목별로 합산.
    - **Caching**: HUD는 매 틱, 탭별 상세 데이터는 5틱 주기로 갱신.

## 3. Frontend Tasks (Visualization)
- **HUD**: 최상단 헤더에 `Avg Leisure` 및 `Tax Rate` 뱃지 위젯 추가.
- **Society Tab**: Recharts `PieChart`를 사용하여 **Time Allocation Breakdown** 구현.
- **Government Tab**: Recharts `StackedBarChart`를 사용하여 **Tax Revenue Composition** 구현.

## 4. Verification
- `/api/simulation/dashboard` 응답 JSON이 확정된 Contract와 일치하는지 확인.
- 대시보드 화면에서 차트가 실시간으로(캐싱 주기 맞춰) 업데이트되는지 확인.
