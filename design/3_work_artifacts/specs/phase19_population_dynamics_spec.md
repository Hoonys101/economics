# Phase 19: Population Dynamics - The Evolutionary Strategy

## 1. 개요 (Overview)
기존의 단순 경제적 비용 모델을 폐기하고, **진화심리학(Evolutionary Psychology)**과 **사회학(Sociology)**적 접근을 통합한 고도화된 인구 역학 모델을 구현합니다.
에이전트는 자신의 '유전자 생존 확률'을 극대화하기 위해 환경에 적응(Adaptation)하며, 이 과정에서 현대 사회의 저출산 현상이 **"합리적 선택의 결과"**로 창발(Emergence)되도록 설계합니다.

## 2. 핵심 가설 및 메커니즘 (Core Mechanisms)

### 2.1 The Expectation Mismatch (기대와 현실의 괴리)
"많이 배웠으니 많이 벌어야 한다"는 보상 심리가 충족되지 않을 때의 박탈감을 모델링합니다.

*   **Logic**:
    *   `Expected_Wage` = $f(\text{Education\_Level}, \text{Peer\_Average})$
    *   `Reservation_Utility` (최소 요구 만족도)는 `Expected_Wage`에 비례하여 상승.
    *   `Actual_Utility` < `Reservation_Utility` 상태에서는 **"생존 모드"**로 인식하여 장기 투자(출산)를 중단.

### 2.2 Time Allocation & Opportunity Cost (시간 자원 배분)
모든 에이전트는 하루 24시간의 유한한 자원을 가집니다.

*   **Constraint**: $T_{total} = T_{labor} + T_{leisure} + T_{housework} + T_{childcare}$
*   **Shadow Work**: 삶의 질(`Quality of Life`)을 유지하기 위한 필수 가사 노동 시간($T_{housework}$) 존재.
*   **Trade-off**:
    *   고소득(High Wage) $\rightarrow$ 노동 시간 가치 상승 $\rightarrow$ 직접 육아($T_{childcare}$)의 기회비용 급증.
    *   시장 서비스(보육/가사 도우미) 구매 비용 vs 직접 노동 기회비용 비교.
    *   **결론**: "내가 키우면 손해고, 남을 쓰면 너무 비싸다" $\rightarrow$ **출산 포기**.

### 2.3 r/K Selection Switch (생존 전략 스위칭)
환경의 불확실성과 경쟁 강도에 따라 번식 전략을 선택합니다.

*   **r-Strategy (양적 전략)**:
    *   Trigger: 높은 사망률(치안 부재), 낮은 신분 상승 가능성, 미래 불확실성.
    *   Action: 조기 결혼, 다산, 교육 투자 최소화.
*   **K-Strategy (질적 전략)**:
    *   Trigger: 낮은 사망률, 높은 경쟁 강도, "개천에서 용 나기 어려움(High Cost of Ascent)".
    *   Action: 만혼, 소수 출산, 교육비 집중 투자(엘리트 양성).

## 3. 구현 설계 (Implementation Design)

### 3.1 Household Agent 확장
`simulation/core_agents.py`

```python
class Household(BaseAgent):
    # ... existing ...
    
    # Phase 19 Attributes
    self.education_level: int = 0  # 0~5 (None, Elem, High, Univ, Master, PhD)
    self.expected_wage: float = 0.0
    
    # Time Allocation (Hours per day)
    self.time_budget: Dict[str, float] = {
        "labor": 8.0,
        "leisure": 8.0,
        "housework": 8.0, # Includes childcare
    }
    
    # Offspring
    self.children: List[int] = [] # IDs of children agents
    self.is_fertile: bool = True  # Age based (e.g., 20-45)
```

### 3.2 Evolutionary Engine (`simulation/ai/evolutionary_engine.py`)
새로운 의사결정 모듈 `EvolutionaryDecisionEngine`을 도입하여 `HouseholdAI`를 보조합니다.

#### A. Expectation Calculation
$$ W_{expect} = W_{base} \times (1 + r_{edu})^{\text{Edu\_Level}} \times \alpha_{\text{peer}} $$
*   교육 수준이 높을수록 눈높이가 기하급수적으로 상승.

#### B. Reproduction Decision (매 틱/주기 실행)
1.  **Check Biological Constraint**: 나이 (20~45세).
2.  **Check Economic Viability**:
    *   `Disposable_Income` > `Child_Min_Cost` ?
    *   `Actual_Utility` > `Reservation_Utility` ? (심리적 여유)
3.  **Check Time Viability**:
    *   `Available_Time` = 24 - `Required_Labor` - `Min_Housework`
    *   `Available_Time` > `Childcare_Time_Needed` ?
4.  **Strategy Selection (r/K)**:
    *   `Social_Capillarity` (상승 비용)이 높으면 $\rightarrow$ **K-strategy** (자녀 수 제한, 교육비 저축).
    *   `Uncertainty`가 높으면 $\rightarrow$ **r-strategy** (조건 완화, 확률적 출산).

### 3.3 Demographic Manager (`simulation/systems/demographic_manager.py`)
전체 인구 통계, 출생/사망 처리, 세대 교체를 담당하는 시스템 에이전트.

*   `birth_process()`: 새로운 `Household` 객체 생성, 부모의 형질(Talent) 유전, 초기 자산 분배.
*   `aging_process()`: 에이전트 나이 증가, 은퇴 및 자연사 처리.

## 4. 검증 시나리오 (Verification Scenarios)

### Scenario A: "The Rat Race" (현대 사회)
*   **환경**: 고학력(High Expected Wage), 고세율/고물가, 높은 경쟁.
*   **예측**: 맞벌이 부부의 시간 빈곤 $\rightarrow$ 출산율 급락 (0.7명대).

### Scenario B: "The Baby Boom" (전후 복구기)
*   **환경**: 저학력(Low Expected Wage), 급격한 경제 성장(Hope), 낮은 경쟁.
*   **예측**: "내일은 더 낫다"는 기대 $\rightarrow$ 다산 (3.0명대).

## 5. File Changes
- `[MODIFY] config.py`: 교육 비용, 양육 시간 비용, 나이 설정 등 상수 추가.
- `[MODIFY] simulation/core_agents.py`: 학력, 시간 예산, 자녀 속성 추가.
- `[NEW] simulation/systems/demographic_manager.py`: 인구 관리 시스템.
- `[MODIFY] simulation/ai/household_ai.py`: 출산 의사결정 로직 위임/통합.
- `[NEW] tests/verify_population_dynamics.py`: 시나리오별 출산율 검증.
