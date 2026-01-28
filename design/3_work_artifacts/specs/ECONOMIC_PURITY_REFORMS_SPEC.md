# Spec: Settlement System & Economic Purity (WO-112)

**Objective**: 이 문서는 기술부채 `TD-101(그림자 경제)`와 `TD-102(잔차 증발)`를 근본적으로 해결하기 위한 `SettlementSystem`의 설계 명세를 정의합니다. `audit_economic_v2.md`에서 지적된 모든 자산 무결성 위반 사항을 해소하고, 시뮬레이션 내 모든 가치 이동의 원자성(Atomicity)과 제로섬(Zero-Sum) 원칙을 강제하는 것을 목표로 합니다.

---

## 1. Core Principles & Architectural Mandates

1.  **Single Source of Truth (SSoT)**: 모든 자산(cash)의 상태 변경은 오직 `SettlementSystem`을 통해서만 수행되어야 합니다.
2.  **Private Asset Attributes**: 모든 에이전트(`Household`, `Firm` 등)의 `assets` 속성은 `_assets`로 변경되어 **private**으로 취급됩니다. 외부에서는 오직 읽기 전용(`@property`)으로만 접근할 수 있습니다. `agent.assets += 100`과 같은 직접적인 수정은 원천적으로 금지됩니다.
3.  **Atomic Transfers**: 모든 자산 이전은 '차변(Debit)'과 '대변(Credit)'이 하나의 트랜잭션으로 묶여 실패 시 롤백을 보장하는 원자적 연산으로 처리됩니다.
4.  **Unidirectional Dependency**: `SettlementSystem`은 에이전트 클래스에 의해 직접 임포트되지 않습니다. 대신, `SimulationState` DTO를 통해 컨텍스트로 주입되어 순환 참조를 방지합니다.

---

## 2. API & Interface Definition (`simulation/finance/api.py`)

### 2.1. `IFinancialEntity` (Protocol)
모든 경제 주체(에이전트)가 따라야 할 금융 인터페이스입니다.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IFinancialEntity(Protocol):
    """
    자산을 소유하고 거래할 수 있는 모든 경제 주체에 대한 인터페이스.
    자산은 읽기 전용이며, 수정은 SettlementSystem을 통해서만 가능하다.
    """
    id: int

    @property
    def assets(self) -> float:
        """현재 보유 자산을 반환합니다. (Read-Only)"""
        ...

    def _add_assets(self, amount: float) -> None:
        """
        [PROTECTED] SettlementSystem만이 호출해야 하는 자산 증가 메서드.
        """
        ...

    def _sub_assets(self, amount: float) -> None:
        """
        [PROTECTED] SettlementSystem만이 호출해야 하는 자산 감소 메서드.
        """
        ...
```

### 2.2. `ISettlementSystem` (Interface)
새로운 정산 시스템의 추상 인터페이스입니다.

```python
from abc import ABC, abstractmethod
from typing import Optional

from .api import IFinancialEntity

class ISettlementSystem(ABC):
    """
    모든 자산 이전을 원자적으로 처리하는 정산 시스템의 인터페이스.
    """

    @abstractmethod
    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[dict] = None,
        credit_context: Optional[dict] = None
    ) -> bool:
        """
        한 에이전트에서 다른 에이전트로 자산을 이전합니다.

        Args:
            debit_agent: 차변 계좌 (돈을 보내는 주체).
            credit_agent: 대변 계좌 (돈을 받는 주체).
            amount: 이전할 금액.
            memo: 거래 기록을 위한 메모.

        Returns:
            거래 성공 여부.
        """
        ...
```

---

## 3. `SettlementSystem` Detailed Design

**위치**: `simulation/systems/settlement_system.py`

이 클래스는 `ISettlementSystem`을 구현하며, 모든 자산 이동의 중앙 허브 역할을 합니다.

### 3.1. 로직 단계 (Pseudo-code)

```python
class SettlementSystem(ISettlementSystem):
    def __init__(self, logger):
        self.logger = logger
        # self.transaction_log = ... # (Optional) 원장 시스템

    def transfer(self, debit_agent, credit_agent, amount, memo) -> bool:
        # 1. 유효성 검사 (Pre-condition)
        if amount <= 0:
            self.logger.warning(f"Invalid transfer amount: {amount}")
            return False
        
        if debit_agent.id == credit_agent.id:
            self.logger.warning(f"Self-transfer is not allowed: Agent {debit_agent.id}")
            return False

        # 2. 지불 능력 확인 (Solvency Check)
        if debit_agent.assets < amount:
            self.logger.error(
                f"INSUFFICIENT_FUNDS | Agent {debit_agent.id} "
                f"has {debit_agent.assets} but needs {amount} for '{memo}'"
            )
            # 여기에 파산 처리 로직을 트리거할 수 있음
            return False

        # 3. 원자적 이전 (Atomic Operation)
        try:
            # 이 블록은 데이터베이스 트랜잭션처럼 동작해야 함
            debit_agent._sub_assets(amount)
            credit_agent._add_assets(amount)

        except Exception as e:
            # CRITICAL: 롤백 로직이 필요하지만, 현재 메모리 기반에서는
            # 상태 변경 전 검증을 철저히 하는 것으로 대체.
            # 만약 _sub_assets가 성공하고 _add_assets가 실패하는 극단적인 경우를 대비한 로깅
            self.logger.critical(
                f"ATOMICITY_FAILURE | Rolled back transfer of {amount} from "
                f"{debit_agent.id} to {credit_agent.id}. Error: {e}"
            )
            # 롤백: 상태를 원상 복구
            debit_agent._add_assets(amount) 
            return False

        # 4. 로깅
        self.logger.info(
            f"TRANSFER | From: {debit_agent.id}, To: {credit_agent.id}, "
            f"Amount: {amount:.2f}, Memo: {memo}"
        )
        return True
