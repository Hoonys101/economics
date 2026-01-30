# Insight Report: Agent Decision Rejection Logging

## 현상 (Phenomenon)
시뮬레이션에서 가계(Household) 에이전트가 생존에 필수적인 식량을 소비하지 않아 기아 상태에 빠지는 현상이 발생했으나, 기존 로그만으로는 그 원인이 '구매력 부족' 때문인지, '시장 재고 소진' 때문인지 명확히 구분할 수 없었습니다.

## 원인 (Cause)
기존 `CommerceSystem`은 소비 활동의 성공적인 결과만을 주로 처리했으며, 에이전트가 특정 행동을 '하지 않기로' 결정한 이유나 실패한 결정의 구체적인 맥락(context)을 기록하는 기능이 부재했습니다.

## 해결 (Solution)
`CommerceSystem` 내에 "ThoughtStream" 로깅 로직을 추가했습니다. 식량 소비량이 0이고 생존 욕구가 높을 때, 에이전트의 자산과 당시 시장 가격을 비교하여 소비 실패의 원인을 'INSOLVENT'(자금 부족) 또는 'STOCK_OUT'(재고 부족)으로 구체화하여 `agent_thoughts` 데이터베이스 테이블에 기록하도록 구현했습니다. (`simulation/systems/commerce_system.py`)

## 교훈 (Lesson Learned)
에이전트의 주요 결정, 특히 '거부된 결정(rejected decisions)'의 원인을 상세히 기록하는 것은 복잡계 시뮬레이션의 디버깅 효율을 극적으로 향상시킵니다. 이는 예기치 않은 거시적 현상의 미시적 원인을 추적하고, 에이전트의 행동 모델을 개선하는 데 필수적인 데이터가 됩니다.
