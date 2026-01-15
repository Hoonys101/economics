📄 Drafting Spec with instruction: 'Write a Zero-Question Implementation Spec for refactoring `modules/finance/system.py` to enforce Double-Entry Bookkeeping. REQUIREMENTS: 1) Replace one-way `grant()` with bidirectional `transfer(debtor, creditor, amount)` pattern. 2) Fix `grant_bailout_loan`: add `firm.cash_reserve += amount` after government deduction. 3) Fix `issue_treasury_bonds` QE path: add `central_bank.assets['cash'] -= amount` when CB purchases bonds. 4) All monetary ops must have explicit DEBTOR and CREDITOR. Include: Data Flow Diagram, Pseudo-code, Test Cases. Output in Korean.'...
📖 Attached context: modules\finance\system.py
📖 Attached context: modules\finance\api.py
📖 Attached context: design\specs\SOVEREIGN_DEBT_SPEC.md
📖 Attached context: reports\temp\report_20260116_073516_Analyze__modules_fin.md
🚀 [GeminiWorker] Running task with manual: spec_writer.md

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_Write_a_Zero_Question_Implemen.md
============================================================

✅ Spec Draft Saved: C:\coding\economics\design\drafts\draft_Write_a_Zero_Question_Implemen.md
============================================================
네, 알겠습니다. 팀장님의 지시에 따라, `modules/finance/system.py`의 복식부기 원칙을 강제하기 위한 리팩토링 명세서와 업데이트된 API 정의를 작성하겠습니다. 모든 화폐 이동이 명시적인 차변(Debtor)과 대변(Creditor)을 갖도록 `_transfer` 패턴을 도입하고, 발견된 화폐 소멸/창출 버그를 수정하는 데 초점을 맞추겠습니다.

다음은 Jules가 추가 질문 없이 즉시 구현에 착수할 수 있도록 작성된 "Zero-Question" 명세서 및 관련 파일입니다.

---

### **생성 파일 1: `design/specs/FINANCE_REFACTOR_SPEC.md`**

이 문서는 리팩토링의 목표, 데이터 흐름, 상세 의사코드, 그리고 검증 계획을 포함합니다.

```markdown
# [WO-27] Phase 27.1 Specification: Finance System Double-Entry Bookkeeping Refactor

**Status:** PENDING IMPLEMENTATION
**Version:** 1.0
**Primary Goal:** `modules/finance/system.py` 내 모든 화폐 이동 로직에 복식부기(Double-Entry Bookkeeping) 원칙을 강제하여, 시스템 내 화폐 창출 및 소멸 버그를 근절하고 재정 무결성을 확보합니다.

---

## 1. Executive Summary
- **Problem**: `issue_treasury_bonds` (QE 경로) 및 `grant_bailout_loan` 함수에서 단방향 자산 변경으로 인해 시스템 총 통화량이 변하는 심각한 버그가 `reports/temp/report_20260116_073516_Analyze__modules_fin.md`에서 발견되었습니다.
- **Solution**: 모든 자산 이전을 담당하는 중앙화된 비공개 헬퍼 메서드 `_transfer(debtor, creditor, amount)`를 도입합니다. 이 메서드는 차변(자산 감소)과 대변(자산 증가)을 한 트랜잭션으로 묶어 화폐의 보존을 보장합니다.
- **Impact**: 재정 시스템의 모든 화폐 흐름이 명확해지고, 예측 가능하며, 디버깅이 용이해집니다.

## 2. Core Architectural Change: The `_transfer` Helper
모든 직접적인 `assets +=` 또는 `cash_reserve -=` 호출은 새로운 `_transfer` 메서드 호출로 대체됩니다.

- **`_transfer(self, debtor: Any, creditor: Any, amount: float) -> None`**
  - **debtor (차변 주체):** 자금이 나가는 에이전트 (e.g., `Government`, `Bank`)
  - **creditor (대변 주체):** 자금이 들어오는 에이전트 (e.g., `Firm`, `Government`)
  - **amount (금액):** 이전될 자금의 양

## 3. Data Flow Diagram (AS-IS vs. TO-BE)

### AS-IS (현재 구조)
- **Bailout**: `Government.assets -= amount` --> (Money Destroyed)
- **QE Bond**: `(No Debtor)` --> `Government.assets += amount` (Money Created)

### TO-BE (리팩토링 후 구조)
```
                  +--------------------------------+
                  | FinanceSystem._transfer()      |
                  | 1. debtor.assets   -= amount   |
                  | 2. creditor.assets += amount   |
                  +--------------------------------+
                             ^           |
                             |           |
