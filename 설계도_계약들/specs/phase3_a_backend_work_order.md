# [Phase 3-A] Backend Data Aggregation - Work Order

**목표**: Phase 5 실험 데이터를 대시보드 API(`DashboardSnapshotDTO`)에 포함시키기 위한 백엔드 가공 로직 구현.

## 1. DTO 확장 (simulation/dtos.py)
아래 필드들을 기존 DTO에 추가하십시오. (Type Hint 및 기본값 준수)

- `DashboardGlobalIndicatorsDTO`: 
    - `avg_tax_rate: float`
    - `avg_leisure_hours: float`
    - `parenting_rate: float`
- `SocietyTabDataDTO`:
    - `time_allocation: Dict[str, float]`  # {"work": ..., "parenting": ...}
    - `avg_leisure_hours: float`
- `GovernmentTabDataDTO`:
    - `tax_revenue_breakdown: Dict[str, float]`
    - `welfare_spending: float`
    - `current_avg_tax_rate: float`

## 2. 집계 로직 고도화 (simulation/viewmodels/snapshot_viewmodel.py)
`SnapshotViewModel` 내의 각 비공개 메서드를 수정하여 데이터를 집계하십시오.

- **Time Allocation**: 에이전트들의 `leisure_type`과 `time_worked`를 전역적으로 집계하십시오. (`work`, `parenting`, `self_dev`, `entertainment`, `idle`)
- **Avg Tax Rate**: `total_income_tax_collected / max(1, total_household_income)` (또는 정부가 기록한 실효세율 데이터 활용).
- **Parenting Rate**: `(Parenting Hours / Total Leisure Hours) * 100`.
- **Caching**: 
    - HUD(`_get_global_indicators`)는 매 틱 계산.
    - Tab 데이터(`_get_society_data`, `_get_government_data`)는 5~10틱 주기로 캐싱.

## 3. 검증 (Verification)
- `tests/test_dashboard_api.py`를 실행하거나, 시뮬레이션 가동 후 `GET /api/simulation/dashboard` 응답 JSON에 위 필드들이 유효한 숫자로 채워져 있는지 확인하십시오.
