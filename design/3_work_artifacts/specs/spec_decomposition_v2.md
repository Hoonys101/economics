# Refactoring Specification: HR & Sales Engines

This document outlines the refactoring plan for `HREngine` and `SalesEngine` to align with the project's stateless, orchestrator-driven architecture. The changes address critical risks identified in the pre-flight audit, focusing on enforcing abstraction purity, eliminating side-effects, and clarifying the role of the `Firm` agent as the sole "Doer".

---

## 1. HR Engine (`HREngine`) Refactoring

### 1.1. 🚨 Risk & Impact Audit (Summary)

This refactoring directly addresses the following audit findings:
- **CRITICAL: Broken Contract (`process_payroll`)**: The primary `Firm -> HREngine` call site is non-functional. This spec corrects the `Firm`'s implementation to use the `HRPayrollContextDTO`.
- **CRITICAL: Hidden Side-Effects**: The engine's direct mutation of `employee` agents (`.quit()`, `.labor_income_this_tick`) is eliminated. These actions are now returned as data (`HRPayrollResultDTO`) for the `Firm` orchestrator to apply.
- **CRITICAL: Leaky Abstractions**: Methods like `create_fire_transaction` that required a `wallet` handle are removed or redesigned to operate on DTOs, removing the engine's privileged access to the firm's core components.

### 1.2. API & DTO Definitions (`modules/hr/api.py`)

- **`EmployeeUpdateDTO`**: A data-only structure describing a change to be applied to an employee agent.
- **`HRPayrollResultDTO`**: The new return type for `process_payroll`, encapsulating all outcomes.
- **`IHREngine`**: The updated interface, enforcing the new return type.

```python
# DTOs
from dataclasses import dataclass, field
from typing import List
from simulation.models import Transaction

@dataclass(frozen=True)
class EmployeeUpdateDTO:
    """Data instructing the Orchestrator on how to update an employee agent."""
    employee_id: int
    net_income: float = 0.0
    fire_employee: bool = False
    severance_pay: float = 0.0

@dataclass(frozen=True)
class HRPayrollResultDTO:
    """Encapsulates all outcomes from the payroll process."""
    transactions: List[Transaction] = field(default_factory=list)
    employee_updates: List[EmployeeUpdateDTO] = field(default_factory=list)

# Interface
from abc import ABC, abstractmethod
from simulation.components.state.firm_state_models import HRState
from simulation.dtos.hr_dtos import HRPayrollContextDTO
from simulation.dtos.config_dtos import FirmConfigDTO

class IHREngine(ABC):
    @abstractmethod
    def process_payroll(
        self,
        hr_state: HRState,
        context: HRPayrollContextDTO,
        config: FirmConfigDTO,
    ) -> HRPayrollResultDTO:
        """
        Processes payroll and returns a DTO with transactions and employee updates.
        This method MUST NOT have external side-effects.
        """
        ...
```

### 1.3. Logic & Orchestration

#### 1.3.1. Engine Logic (`HREngine.process_payroll`) (Pseudo-code)

The engine's responsibility is now purely calculation.

```python
# Inside HREngine.process_payroll

# 1. Initialize result object
result = HRPayrollResultDTO(transactions=[], employee_updates=[])

# 2. Iterate over employees
for employee in list(hr_state.employees):
    # ... wage and tax calculation ...
    wage = self.calculate_wage(employee, base_wage, config)

    # 3. Affordability Check
    if firm_can_afford(wage):
        # ... calculate net_wage and income_tax ...

        # 4. APPEND data to result DTO (NO direct action)
        result.transactions.append(tx_wage)
        result.transactions.append(tx_tax)
        result.employee_updates.append(
            EmployeeUpdateDTO(employee_id=employee.id, net_income=net_wage)
        )

    elif firm_is_insolvent():
        # ... calculate severance_pay ...
        if firm_can_afford(severance_pay):
            # 5. APPEND firing instruction to result DTO
            result.transactions.append(tx_severance)
            result.employee_updates.append(
                EmployeeUpdateDTO(employee_id=employee.id, fire_employee=True, severance_pay=severance_pay)
            )
        else:
            # ... handle zombie state (mutates hr_state, which is allowed)
            self._record_zombie_wage(...)
# 6. Return the result object
return result
```

#### 1.3.2. Orchestrator Workflow (`Firm.generate_transactions`) (Pseudo-code)

The `Firm` agent becomes the "Doer", applying the results calculated by the engine.

