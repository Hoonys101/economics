# API 계약 (API Contract)

**작성일**: 2025-12-29
**분석 대상 코드**: `app.py`, `static/js/modules/api.js`

## 1. Simulation Control

### `GET /api/simulation/update`
- **설명**: 시뮬레이션의 현재 상태(Tick 진행 없이)를 조회합니다.
- **용도**: 초기 로딩, 폴링(Polling).
- **응답 (JSON)**:
    ```json
    {
      "status": "paused",
      "tick": 100,
      "gdp": 12345.6,
      "population": 20,
      "trade_volume": 500,
      "chart_update": { ... },
      "market_update": { ... }
    }
    ```

### `POST /api/simulation/tick`
- **설명**: 시뮬레이션을 1 틱 진행시키고 결과를 반환합니다.
- **헤더**: `Authorization: Bearer <TOKEN>`
- **응답 (JSON)**: `GET /api/simulation/update`와 동일한 구조 (상태는 `running`).

### `POST /api/simulation/start`
- **설명**: 시뮬레이션 시작 요청 (로깅 용도).

### `POST /api/simulation/stop`
- **설명**: 시뮬레이션 중단 및 인스턴스 해제.

### `POST /api/simulation/reset`
- **설명**: 시뮬레이션을 초기화(0 틱)하고 재시작합니다.

## 2. Configuration

### `GET /api/config`
- **설명**: 현재 시뮬레이션 설정(`config.py`) 값을 조회합니다.

### `POST /api/config`
- **설명**: 설정을 변경하고 시뮬레이션을 재설정합니다.
- **본문**: `{ "NUM_HOUSEHOLDS": 50, ... }`

## 3. Data Access

### `GET /api/economic_indicators`
- **파라미터**: `start_tick`, `end_tick`
- **설명**: 기간별 경제 지표 이력을 조회합니다.

### `GET /api/market/transactions`
- **파라미터**: `since` (tick)
- **설명**: 특정 틱 이후의 거래 내역을 조회합니다.
