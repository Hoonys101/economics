# [AUDIT-ECONOMIC-V2] 경제적 무결성 및 누출 정밀 추적

본 보고서는 시뮬레이션 내 자산의 생성, 소멸, 이동 과정에서 발생하는 무결성 위반 사항을 정밀 진단한 결과입니다.

## 1. 발견된 누출 지점 리스트 (Leak Points)

| 중요도 | 컴포넌트 | 파일 위치 | 현상 |
|:---:|:---:|:---|:---|
| **High** | **Transaction Integrity** | `simulation/systems/transaction_processor.py` | 거래(Trade)와 세금(Tax)이 별도의 트랜잭션으로 처리되어, 거래는 성공했으나 세금 징수가 실패할 경우 세수 누락 발생 (원자성 위반). |
| **Medium** | **Inheritance Logic** | `simulation/systems/transaction_processor.py` | 상속 분배 시 부동소수점 연산 후 남은 자투리 금액(Dust)이 마지막 상속자에게 전달되지만, **전송 실패** 또는 **Rounding 오차**로 인해 사망한 에이전트에게 잔액이 남을 경우, 에이전트 삭제와 함께 자산 증발. |
| **Medium** | **Bankruptcy Logic** | `simulation/systems/lifecycle_manager.py` | 기업(Firm) 파산 시에는 `liquidation_rounding_cleanup`이 존재하나, 가계(Household) 사망/파산 시에는 잔액 청소 로직이 부재함. 상속 처리 후 남은 미세한 잔액이 시스템에서 소멸됨. |
| **Low** | **Money Supply Tracking** | `simulation/agents/government.py` | 국채 발행(Bond Issuance)을 통한 자금 조달 시 `lender_of_last_resort` 타입이 아니면 `total_money_issued` 통계에 즉시 반영되지 않을 가능성 존재 (통계 불일치). |

---

## 2. 원자성 위반 코드 블록 (Atomicity Violations)

### A. 거래와 세금의 분리 (Transaction Processor)

`simulation/systems/transaction_processor.py`의 `execute` 메서드 내 로직을 보면, 물품 대금 결제(`settlement.transfer`)가 성공한 **후**에 세금 징수(`government.collect_tax`)를 시도합니다.

```python
# simulation/systems/transaction_processor.py (Lines ~60-64)

            elif tx.transaction_type == "goods":
                # Goods: Apply Sales Tax
                tax_amount = trade_value * sales_tax_rate

                # ... (Solvency Check 생략)

                # 1. 물품 대금 이전 (성공 시 True)
                success = settlement.transfer(buyer, seller, trade_value, f"goods_trade:{tx.item_id}")

                # 2. 세금 징수 (별도 트랜잭션)
                if success and tax_amount > 0:
                    # 만약 buyer의 잔고가 (trade_value + tax_amount)보다 적었다면,
                    # 위 transfer로 잔고가 소진되어 아래 collect_tax는 실패함.
                    # 결과: 물건은 샀지만 세금은 내지 않음 (Tax Evasion).
                    government.collect_tax(tax_amount, f"sales_tax_{tx.transaction_type}", buyer, current_time)
```

**수학적 증명:**
- 초기 상태: Buyer=$100, Seller=$0, Gov=$0. 가격=$100, 세금=$5.
- 의도: 거래 불가 (잔고 부족 $100 < $105) 혹은 부분 결제?
- 실제 동작:
    1. `transfer(100)` -> 성공. Buyer=$0, Seller=$100.
    2. `collect_tax(5)` -> 실패 (잔고 $0). Gov=$0.
- 최종 상태: Buyer=$0, Seller=$100, Gov=$0. (총합 $100 보존).
- **무결성 위반:** 세법 상 $5의 세금이 징수되어야 하나 누락됨. 시스템 내 총량은 보존되지만, "거래=가격+세금"이라는 원자적 규칙이 깨짐.

### B. 상속 분배의 미세 누출 (Inheritance Dust)

`transaction_processor.py` 내 상속 로직에서 마지막 상속자에게 잔액을 몰아주지만, 전송 실패 시 처리가 미흡합니다.

```python
# simulation/systems/transaction_processor.py

                    # ...
                    remaining_amount = total_cash - distributed_sum
                    if remaining_amount > 0:
                        # 여기서 전송 실패 시(예: 최소 전송 단위 미만 등), remaining_amount는 buyer(사망자)에게 남음.
                        if not settlement.transfer(buyer, last_heir, remaining_amount, "inheritance_distribution_final"):
                            all_success = False
```

이후 `LifecycleManager`는 사망한 에이전트를 `state.households` 리스트에서 제거합니다. 이때 사망자 계좌에 남은 `remaining_amount`는 별도의 회수 절차(Escheatment to Gov)가 없다면 메모리 상에서만 존재하다가 GC(Garbage Collection)되거나 무시되어 **경제 시스템 밖으로 증발**합니다.

---

## 3. 해결을 위한 슈도코드 (Pseudocode Solutions)

### A. 원자적 거래 실행 (Atomic Execution)

`SettlementSystem`에 "복수 트랜잭션 원자적 실행" 기능을 추가하거나, `TransactionProcessor`에서 **가조회(Pre-check)** 후 실행해야 합니다.

```python
# [Solution] TransactionProcessor Fix

def process_goods_transaction(buyer, seller, trade_value, tax_amount, government):
    total_required = trade_value + tax_amount

    # 1. 사전 검증 (Pre-check)
    if buyer.assets < total_required:
        # 거래 전면 거부 (Atomic Fail)
        return False

    # 2. 순차 실행 (이미 잔고 확인했으므로 성공 보장 가능, 단 동시성 이슈 없을 시)
    # 더 안전하게는 settlement.transfer_batch() 등을 구현
    success_trade = settlement.transfer(buyer, seller, trade_value, "goods_trade")
    if success_trade:
        success_tax = government.collect_tax(tax_amount, "sales_tax", buyer)
        if not success_tax:
            # 매우 드문 경우(동시성 등) 실패 시 롤백 필요
            # settlement.transfer(seller, buyer, trade_value, "rollback_goods")
            # Log Critical Error
            pass
    return True
```

### B. 사망자/파산자 잔액 청소 (Dust Cleanup)

`LifecycleManager`에서 에이전트를 제거하기 직전, 반드시 잔액을 0으로 만들어야 합니다.

```python
# [Solution] LifecycleManager Fix

def _handle_agent_liquidation(self, state):
    # ... (기존 상속 처리) ...

    # Household Liquidation Cleanup
    for household in inactive_households:
        # 1. 상속/파산 처리 후 잔액 확인
        remaining_dust = household.assets

        if remaining_dust > 0:
            # 2. 정부로 강제 귀속 (Escheatment)
            # settlement_system이 0.000001이라도 전송 가능해야 함
            self.settlement_system.transfer(
                household,
                state.government,
                remaining_dust,
                "liquidation_cleanup_household"
            )

        # 3. Double Check & Destroy (만약 정부 전송도 실패하면 강제 소각 기록)
        if household.assets > 0:
             self.settlement_system.record_destruction(household.assets, "force_clear")
             household._assets = 0.0 # 강제 초기화

        # 4. 리스트에서 제거
        state.households.remove(household)
```

### C. Gery Pattern 검증 결과
- `simulation/core_agents.py`에서 발견된 `self._econ_state.assets += amount`는 `Household` 클래스의 내부 메서드 `_add_assets` 구현체로 확인되었습니다. 이는 외부에서 직접 호출되지 않고 `SettlementSystem` 등을 통해 간접 호출되므로 **직접적인 누출 지점이 아님**을 확인했습니다.