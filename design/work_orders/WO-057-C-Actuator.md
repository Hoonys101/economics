# [WORK ORDER] WO-057-C: The Actuator (Policy Execution)

> **Assignee**: Jules Charlie
> **Goal**: AI의 결정을 정책 변수(금리/세율)로 변환하여 실행하고, 30틱 주기를 제어함.

## 📂 Context Table
| 분류 | 파일 리스트 | 활용 가이드 |
| :--- | :--- | :--- |
| **Source** | `simulation/policies/smart_leviathan_policy.py` | 기존 스캐폴딩 코드 참고 |
| **Contract** | `config.py` | `GOV_ACTION_INTERVAL(30)` 및 변동폭 제한 준수 |
| **Destination**| `simulation/policies/smart_leviathan_policy.py` | 실제 정책 반영 로직 완성 |

## 🧩 구현 요구 사항 (Zero-Question)
1.  **Action Mapping**: AI 브레인이 보낸 `Action Index`를 실제 `Interest_Rate_Delta`(-0.25%, 0, +0.25%) 및 `Tax_Delta`로 변환하는 매핑 로직을 완성하십시오.
2.  **Interval Control**: `last_action_tick`을 활용하여 **30틱(1개월)** 주기로만 정책이 변경되도록 제어 루프를 구현하십시오.
3.  **Logging**: 정책 변경 시 인플레이션/실업률 수치와 함께 변경 사유를 `logger.info`로 남기십시오.

## ⚠️ 제약 사항
- `Government.py` 내부의 기존 테일러 준칙 로직과 섞이지 않도록 `SmartLeviathanPolicy` 클래스 내부에서만 로직을 완결할 것.
