# [WORK ORDER] WO-057: The Smart Leviathan (Technocrat Edition)

> **Status**: [!IMPORTANT]
> **Priority**: HIGH (Adaptive Governance)
> **Assignee**: Jules (Parallel Squad: Alpha, Bravo, Charlie)
> **Goal**: 정부 의사결정 체계를 가중치가 포함된 AI 최적화 모델로 승격시킨다.

## 📂 Context Table (반드시 숙지할 파일 그룹)

| 분류 | 역할 | 파일 리스트 | 활용 가이드 |
| :--- | :--- | :--- | :--- |
| **Source** | 참조 원본 | `simulation/ai/household_ai.py`<br>`simulation/agents/government.py` | Q-Learning 이식 및 기존 함수 시그니처 참고 |
| **Contract** | 제약 준수 | `simulation/dtos.py`<br>`config.py` | `GovernmentStateDTO` 정의 및 변동폭 상수 확인 |
| **Destination**| 수정 대상 | `simulation/ai/government_ai.py` [NEW]<br>`simulation/agents/government.py`<br>`simulation/engine.py` | 모듈별 기능 이식 및 통합 |

## 🧩 작업 분할 (Parallel Assignment)

본 작업은 세 가지 모듈로 나뉘며, 각 담당자는 지정된 메서드 외의 영역을 침범하지 마십시오.

### 1. [Brain Module] GovernmentAI (담당: Jules Alpha)
- **Task**: `simulation/ai/government_ai.py`를 생성하고 `BaseAI`를 상속받은 적응형 엔진 구현.
- **Method Strategy**: `HouseholdAI.update_q_table`을 이식하되, 보상의 기준을 `(Inf, Unemp, Debt)`의 편차 제곱합으로 정의.
- **Constraint**: 정치적 편향 없이 오직 매크로 수치 수렴에만 집중할 것.

### 2. [Sensory Module] Macro Data Pipeline (담당: Jules Bravo)
- **Task**: `simulation/engine.py`에서 정부에게 전달할 `MacroState` 가공 로직 구현.
- **Method Strategy**: 매 틱 시장 지표를 `deque(maxlen=10)`에 저장하고, 이들의 평균값(SMA)을 `GovernmentStateDTO`로 변환하여 에이전트에게 공급.

### 3. [Actuator Module] Policy Execution (담당: Jules Charlie)
- **Task**: `simulation/agents/government.py` 내의 정책 실행 로직 교체.
- **Method Strategy**: `adjust_fiscal_policy` 메서드를 삭제하고, AI 액션 수령 후 현재 금리/세율에 델타값을 더하는 `apply_policy_delta` 구현.
- **Decision Frequency**: 정부의 행동(Action)은 매 틱이 아닌 **`GOV_ACTION_INTERVAL` (30틱)** 마다 단 한 번씩만 수행합니다. (FOMC 원칙 준수)
- **Alert**: [!IMPORTANT] 금리 ±0.25%p, 세율 ±1.0%p Clipping 필수.

## 🛡️ Architect Prime's Technical Review (Implementation Notes)

- **State Discretization (Alpha)**: 상태 변수(Inf, Unemp 등)를 너무 세밀하게 나누지 마십시오. 설계서에 명시된 대로 각 3단계(Low/Ideal/High)로 이산화하여 총 81개 상태 내에서 빠르게 수집되도록 하십시오.
- **Action Throttling (Charlie)**: 정책 효과가 나타날 시간적 여유를 주기 위해 반드시 30틱 간격의 의사결정 주기를 준수하십시오.
- **Target Constants**: `config.py`에 정의된 `TARGET_INFLATION_RATE(2%)`와 `TARGET_UNEMPLOYMENT_RATE(4%)`를 보상 함수의 정답지로 사용하십시오.

## ⚠️ 기술부채 및 인사이트 보고 (Insight Reporting)
작업 중 발견한 **'정책 시차에 따른 오버슈팅'** 문제나 **'보상 함수의 가중치 불균형'**에 대한 통찰을 `communications/insights/WO-057-Insight.md`에 상세히 기록하십시오.

---
**"시장에 보이지 않는 손이 있다면, 정부에는 명석한 두뇌가 있어야 한다."**
