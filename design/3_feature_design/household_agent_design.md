# 가계 에이전트 설계 (V2 - Multi-Channel Aggressiveness)

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/decisions/ai_driven_household_engine.py`, `simulation/ai/household_ai.py`

## 1. 목표

가계 에이전트는 AI(`HouseholdAI`)가 결정한 **소비, 노동, 투자 채널의 적극성(Aggressiveness)**을 기반으로 시장에 참여합니다. 생존 욕구를 최우선으로 충족하면서 자산을 증식하는 것을 목표로 합니다.

## 2. 의사결정 프로세스

AI가 출력하는 `HouseholdActionVector`는 다음과 같이 처리됩니다.

### 2.1. Consumption Channel (소비 결정)
- **입력**: `consumption_aggressiveness` (Dict[item_id, float]) - 각 상품별 적극성
- **로직**:
    - `decide_action_vector`에서 각 상품별로 독립적인 Q-Table을 통해 적극성을 결정합니다.
    - **적극성(Aggressiveness)의 의미**:
        - 지불 용의(Willingness to Pay)를 조절합니다.
        - 적극성이 높을수록 시장 평균가보다 비싸도 구매를 시도합니다.
        - 적극성이 낮으면 저가 매수 기회를 노리거나 구매를 미룹니다.
- **실행**:
    - 예산 제약(자산의 일정 비율) 내에서 적극성이 높은 품목을 우선적으로 구매 시도합니다.
    - `BUY` 주문 생성 시 가격: `시장가 * (1.0 + (agg - 0.5) * adjustment)`

### 2.2. Work Channel (노동 공급)
- **입력**: `work_aggressiveness` (0.0 ~ 1.0)
- **로직**:
    - **실업 상태**: 구직 활동의 적극성을 결정합니다.
        - 적극성이 높으면(`> 0.5`) 낮은 임금이라도 수락하여 취업하려 합니다 (희망 임금 하향).
        - 적극성이 낮으면(`< 0.5`) 더 높은 임금을 주는 일자리를 기다립니다.
    - **취업 상태**: 이직 또는 임금 인상 요구를 고려할 수 있습니다(현재 구현에 따라 다름).
- **실행**: 노동 시장(`labor`)에 `SELL` 주문(노동 공급)을 제출합니다.

### 2.3. Investment Channel (투자)
- **입력**: `investment_aggressiveness` (0.0 ~ 1.0)
- **전제 조건**: 최소 자산(`HOUSEHOLD_MIN_ASSETS_FOR_INVESTMENT`) 이상 보유 시에만 활성화됩니다.
- **로직**:
    - 포트폴리오 비중을 결정합니다.
    - 적극성이 높을수록 자산의 더 많은 부분을 주식에 투자합니다.
- **실행**: 주식 시장(`stock_market`)에 기업 주식 `BUY` 주문을 제출합니다.

## 3. 욕구 및 소비 메커니즘

- **Utility Effects**: 상품(`config.py`)에 정의된 `utility_effects`를 기반으로, 구매 후 소비 시 `needs`가 해소됩니다.
- **Consumption Reset**: 매 틱마다 소비량(`current_consumption`)이 초기화되어 정확한 GDP 흐름을 반영합니다.
