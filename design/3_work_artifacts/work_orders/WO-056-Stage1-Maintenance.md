# [WORK ORDER] WO-056-Stage1-Maintenance: Money Leakage Fix & Parameter Tuning

> **Status**: [!IMPORTANT]
> **Priority**: CRITICAL (Simulation Integrity)
> **Assignee**: Jules (Implementer)
> **Goal**: 섀도우 모드(Stage 1) 도입 후 발생한 통화 누출(-999.8)을 해결하고, 섀도우 가격 산출 파라미터를 튜닝한다.

## 📂 Context Table

| 분류 | 역할 | 활용 가이드 |
| :--- | :--- | :--- |
| **Source (출처)** | `simulation/agents/government.py` | `run_public_education` 및 `total_money_issued` 로직 점검 |
| **Contract (계약)** | `simulation/systems/reflux_system.py` | `capture` 및 `distribute` 시점 확인 |
| **Destination (목적지)** | `simulation/engine.py` | `run_tick` 내의 정부 모듈 호출 순서 및 통화량 체크 로직 |

## 💡 구현 및 수정 전략 (Transplant Strategy)

### 1. 통화 누출(-999.8) 원인 파악 및 수정
- **현상**: `Tick 1`에서 약 1000 단위의 통화 누출 발생. 교육 시스템(`run_public_education`)의 `spent_total`과 `reflux_system` 연동 부위가 의심됨.
- **점검 항목**:
    - `Government.assets`가 0인 상태에서 지출이 발생하여 마이너스로 가는지 확인.
    - `total_money_issued`가 누적(Cumulative)으로 관리되는데, `Simulation._calculate_total_money`에서 누락된 항목이 있는지 확인.
    - 특히 `student_share`가 가계 자산에서 차감된 후 `reflux_system`에 정확히 캡처되는지, 그리고 이것이 `total_money_issued`에 중복 계산되지는 않는지 점검.

### 2. Shadow Mode 파라미터 튜닝
- `firms.py`의 `_calculate_invisible_hand_price`에서 `Sensitivity`를 `0.1`에서 시뮬레이션 상황에 맞게 조정 (너무 가파른 변동 방지).
- `government.py`의 `Taylor Rule` 로그 출력이 너무 빈번할 경우 로그 밀도 조절.

## ⚠️ 제약 사항 및 팁
> [!IMPORTANT]
> - `Simulation._calculate_total_money` 메서드의 시그니처를 변경하지 마십시오.
> - `total_money_issued`는 정부가 '새로 발행한' 돈만 기록해야 하며, 가계에서 걷은 돈(Tax)은 `destroyed`로 기록되어야 합니다.
> - 교육비의 `student_share`는 이미 시중에 있는 돈의 이동이므로 `issued`에 포함해서는 안 됩니다.

## 🧠 실무자 인사이트 공유 (Mandatory Insight Reporting)
- 작업 중 발견한 구조적 결함(예: 정부 자산이 Gold Standard 하에서 예외적으로 처리되는 방식 등)이 있다면 반드시 `communications/insights/WO-056-Stage1-Insight.md`에 보고하십시오.
