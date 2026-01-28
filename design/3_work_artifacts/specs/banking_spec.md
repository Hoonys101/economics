# W-1 Specification: Phase 3 - Banking & Monetary Policy

**모듈**: Phase 3 - Financial System  
**상태**: 🟡 Drafting (설계 진행 중)  
**작성자**: Architect (Antigravity)  
**대상 파일**: `config.py`, `simulation/bank.py`, `simulation/core_agents.py`, `simulation/engine.py`

---

## 1. 개요 (Overview)
시뮬레이션 경제에 **"금융(Finance)"**을 도입한다.
가계와 기업은 자금이 부족할 때 대출을 받을 수 있으며, 여유 자금을 예치하여 이자를 받을 수 있다(자금 선순환). 
**중앙은행(Central Bank)**은 기준 금리를 조절하여 과열된 경기를 식히거나 침체된 경기를 부양한다.

## 2. 아키텍처 및 데이터 모델

### 2.1 Central Bank (Government Role Expansion)
*   **역할**: 기준 금리(`BASE_ANNUAL_RATE`) 결정 및 통화 정책 수행.
*   **로직**:
    *   인플레이션(CPI 상승률), 실업률 등을 감안하여 연 4회(분기별) 또는 매 틱 금리 조정.

### 2.2 Commercial Bank (New System Agent)
*   **역할**: 예금 수취(Deposit) 및 대출 실행(Loan). **자금 중개 기능(Financial Intermediation)** 수행.
*   **속성**:
    *   `reserves` (float): 지급준비금.
    *   `deposits` (List[Deposit]): 고객 예금 계좌.
    *   `loans` (List[Loan]): 실행된 대출 목록.
*   **이자율 구조**:
    *   `loan_rate` = `BASE_RATE` + `CREDIT_SPREAD`
    *   `deposit_rate` = `loan_rate` - `BANK_MARGIN`

### 2.3 Financial Instruments (DTOs)
```python
@dataclass
class Loan:
    borrower_id: int
    principal: float       # 원금
    remaining_balance: float # 잔액
    annual_interest_rate: float # 연이율
    term_ticks: int        # 만기 (틱)
    start_tick: int        # 대출 실행 틱

@dataclass
class Deposit:
    depositor_id: int
    amount: float          # 예치금
    annual_interest_rate: float # 연이율
```

---

## 3. 세부 구현 명세

### 3.1 Config 수정 (Critical Refinement 1: Interest Rate Scaling)
```python
# --- Banking & Time Scale ---
TICKS_PER_YEAR = 100.0          # 1년 = 100틱 (모든 이자 계산의 기준)
INITIAL_BASE_ANNUAL_RATE = 0.05 # 연 5% (틱당 금리가 아님!)

# 파생 상수 (계산용)
# TICK_INTEREST_RATE = BASE_ANNUAL_RATE / TICKS_PER_YEAR

LOAN_DEFAULT_TERM = 50          # 6개월 (50틱)
CREDIT_SPREAD_BASE = 0.02       # 연 2% 가산금리
BANK_MARGIN = 0.02              # 예대마진 (연 2%)
```

### 3.2 Bank Class Logic (`simulation/bank.py`) (Critical Refinement 2: The "Link")
*   **`grant_loan(agent, amount)`**:
    *   대출 심사 (LTV, DTI 등).
    *   `Loan` 생성.
*   **`deposit(agent, amount)`**:
    *   `Deposit` 생성. `agent.assets` 차감, `bank.reserves` 증가.
*   **`run_tick()` (매 틱 실행)**:
    1.  **이자 수취 (Collect Interest)**: 모든 대출자로부터 이자 걷기. 
        *   `tick_payment = (balance * annual_rate) / TICKS_PER_YEAR`
    2.  **이자 지급 (Pay Interest)**: 모든 예금주에게 이자 지급.
        *   `tick_interest = (amount * annual_rate) / TICKS_PER_YEAR`
        *   `bank.reserves` 차감, `agent.assets` 증가 (유동성 공급).
    3.  **원금 상환**: 만기 시 혹은 분할 상환 처리.

### 3.3 AI Awareness Logic (Critical Refinement 3: Debt Perception)
*   **HouseholdAI / FirmAI State Update**:
    *   `get_state()` 메서드에 반드시 부채 관련 Feature를 추가해야 함.
    *   `debt_ratio` = `total_liabilities` / `total_assets` (부채 비율)
    *   `interest_burden` = `tick_interest_payment` / `tick_income` (이자 상환 부담)
*   **행동 변화**:
    *   `debt_ratio`가 높으면 소비/투자(Action Aggressiveness)를 줄이도록 학습되거나, Rule-based 로직으로 강제 긴축(Austerity) 발동.

### 3.4 Integration (`engine.py`)
*   **`run_tick`**:
    1.  `bank.run_tick()` 호출 (이자 수취/지급, 자금 순환).
    2.  `government.update_monetary_policy()` 호출.

---

## 4. 검증 계획 (Verification)
1.  **금리 스케일 검증**: 100틱(1년) 동안 이자가 연이율(5%)만큼 발생하는지 확인. (틱당 5% 폭탄 금지)
2.  **자금 순환 검증**: 대출 이자로 사라진 돈이 예금 이자로 다시 시장에 풀리는지 확인 (M2 통화량 모니터링).
3.  **AI 반응 검증**: 대출을 받은 AI가 부채 비율이 높아지면 소비를 줄이는지 확인.

---

## 5. 작업 체크리스트
- [ ] `config.py`: `TICKS_PER_YEAR`, `ANNUAL_RATE` 도입
- [ ] `Loan`, `Deposit` DTO 정의
- [ ] `Bank` 클래스: 대출(Loan) 및 **예금(Deposit)** 기능 구현
- [ ] `government.py`: 통화 정책 로직
- [ ] **AI State Update**: `debt_ratio`, `interest_burden` 추가 (필수)
- [ ] 검증 스크립트: `verify_banking.py`
