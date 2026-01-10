# Work Order: WO-039 - Visual Analytics (The Pulse)

## Phase: 20.5 Step 3 (Parallel Track B)

## Objective
시뮬레이션의 주요 거시 지표를 시계열 차트(Time Series Chart)로 시각화합니다.

---

## Implementation Specs

### 1. Data Persistence
- `st.session_state['history']` 리스트 생성.
- 매 틱마다 `connector.get_metrics()` 반환값을 append.
- 구조: `[{tick: 0, gdp: 100, ...}, {tick: 1, gdp: 102, ...}, ...]`

### 2. Visualization Tool
- **Primary**: `st.line_chart` (간편함)
- **Alternative**: `Altair` (커스텀 필요 시)

### 3. Key Charts
| Category | Metrics |
|---|---|
| **Demographics** | `total_population`, `tfr` (합계출산율 - 추후 tracker 추가 필요) |
| **Economics** | `average_assets`, `gini_coefficient` (tracker에서 제공 시) |
| **Real Estate** | `avg_rent`, `homeownership_rate` (connector 확장 필요) |

### 4. Auto-Refresh
- 틱 진행 시 `st.session_state['history']`에 데이터 append 후 차트 자동 갱신.
- `st.rerun()` 호출로 전체 UI 갱신.

---

## Files to Modify
1. **`dashboard/app.py`**: Add history tracking and chart rendering.
2. **`simulation/interface/dashboard_connector.py`**: Extend `get_metrics()` if additional data needed.

---

## Verification
- Run 50 ticks via dashboard.
- Confirm charts show continuous time series without gaps.
- Screenshot or log chart output.

## Deliverable
- PR to main with working time-series charts.
