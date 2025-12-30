# 기업 에이전트 설계 (V2 - Multi-Channel Aggressiveness)

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/decisions/ai_driven_firm_engine.py`, `simulation/ai/firm_ai.py`

## 1. 목표

기업 에이전트는 AI(`FirmAI`)가 결정한 **5가지 채널의 적극성(Aggressiveness)**을 기반으로 `AIDrivenFirmDecisionEngine`을 통해 구체적인 시장 주문을 생성합니다. 이를 통해 이윤을 극대화하고 기업 가치를 높이는 것을 목표로 합니다.

## 2. 의사결정 프로세스

AI가 출력하는 `FirmActionVector`의 각 요소는 다음과 같이 구체적인 행동으로 변환됩니다.

### 2.1. Sales Channel (판매 및 가격 결정)
- **입력**: `sales_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - 목표 가격 설정: `시장가 * (1.0 + (0.5 - agg) * 0.4)`
    - **Aggressiveness가 높을수록(1.0)**: 목표 가격을 시장가보다 낮게 설정하여 판매량을 늘리려 합니다 (박리다매).
    - **Aggressiveness가 낮을수록(0.0)**: 목표 가격을 시장가보다 높게 설정하여 마진을 높이려 합니다 (고가 전략).
- **실행**: 보유 재고가 있을 경우 계산된 가격으로 판매(`SELL`) 주문을 제출합니다.

### 2.2. Hiring Channel (고용 및 임금 결정)
- **입력**: `hiring_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - 생산 목표 달성을 위해 필요한 노동력(`needed_labor`)을 계산합니다.
    - 임금 설정: `시장 평균 임금 * (1.0 + adjustment)`
    - **Aggressiveness가 높을수록**: 더 높은 임금을 제시하여 인력을 확실히 확보하려 합니다.
    - **긴급성(Urgency)**: 인력 부족이 심각할 경우 Aggressiveness에 가중치가 더해집니다.
- **실행**: 필요한 인력만큼 노동 구매(`BUY`) 주문을 제출합니다.

### 2.3. Dividend Channel (배당 정책)
- **입력**: `dividend_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - 배당률(`dividend_rate`) 결정: `최소 배당률` + `agg * (최대 - 최소)`
    - **Aggressiveness가 높을수록**: 이익의 더 많은 부분을 주주에게 환원합니다 (주가 부양 효과).
    - **Aggressiveness가 낮을수록**: 이익을 사내 유보하여 재투자에 활용합니다.

### 2.4. Equity Channel (자사주 관리)
- **입력**: `equity_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - **0.0 ~ 0.4 (Buyback)**: 시장가보다 약간 높게 자사주를 매입하여 주가를 방어합니다.
    - **0.6 ~ 1.0 (Issuance)**: 보유 자사주를 시장가보다 약간 낮게 매각하여 자금을 조달합니다.
    - **0.4 ~ 0.6 (Hold)**: 관망합니다.

### 2.5. Capital Channel (설비 투자)
- **입력**: `capital_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - **Aggressiveness > 0.6**: 자산의 일부를 소모하여 생산성(`capital_stock`)을 높이는 투자를 감행합니다.
    - 정부 보조금 정책(`RD_SUBSIDY_RATE`)이 있을 경우 투자 효과가 증대됩니다.

## 3. 상태 관리 및 메모리

- **Last Prices**: 각 상품별로 마지막으로 시도한(또는 성공한) 가격을 기억하여 다음 틱의 기준 가격으로 활용합니다.
- **Employee Wages**: 기존 직원들의 임금을 기억하여 임금 하방 경직성을 구현합니다. (급격한 임금 삭감 방지)
