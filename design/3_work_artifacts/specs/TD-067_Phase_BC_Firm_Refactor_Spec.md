# Work Order: TD-067 Phase B/C - Deconstruct `Firm` Facade

**Phase:** 31 (Architecture Refinement)
**Priority:** HIGH
**Prerequisite:** TD-067 Phase A (FinanceDepartment Extraction) ✅ Completed

## 1. Problem Statement
The `Firm` class (`simulation/firms.py`) acts as a "God Class" facade, violating the Single Responsibility Principle. Despite Phase A successfully extracting `FinanceDepartment`, the class still proxies **20+ attributes** from its sub-components (e.g., `firm.assets` is an alias for `firm.finance.assets`), resulting in "Wrapper Bloat" (`TD-067`). This creates:
- High maintenance overhead (duplicate getters/setters)
- Confused data ownership (unclear which component owns state)
- Brittle tests (`tests/test_corporate_manager.py` tightly coupled to Firm structure)
- Violation of encapsulation (external modules directly manipulate internal state)

## 2. Objective
Eliminate the facade pattern in the `Firm` class by:
1. **Removing all wrapper properties** (Phase B)
2. **Reducing `CorporateManager` coupling** via encapsulation methods (Phase C)
3. **Refactoring all call sites** to interact directly with sub-components (`firm.hr`, `firm.finance`, etc.)

External modules and tests **must** be adapted to the new architecture, enforcing strict Separation of Concerns (SoC).

## 3. Target Architecture

### Current State (Phase A Completed)
```
Firm (God Class Facade)
├── HRDepartment (owns employees, wages)
├── FinanceDepartment (owns assets, profit, debt)
├── ProductionDepartment (owns inventory, capital)
└── SalesDepartment (owns pricing, orders)
    └── 20+ @property wrappers exposing internal state
```

### Target State (Phase B/C)
```
Firm (Pure Orchestrator)
├── HRDepartment
│   └── Public API: hire(), fire(), get_employees()
├── FinanceDepartment
│   └── Public API: invest(), pay_dividend(), get_assets()
├── ProductionDepartment
│   └── Public API: produce(), get_inventory()
└── SalesDepartment
    └── Public API: set_price(), post_order()
```

**Key Changes:**
- `Firm` becomes a **container** only, no wrapper properties
- External access: `firm.finance.get_assets()` instead of `firm.assets`
- `CorporateManager` calls encapsulated methods: `firm.finance.invest(amount)` instead of `firm.assets -= amount`

---

## 4. Implementation Plan

### Track A: DTO & Interface Definition

1. **Create `simulation/dtos/firm_dtos.py`**:
   - Define `FirmStateDTO`: Read-only snapshot of all Firm state for external consumers (e.g., Dashboard, Analytics)
   - Define `FinancialTransactionDTO`: Encapsulates investment/dividend operations
   - Define `HiringRequestDTO`: Encapsulates hiring/firing operations

2. **Create `simulation/firms/interfaces.py`**:
   - Define `IFinanceDepartment`, `IHRDepartment`, `IProductionDepartment`, `ISalesDepartment` abstract base classes
   - Each interface declares public methods (e.g., `IFinanceDepartment.invest(amount: float)`)

### Track B: Eliminate Wrapper Properties

1. **Remove All Wrappers from `Firm` (`simulation/firms.py:L181-299`)**:
   - Delete `@property` getters/setters for:
     - `employees`, `employee_wages`, `retained_earnings`, `dividends_paid_last_tick`
     - `consecutive_loss_turns`, `current_profit`, `revenue_this_turn`, `cost_this_turn`
     - `profit_history`, `last_revenue`, `last_marketing_spend`, `last_daily_expenses`
     - `last_sales_volume`, `sales_volume_this_tick`
   - **Total: ~20 properties to remove**

2. **Consolidate Logic into Components**:
   - Move `calculate_valuation()` → `FinanceDepartment.calculate_valuation()`
   - Move `get_book_value_per_share()` → `FinanceDepartment.get_book_value_per_share()`
   - Move `get_financial_snapshot()` → `FinanceDepartment.get_snapshot()`

### Track C: Reduce `CorporateManager` Coupling

1. **Add Encapsulation Methods to `FinanceDepartment`**:
   ```python
   def invest_in_automation(self, amount: float) -> bool:
       """Deduct investment from assets. Returns success status."""
       if self.assets >= amount:
           self.assets -= amount
           return True
       return False
   
   def invest_in_rd(self, amount: float) -> bool:
       """Deduct R&D budget from assets."""
       # Same pattern
   
   def invest_in_capex(self, amount: float) -> bool:
       """Deduct CAPEX from assets."""
       # Same pattern
   
   def set_dividend_rate(self, rate: float) -> None:
       """Set dividend payout rate."""
       self.dividend_rate = rate
   ```

2. **Refactor `CorporateManager` (`simulation/decisions/corporate_manager.py`)**:
   - Replace direct state manipulation:
     - `firm.assets -= budget` → `firm.finance.invest_in_automation(budget)`
     - `firm.dividend_rate = x` → `firm.finance.set_dividend_rate(x)`
     - `firm.automation_level = x` → `firm.production.set_automation_level(x)`
   - **Affected Methods**:
     - `_manage_automation()` (L181-254)
     - `_manage_r_and_d()` (L256-303)
     - `_manage_capex()` (L305-333)
     - `_manage_dividends()` (L335-341)
     - `_manage_hiring()` (L417-530)

### Track D: Refactor All Call Sites

