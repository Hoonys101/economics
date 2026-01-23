# Audit Report: Economic Integrity & Leak Analysis

## [발견된 누출 지점 리스트]

1.  **Phantom Tax Revenue (통계 누락)**
    *   **위치:** `simulation/systems/transaction_processor.py`, `simulation/systems/tax_agency.py`
    *   **문제:** `TransactionProcessor`가 `SettlementSystem`을 통해 세금을 정부로 이체하지만, 이후 호출되는 `government.collect_tax` -> `tax_agency.collect_tax` -> `finance_system.collect_corporate_tax` 체인에서 `FinanceSystem`이 레거시 경고와 함께 `False`를 반환합니다. 이로 인해 `TaxAgency`가 통계 집계를 중단하여, 실제 자산은 정부로 이동했으나 `total_collected_tax` 및 재정 수입 통계에는 0으로 기록됩니다.
    *   **영향:** 정부 예산 수립(Smart Leviathan 등)이 잘못된 수입 데이터에 기반하게 됨.

2.  **Reflux Alchemy (M2 인플레이션)**
    *   **위치:** `simulation/systems/lifecycle_manager.py`
    *   **문제:** 에이전트 청산 시 `inventory`의 *가치(Value)*를 계산하여 `reflux_system.capture(value)`를 호출합니다. 만약 `RefluxSystem`의 잔고가 M2(통화량)에 포함된다면, 실물(재고)이 소멸되면서 동일 가치의 현금이 `RefluxSystem`에 생성되는 결과가 됩니다. 이는 판매되지 않은 재고를 현금화해주는 꼴이 되어 M2를 인위적으로 팽창시킵니다.
    *   **영향:** 제로섬 위반. 실물 경기가 침체되어도 파산 시 통화량이 늘어나는 기현상 발생.

3.  **Inheritance Dust (부동 소수점 잔차)**
    *   **위치:** `simulation/systems/inheritance_manager.py` (Line ~225)
    *   **문제:** `cash_share = round(total_cash / num_heirs, 2)` 로직을 사용합니다. `total_cash`가 10.00이고 3명이 상속받을 경우 3.33이 되며 총 9.99가 분배되어 0.01이 남습니다(이는 잔차 처리 로직이 회수함). 그러나 반대로 반올림이 *올림* 처리되는 경우(예: 정밀도 문제로 x.xx5 -> x.xx+1), 분배 총액이 보유 자산을 초과하여 `SettlementSystem`에서 `InsufficientFundsError`를 유발하거나 트랜잭션이 실패할 수 있습니다.
    *   **영향:** 상속 프로세스 불안정 및 미세한 자산 증발/생성.

4.  **Dangerous Fallback Logic (원자성 위반 위험)**
    *   **위치:** `simulation/systems/transaction_processor.py`, `simulation/systems/inheritance_manager.py`
    *   **문제:** `if settlement: ... else: ...` 블록에서 `else` 부분은 `buyer.withdraw()`와 `government.deposit()`을 개별적으로 호출합니다. `withdraw` 성공 후 `deposit` 실패(예외 발생 등) 시 자산이 소멸됩니다. 현재 시스템은 `SettlementSystem`이 필수이므로 이 레거시 코드는 삭제되어야 합니다.

---

## [원자성 위반 코드 블록]

### 1. TransactionProcessor.py (Manual Fallback)
```python
# simulation/systems/transaction_processor.py

if settlement:
    settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")
    if tax_amount > 0:
        settlement.transfer(buyer, government, tax_amount, f"sales_tax:{tx.item_id}")
else:
    # [VIOLATION]: Non-atomic operations.
    # If logic crashes after withdraw but before deposits, money is destroyed.
    buyer.withdraw(trade_value + tax_amount)
    seller.deposit(trade_value)
    government.deposit(tax_amount)
```

### 2. InheritanceManager.py (Floating Point Division)
```python
# simulation/systems/inheritance_manager.py

# [VIOLATION]: Rounding can lead to sum(shares) > total_cash
cash_share = round(total_cash / num_heirs, 2)
total_distributed = 0.0

for heir in heirs:
    if settlement:
        # If cash_share * num_heirs > deceased.assets due to rounding up,
        # the last transfer implies creating money or throws InsufficientFunds.
        settlement.transfer(deceased, heir, cash_share, ...)
```

---

## [해결을 위한 슈도코드]

### 1. Tax Stats Fix (Phantom Revenue)
세금 *이체*와 *기록*을 분리합니다. `TaxAgency`는 이체를 시도하지 않고 기록만 수행하는 모드를 지원해야 합니다.

```python
# simulation/systems/tax_agency.py

def record_tax_revenue(self, government, amount, tax_type):
    """
    Records tax revenue statistics WITHOUT attempting asset transfer.
    Must be called AFTER a successful SettlementSystem transfer.
    """
    government.total_collected_tax += amount
    government.revenue_this_tick += amount
    government.tax_revenue[tax_type] = government.tax_revenue.get(tax_type, 0.0) + amount
    # Log success...

# simulation/systems/transaction_processor.py

if settlement:
    # 1. Execute Transfer
    settlement.transfer(buyer, government, tax_amount, f"tax:{tx.transaction_type}")

    # 2. Record Statistics (Safe)
    government.tax_agency.record_tax_revenue(government, tax_amount, f"tax_{tx.transaction_type}")
```

### 2. Reflux Fix (M2 Inflation)
재고 가치를 '화폐'로 변환하지 않고, '엔트로피 손실'로만 기록합니다.

```python
# simulation/systems/lifecycle_manager.py

if state.reflux_system:
    inv_value = self._calculate_inventory_value(firm.inventory, state.markets)
    # Do NOT capture() as money. Use a stat-only method.
    if inv_value > 0:
        state.reflux_system.record_value_loss(inv_value, "liquidation_inventory")
        # Or if capture() implies adding to balance, ensure Reflux Balance is EXCLUDED from M2 calculation.
```

### 3. Inheritance Fix (Integer Distribution)
페니(Penny) 단위로 정수 연산을 수행하여 잔차를 분배합니다.

```python
# simulation/systems/inheritance_manager.py

# Convert to smallest unit (cents) to avoid float errors
total_cents = int(deceased.assets * 100)
base_share_cents = total_cents // num_heirs
remainder_cents = total_cents % num_heirs

for i, heir in enumerate(heirs):
    amount_cents = base_share_cents
    if i < remainder_cents:
        amount_cents += 1 # Distribute dust one by one

    amount = amount_cents / 100.0

    settlement.transfer(deceased, heir, amount, "inheritance_share")
```
