# 경제 시뮬레이션 UI 설계 (v2)

## 1. 개요 (Overview)
이 문서는 경제 시뮬레이션의 상태를 시각적으로 모니터링하고, **시뮬레이션 설정을 변경**하며, 상세한 지표를 분석하기 위한 웹 기반 UI의 설계를 정의합니다.

## 2. 목표 (Goals)
- **시뮬레이션 설정**: 시뮬레이션 시작 전, `config.py`의 주요 파라미터(초기 인구, 기업 수 등)를 UI에서 직접 수정하고 적용합니다.
- **시뮬레이션 제어**: 시작, 일시정지, 재설정 기능을 제공합니다.
- **상세 실시간 모니터링**: GDP, 실업률 외에 **거래량, 주요 판매 상품, 가계/기업의 평균 욕구 수준** 등 다양한 지표를 실시간으로 표시합니다.
- **다차원 데이터 시각화**: **가계 자산 분포, 가계/기업 욕구 분포** 등 분포도를 포함한 다채로운 그래프를 제공합니다.
- **이벤트 로깅**: 시뮬레이션의 주요 이벤트나 디버그 메시지를 확인합니다.

## 3. 기술 스택 (Tech Stack)
- **백엔드**: Flask
- **프론트엔드**: HTML, CSS, JavaScript, **Bootstrap (Modal, Forms 사용)**, Chart.js

## 4. 화면 구성 (Screen Layout)
- **Header**: 제목, `[설정 변경]` 버튼
- **Settings Modal**: 설정 변경 폼
- **Control Panel**: 제어 버튼
- **Main Dashboard**: 핵심 지표 카드
- **Charts Area**: 각종 차트
- **Market Activity Log (신규)**:
  - **미체결 주문 (Open Orders)**: 현재 시장에 등록된 판매/구매 주문 목록을 실시간으로 표시하는 테이블 (Tick, Agent, Type, Item, Qty, Price)
  - **체결된 거래 (Completed Transactions)**: 최근 성사된 거래 내역을 표시하는 테이블 (Tick, Buyer, Seller, Item, Qty, Price)
- **Log Viewer**: 기존 로그 뷰어

## 5. API 엔드포인트 설계 (API Endpoint Design - 확장)
| 경로 (Path) | HTTP 메소드 | 설명 | 요청 바디 | 응답 (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| `/api/config` | `GET` | 현재 시뮬레이션 설정을 가져옵니다. | 없음 | `{ "initial_households": 100, "initial_firms": 10, ... }` |
| `/api/config` | `POST` | 시뮬레이션 설정을 업데이트합니다. | `{ "initial_households": 150, ... }` | `{ "status": "success" }` |
| `/api/simulation/state` | `GET` | 시뮬레이션의 현재 상태와 **상세 지표**를 가져옵니다. | 없음 | `{ "status": "running", "tick": 102, "gdp": 15000, "trade_volume": 500, "top_selling_good": "Food", ... }` |
| `/api/simulation/chart_data` | `GET` | 시각화에 필요한 **모든 차트 데이터**를 가져옵니다. | 없음 | `{ "gdp_history": [...], "wealth_distribution": [...], "household_needs_distribution": {...}, "firm_needs_distribution": {...}, "sales_by_good": {...} }` |
| `/api/simulation/start` | `POST` | 시뮬레이션을 시작합니다. | 없음 | `{ "status": "success" }` |
| `/api/simulation/pause` | `POST` | 시뮬레이션을 일시정지합니다. | 없음 | `{ "status": "success" }` |
| `/api/simulation/reset` | `POST` | 시뮬레이션을 초기 상태로 재설정합니다. | 없음 | `{ "status": "success" }` |
| `/api/simulation/market_activity` | `GET` | 최근 주문 및 거래 내역을 가져옵니다. | 없음 | `{ "open_orders": [...], "transactions": [...] }` |

## 6. 구현 계획 (Implementation Plan)
1. **`config.py` 분석**: UI로 제어할 설정 변수 확정
2. **`app.py` 확장**: `/api/config` GET/POST 엔드포인트 구현. `/api/simulation/state`, `/api/simulation/chart_data`가 더 많은 데이터를 반환하도록 수정 (임시 데이터 사용)
3. **`templates/index.html` 수정**:
    - Bootstrap Modal을 사용해 설정 UI 추가
    - 대시보드 및 차트 영역에 새로운 지표와 그래프 영역 추가
4. **JavaScript 로직 수정**:
    - 설정 저장 및 불러오기 기능 구현
    - 확장된 데이터에 맞게 대시보드 및 모든 차트를 업데이트하는 로직으로 수정
5. **시뮬레이션 엔진 연동**: 실제 시뮬레이션 데이터를 API에 연결