# Jules Dispatch: The Invisible Hand (Stage 1: Shadow Mode)

**Target:** Jules (Implementationist)
**Context:** Phase 24 (Adaptive Evolution)
**Goal:** Implement "The Invisible Hand" logic in **Shadow Mode** to collect data for parameter tuning.

---

## 🛑 STAGE 1: SHADOW MODE PROTOCOL
수석 아키텍트의 명령에 따라, 본 단계에서는 **기존의 하드 가드레일을 유지**한 상태에서 '보이지 않는 손'이 제안하는 가격과 임금을 **로깅(Shadow Logging)**만 수행합니다. 

### 1.1. Price Discovery 2.0 (Firms)
* **File:** `simulation/firms.py`
* **Action:** `Firm` 클래스에 차기 가격 후보를 계산하는 `_calculate_invisible_hand_price()` 메서드 추가.
* **Formula:**
 * `Candidate = Current_Price * (1 + Sensitivity * (Demand - Supply) / Supply)`
 * `Shadow_Price = (Candidate * 0.2) + (Current_Price * 0.8)`
* **Logging:** 매 틱 `Shadow_Price`와 `Current_Price`, 그리고 `Excess_Demand` 비율을 전용 로그 파일 또는 DB에 기록하십시오.

### 1.2. Labor Market Mechanism (Households)
* **File:** `simulation/core_agents.py`
* **Action:** 가계가 실업/취업 상태에 따라 예약 임금을 어떻게 조절할지 계산하는 `_calculate_shadow_reservation_wage()` 추가.
* **Stickiness Logic:**
 * `Wage_Increase_Rate`: 0.05 (상승 시)
 * `Wage_Decay_Rate`: 0.02 (하락 시)
* **Startup Cost Shadow Index:** `Avg_Wage * 6` 기반의 가상 창업 비용 산출 로직 구현.

### 1.3. Central Bank (Government)
* **File:** `simulation/agents/government.py`
* **Action:** 테일러 준칙 2.0에 따른 목표 금리 계산.
* **Formula:** `Target_Rate = Real_GDP_Growth + Inflation + 0.5*(Inf - Target_Inf) + 0.5*(GDP_Gap)`
* **Logging:** 현재 금리와 테일러 준칙 제안 금리의 차이(`Gap`)를 기록하십시오.

---

## 2. Verification (Stage 1)
* **No Functional Change:** 기존 시뮬레이션의 경제 지표가 이 작업 전후로 변하지 않아야 합니다 (Shadow Mode이므로).
* **Log Integrity:** `logs/shadow_hand_stage1.csv` 파일에 모든 에이전트의 제안 가격과 시장 임금이 정확히 찍히는지 확인하십시오.

---

## Reference Documents
* `설계도_계약들/specs/phase24_invisible_hand_spec.md`
* `C:/Users/Gram Pro/.gemini/antigravity/brain/978849a0-0670-4a7e-ab62-e7dbb8f1f778/implementation_plan.md`

**Execute Shadow Mode.**
