# [SPEC CLARIFICATION] WO-057-A: The Brain (Response to Jules Alpha)

Jules Alpha 요원의 날카로운 질문에 대해 수석 아키텍트의 의도를 반영하여 다음과 같이 명세를 확정(Clarify)합니다.

## 1. 부채(Debt Gap) 정의
- **계산식**: `Debt_Ratio = max(0, -government.assets) / current_gdp`
- **Debt Gap**: `Debt_Gap = Debt_Ratio - 0.60` (기준치 60%)
- **설명**: 현재 정부 자산(`assets`)이 음수일 경우 이를 국가 부채로 간주하며, GDP 대비 부채 비율이 60%를 초과할 경우 AI는 보상 함수에서 페널티를 받게 됩니다.

## 2. 액션 공간 (Action Space) 확정
정부 AI는 'Technocrat Edition' 지침에 따라 **통화 정책(금리)과 재정 정책(세율)을 모두 제어**합니다. 5가지 불연속 액션을 다음과 같이 정의하십시오.

| Index | Label | Action (Deltas) |
| :--- | :--- | :--- |
| **0** | **Dovish Pivot** | 금리 `-0.25%p` |
| **1** | **Neutral** | 변동 없음 (Hold) |
| **2** | **Hawkish Shift** | 금리 `+0.25%p` |
| **3** | **Fiscal Ease** | 세율 `-1.0%p` |
| **4** | **Fiscal Tight** | 세율 `+1.0%p` |

## 3. 통합 및 의존성
- **파일**: `simulation/ai/government_ai.py`만 수정하는 것이 원칙이나, `SmartLeviathanPolicy`가 이 브레인을 정상적으로 호출할 수 있도록 인터페이스 시그니처를 맞추어야 합니다.
- **금리 제어**: 본 미션에서는 정부(Leviathan)가 중앙은행의 역할을 겸임하여 금리와 세율을 '동시 조율(Coordination)'하는 능력을 학습하는 것이 핵심입니다.

## 4. 보상 함수 재강조
> `Reward = - ( 0.5*Inf_Gap^2 + 0.4*Unemp_Gap^2 + 0.1*Debt_Gap^2 )`
- 이 식을 통해 AI는 금리를 올려 물가를 잡을 것인지, 세율을 낮춰 고용을 살릴 것인지를 '부채 수준'을 고려하며 스스로 결정하게 됩니다.

---
**추가 질문 사항이 없다면 즉시 구현에 착수하십시오.**
