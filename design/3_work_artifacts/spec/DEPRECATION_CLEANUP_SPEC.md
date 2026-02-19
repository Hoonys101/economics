file: design/3_work_artifacts/specs/refactor_deprecations_spec.md
```markdown
# Specification: Deprecation Cleanup & Standardization (Track B)

## 1. Overview
This specification details the refactoring plan to eliminate three identified technical debt items: the deprecated `Government.collect_tax` method, the legacy `HouseholdFactory` implementation, and the `StockOrder` model. This effort aims to enforce **Zero-Sum Integrity** via atomic settlement and standardize **Dependency Injection** patterns.

## 2. Refactoring Targets

### 2.1. Government.collect_tax -> settle_atomic (TD-DEPR-GOV-TAX)
- **Goal**: Remove the `collect_tax` wrapper and enforce explicit, balanced atomic transactions.
- **Affected File**: `simulation/agents/government.py`
- **Logic Change**:
  - **Before**: `transfer(sender, receiver, amount, memo)` (Implicitly handled by `SettlementSystem.transfer` wrapper).
  - **After**: `settle_atomic(debits=[(payer, amount)], credits=[(payee, amount)], ...)` (Explicit double-entry).
- **Refactoring Pattern (Pseudo-code)**:
  ```python
  # In simulation/agents/government.py

  # DEPRECATE/REMOVE:
  # def collect_tax(self, amount, tax_type, payer, tick):
  #     ... transfer(...) ...

  # REPLACE CALL SITES (Internal/External) WITH:
  # Assuming logic is moved to TaxService or updated in place:
  def _execute_tax_collection(self, payer: AgentID, amount_pennies: int, memo: str, tick: int) -> bool:
      return self.settlement_system.settle_atomic(
          debits=[(payer, amount_pennies)],
          credits=[(self.id, amount_pennies)],
          tick=tick,
          memo=memo
      )
  ```
- **Constraint**: Ensure `amount` is converted to pennies (`int`) if currently `float`.

### 2.2. HouseholdFactory Legacy Cleanup (TD-DEPR-FACTORY)
- **Goal**: Unify `HouseholdFactory` usage to the new `simulation.factories.agent_factory` pattern.
- **Affected File**: `simulation/systems/demographic_manager.py`
- **Logic Change**:
  - **Before**: Instantiated with `HouseholdFactoryContext` (heavy state). Method calls were simple.
  - **After**: Instantiated with `config_module` (light state). Method calls require `simulation` injection.
- **Refactoring Pattern**:
  ```python
  # In simulation/systems/demographic_manager.py

  # 1. Update Import
  # FROM: from modules.household.factory import HouseholdFactory
  # TO:   from simulation.factories.agent_factory import HouseholdFactory

  # 2. Update __init__
  # self.household_factory = HouseholdFactory(self.config)

  # 3. Update process_births / create_agent calls
  # child = self.household_factory.create_newborn(
  #     parent=parent,
  #     simulation=simulation,  # <--- NEW INJECTION
  #     new_id=new_id
  # )
  ```

### 2.3. StockOrder -> CanonicalOrderDTO (TD-DEPR-STOCK-DTO)
- **Goal**: Remove `StockOrder` class and use `CanonicalOrderDTO` exclusively.
- **Affected File**: `simulation/models.py`, `tests/unit/test_market_adapter.py`
- **Logic Change**: Standardize field names (`side` vs `order_type`, `item_id` vs `firm_id`).
- **Refactoring Pattern**:
  ```python
  # In simulation/models.py
  # Remove StockOrder class definition.
  # Add Alias if strictly necessary for transition, but prefer removal.
  from modules.market.api import CanonicalOrderDTO as OrderDTO

  # In Adapter/Conversion Logic:
  # Ensure 'item_id' is formatted as f"stock_{firm_id}"
  # Ensure 'price_pennies' is calculated.
  ```

## 3. Verification Plan

### 3.1. New Test Cases
- **`tests/integration/test_refactored_taxation.py`**:
    - Verify `settle_atomic` is called with balanced debits/credits during tax collection.
    - Assert `Government` wallet balance increases and `Payer` wallet balance decreases exactly by `amount`.
- **`tests/unit/systems/test_demographics_factory_integration.py`**:
    - Verify `DemographicManager` successfully creates a newborn using the new factory signature.
    - specific check: `create_newborn` receives the `simulation` mock.

### 3.2. Existing Test Impact
- **`tests/integration/test_government_tax.py`**: Will require updates to mock `settle_atomic` instead of `transfer` if `transfer` was being mocked.
- **`tests/unit/test_household_factory.py`**: This file tests the *legacy* factory. It should be deprecated or rewritten to test `simulation.factories.agent_factory`.
- **`tests/unit/test_market_adapter.py`**: Update to remove `StockOrder` input tests or update them to test legacy-dict-to-Canonical conversion only.

## 4. Risk Analysis (Audit)
- **Risk**: `settle_atomic` enforces strict zero-sum. If `Government.collect_tax` previously allowed creating money (if sender had insufficient funds but `transfer` forced it), `settle_atomic` might fail.
    - **Mitigation**: Ensure tax logic checks `payer.wallet.balance` before attempting collection, or handle `settle_atomic` failure gracefully (record partial/failed tax).
- **Risk**: `DemographicManager` relies on `HouseholdFactory`. If `simulation` object passed is incomplete (missing `goods_data`), factory might crash.
    - **Mitigation**: Ensure `process_births` has access to a valid `simulation` state or DTO.

## 5. Reference Standards
- **[FINANCIAL_INTEGRITY.md]**: Penny Standard & Zero-Sum.
- **[SEO_PATTERN.md]**: Stateless Engines (Factory should be stateless/light).
```

