# V2 에이전트 특질 및 학습 방식 설계

**작성일**: 2025-12-29
**분석 대상 코드**: `simulation/core_agents.py`, `simulation/ai/api.py`, `simulation/ai/household_ai.py`

## 1. 개요

V2 아키텍처에서 에이전트의 다양성을 확보하기 위해 **특질(Personality)** 시스템이 도입되었습니다. 현재 가계(Household) 에이전트의 욕구 성장 패턴에 주로 적용되고 있습니다.

## 2. 에이전트 특질 (Personality)

### 2.1. 종류 및 정의 (`simulation/ai/enums.py`)

1.  **MISER (수전노형)**
    -   **특징**: 자산 축적을 중시하며, 소비보다는 저축을 선호합니다.
    -   **욕구 가중치**: `Asset` 욕구가 빠르게 증가하며, `Social` 욕구 증가는 억제됩니다.

2.  **STATUS_SEEKER (지위추구형)**
    -   **특징**: 사회적 지위를 과시하기 위한 소비를 선호합니다.
    -   **욕구 가중치**: `Social` 욕구가 빠르게 증가합니다.

3.  **GROWTH_ORIENTED (학습형/성장형)**
    -   **특징**: 자기 계발과 미래 가치를 중시합니다.
    -   **욕구 가중치**: `Improvement` 욕구가 빠르게 증가합니다.

### 2.2. 작동 메커니즘 (Household)

- **Desire Weights**: `simulation/core_agents.py`의 `Household` 클래스는 `_initialize_desire_weights` 메서드를 통해 Personality에 따른 가중치를 설정합니다.
- **Needs Update**: 매 틱 `update_needs` 호출 시, 기본 성장률(`BASE_DESIRE_GROWTH`)에 해당 가중치를 곱하여 각 욕구(`survival`, `asset`, `social`, `improvement`)를 차등적으로 증가시킵니다.
    - 예: `needs["asset"] += base_growth * self.desire_weights["asset"]`
- **행동 유도**: 특정 욕구가 빠르게 증가하면 해당 욕구의 결핍도가 커지므로, AI는 이를 해소하기 위한 행동(예: MISER는 자산 증식, STATUS_SEEKER는 사치품 구매)을 선택할 유인이 커집니다.

## 3. 학습 초점 (Learning Focus)

**참고**: `Learning Focus`는 `BaseAIEngine`(`api.py`)에 구현되어 있으나, 현재 활성화된 V2 Vector Architecture(`FirmAI`, `HouseholdAI`)에서는 독립 채널 Q-Table 업데이트 방식을 사용하므로 `update_learning_v2`에서는 이 파라미터가 직접적으로 사용되지 않고 있습니다. (Legacy Feature)

- **개념**: 최종 보상 신호를 전략(Strategy)과 전술(Tactic) 중 어디에 더 반영할지 결정하는 파라미터.
- **현황**: V2 모델은 채널별 독립 학습을 수행하므로, 각 채널 Q-Table은 `base_alpha`를 사용하여 균일하게 학습합니다. 향후 메타 학습 도입 시 재활용될 가능성이 있습니다.
