# API Contract & Data Specification

이 문서는 프론트엔드(`index.html`)가 소비하는 데이터 구조를 명시하여, 백엔드(`app.py`)가 반환해야 할 데이터의 구조를 강제하는 계약(Contract)입니다.

## 1. Simulation Update (`/api/simulation/update`)

대시보드의 상태를 갱신하기 위해 주기적으로 호출되는 메인 엔드포인트입니다.

- **Method**: `GET`
- **Params**: `since` (int, optional) - 클라이언트가 마지막으로 수신한 Tick

### Response Schema

```json
{
  "status": "running" | "paused",  // 시뮬레이션 실행 상태
  "tick": number,                  // 현재 시뮬레이션 Tick
  "gdp": number,                   // GDP (총 소비량)
  "population": number,            // 총 인구 수
  "unemployment_rate": number,     // 실업률 (%)
  "trade_volume": number,          // 총 거래량 (Food Trade Volume)
  "top_selling_good": string,      // (현재 미구현 "N/A")
  "average_household_wealth": number, // 평균 가계 자산
  "average_firm_wealth": number,      // 평균 기업 자산
  "household_avg_needs": number,      // 가계 평균 욕구 충족도 (현재 0)
  "firm_avg_needs": number,           // 기업 평균 욕구 충족도 (현재 0)
  "chart_update": {
    "new_gdp_history": number[],      // GDP 차트 업데이트를 위한 새로운 데이터 포인트 배열
    "wealth_distribution": [],        // (미사용)
    "household_needs_distribution": {} // (미사용)
  },
  "market_update": {
    "open_orders": [],  // (미사용)
    "transactions": []  // (미사용, 별도 API로 분리됨)
  }
}
```

### Frontend Consumption (`index.html`)

- `data.status` -> `#simStatus`
- `data.tick` -> `#simTick`
- `data.gdp` -> `#simGdp`
- `data.population` -> `#simPopulation`
- `data.trade_volume` -> `#simTradeVolume`
- `data.average_household_wealth` -> `#simAvgHouseholdWealth`
- `data.average_firm_wealth` -> `#simAvgFirmWealth`
- `data.household_avg_needs` -> `#simHouseholdNeeds`
- `data.firm_avg_needs` -> `#simFirmNeeds`
- `data.top_selling_good` -> `#simTopGood`
- `data.unemployment_rate` -> `#simUnemployment` (formatted as %)
- `data.chart_update.new_gdp_history` -> `gdpChart` (Chart.js)

---

## 2. Market Transactions (`/api/market/transactions`)

실시간 거래 내역 리스트를 갱신하기 위한 엔드포인트입니다.

- **Method**: `GET`
- **Params**: `since` (int, optional) - 마지막으로 수신한 Transaction의 TimeStamp(Tick)

### Response Schema (Array of Objects)

```json
[
  {
    "run_id": number,
    "time": number,          // 거래 발생 Tick
    "buyer_id": number,      // 구매자 ID
    "seller_id": number,     // 판매자 ID
    "item_id": string,       // 품목 ID ('labor', 'basic_food', etc.)
    "quantity": number,      // 거래 수량
    "price": number,         // 거래 단가
    "market_id": string,     // 시장 ID
    "transaction_type": string // 'goods' | 'labor' | 'research_labor'
  }
]
```

### Frontend Consumption (`index.html`)

- **List Rendering**: 응답 배열을 순회하며 리스트 아이템 생성
- **Icon/Color Logic**:
    - `item_id === 'labor'` ? '💼' (#1E86FF) : '📦' (#00C9A7)
- **Text Display**:
    - Name: `Labor Contract` or `Trade: {item_id}`
    - Description: `Buyer: {buyer_id}, Seller: {seller_id}, Qty: {quantity}, Price: {price}`
    - Tick: `Tick {time}`

---

## 3. Configuration (`/api/config`)

시뮬레이션 초기 설정 값을 조회하거나 업데이트합니다.

- **Method**: `GET` | `POST`

### Response Schema (GET)

`config.py`의 모든 대문자 변수(상수)를 Key-Value 형태로 반환.

```json
{
  "NUM_HOUSEHOLDS": number,
  "NUM_FIRMS": number,
  "SIMULATION_TICKS": number,
  "INITIAL_HOUSEHOLD_ASSETS_MEAN": number,
  "INITIAL_FIRM_CAPITAL_MEAN": number,
  ...
}
```

### Frontend Consumption (`index.html` - Settings Modal)

- `NUM_HOUSEHOLDS` -> `#NUM_HOUSEHOLDS` input
- `NUM_FIRMS` -> `#NUM_FIRMS` input
- `SIMULATION_TICKS` -> `#SIMULATION_TICKS` input
- `INITIAL_HOUSEHOLD_ASSETS_MEAN` -> `#INITIAL_HOUSEHOLD_ASSETS_MEAN` input
- `INITIAL_FIRM_CAPITAL_MEAN` -> `#INITIAL_FIRM_CAPITAL_MEAN` input

---

## 4. Control Endpoints

시뮬레이션 제어 명령을 전송합니다.

- **Endpoints**:
    - `/api/simulation/start`
    - `/api/simulation/pause`
    - `/api/simulation/stop`
    - `/api/simulation/reset`
    - `/api/simulation/shutdown`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <SECRET_TOKEN>`

### Response Schema

```json
{
  "status": "success" | "error" | "already_running",
  "message": string
}
```
