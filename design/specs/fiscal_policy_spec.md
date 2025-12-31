# W-1 Specification: Phase 4 - Fiscal Policy & The Welfare State

**모듈**: Phase 4 - Government & Stability  
**상태**: 🟡 Drafting (기획 단계)  
**작성자**: Architect (Antigravity)  
**전제**: Phase 3 (Banking) 구현 완료  
**대상 파일**: `config.py`, `simulation/agents/government.py`, `simulation/bank.py`, `simulation/core_agents.py`

---

## 1. 개요 (Overview)
금융(Phase 3) 도입으로 인한 빈부격차 확대와 불황(Crisis)을 방어하기 위해 **"정부의 적극적 개입(Fiscal Policy)"**을 구현한다.
핵심은 **"부의 재분배(Redistribution)"**와 **"사회 안전망(Safety Net)"**이며, 이를 통해 시뮬레이션의 **장기적 동적 평형(Dynamic Equilibrium)**을 달성한다.

## 2. 아키텍처 및 정책 모델

### 2.1 Policy Configuration (Regime System)
정부의 성격을 결정하는 정책 파라미터를 도입하여 다양한 경제 체제 실험을 지원한다.

*   **`FISCAL_MODEL`**:
    *   `"LIBERTARIAN"` (야경 국가): 저세율, 복지 없음, 파산 시 가혹한 처벌.
    *   `"SOCIAL_DEMOCRACY"` (복지시): 고세율(누진세), 강력한 실업급여/기본소득.
    *   `"MIXED"` (혼합 경제): 절충안 (Default).

### 2.2 Advanced Taxation (조세 고도화)
*   **누진세 (Progressive Income Tax)**:
    *   소득 구간(Tax Brackets)별 차등 세율 적용.
    *   예: 하위 50%(0%), 중위(10%), 상위 10%(40%).
*   **보유세 (Wealth Tax)**:
    *   순자산(Net Worth)이 일정 임계치(`WEALTH_TAX_THRESHOLD`)를 초과하는 가계에 대해 매 틱 과세.
    *   목표: 노동 없는 부의 무한 축적 견제.

### 2.3 Welfare System (사회 안전망)
*   **실업 급여 (Unemployment Benefit)**:
    *   **자격**: `is_employed = False` AND `looking_for_work = True` (노동 시장에 오퍼를 냄).
    *   **지급액**: `SURVIVAL_COST` * 0.8 (굶어 죽지 않을 정도).
    *   **재원**: 국고(Treasury). 부족 시 국채 발행(Money Printing) 또는 지급 축소.
*   **재난 지원금 (Stimulus Check)**:
    *   **조건**: GDP가 2분기 연속 하락하거나, 기아 사망자 급증 시 발동.
    *   **지급**: 모든 가계에 일시금 지급 (Helicopter Money).

### 2.4 Bankruptcy Court (회생 절차)
*   **`BankruptcyProcedure`**:
    1.  **청산 (Liquidation)**: 가계의 현금 및 유동화 가능한 자산(주식 등)을 전량 매각하여 은행 빚 상환.
    2.  **탕감 (Forgiveness)**: 남은 빚은 소멸(Write-off). 은행의 손실로 기록(Bad Debt).
    3.  **패널티 (Penalty)**:
        *   신용 불량 (`credit_rating = 0`): `CREDIT_RECOVERY_TICKS` 동안 신규 대출 불가.
        *   자존감 하락: 사회적 욕구(Social Need) 충족도 초기화.

---

## 3. 세부 구현 명세

### 3.1 Config 추가 (`config.py`)
```python
# --- Phase 4: Fiscal Policy ---
# Tax Brackets: [(threshold_multiplier, rate)]
# multiplier는 평균 소득 대비 배수
TAX_BRACKETS = [
    (0.5, 0.0),   # 평균의 0.5배 이하: 면세
    (2.0, 0.15),  # 평균의 2배 이하: 15%
    (float('inf'), 0.40) # 그 이상: 40%
]

WEALTH_TAX_THRESHOLD = 50000.0  # 보유세 부과 기준 자산
WEALTH_TAX_RATE = 0.005 # 틱당 0.5% (연 50%... 너무 쎈가? 연환산 고려 필요)

UNEMPLOYMENT_BENEFIT_RATIO = 0.8 # 생존 비용 대비 지급 비율
STIMULUS_TRIGGER_GDP_DROP = -0.05 # GDP 5% 하락 시
```

### 3.2 Government Logic Update
*   **`collect_tax()` 개선**: 단순 세율 곱하기 → `_calculate_progressive_tax(income)` 호출.
*   **`run_welfare_check()` 추가**:
    *   매 틱 가계 상태 전수 조사.
    *   실업자에게 급여 지급.
    *   보유세 징수.

### 3.3 Bankruptcy Mechanism (in Bank)
*   **`process_default(agent)`**:
    *   이자 연체 발생 시 호출.
    *   자산 처분 로직 실행.
    *   `agent.reset_financial_status()` 호출.

---

## 4. 검증 계획
1.  **지니계수 완화**: 누진세 도입 전후 지니계수 변화 비교.
2.  **생존율 향상**: 불황 시 실업급여로 인한 아사자 감소 확인.
3.  **좀비 기업/가계 퇴출**: 파산 절차를 통해 부실 에이전트가 리셋되고 경제가 다시 활력을 찾는지 확인.

---

## 5. 작업 체크리스트
- [ ] Config: 누진세율 및 복지 파라미터 정의
- [ ] Government: `run_welfare_check`, `calc_progressive_tax` 구현
- [ ] Bank/Agent: 파산 및 회생(Rehab) 로직 구현
- [ ] Engine: GDP 트래킹 및 경기 침체 감지 로직 (Stimulus Trigger)