file: communications/insights/analyze-deprecations.md
```markdown
# Insight: Deprecation Analysis & Refactoring Strategy

## 1. Technical Debt Breakdown

### TD-DEPR-GOV-TAX (Government.collect_tax)
- **Current State**: The `collect_tax` method is a legacy wrapper around `transfer`. It obscures the transactional nature of taxation and relies on implicit side-effects.
- **Target State**: Direct usage of `SettlementSystem.settle_atomic`.
- **Architectural Gain**: Enforces **Zero-Sum Integrity**. Every tax penny collected must have a clear source (Payer) and destination (Government Treasury). This eliminates "Magic Money" creation risks during fiscal operations.

### TD-DEPR-FACTORY (HouseholdFactory)
- **Current State**: Two factory implementations exist. The legacy one in `modules/household` couples the factory with a heavy `Context` object.
- **Target State**: `simulation.factories.agent_factory`.
- **Architectural Gain**: Adheres to the **SEO Pattern** (Stateless Engine). The new factory acts closer to a pure function/engine, taking the simulation state as an argument rather than holding it. This improves testability and reduces circular dependencies.

### TD-DEPR-STOCK-DTO (StockOrder)
- **Current State**: `StockOrder` model uses divergent field names (`order_type`, `firm_id`) compared to the system-wide `CanonicalOrderDTO`.
- **Target State**: Unified `CanonicalOrderDTO`.
- **Architectural Gain**: Simplifies Market Adapter logic and ensures consistent `item_id` formatting (`stock_{id}`) across the system.

## 2. Refactoring Patterns & constraints

### Pattern: Atomic Settlement
```python
# Strict Zero-Sum Enforcement
success = settlement_system.settle_atomic(
    debits=[(payer_id, amount_pennies)],
    credits=[(government_id, amount_pennies)],
    tick=current_tick,
    memo="tax_collection"
)
```
*Constraint*: `amount` must be `int` (pennies). Floating point tax rates must be resolved to integers *before* settlement requests.

### Pattern: Dependency Injection (Factory)
```python
# Explicit Dependency Injection
child = factory.create_newborn(
    parent=parent_agent,
    simulation=simulation_instance, # <--- Critical: Explicit Context
    new_id=next_id
)
```
*Constraint*: The `simulation` object passed must provide `goods_data` and `ai_trainer`.

## 3. Recommended Actions
1.  **Execute Refactor**: Apply the patterns defined in `design/3_work_artifacts/specs/refactor_deprecations_spec.md`.
2.  **Audit Tests**: Run `tests/integration/test_government_tax.py` immediately after changes to ensure revenue recording logic remains intact.
3.  **Clean Up**: Delete `modules/household/factory.py` once `DemographicManager` is updated.
```