+----------------------+     |           |     +-----------------------+
| debtor (차변)        | ----+           +---> | creditor (대변)       |
| (e.g., Government)   |                       | (e.g., Firm)          |
+----------------------+                       +-----------------------+

```
- **Bailout**: `Government` -> `_transfer` -> `Firm`
- **QE Bond**: `CentralBank` -> `_transfer` -> `Government`
- **Market Bond**: `Bank` -> `_transfer` -> `Government`

## 4. Implementation Pseudo-code

### 4.1. `modules/finance/system.py`
Jules는 아래 의사코드를 참조하여 `FinanceSystem` 클래스를 수정해야 합니다.

#### **[NEW] `_transfer` private method**
```python
# FinanceSystem 클래스 내에 새로운 비공개 메서드로 추가

def _transfer(self, debtor: Any, creditor: Any, amount: float) -> None:
    """
    Handles the movement of funds between two entities, ensuring double-entry.
    This is a private helper method.

    Args:
        debtor: The entity from which money is withdrawn.
        creditor: The entity to which money is deposited.
        amount: The amount of money to transfer.
    """
    if amount <= 0:
        return # 혹은 에러 처리

    # --- Debtor (차변) 처리 ---
    if isinstance(debtor, Government) or isinstance(debtor, Bank):
        # Government와 Bank는 'assets' 속성 사용
        debtor.assets -= amount
    elif isinstance(debtor, Firm):
        # Firm은 'cash_reserve' 속성 사용
        debtor.cash_reserve -= amount
    elif isinstance(debtor, CentralBank):
        # CentralBank는 'assets' 딕셔너리의 'cash' 키 사용
        debtor.assets['cash'] = debtor.assets.get('cash', 0) - amount
    else:
        raise TypeError(f"Unsupported debtor type: {type(debtor)}")

    # --- Creditor (대변) 처리 ---
    if isinstance(creditor, Government) or isinstance(creditor, Bank):
        creditor.assets += amount
    elif isinstance(creditor, Firm):
        creditor.cash_reserve += amount
    elif isinstance(creditor, CentralBank):
        creditor.assets['cash'] = creditor.assets.get('cash', 0) + amount
    else:
        raise TypeError(f"Unsupported creditor type: {type(creditor)}")

```

#### **[REFACTOR] `issue_treasury_bonds` method**
```python
# 기존 issue_treasury_bonds 메서드를 아래와 같이 수정

def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
    # ... (기존 채권 발행 로직: yield_rate 계산 등은 동일) ...

    # ... (new_bond 생성 로직은 동일) ...

    qe_threshold = getattr(self.config_module, "QE_INTERVENTION_YIELD_THRESHOLD", 0.10)
    if yield_rate > qe_threshold:
        # Central Bank가 개입 (QE)
        self.central_bank.purchase_bonds(new_bond)
        # BUG FIX: 중앙은행을 차변, 정부를 대변으로 자금 이전
        self._transfer(debtor=self.central_bank, creditor=self.government, amount=amount)
    else:
        # 시장에 매각 (상업은행이 매입)
        if self.bank.assets >= amount:
            # BUG FIX: 상업은행을 차변, 정부를 대변으로 자금 이전
            self._transfer(debtor=self.bank, creditor=self.government, amount=amount)
        else:
            return [] # 채권 발행 실패

    self.outstanding_bonds.append(new_bond)
    # self.government.assets += amount # 이 라인은 _transfer 메서드로 대체되었으므로 삭제

    return [new_bond]
```

#### **[REFACTOR] `grant_bailout_loan` method**
```python
# 기존 grant_bailout_loan 메서드를 아래와 같이 수정

def grant_bailout_loan(self, firm: 'Firm', amount: float) -> BailoutLoanDTO:
    # ... (기존 loan DTO 생성 로직은 동일) ...

    # BUG FIX: 정부를 차변, 기업을 대변으로 자금 이전
    self._transfer(debtor=self.government, creditor=firm, amount=amount)

    # 기업의 부채 추가 및 상태 변경
    firm.finance.add_liability(amount, loan.interest_rate)
    firm.has_bailout_loan = True

    return loan
