# Architecture Standard: Test Refactoring Guide (SSoT Alignment)

## 1. Core Principle: Single Source of Truth (SSoT)
경제 시뮬레이션의 모든 자산(Assets)과 부채(Liabilities)의 진실은 이제 에이전트 객체(`Agent`)가 아닌 `SettlementSystem` 에 들어있습니다.

### 🚫 Anti-Pattern (Legacy)
```python
# 에이전트 내부 속성을 직접 검사 (X)
assert government.assets == 5000.0 
```

### ✅ Modern Pattern (SSoT)
```python
# SettlementSystem을 통해 조회 (O)
assert settlement_system.get_balance(government.id) == 5000.0
```

---

## 2. DTO-First Mocking
모든 Mocking은 실제 구현과 동일한 타입(Dataclass)을 반환해야 합니다.

- **Rule**: `MagicMock(spec=LoanInfoDTO)` 또는 실제 DTO 인스턴스를 사용하십시오.
- **Reason**: `TypedDict` 나 `dict` 는 속성 접근 시 `AttributeError`를 유발합니다.

---

## 3. Zero-Sum Integrity Validation
트랜잭션 테스트 시 반드시 시스템 전체 통화량이 보존되는지 확인하십시오.

```python
initial_total = sum(settlement_system.get_all_balances())
# ... Run Transaction ...
final_total = sum(settlement_system.get_all_balances())
assert initial_total == final_total
```

---

## 4. Covenant & Signature Hygiene
`BailoutCovenant` 및 `BorrowerProfileDTO` 처럼 변경이 잦은 계약 구조는 반드시 최신 `api.py` 정의를 따르십시오.
- `BailoutCovenant`는 이제 `executive_salary_freeze` 대신 `executive_bonus_allowed`를 사용합니다 (예시).
