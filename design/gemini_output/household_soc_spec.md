# TD-044: Household God Class Refactoring

## 1. 개요 (Overview)
*   **Goal**: `simulation/core_agents.py`의 `Household` 클래스를 리팩토링하여 `EconomyManager`와 `LaborManager`를 분리합니다.
*   **Prerequisite**: TD-045 (Firm SoC) 완료 후 동일한 Composition 패턴 적용
*   **Target Files**: 
    - `simulation/core_agents.py` (수정)
    - `simulation/components/economy_manager.py` (신규)
    - `simulation/components/labor_manager.py` (신규)

## 2. 아키텍처 설계 (Architecture Design)

### 2.1 Class Diagram (After)
```
Household (Coordinator/Façade)
    ├── EconomyManager (Composition)
    │     └── consume(), save(), pay_taxes(), get_inventory_value()
    └── LaborManager (Composition)
          └── work(), search_job(), update_skills(), get_income()
```

### 2.2 책임 분리 (Responsibility Mapping)

| 기존 메서드 (Household) | 이동 대상 | 비고 |
|---|---|---|
| `consume()`, `_calculate_consumption()` | `EconomyManager` | 소비/저축 로직 |
| `get_inventory_value()`, `pay_taxes()` | `EconomyManager` | 재정 로직 |
| `work()`, `search_job()` | `LaborManager` | 노동 로직 |
| `update_skills()`, `get_productivity()` | `LaborManager` | 스킬 관리 |
| `update_needs()`, `make_decision()` | `Household` (유지) | 조정/위임 역할 |

## 3. Key Considerations from Pre-flight Audit (Refined Requirements)

Based on TD-045 pattern and Auto-Audit findings, the following constraints are MANDATORY:

1.  **State Ownership (Assets/Inventory)**:
    *   `Household` class MUST retain ownership of `self.assets` and `self.inventory`.
    *   `EconomyManager` and `LaborManager` are NOT allowed to modify these directly.
    *   **Action**: Implement `household.adjust_assets(delta)` and `household.modify_inventory(item, qty)` methods. Managers call these methods.

2.  **Façade Pattern for API Compatibility**:
    *   External callers (e.g., `decision_engine`) should NOT need to change.
    *   Use `@property` decorators to expose manager attributes through `Household`.
    *   Example: `household.income` → internally calls `self.labor_manager.get_income()`

3.  **Explicit Execution Order**:
    *   The `update_needs` method should orchestrate calls in this order:
        1.  `LaborManager.work()` (Earn income)
        2.  `EconomyManager.consume()` (Spend on needs)
        3.  `EconomyManager.pay_taxes()` (Settle with government)

4.  **Data Flow Interface**:
    *   `LaborManager.work()` returns a `LaborResult` DTO (hours_worked, income_earned).
    *   `EconomyManager.consume()` returns a `ConsumptionResult` DTO (items_consumed, satisfaction).

## 4. 구현 계획 (Implementation Plan)

### Step 1: Create Manager Classes
```python
# simulation/components/economy_manager.py
class EconomyManager:
    def __init__(self, household: "Household", config_module):
        self._household = household
        self._config = config_module
    
    def consume(self) -> ConsumptionResult:
        # Logic moved from Household.consume()
        ...
```

### Step 2: Refactor Household
```python
# simulation/core_agents.py (Modified)
class Household:
    def __init__(self, ...):
        ...
        self.economy_manager = EconomyManager(self, config_module)
        self.labor_manager = LaborManager(self, config_module)
    
    @property
    def income(self) -> float:
        return self.labor_manager.get_income()
    
    def update_needs(self, ...):
        # Orchestrate managers
        labor_result = self.labor_manager.work(...)
        self.adjust_assets(labor_result.income_earned)
        consumption_result = self.economy_manager.consume(...)
        ...
```

## 5. 검증 계획 (Verification Plan)
1.  **Unit Test**: 기존 `tests/test_core_agents.py` 통과 필수
2.  **Regression Test**: `python -m pytest tests/` 전체 통과
3.  **API Compatibility**: `decision_engine`에서 `Household` 접근 시 동일하게 동작해야 함

## 6. 제약 사항 (Constraints)
*   기존 `Household`의 public API를 변경하지 마십시오.
*   모든 Manager 클래스는 Type Hint와 Docstring을 포함해야 합니다.
*   TD-045 완료 후 `simulation/components/` 디렉토리가 존재한다고 가정합니다.
