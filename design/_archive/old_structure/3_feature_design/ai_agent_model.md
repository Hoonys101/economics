# AI 에이전트 모델 설계 (V2 - Multi-Channel Aggressiveness)

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/ai/firm_ai.py`, `simulation/ai/household_ai.py`, `simulation/ai/api.py`

## 1. 개요

V2 AI 모델은 기존의 계층적(Intention-Tactic) 구조에서 벗어나, **다채널 적극성 벡터(Multi-Channel Aggressiveness Vector)** 방식으로 진화했습니다. 각 에이전트는 자신의 주요 활동 영역(채널)별로 독립적인 '적극성(Aggressiveness)' 수준을 결정하며, 이를 통해 복합적인 의사결정을 수행합니다.

## 2. 핵심 아키텍처

### 2.1. Aggressiveness (적극성)
- AI의 출력은 이산적인 행동(Action)이 아닌, **0.0 ~ 1.0 사이의 연속적인 적극성 값**입니다.
- Q-Learning을 위해 이 값은 `[0.0, 0.25, 0.5, 0.75, 1.0]`의 5단계로 이산화되어 학습됩니다.
- **의미**:
    - `0.0 (Passive)`: 소극적, 보수적, 저가 매수/고가 매도 시도, 현상 유지.
    - `0.5 (Neutral)`: 중립적, 시장 평균 추종.
    - `1.0 (Aggressive)`: 적극적, 공격적, 시장가 매수/매도, 급격한 변화 시도.

### 2.2. 독립 채널 Q-Learning (Independent Channel Q-Learning)
에이전트는 단일 Q-테이블이 아닌, 각 채널별로 **독립적인 Q-테이블**을 가집니다. 이를 통해 각 영역의 특성에 맞는 최적의 전략을 병렬적으로 학습합니다.

| 에이전트 | 채널 (Channel) | 설명 | Q-Table Manager |
|---|---|---|---|
| **기업 (Firm)** | Sales | 판매 가격 결정 (저가 공세 vs 고가 전략) | `q_sales` |
| | Hiring | 고용 및 임금 결정 (적극 채용 vs 소극 채용) | `q_hiring` |
| | Dividend | 배당 성향 결정 (고배당 vs 유보) | `q_dividend` |
| | Equity | 자사주 매입/매각 결정 (주가 부양 vs 자금 조달) | `q_equity` |
| | Capital | 설비 투자 결정 (공격적 확장 vs 긴축) | `q_capital` |
| **가계 (Household)** | Consumption | 품목별 소비 성향 (생필품, 사치품 등 개별 적용) | `q_consumption[item_id]` |
| | Work | 노동 공급 적극성 (구직 활동 강도, 희망 임금) | `q_work` |
| | Investment | 주식 투자 적극성 (포트폴리오 비중) | `q_investment` |

### 2.3. 상태 정의 (State Definition)

각 채널은 공통적인 거시 상태(`_get_common_state`)를 공유하거나, 필요시 채널별 특화 상태를 가질 수 있습니다.

- **기업 공통 상태**: `(재고 수준, 보유 현금 수준)`
    - 재고 수준: 목표 대비 현재 비율 (0.2 ~ 1.5 구간)
    - 현금 수준: 절대 금액 로그 스케일 (100 ~ 10000 구간)
- **가계 공통 상태**: `(자산 수준, 평균 욕구 결핍도)`
    - 자산 수준: 절대 금액 (100 ~ 10000 구간)
    - 욕구 결핍도: 전체 욕구의 평균치 (20 ~ 80 구간)

## 3. 학습 메커니즘

### 3.1. 보상 함수 (Reward Function)

행동의 결과는 다음 틱에 계산되며, 모든 채널은 동일한(또는 유사한) 통합 보상을 공유하여 '전체적인 성공'을 학습합니다.

- **기업 보상**: `자산 증분(Profit)` + `주가 부양 보상(Market Cap Incentive)`
    - 주가 보상은 경영진이 주주 가치를 제고하도록 유도하는 장치입니다.
- **가계 보상**: `자산 증분(Wealth Delta)` + `욕구 해소분(Need Satisfaction)`
    - 생존 및 삶의 질 향상이 자산 증식만큼 중요하게 작용합니다.

### 3.2. Q-테이블 업데이트
매 틱(`update_learning_v2`)마다 각 채널의 `(State, Action, Reward, Next State)` 튜플을 사용하여 Q-값을 갱신합니다.

## 4. 레거시와의 차이점 (Legacy vs V2)

| 항목 | V1 (Legacy) | V2 (Current) |
|---|---|---|
| **구조** | Intention(전략) -> Tactic(전술) 계층 구조 | Multi-Channel Action Vector (병렬 구조) |
| **출력** | 이산적 행동 (`BUY_FOOD`, `LOWER_PRICE`) | 연속적 적극성 (`0.75`, `0.2`) |
| **학습** | 통합 Q-테이블 또는 계층적 테이블 | 채널별 독립 Q-테이블 |
| **유연성** | 정의된 행동만 가능 | 파라미터 조정을 통한 미세 조절 가능 |
