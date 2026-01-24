# [AUDIT-ECONOMIC-V2] 경제적 무결성 및 누출 정밀 추적 보고서

## [발견된 누출 지점 리스트]

### 1. 상속 시스템의 부동소수점 절삭 누출 (Precision Leak)
*   **위치**: `simulation/systems/inheritance_manager.py` (Line 225 근처)
*   **현상**: `total_pennies = int(total_cash * 100)` 로직에서 소수점 셋째 자리 이하의 `total_cash`가 절삭되어 시스템에서 사라짐.
*   **영향**: `deceased.assets`가 10.005일 경우, 0.005가 증발함. 제로섬 게임에서 미세한 디플레이션 유발.

### 2. 거래 시스템의 '팬텀 택스' (Phantom Tax / Statistical Leak)
*   **위치**: `simulation/systems/transaction_processor.py` (Line 71, 107, 122)
*   **현상**:
    1. `SettlementSystem.transfer`를 통해 구매자->정부로 세금 자산이 실제로 이동함 (자산 이동 성공).
    2. 이후 호출되는 `government.collect_tax`는 내부적으로 `FinanceSystem.collect_corporate_tax`를 호출하나, `FinanceSystem`은 이를 Legacy 호출로 간주하여 `False`를 반환하고 경고 로그를 남김.
    3. 결과적으로 `Government` 객체의 자산(`assets`)은 증가하지만, 통계(`total_collected_tax`)는 증가하지 않음.
*   **영향**: 정부의 재정 상태표(Assets)와 손익계산서(Revenue Stats)의 불일치 발생.

### 3. 파산 청산 시 잔여 자산 소멸 (Residual Dust)
*   **위치**: `simulation/systems/lifecycle_manager.py`
*   **현상**: `firm.assets > 1e-6`인 경우 `_sub_assets`로 강제 소멸시키고 `total_money_destroyed`에 기록함.
*   **영향**: `total_money_destroyed`로 추적은 되나, 경제적으로는 정부로 귀속되거나 재분배되어야 할 자산이 물리적으로 파괴됨.

---

## [원자성 위반 코드 블록]

### 1. TransactionProcessor의 비원자적 송금 (Non-Atomic Transfers)
`simulation/systems/transaction_processor.py`의 Line 60-70 구간:

```python
# 현재 코드 구조
if settlement:
    # 1. 물품 대금 송금 (성공 가능성 높음)
    settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")

    if tax_amount > 0:
        # 2. 세금 송금 (별도 호출)
        # 만약 1번은 성공했으나, 그 사이 상태 변경 등으로 2번이 실패하면?
        # 구매자는 물건을 샀으나 세금을 내지 않은 상태가 됨 (탈세 버그).
        settlement.transfer(buyer, government, tax_amount, f"sales_tax:{tx.item_id}")
```

*   **증명**: `buyer.assets` 차감액은 `trade_value + tax_amount`이어야 하나, 두 번째 `transfer`가 실패할 경우 `trade_value`만 차감됨. `TransactionProcessor` 레벨에서는 롤백 메커니즘이 없음.

### 2. TransactionProcessor와 TaxAgency의 이중 책임 (Double Responsibility Risk)
```python
# 현재 코드
settlement.transfer(buyer, government, tax_amount, ...) # 자산 이동 1
government.collect_tax(tax_amount, ...) # 내부적으로 자산 이동 시도 가능성 (현재는 차단됨)
```
*   만약 `FinanceSystem.collect_corporate_tax`가 활성화된다면 이중 과세(Double Charge)가 발생함. 현재는 비활성화되어 '통계 누락'만 발생함.

---

## [해결을 위한 슈도코드]

### 1. TransactionProcessor 수정 (팬텀 택스 및 원자성 해결)

```python
# simulation/systems/transaction_processor.py

def execute(self, state):
    # ...
    # 1. 원자성 확보를 위해 총액 계산
    total_deduction = trade_value + tax_amount

    # 2. 사전 검증 (SettlementSystem이 하겠지만, 명시적으로)
    if buyer.assets < total_deduction:
        return # 거래 취소

    # 3. 송금 실행 (순차적 실행이되, 실패 시 처리 필요)
    # 가장 안전한 방법: Bundle Transfer 기능을 SettlementSystem에 추가하거나
    # 순차 실행 후 실패 시 보정. 여기서는 순차 실행 + 통계 수정 제안.

    if settlement:
        # 판매자에게 송금
        s1 = settlement.transfer(buyer, seller, trade_value, ...)
        if s1 and tax_amount > 0:
            # 세금 송금
            s2 = settlement.transfer(buyer, government, tax_amount, ...)
            if s2:
                # [FIX] collect_tax 대신 record_revenue 사용
                # 자산은 이미 이동했으므로 통계만 기록
                government.record_revenue(tax_amount, "sales_tax", buyer.id, current_time)
            else:
                # 세금 납부 실패 시? (심각한 오류, 롤백 필요하나 복잡함)
                # 최소한 로그 남김.
                logger.critical("Tax transfer failed after goods transfer!")
```

### 2. InheritanceManager 수정 (부동소수점 누출 해결)

```python
# simulation/systems/inheritance_manager.py

def process_death(...):
    # ...
    total_cash = deceased.assets # 예: 10.005

    # [FIX] 정수 변환 전 잔여물 계산
    total_pennies = int(total_cash * 100) # 1000 pennies
    distributed_cash = total_pennies / 100.0 # 10.00

    residual_dust = total_cash - distributed_cash # 0.005

    # 상속 로직 수행 (pennies 기준)
    # ...

    # [FIX] 잔여 먼지 처리 (마지막 상속자 혹은 정부에게 귀속)
    if residual_dust > 0:
        target = heirs[-1] if heirs else government
        settlement.transfer(deceased, target, residual_dust, "inheritance_dust_sweep")
```

### 3. LifecycleManager 수정 (파산 먼지 회수)

```python
# simulation/systems/lifecycle_manager.py

# [FIX] 파괴 대신 정부 귀속
if firm.assets > 0:
    # 1e-6 체크 제거하고 전액 정부로 이체
    settlement.transfer(firm, state.government, firm.assets, "liquidation_dust_sweep")
    state.government.record_revenue(firm.assets, "liquidation_dust", firm.id, state.time)
```