1. **Update `Firm` Internal Methods**:
   - `make_decision()`: Access sub-components directly
   - `get_agent_data()`: Build response from `firm.finance.get_snapshot()`, `firm.hr.get_employees()`, etc.
   - `update_needs()`: Delegate to sub-components instead of direct attribute access

2. **Refactor Test Suite**:
   - **`tests/test_corporate_manager.py`**:
     - Update `firm_mock` fixture to mock sub-components:
       ```python
       firm_mock.finance = MagicMock()
       firm_mock.finance.assets = 10000.0
       firm_mock.hr = MagicMock()
       firm_mock.hr.employees = []
       ```
     - Update assertions: `assert firm_mock.finance.assets == expected`
   
   - **`tests/test_firms.py`**:
     - Update `test_book_value_with_liabilities`: Call `firm.finance.get_book_value_per_share()`
     - Update mock chains: `firm.finance.loan_market.bank` instead of `firm.decision_engine.loan_market.bank`

3. **Refactor External Modules**:
   - **`simulation/engine.py`**: Update any direct `firm.assets` access
   - **Dashboard/Analytics**: Use `FirmStateDTO` for read-only access

---

## 5. Verification Plan

### Automated Tests
1. **Component Unit Tests**:
   - Create `tests/simulation/firms/test_finance_department.py`
   - Test `invest_in_automation()`, `calculate_valuation()`, etc. in isolation

2. **Integration Tests**:
   - **`tests/test_corporate_manager.py`**: All existing tests must pass after refactoring
   - **`tests/test_firms.py`**: All existing tests must pass
   - **Golden Fixture Compatibility**: Run `tests/verification/verify_mitosis.py` to ensure no regression

3. **Regression Tests**:
   - Run full test suite: `pytest tests/`
   - Ensure no `AttributeError` for removed wrapper properties

### Manual Verification
1. **Static Analysis**: Run `ruff check simulation/` to detect unused imports
2. **Code Review**: Verify no direct `firm.assets` access remains in `CorporateManager`

---

## 6. 🚨 Risk & Impact Audit (Mitigation Plan)

### Risk: Widespread Test Breakage
- **Description**: Removing 20+ wrapper properties will break dozens of tests that directly get/set attributes on `Firm` instances.
- **Mitigation**: 
  - This is **intentional technical debt repayment**. All broken tests must be refactored to use sub-components.
  - Prioritize `test_corporate_manager.py` (highest coupling) first.
  - Use IDE refactoring tools to batch-replace `firm.assets` → `firm.finance.assets`.

### Risk: Breaking Dependent Modules
- **Description**: Modules like `CorporateManager`, `Simulation.engine`, and Dashboard may directly access `firm.assets`.
- **Mitigation**:
  - For **read operations**: Introduce `FirmStateDTO` for external consumers.
  - For **write operations**: Use encapsulation methods (`firm.finance.invest()`).
  - Grep search for all `firm.assets` usages before starting.

### Risk: Jules Regression to God Class
- **Description**: Jules may attempt to "simplify" by re-adding wrapper properties or consolidating logic back into `Firm`.
- **Mitigation** (⚠️ **CRITICAL**):
  - **Explicitly state in spec**: "Do NOT add any `@property` wrappers to `Firm`. All state access must go through sub-components."
  - **Reference existing SoC structure**: Mention `simulation/components/economy_manager.py`, `simulation/systems/world_state.py` as examples of correct SoC.
  - **Require explicit confirmation**: Jules must acknowledge "I will not create God Class wrappers" in PR description.

### Risk: Golden Fixture Incompatibility
- **Description**: `conftest.py` fixtures may rely on `firm.assets` for setup.
- **Mitigation**:
  - Review `tests/conftest.py` for any `Firm` fixture setup.
  - Update fixtures to use sub-components: `firm.finance.assets = 1000.0`.
  - Run `verify_mitosis.py` as gate check before merging.

---

## 7. 🛡️ SoC Preservation Guidelines (For Jules)

### ✅ DO:
- Access state via sub-components: `firm.finance.assets`, `firm.hr.employees`
- Add encapsulation methods to components: `FinanceDepartment.invest(amount)`
- Use DTOs for cross-module communication: `FirmStateDTO`
- Keep `Firm` as a pure orchestrator (no business logic)

### ❌ DO NOT:
- Add `@property` wrappers to `Firm` (e.g., `@property def assets(self): return self.finance.assets`)
- Move logic from components back into `Firm`
- Create "convenience methods" that bypass sub-components
- Consolidate `FinanceDepartment`, `HRDepartment` back into `Firm`

### 📋 Pre-Merge Checklist:
- [ ] Zero `@property` wrappers in `Firm` class
- [ ] All `CorporateManager` methods use encapsulation APIs
- [ ] `tests/test_corporate_manager.py` passes
- [ ] `tests/verification/verify_mitosis.py` passes
- [ ] No direct `firm.assets` access outside `FinanceDepartment`

---

## 8. Mandatory Reporting (Jules's Guideline)
During implementation, any unforeseen challenges, architectural friction, or potential improvements discovered must be logged as a new entry in `communications/insights/`. Any identified technical debt must be proposed for inclusion in `design/TECH_DEBT_LEDGER.md`.

---

## 9. Success Criteria
- ✅ All 20+ wrapper properties removed from `Firm`
- ✅ `CorporateManager` uses encapsulation methods (no direct state manipulation)
- ✅ All tests pass (including `test_corporate_manager.py`, `verify_mitosis.py`)
- ✅ Static analysis clean (no unused imports, no `AttributeError`)
- ✅ No God Class regression (verified by code review)
