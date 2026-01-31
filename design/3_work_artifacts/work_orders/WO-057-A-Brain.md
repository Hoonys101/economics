# [WORK ORDER] The Brain (Government AI Engine)

> **Assignee**: Jules Alpha
> **Goal**: 81개 상태를 갖는 Q-Learning 기반 정부 의사결정 엔진 구현.

## 📂 Context Table
| 분류 | 파일 리스트 | 활용 가이드 |
| :--- | :--- | :--- |
| **Source** | `simulation/ai/household_ai.py` | Q-Learning 구현 패턴 참고 |
| **Contract** | `design/specs/phase24_smart_leviathan_spec.md` | 보상 함수 및 상태 이산화 가이드 준수 |
| **Destination**| `simulation/ai/government_ai.py` | 신규 엔진 구현 |

## 🧩 구현 요구 사항 (Zero-Question)
1. **State Discretization**: Inf, Unemp, GDP Gap, Debt의 4개 지표를 각각 3단계(Low/Ideal/High)로 구분하여 총 **81개 상태**를 생성하는 `get_state()` 메서드를 완성하십시오.
2. **Reward Function**: `Reward = - ( 0.5*Inf_Gap^2 + 0.4*Unemp_Gap^2 + 0.1*Debt_Gap^2 )` 산식을 적용하십시오. (상수는 `config` 참조)
3. **Q-Table Persistence**: 학습된 데이터가 시뮬레이션 종료 시 저장 가능하도록 `save_policy()` 구조를 마련하십시오.

## ⚠️ 제약 사항
- 정치적 로직을 배제하고 오직 거시 경제 균형 수렴에만 집중할 것.
