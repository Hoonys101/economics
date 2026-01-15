# Spec: WO-065 Monetary Integrity & Suture (통화 정합성 및 봉합)

## 1. 개요 (Overview)
- **목표**: 상속, 경제적 충격(Shock), 자산 청산 과정에서 발생하는 모든 통화의 이동과 소멸을 추적하여 `Government`의 통화 장부(`total_money_issued`, `total_money_destroyed`)와 실제 유통 통화량의 정합성을 100% 일치시킴.
- **배경**: 현재 Tick 600 쇼크 시 발생하는 자산 소멸이 장부에 기록되지 않고 있으며, 상속 시 은행 예금(Deposits)이 누락되는 정합성 결함이 발견됨.

## 2. 상세 로직 및 알고리즘 (Pseudo-code)

### 2.1 InheritanceManager: 은행 예금 상속 (Suture 1)
- **로직**:
    1. **예금 조회**: `simulation.bank.get_deposit_balance(deceased.id)`를 통해 고인의 예금 총액 파악.
    2. **가치 평가**: `total_wealth = cash + real_estate + stock + deceased_deposits`.
    3. **상속인 존재 시**:
        - `simulation.bank.withdraw(deceased.id, deceased_deposits)`로 고인 계좌 정리.
        - `simulation.bank.deposit(heir.id, share_amount)`로 상속인들에게 분할 예치.
    4. **상속인 부재 시 (Escheatment)**:
        - `simulation.bank.withdraw(deceased.id, deceased_deposits)` 수행.
        - `simulation.bank.assets -= deceased_deposits` (은행 지준금에서 실제 인출).
        - `simulation.government.collect_tax(deceased_deposits, "escheatment", deceased.id, simulation.time)` 호출하여 국고 귀속 및 장부 기록.

### 2.2 Engine: Tick 600 자산 소멸 기록 (Suture 2)
- **로직**:
    - `simulation/engine.py`의 `run_tick` 내 쇼크 발생 블록 수정.
    ```python
    if self.time == 600:
        total_lost = 0.0
        for h in self.households:
            loss = h.assets * 0.5
            h.assets -= loss
            total_lost += loss
        # 장부 봉합 (Suture)
        if hasattr(self.government, 'total_money_destroyed'):
            self.government.total_money_destroyed += total_lost
    ```

### 2.3 Escheatment(국고 귀속) 프로세스 강화
- **원칙**: 모든 연고 없는 자산(가계 사망, 기업 파산 시 남은 자산)은 반드시 `Government.collect_tax`를 통해 국고로 귀속되어야 함.
- **기업 청산**: 주주가 없는 상태에서 청산되는 기업의 잔여 자산은 전액 국고 귀속 처리 (`process_liquidation` 로직 보강).

## 3. 인터페이스 계약 (Interface)
- **`IInheritanceManager.process_death`**: 고인의 모든 금융 자산(현금 + 예금)을 포함하도록 시그니처 또는 내부 구현 확장.
- **`IBank.transfer_deposit`**: (선택 사항) 계좌 간 직접 이체 메서드 추가 시 더 효율적.

## 4. 검증 계획 (Verification)
- **Initial Verification**: `python scripts/failure_diagnosis.py`를 실행하여 현재 발생하는 Delta 수치를 기록.
- **Final Verification**: 수정 후 `test_monetary_integrity.py`를 작성하여 대규모 상속 및 쇼크 발생 후 Delta가 0에 수렴하는지 확인.

---
**[Reporting Instruction]**: Jules는 본 명세 구현 중 통화가 장부 밖으로 새어 나가는 지점(Leakage)을 추가 발견할 경우 즉시 `communications/insights/`에 보고하십시오.