```

### 4.2. `modules/finance/api.py`
`system.py`의 `grant_bailout_loan` 함수가 외부(Government 에이전트)에서 호출될 수 있으므로, `IFinanceSystem` 인터페이스에 해당 메서드가 정의되어 있어야 합니다.

```python
# IFinanceSystem 프로토콜에 grant_bailout_loan 메서드 시그니처 추가

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]: # current_tick 인자 추가
        """Issues new treasury bonds to the market."""
        ...

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> BailoutLoanDTO: # 이 메서드 추가
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        ...

    def service_debt(self, current_tick: int) -> None: # current_tick 인자 추가
        """Manages the servicing of outstanding government debt."""
        ...
```

## 5. Verification Plan
아래 테스트 케이스들은 시스템의 총 통화량이 자금 이전 전후로 동일하게 유지되는지를 검증하는 데 초점을 맞춥니다.

1.  **Test Case 1: Bailout Loan Execution**
    - **Setup**: Government (assets=10000), Firm (cash_reserve=100). 총 통화량 = 10100.
    - **Action**: `grant_bailout_loan(firm, amount=500)` 호출.
    - **Assert**:
        - `government.assets` == 9500
        - `firm.cash_reserve` == 600
        - 총 통화량(government.assets + firm.cash_reserve) == 10100 (유지)

2.  **Test Case 2: QE Bond Issuance**
    - **Setup**: Government (assets=10000), CentralBank (assets['cash']=5000). 총 통화량 = 15000.
    - **Action**: `issue_treasury_bonds(amount=1000)` 호출 (QE 조건 충족 가정).
    - **Assert**:
        - `central_bank.assets['cash']` == 4000
        - `government.assets` == 11000
        - 총 통화량(government.assets + central_bank.assets['cash']) == 15000 (유지)

3.  **Test Case 3: Market Bond Issuance**
    - **Setup**: Government (assets=10000), Bank (assets=20000). 총 통화량 = 30000.
    - **Action**: `issue_treasury_bonds(amount=2000)` 호출 (시장 매각 조건 충족).
    - **Assert**:
        - `bank.assets` == 18000
        - `government.assets` == 12000
        - 총 통화량(government.assets + bank.assets) == 30000 (유지)

## 6. Mandatory Reporting for Jules
**[Routine]**
구현 완료 후, 위 `Verification Plan`의 테스트 케이스를 실행하고 결과를 `communications/reports/`에 로그로 남겨주십시오. 또한, 리팩토링 과정에서 발견한 추가적인 기술 부채나 개선 아이디어가 있다면 `communications/insights/` 폴더에 `[Finance_Refactor_Insight].md` 파일로 정리하여 보고해야 합니다.
```

---

### **생성 파일 2: `modules/finance/api.py`**

`IFinanceSystem` 프로토콜을 업데이트하여 `grant_bailout_loan`을 포함하고, `issue_treasury_bonds`와 `service_debt`의 시그니처를 구현과 일치시킵니다.

```python
from typing import Protocol, Dict, List
from dataclasses import dataclass

# Forward reference for type hinting
class Firm: pass

@dataclass
class BondDTO:
    """Data Transfer Object for government bonds."""
    id: str
    issuer: str
    face_value: float
    yield_rate: float
    maturity_date: int

@dataclass
class BailoutLoanDTO:
    """Data Transfer Object for corporate bailout loans."""
    firm_id: int
    amount: float
    interest_rate: float
    covenants: Dict[str, bool]

class IFinanceSystem(Protocol):
    """Interface for the sovereign debt and corporate bailout system."""

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        ...

    def issue_treasury_bonds(self, amount: float, current_tick: int) -> List[BondDTO]:
        """Issues new treasury bonds to the market."""
        ...

    def grant_bailout_loan(self, firm: 'Firm', amount: float) -> BailoutLoanDTO:
        """Converts a bailout from a grant to an interest-bearing senior loan."""
        ...

    def service_debt(self, current_tick: int) -> None:
        """Manages the servicing of outstanding government debt."""
        ...

```

============================================================