```python
# Inside Firm.generate_transactions

# 1. GATHER: Assemble the context DTO
payroll_context = HRPayrollContextDTO(
    exchange_rates=market_context['exchange_rates'],
    tax_policy=... ,
    current_time=current_time,
    firm_id=self.id,
    wallet_balances=self.wallet.get_all_balances(),
    # ... other fields
)

# 2. CALL: Execute the stateless engine
payroll_result = self.hr_engine.process_payroll(
    self.hr_state,
    payroll_context,
    self.config
)

# 3. APPLY: Process the results
# 3.1. Apply transactions
all_transactions.extend(payroll_result.transactions)

# 3.2. Apply employee state changes
for update in payroll_result.employee_updates:
    # Find the actual agent instance
    employee = agent_registry.get(update.employee_id)
    if not employee: continue

    # Apply income update
    if update.net_income > 0:
        employee.labor_income_this_tick = (employee.labor_income_this_tick or 0.0) + update.net_income

    # Apply firing
    if update.fire_employee:
        employee.quit()
        self.hr_engine.finalize_firing(self.hr_state, update.employee_id) # Engine mutates its own state model
```

### 1.4. 검증 계획 (Testing & Verification Strategy)

1.  **Existing Test Impact**: The test `tests/test_firm_lifecycle.py::TestFirmLifecycle::test_generate_transactions_payroll` is expected to fail due to the `process_payroll` signature change.
2.  **New Test Cases**:
    *   A new unit test for `HREngine` will be created to validate that `process_payroll` correctly returns a `HRPayrollResultDTO` for various scenarios (payment, insolvency, zombie). This test will use mock employee data and a `HRPayrollContextDTO`.
    *   The failing `TestFirmLifecycle` test will be repaired. The mock for `hr_engine.process_payroll` will be updated to return a `HRPayrollResultDTO` instance. Assertions will be added to verify that the `Firm` correctly processes the `employee_updates` (e.g., checks if `employee.quit` was called).

---

## 2. Sales Engine (`SalesEngine`) Refactoring

### 2.1. 🚨 Risk & Impact Audit (Summary)

The `SalesEngine` is in a better state but can be improved for clarity and to strictly adhere to the Orchestrator pattern.
- **Side-Effect Isolation**: The `adjust_marketing_budget` method currently mutates `SalesState` directly. While permissible, this refactoring will change it to return the calculated budget, making the `Firm`'s "set budget" action explicit.
- **Clarity & Orchestration**: This change makes the data flow clearer: Firm asks Engine "what should the budget be?", Engine answers, Firm sets the budget and generates the corresponding transaction.

### 2.2. API & DTO Definitions (`modules/sales/api.py`)

A result DTO is introduced for marketing budget calculation.

```python
# DTO
from dataclasses import dataclass

@dataclass(frozen=True)
class MarketingAdjustmentResultDTO:
    """Result from a marketing budget calculation."""
    new_budget: float

# Interface
from abc import ABC, abstractmethod
from simulation.components.state.firm_state_models import SalesState
from modules.system.api import MarketContextDTO

class ISalesEngine(ABC):
    @abstractmethod
    def adjust_marketing_budget(
        self,
        sales_state: SalesState,
        market_context: MarketContextDTO,
        total_revenue: float
    ) -> MarketingAdjustmentResultDTO:
        """Calculates the new marketing budget and returns it as a DTO."""
        ...
```

### 2.3. Logic & Orchestration

#### 2.3.1. Engine Logic (`SalesEngine.adjust_marketing_budget`)

The method is simplified to only perform the calculation and return the result.

```python
# Inside SalesEngine.adjust_marketing_budget
# ... existing logic to calculate budget_based_on_revenue ...
# ... existing logic to calculate new_budget ...

# DO NOT set state.marketing_budget here.
# Instead, return the calculated value in the DTO.
return MarketingAdjustmentResultDTO(new_budget=new_budget)
```

#### 2.3.2. Orchestrator Workflow (`Firm.generate_transactions`)

The `Firm` now explicitly sets the budget based on the engine's recommendation before generating the spending transaction.

```python
# Inside Firm.generate_transactions, after payroll and finance sections

# 1. CALL: Get the budget recommendation
market_adjustment_result = self.sales_engine.adjust_marketing_budget(
    self.sales_state,
    market_context,
    self.finance_state.last_revenue
)

# 2. APPLY: The Firm explicitly sets its state
self.sales_state.marketing_budget = market_adjustment_result.new_budget

# 3. GENERATE TRANSACTION: The firm now generates the transaction based on its updated state
tx_marketing = self.sales_engine.generate_marketing_transaction(
    self.sales_state, # now contains the new budget
    self.id,
    self.wallet.get_balance(DEFAULT_CURRENCY),
    gov_id,
    current_time
)
if tx_marketing:
    transactions.append(tx_marketing)
```

### 2.4. 🚨 Mandatory Reporting Verification
All insights and identified technical debt from this refactoring process (e.g., the need to update test mocks, the fragility of the pre-refactor state) have been noted. A corresponding report will be filed in `communications/insights/refactor_hr_sales_engine.md` upon completion of the implementation phase. This fulfills the mandatory reporting requirement.
