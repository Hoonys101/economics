# [SPEC] WO-057: The Smart Leviathan (Adaptive Policy AI)

## 1. 아키텍처 개요 (Architecture Overview)

본 설계는 정부 에이전트를 '정적 공식'에서 '목적 지향적 최적화 엔진'으로 승격시키는 것을 목표로 합니다.
- **Role**: Technocrat AI (조향 장치)
- **Engine**: Q-Learning (Macro Stance Optimization)
- **Constraint**: Action Clipping & Policy Lag Effect

## 2. 데이터 구조 (Data & Interface)

### 2.1 GovernmentStateDTO
정부 AI가 관측하는 거시 경제 상태 변수입니다.

| Attribute | Type | Description | Discretization (States) |
| :--- | :--- | :--- | :--- |
| `inflation_gap` | `float` | `Current_Inf - Target_Inf` | `Low (<0%), Ideal (0~3%), High (>3%)` |
| `unemployment_gap`| `float` | `Actual_Unemp - Natural_Unemp`| `Low (<3%), Ideal (3~5%), High (>5%)` |
| `output_gap` | `float` | `Actual_GDP - Potential_GDP` | `Negative, Neutral, Positive` |
| `fiscal_health` | `float` | `Debt / GDP Ratio` | `Safe (<60%), Warning (60-100%), Critical (>100%)` |

> **Total States**: 3^4 = 81 States (수렴 최적화)

### 2.2 Action Space (Delta-Based)
경제 쇼크 방지를 위한 Clipping이 적용된 증분 액션입니다.

| Action Index | Interest Rate Delta | Tax Rate Delta | Label |
| :--- | :--- | :--- | :--- |
| 0 | `-0.25%p` | `0` | Dovish Pivot |
| 1 | `0` | `0` | Neutral Hold |
| 2 | `+0.25%p` | `0` | Hawkish Shift |
| 3 | `0` | `-1.0%p` | Fiscal Expansion |
| 4 | `0` | `+1.0%p` | Fiscal Contraction |

## 3. 핵심 로직: 적응형 통치 엔진 (Technocrat Engine)

### 3.1 보상 함수 (Reward Function)
정부의 성적표는 거시 경제 지표의 목표 편차 제곱합의 음수값으로 정의합니다.

> `Reward = - ( w1 * (Inf_Gap^2) + w2 * (Unemp_Gap^2) + w3 * (Debt_Gap^2) )`
- **Initial Weight**: `w1(물가)=0.5`, `w2(고용)=0.4`, `w3(재정)=0.1`

### 3.2 정책 시차 및 빈도 제어 (Lag & Throttling)
- **Observation Lag**: 정부는 최근 **10틱 이동평균(SMA)** 데이터를 관측하여 단기 노이즈를 필터링합니다.
- **Decision Frequency**: 매 틱 액션을 취하지 않고, **`GOV_ACTION_INTERVAL` (30틱, 약 1개월)** 마다 한 번씩만 정책 결정을 수행합니다. (FOMC 원칙)

## 4. 클래스 설계 (Class Design)

### [NEW] `simulation/ai/government_ai.py`
- `class GovernmentAI(BaseAI)`: 정부용 Q-Table 관리 및 액션 선택.
- `update_q_table()`: 거시 경제 지표와 이전 액션에 따른 보상 정산.

### [MODIFY] `simulation/agents/government.py`
- `self.policy_ai`: `GovernmentAI` 인스턴스 보유.
- `make_policy_decision()`: AI로부터 액션을 수령하여 실제 `base_interest_rate` 및 `income_tax_rate` 업데이트.

## 5. 단계별 구현 계획 (Jules 지침)

1. **Step 1 (Scaffolding)**: `GovernmentAI` 클래스 생성 및 `engine.py`에서 거시 지표 수집기 연동.
2. **Step 2 (Experience Loop)**: 시뮬레이션 실행 중 정부가 '현재 상태'와 '보상'을 계산하여 Q-Table을 업데이트하는 루틴 구현.
3. **Step 3 (Action Link)**: AI의 결정을 실제 경제 시스템 변수에 반영하고, 정책 변경 사유를 로그로 출력.

## 6. 검증 지표 (Success Metrics)
- **Stability**: 자율 금리 조정 하에서 인플레이션이 2.0% ± 0.5% 내로 수렴하는가?
- **Anti-Crisis**: 급격한 GDP 하락 발생 시 AI가 즉각적으로 Dovish/Expansionary 액션을 취하는가?
- **Explainability**: 로그에 "Inf High -> Raising Rate" 식의 타당한 근거가 남는가?
