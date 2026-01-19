# WO-081: Bank Interface Segregation & Refactoring

## 🎯 Objective
`Bank` 클래스의 인터페이스를 리팩토링하여, **고객 서비스(Agent Service)**와 **금융 엔티티(Financial Entity)**로서의 역할을 명확히 분리합니다. 이를 통해 통합 테스트 시 발생하는 `TypeError`와 금융 시스템 연동 오류를 근본적으로 해결합니다.

> **Warning**: Do NOT implement "data saving" or "fixtures" in this task. Focus ONLY on the code refactoring.

---

## 🔨 Tasks

### 1. Interface Definition
`Bank` 클래스는 두 가지 역할을 명확히 구분해야 합니다.

1. **`IBankService` (For Core Agents: Household, Firm)**
   - Methods:
     - `deposit_from_customer(agent_id: int, amount: float) -> str`
       - Returns `deposit_id`.
       - Replaces usage of `deposit(agent_id, amount)`.
     - `withdraw_for_customer(agent_id: int, amount: float) -> bool`
       - Returns `success`.
       - Replaces usage of `withdraw(agent_id, amount)`.

2. **`IFinancialEntity` (For Finance System: CentralBank, Treasury)**
   - Inherits from `modules.finance.interfaces.IFinancialEntity`.
   - Methods:
     - `deposit(amount: float) -> None`
       - Increases Bank's **Reserve/Equity** (not customer deposits).
     - `withdraw(amount: float) -> None`
       - Decreases Bank's **Reserve/Equity**.
       - Must raise `InsufficientFundsError` if insufficient.

### 2. Bank Class Refactoring (`simulation/bank.py`)
- Rename current `deposit` methods to `deposit_from_customer`.
- Rename current `withdraw` methods to `withdraw_for_customer`.
- Implement strict `IFinancialEntity` methods.
- **Strictly Avoid**: Do NOT use `*args` or `len(args)` checks. Use explicit method names.

### 3. Usage Update (Global Search & Replace)
You must update all call sites that use the old methods.

- **`simulation/loan_market.py`**:
  - `bank.deposit(..., ...)` -> `bank.deposit_from_customer(..., ...)`
  - `bank.withdraw(..., ...)` -> `bank.withdraw_for_customer(..., ...)`
- **`simulation/agents/government.py`** (if applicable):
  - Check bailouts logic. If it injects capital, it should use `IFinancialEntity.deposit(amount)`.
- **Tests**:
  - Update `tests/test_bank.py` and other tests to use new method names.

---

## ✅ Acceptance Criteria

1. [ ] `Bank` class implements `IFinancialEntity` without conflicting with customer methods.
2. [ ] No usage of `*args` or dynamic dispatch based on argument count in `Bank`.
3. [ ] All tests passing (especially `test_bank.py` and `test_system.py`).
4. [ ] Zero-Sum principle requires that `IFinancialEntity.deposit/withdraw` affect `self.assets` directly.

---

## ⚠️ Constraints
- **Zero-Sum**: When implementing `withdraw_for_customer`, ensure asset transfer logic remains correct (currently handled via `Transaction` in LoanMarket, so Bank just updates internal ledger).
- **Scope**: Do NOT fix `FixtureHarvester` or create golden files in this session. Focus on the class API.