```

---

## 4. Refactoring Guide

### 4.1. `TransactionProcessor` 리팩토링
`TransactionProcessor`는 더 이상 직접 자산을 수정하지 않고, 모든 금융 결제를 `SettlementSystem`에 위임합니다.

**Before:**
```python
# simulation/systems/transaction_processor.py

# ... tax_amount 계산 ...
buyer.assets -= (trade_value + tax_amount)
seller.assets += trade_value
government.collect_tax(tax_amount, ...) # 내부에서 government.assets += ...
```

**After:**
```python
# simulation/systems/transaction_processor.py

# self.settlement_system 이 SimulationState 를 통해 주입되었다고 가정
settlement_system = state.settlement_system

# ... tax_amount 계산 ...
total_debit = trade_value + tax_amount

# Step 1: 구매자가 판매자에게 상품 대금 지불
success1 = settlement_system.transfer(
    debit_agent=buyer,
    credit_agent=seller,
    amount=trade_value,
    memo=f"goods_purchase:{tx.item_id}"
)

# Step 2: 구매자가 정부에게 세금 납부
success2 = settlement_system.transfer(
    debit_agent=buyer,
    credit_agent=government,
    amount=tax_amount,
    memo=f"sales_tax:{tx.item_id}"
)

if not (success1 and success2):
    # 거래 실패 처리 (예: 로그 남기기)
    logger.error(f"Transaction failed for tx id {tx.id}")
```
**핵심**: `TransactionProcessor`의 역할은 '무엇을, 왜' 전송해야 하는지 결정하는 것으로 축소되고, '어떻게' 전송할 것인지는 `SettlementSystem`이 전담합니다.

### 4.2. `InheritanceManager` 리팩토링 (잔차 증발 해결)
상속 과정에서 발생하는 부동소수점 잔차는 `SettlementSystem`을 통해 국고로 귀속시킵니다.

**Before:**
```python
# simulation/systems/inheritance_manager.py
num_heirs = len(heirs)
cash_share = deceased.assets / num_heirs
for heir in heirs:
    heir.assets += cash_share
deceased.assets = 0.0 # <--- 잔차 증발 발생 지점!
```

**After:**
```python
# simulation/systems/inheritance_manager.py
settlement_system = simulation.state.settlement_system # 컨텍스트에서 주입
government = simulation.government

num_heirs = len(heirs)
total_cash = deceased.assets
cash_share = round(total_cash / num_heirs, 2) # 소수점 2자리로 반올림
total_distributed = 0.0

for heir in heirs:
    # 1. 상속 집행
    settlement_system.transfer(
        debit_agent=deceased,
        credit_agent=heir,
        amount=cash_share,
        memo=f"inheritance_from:{deceased.id}"
    )
    total_distributed += cash_share

# 2. 잔차 계산 및 국고 귀속 (Residual Catch-all)
remainder = total_cash - total_distributed
if remainder > 0:
    settlement_system.transfer(
        debit_agent=deceased,
        credit_agent=government,
        amount=remainder,
        memo="inheritance_residual_dust"
    )

# deceased.assets 는 이제 0에 가까워야 함
```
자산 청산(Liquidation) 과정(`deceased.assets += sale_price`) 또한 `settlement_system.transfer(debit_agent=government, credit_agent=deceased, ...)` 호출로 변경되어야 합니다.

---

## 5. Risk & Impact Audit (설계 반영)

-   **God Class Decomposition**: 이 설계는 `TransactionProcessor`의 책임을 줄이는 첫 단계입니다. `SettlementSystem` 도입 후, `TransactionProcessor`는 `TaxAgent`, `ClearingHouse` 등으로 추가 분해되어야 합니다.
-   **Test Infrastructure Impact**: 기존 테스트 코드 중 `agent.assets = ...`를 사용하는 부분은 모두 실패할 것입니다. 테스트 스위트 리팩토링이 병행되어야 하며, `tests/verification/verify_zero_sum.py`와 같은 무결성 검증 스크립트의 역할이 더욱 중요해집니다.
-   **Enforcing Access Control**: `_assets`로의 변경과 `SettlementSystem` 사용 강제는 이 리팩토링의 **핵심 성공 기준**입니다. 코드 리뷰 시 이 부분이 엄격하게 검토되어야 합니다.

---

## 6. 🚨 Jules-bot Mandatory Reporting

-   **[Insight]**: 이 리팩토링을 진행하면서 발견하는 새로운 설계 개선 아이디어나 잠재적 문제점을 `communications/insights/` 폴더에 `WO-112-settlement-insights.md`로 기록하십시오.
-   **[Tech Debt]**: `SettlementSystem`으로 즉시 전환하기 어려운 레거시 코드가 있다면, 해당 모듈을 `design/TECH_DEBT_LEDGER.md`에 'SettlementSystem 미적용' 항목으로 등록하십시오.
