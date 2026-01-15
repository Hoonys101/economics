# W-1 Specification: WO-064 - Banking Credit Engine (Credit Creation)

**모듈**: Financial System (Bank)
**상태**: 🟢 Approved (Ready for Implementation)
**작성자**: Scribe (Gemini CLI)
**대상 파일**: `simulation/bank.py`, `config.py`

---

## 1. 개요 (Overview)
기본적인 '풀 리저브(Full Reserve)' 모델에서 벗어나, 지급준비금 제도에 기반한 **'신용 창출(Credit Creation)'** 엔진을 구현한다. 은행은 보유한 현금(Assets)보다 더 많은 대출을 실행할 수 있으며, 이 과정에서 발생하는 일시적인 유동성 부족은 중앙은행(Lender of Last Resort)의 발권력을 통해 해결한다.

## 2. 핵심 로직 (Pseudo-code)

### 2.1 신용 창출 대출 승인 (`grant_loan`)
1.  **입력**: `borrower_id`, `amount`, `term_ticks`, `interest_rate`
2.  **지급준비율 검증 (Reserve Requirement Check)**:
    - `required_reserves` = (`current_total_deposits` + `amount`) * `RESERVE_REQ_RATIO`
    - 만약 `self.assets` < `required_reserves` 이면 대출 거절 (유동성 방어).
    - 단, `GOLD_STANDARD_MODE`가 `True`인 경우 기존처럼 `self.assets < amount`를 체크함.
3.  **신용 창출 실행**:
    - 은행의 `assets`가 `amount`보다 적더라도 위 조건을 만족하면 대출 승인.
    - `CREDIT_CREATION` 로그 출력: `[CREDIT_CREATION] Bank {id} created {amount} credit. Reserves: {assets}`
4.  **반환**: `loan_id`

### 2.2 중앙은행 보전 로직 (`check_solvency`)
1.  **목적**: 대출 실행으로 인해 은행의 실물 자산(`assets`)이 마이너스가 된 경우, 중앙은행이 화폐를 발행하여 보전함.
2.  **수행**:
    - 만약 `self.assets < 0`:
        - `injection_amount = abs(self.assets) + 1000.0` (여유 자금 포함)
        - `self.assets += injection_amount`
        - `government.total_money_issued += injection_amount`
        - `LENDER_OF_LAST_RESORT` 경고 로그 출력.

---

## 3. 인터페이스 명세 (DTO/API)

### 3.1 수정된 Bank 메서드
- `grant_loan(...) -> Optional[str]`: 지급준비율 기반 로직으로 변경.
- `check_solvency(government: Any)`: 자산 양수 유지 보전 로직 강화.

---

## 4. 예외 처리 및 방어 기제
- **Default Handling**: 대출자가 파산할 경우, 은행의 자산은 감소하지만 중앙은행이 다시 보전하여 시스템 붕괴를 막음.
- **Gold Standard Compatibility**: `config.GOLD_STANDARD_MODE`에 따라 신용 창출 기능을 On/Off 할 수 있어야 함.

---

## 5. 검증 계획 (Verification)
- **Test 1**: 은행 자산이 5,000일 때, 지급준비율 10% 하에서 10,000 대출이 승인되는지 확인.
- **Test 2**: 대출 승인 후 은행 자산이 음수가 되었을 때, `check_solvency` 호출 후 자산이 양수로 복구되고 통화량이 증가하는지 확인.

---

### [Mandatory Reporting]
**Jules Checkpoint**:
1. 신용 창출로 인한 통화량 팽창 속도가 인플레이션에 미치는 영향 보고.
2. 은행의 마이너스 자산 발생 빈도 및 중앙은행 의존도 보고.
