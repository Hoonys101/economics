# 📜 Work Order: (Implementation of Shareholder & Dividend)

**수신**: Manager AI (Jules)
**참조**: All Modules
**목표**: "기업 이익의 가계 환류(Reflux) 시스템 구현 및 노동 vs 자본 소득 실험"

## 1. 배경 및 목적
- **현재 문제**: 기업이 수익을 창출해도 가계로 환류되지 않고 내부에 고여 '돈맥경화(Distribution Trap)'를 유발함.
- **해결 방안**:
 1. **소유권 확립**: 창업한 가계에게 기업의 소유권(지분)을 부여.
 2. **이익 환원**: 기업의 잉여 현금을 배당금(Dividend) 형태로 가계에 지급.
 3. **데이터 분리**: 가계의 소득을 **노동(Labor)**과 **자본(Capital)**으로 구분 집계.

## 2. 구현 명세 (Technical Specifications)

### A. 데이터 구조 변경 (Data Structure)
1. **Firm** (`simulation/firms.py`)
 - 속성 추가: `self.owner_id` (Type: `int | None`)
 - 초기화(`__init__`) 시 창업자의 ID를 받아 저장. (기본값 None)
2. **Household** (`simulation/core_agents.py`)
 - 속성 추가: `self.portfolio` (Type: `List[int]`)
 - 자신이 소유한 기업들의 ID 목록 관리.

### B. 로직 변경: 창업 (Startup Logic)
- **위치**: `simulation/engine.py` 또는 `ActionProposalEngine` 내 창업 로직
- **Action**:
 1. 가계 현금 차감 (투자금).
 2. 기업 생성 시 `owner_id`에 해당 가계 ID 할당.
 3. 기업 생성 직후, 해당 가계의 `portfolio` 리스트에 기업 ID 추가.
 4. **Log**: `STARTUP | Household {hid} created Firm {fid} (100% Equity)`

### C. 로직 변경: 배당 지급 (Dividend Mechanism)
- **위치**: `simulation/firms.py` 내 신규 메서드 `distribute_profit(self)`
- **실행 시점**: 매 틱(Tick) `update_needs` 또는 회계 정산 직후.
- **지급 조건 (Mandatory Dividend Rule)**:
 - 기업은 **운전 자본(Operating Capital)**으로 '6개월(약 20틱) 치 유지비+임금'을 보유해야 한다. (Reserve Buffer)
 - `Required_Reserves = (self.maintenance_fee + self.avg_wage_paid * count_employees) * 20`
 - `Distributable_Cash = self.assets - Required_Reserves`
- **행동**:
 - 만약 `Distributable_Cash > 0` 이고 `self.owner_id`가 존재하면:
 - 전액을 `owner_id` 가계로 이체 (`firm.assets -= amount`, `household.cash += amount`).
 - **Log**: `DIVIDEND | Firm {fid} -> Household {hid} : ${amount:.2f}`

## 3. 검증 및 데이터 수집 (Verification)
- **Income Tracking**:
 - `Household` 클래스에 `income_labor_cumulative`와 `income_capital_cumulative`를 추가하여 누적 집계.
 - 리포트 생성 시 이 두 지표의 추이를 비교.

## 4. 예상 시나리오 (Hypothesis)
- **초기**: 노동 소득 우세.
- **중기**: 살아남은 기업들이 배당을 시작하며 '자본 소득' 그래프가 상승.
## 5. Q&A 및 기술적 명확화 (Technical Clarifications)
- **Q1: Stock Market 연동 (Compatibility)**
 - `owner_id`는 이번 단계(Private Firm)의 핵심 주권입니다.
 - 단, 기존 `StockMarket` 시스템과의 정합성을 위해, 창업 시 `STOCK_MARKET_ENABLED` 여부와 무관하게 **해당 가계에게 지분 100%를 발행(`shares_owned`)** 하여 포트폴리오를 동기화하십시오. (추후 IPO 대비)
 - 배당 지급 시에는 `owner_id`가 존재하면 주주 명부 조회 없이 즉시 지급하는 `Fast-Track`을 사용해도 좋습니다.

- **Q2: 실행 시점 및 메서드**
 - 신규 메서드 `distribute_profit()`을 구현하십시오.
 - 호출 위치: `simulation/engine.py`의 `run_tick` 루프 내, **모든 기업의 `update_needs()`가 끝난 직후** 일괄 호출합니다.

- **Q3: 평균 임금 계산**
 - 별도 속성(`avg_wage_paid`)을 영구 저장할 필요 없습니다.
 - 메서드 내부에서 `current_avg_wage = sum(self.employee_wages.values()) / len(self.employees)`로 동적 계산하여 사용하십시오.

- **Q4: 누적 소득 데이터**
 - DB 스키마 변경 없이, `Household` 객체의 인스턴스 변수(`self.income_labor_cumulative` 등)로 메모리 상에서 관리하십시오.
 - 리포트 생성(`RECON_REPORT` 등) 시 이 값을 참조합니다.

## 6. Future Integration Requirement (Safety Lock)
본 작업은 "Phase 14-3: Stock Market"으로 가는 **초석**입니다. 따라서 다음 확장을 고려하여 구현하십시오.

1. **확장성 고려**: `Household.portfolio` 구조는 단순 `list[int]`로 시작하되, 향후 `shares_owned` 수량이나 `purchase_price` 등을 담을 수 있는 객체 구조(`PortfolioItem` 등)로 확장하기 용이해야 합니다. (이번 단계에서는 ID 리스트로 충분함)
2. **주식 객체화**: 주식은 단순한 ID 매핑을 넘어, 추후 `Current_Price`, `Dividends_Yield` 등의 속성을 가질 수 있는 독립체임을 염두에 두십시오.
3. **코드 스멜 방지**: `owner_id` 로직이 곳곳에 하드코딩되는 것을 피하고, `firm.get_owners()`와 같은 인터페이스를 통해 접근하도록 하여 추후 다수 주주 시스템으로 전환 시 수정 범위를 최소화하십시오.

## 7. Data Schema Update (Required for Visualization)
테스트 검증을 위해 **Macro Level**에서의 소득 집계가 필요합니다. `economic_indicators` 테이블에 다음 컬럼을 추가하고 데이터를 저장하십시오.

1. **Schema Change (`simulation/db/schema.py`)**:
 - `economic_indicators` 테이블에 `total_labor_income` (REAL), `total_capital_income` (REAL) 컬럼 추가.
2. **DTO Update (`simulation/dtos.py`)**:
 - `EconomicIndicatorData` 클래스에 위 두 필드 추가.
3. **Simulation Engine Update**:
 - 매 틱 통계 집계 시(`calculate_aggregate_stats`), 전체 가계의 `labor_income_this_tick`과 `capital_income_this_tick` 합계를 구하여 저장.
