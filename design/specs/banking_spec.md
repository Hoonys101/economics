# W-1 Specification: Phase 3 - Banking & Monetary Policy

**모듈**: Phase 3 - Financial System  
**상태**: 🟡 Drafting (설계 진행 중)  
**작성자**: Architect (Antigravity)  
**대상 파일**: `config.py`, `simulation/bank.py`, `simulation/core_agents.py`, `simulation/engine.py`

---

## 1. 개요 (Overview)
시뮬레이션 경제에 **"금융(Finance)"**을 도입한다.
가계와 기업은 자금이 부족할 때 **대출(Loan)**을 받을 수 있으며, **중앙은행(Central Bank/Government)**은 기준 금리를 조절하여 과열된 경기를 식히거나 침체된 경기를 부양한다.

## 2. 아키텍처 및 데이터 모델

### 2.1 Central Bank (Government Role Expansion)
*   **역할**: 기준 금리(`BASE_INTEREST_RATE`) 결정.
*   **로직**:
    *   인플레이션(CPI 상승률)이 목표치보다 높으면 -> 금리 인상.
    *   실업률이 높거나 경기가 침체되면 -> 금리 인하.

### 2.2 Commercial Bank (New System Agent)
*   **역할**: 예금 수취 및 대출 실행. (현재는 단일 은행 `Bank`로 추상화)
*   **속성**:
    *   `reserves` (float): 지급준비금.
    *   `loans` (List[Loan]): 실행된 대출 목록.
*   **대출 상품**:
    *   `interest_rate` = `BASE_INTEREST_RATE` + Spread (신용도에 따라 차등).
    *   `term` (ticks): 만기.

### 2.3 Loan (DTO)
```python
@dataclass
class Loan:
    borrower_id: int
    principal: float    # 원금
    remaining_balance: float # 잔액
    interest_rate: float # 이자율 (틱당)
    term_remaining: int # 남은 틱
```

---

## 3. 세부 구현 명세

### 3.1 Config 추가 (`config.py`)
```python
# --- Banking ---
INITIAL_BASE_INTEREST_RATE = 0.05   # 틱당 5% (가정)
MAX_INTEREST_RATE = 0.20
MIN_INTEREST_RATE = 0.01

LOAN_DEFAULT_TERM = 20              # 20틱 만기
CREDIT_SPREAD_BASE = 0.02           # 기본 가산금리
```

### 3.2 Bank Class (`simulation/bank.py`)
*   **`grant_loan(agent, amount)`**:
    *   대출 심사 (LTV, DTI 등 간소화: 자산 대비 50% 한도).
    *   성공 시 `agent.assets += amount`, `agent.liabilities += amount`.
    *   `Loan` 객체 생성 및 리스트 추가.
*   **`collect_payments()`**:
    *   매 틱 호출.
    *   이자 = `remaining_balance * interest_rate`.
    *   원금 상환 = `principal / term`.
    *   Agent 자산에서 차감. 못 갚으면 파산(Bankruptcy) 절차 트리거.

### 3.3 Integration (`engine.py`)
*   **`run_tick`**:
    1.  `bank.collect_payments()` 호출 (선이자 공제).
    2.  `government.update_monetary_policy()` 호출 (금리 조정).

### 3.4 Agent Adaptation
*   **`Firm`**: 적자 시 해고 대신 대출을 받아 버티는 전략 추가. (투자용 대출)
*   **`Household`**: 생존 욕구 충족을 위해 대출을 받는 전략 추가. (생계형 대출)

---

## 4. 검증 계획
1.  **대출 실행**: 에이전트 자산 증가 및 부채 기록 확인.
2.  **이자 상환**: 매 틱 자산 감소 확인.
3.  **금리 변동**: 인플레이션 발생 시 중앙은행이 금리를 올리는지 확인.

---

## 5. 작업 체크리스트
- [ ] `config.py` 상수 추가
- [ ] `Loan` DTO 정의 (`dtos.py` or `models.py`)
- [ ] `Bank` 클래스 구현 (`simulation/bank.py`)
- [ ] `Government`에 금리 결정 로직 추가
- [ ] `Firm`/`Household`에 대출 요청 로직(Rule-based) 추가
- [ ] `Engine` 연동
