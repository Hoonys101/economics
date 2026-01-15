아키텍처 설계 및 구현 지침에 따라 **WO-064: Banking Credit Engine** 구현을 위한 상세 명세서와 API 초안을 작성하겠습니다. 이번 작업은 현대 금융의 핵심인 '신용 창출(Credit Creation)' 기능을 시뮬레이션에 도입하는 것을 목표로 합니다.

먼저 `config.py`에 필요한 상수를 추가하고, 이어서 설계 명세서와 API 파일을 생성하겠습니다.

### 1. `config.py` 업데이트
지급준비율 상수를 추가합니다.

```python
# --- Phase 10: Central Bank & Monetary Policy (Updated for WO-064) ---
RESERVE_REQ_RATIO = 0.1         # 지급준비율 (10%) - 대출 실행 시 최소 보유 자산 기준
```

### 2. 상세 설계 명세서 작성
`설계도_계약들/specs/banking_credit_engine_spec.md` 파일을 생성합니다.

```markdown
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
- `check_solvency(government: Any)`: `run_tick` 종료 시점 또는 `LoanMarket`에서 호출하여 자산 양수 유지.

---

## 4. 예외 처리 및 방어 기제
- **Default Handling**: 대출자가 파산할 경우, 은행의 자산은 감소하지만 중앙은행이 다시 보전하여 시스템 붕괴를 막음 (Moral Hazard 발생 가능성 로그 기록).
- **Gold Standard Compatibility**: `config.GOLD_STANDARD_MODE`에 따라 신용 창출 기능을 On/Off 할 수 있어야 함.

---

## 5. 검증 계획 (Verification)
- **Test 1**: 은행 자산이 5,000일 때, 지급준비율 10% 하에서 10,000 대출이 승인되는지 확인 (성공해야 함).
- **Test 2**: 대출 승인 후 은행 자산이 음수가 되었을 때, `check_solvency` 호출 후 자산이 양수로 복구되고 통화량이 증가하는지 확인.
- **Golden Sample**: `tests/goldens/credit_creation_report.json`

---

## 💡 Mandatory Reporting for Jules
Jules는 구현 과정에서 다음 사항을 `communications/insights/`에 보고해야 합니다.
1. 신용 창출로 인한 통화량 팽창 속도가 인플레이션에 미치는 영향.
2. 은행의 마이너스 자산 발생 빈도 및 중앙은행 의존도.
```

### 3. API 초안 및 로직 스캐폴딩
`simulation/bank.py`에 반영될 핵심 변경 사항을 정의합니다. (Jules가 참고할 코드 가이드)

```python
# simulation/bank.py (Updated Fragments)

def grant_loan(self, borrower_id: int, amount: float, ...) -> Optional[str]:
    # ... 생략 ...
    
    # 1. 지급준비율 및 신용 창출 로직
    is_gold_standard = self._get_config("GOLD_STANDARD_MODE", False)
    reserve_ratio = self._get_config("RESERVE_REQ_RATIO", 0.1)
    
    if is_gold_standard:
        # 금본위제: 100% 지급준비금 (현금 보유량 내에서만 대출)
        if self.assets < amount:
            return None
    else:
        # 현대 금융: 신용 창출 (지급준비율 만족 시 승인)
        total_liabilities = self.get_total_deposits() + amount
        required_reserves = total_liabilities * reserve_ratio
        
        if self.assets < required_reserves:
            logger.warning(f"LOAN_DENIED | Reserve ratio not met. Required: {required_reserves}")
            return None
            
        if self.assets < amount:
            logger.info(f"CREDIT_CREATION | Bank {self.id} creating credit: {amount}. Current Assets: {self.assets}")

    # 2. 대출 실행 (기존 로직 유지)
    # ...
    return loan_id

def check_solvency(self, government: Any):
    """중앙은행의 최종 대부자(Lender of Last Resort) 역할 수행"""
    if self.assets < 0:
        injection = abs(self.assets) + 1000.0
        self.assets += injection
        if hasattr(government, 'total_money_issued'):
            government.total_money_issued += injection
        
        logger.warning(f"LENDER_OF_LAST_RESORT | Bank {self.id} saved by Government. Injected: {injection}")
```

---
**다음 단계:**
팀장(Antigravity)님, 위 설계 명세와 API 초안을 기반으로 Jules에게 구현을 지시하시겠습니까? `config.py` 수정과 `spec.md` 생성을 바로 진행할 수 있습니다. (확인 후 도구 호출 예정)
