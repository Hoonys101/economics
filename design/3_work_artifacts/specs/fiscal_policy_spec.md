# W-1 Specification: Phase 4 - Operation "Leviathan" (Adaptive Governance)

**Module**: Phase 4 - Political Economy  
**Status**: 🟠 In Design (Adaptive Agent Refactoring)  
**Author**: Architect (Antigravity)  
**Philosophy**: "Social phenomena are emergence, not scripts. Agents act rationally to survive within their systemic constraints."

---

## 1. The Political Self: `PoliticalComponent` (Voters)

유권자(Household)는 단순히 소득에 반응하는 기계가 아니라, 내적 가치와 신뢰를 바탕으로 판단한다.

### 1.1 Data Structure
*   **Economic Vision (0.0~1.0)**: 가계의 이념적 성향 (0.0: 안전망/분배 중시 ~ 1.0: 성장/기회 중시). 성격(Personality)에 따라 초기화됨.
*   **Trust Score (0.0~1.0)**: 정부 시스템에 대한 신뢰도.

### 1.2 Approval Logic (지지의 역설)
*   **Approval = (0.4 * Economic_Satisfaction) + (0.6 * (1.0 - Ideological_Distance))**
*   **Paradox Mechanic**: 자산이 적은 서민이라도 '성장 비전'이 높다면, 자신의 경제적 상황과 반대되는 보수 정당(BLUE)을 지지할 수 있다.
*   **Trust Threshold**: 신뢰도가 극도로 낮아지면(0.2 미만) 이념과 상관없이 지지를 철회한다.

---

## 2. The Constraint System: `PolicyLockoutManager`

정치적 결단(고문 해고)에 따른 **'기회비용'**을 시스템적으로 강제한다.

### 2.1 Action Tags
*   모든 정부 액션은 태그(`KEYNESIAN_FISCAL`, `AUSTRIAN_AUSTERITY` 등)를 가진다.

### 2.2 Scapegoating & Lockout
*   **Action**: 고문(Advisor) 해고.
*   **Effect**: 
    *   **Trust Reset**: 대중의 기대심리를 일시적으로 리셋하여 지지율 하락을 방어.
    *   **Lockout**: 해고된 고문의 학파와 관련된 모든 액션 태그는 **20틱 동안 비활성화(Locked)**된다.
    *   **Reasoning**: "실패한 과거의 수단을 다시 쓸 수 없다"는 정치적 명분의 상실을 구현.

---

## 3. The Brain: `AdaptiveGovBrain` (Government)

정당(RED/BLUE)에 따라 서로 다른 목적함수를 가진 의사결정 엔진이다.

### 3.1 Reality-based Utility (현실적 효용)
*   **🔴 RED (Progressive)**: $U = (0.7 \cdot 서민층지지율) + (0.3 \cdot 지니계수개선) - Penalty$
*   **🔵 BLUE (Conservative)**: $U = (0.6 \cdot 자산가지지율) + (0.4 \cdot GDP성장) - Penalty$

### 3.2 Decision Loop
1.  **Perceive State**: 매 틱 거시 경제 지표 및 지지율 수집.
2.  **Filter Actions**: `PolicyLockoutManager`에 의해 잠긴 액션 제거.
3.  **Evaluate Utility**: 가능한 각 액션의 기대 효용 계산.
4.  **Softmax Selection**: 확률적 선택을 통해 '실수 가능성'과 '탐험'을 포함한 현실적 의사결정 수행.

---

## 4. Verification & Emergence
1.  **The Scapegoat Emergence**: 위기 상황에서 정부가 리스크를 감수하고 고문을 희생양으로 삼는지 관측.
2.  **The Paradox Support**: 서민층 내에서 '성장 비전'에 의한 보수당 지지 현상 데이터 검증.
3.  **Policy Cycle**: 고문 교체와 쿨다운으로 인해 발생하는 정책적 단절과 이로 인한 경기 순환(Political Business Cycle) 관측.
