File: modules\firm\api.py
```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Protocol, TypedDict, runtime_checkable
from modules.simulation.dtos.api import FirmStateDTO, FirmConfigDTO
from simulation.models import Order, Transaction

# --- Common DTOs ---

@dataclass(frozen=True)
class FirmStateSnapshotDTO:
    """
    Immutable snapshot of the Firm's state for Engine consumption.
    SEO Pattern: Engines receive this, never the mutable Agent.
    """
    id: int
    funds: int  # Pennies
    price: int  # Current price in pennies
    inventory_volume: int
    production_capacity: float
    # ... other flattened or nested state DTOs as needed
    # Ideally, specific engines receive specific StateDTOs (HRStateDTO, SalesStateDTO)

# --- HR Engine Protocols & DTOs ---

@dataclass(frozen=True)
class HRDecisionInputDTO:
    firm_snapshot: FirmStateDTO
    config: FirmConfigDTO
    current_tick: int
    budget_plan: Any  # BudgetPlanDTO
    labor_market_avg_wage: int # Pennies
    labor_market_min_wage: int # Pennies

@dataclass(frozen=True)
class HRDecisionOutputDTO:
    hiring_orders: List[Order]
    firing_ids: List[int]
    wage_updates: Dict[int, int] # employee_id -> new_wage_pennies
    target_headcount: int

@dataclass(frozen=True)
class HRPayrollContextDTO:
    firm_id: int
    current_time: int
    wallet_balances: Dict[str, int] # Currency -> Amount (Pennies)
    labor_market_min_wage: int
    exchange_rates: Dict[str, float]
    tax_policy: Optional[Any] = None # TaxPolicyDTO

@dataclass(frozen=True)
class EmployeeUpdateDTO:
    employee_id: int
    net_income: int = 0
    fire_employee: bool = False
    severance_pay: int = 0
    quit_job: bool = False

@dataclass(frozen=True)
class ZombieWageEntryDTO:
    employee_id: int
    tick: int
    wage_amount: int

@dataclass(frozen=True)
class HRPayrollResultDTO:
    transactions: List[Transaction]
    employee_updates: List[EmployeeUpdateDTO]
    zombie_wages: List[ZombieWageEntryDTO] = field(default_factory=list)
    employees_to_remove: List[int] = field(default_factory=list)

@runtime_checkable
class IHREngine(Protocol):
    def manage_workforce(self, input_dto: HRDecisionInputDTO) -> HRDecisionOutputDTO:
        ...
    def process_payroll(self, hr_state: Any, context: HRPayrollContextDTO, config: FirmConfigDTO) -> HRPayrollResultDTO:
        """
        Pure function: Calculates payroll transactions and state updates.
        Does NOT mutate hr_state.
        """
        ...

# --- Production Engine Protocols & DTOs ---

@dataclass(frozen=True)
class ProductionInputDTO:
    firm_snapshot: FirmStateDTO
    productivity_multiplier: float = 1.0

@dataclass(frozen=True)
class ProductionResultDTO:
    success: bool
    quantity_produced: float
    quality: float
    specialization: str
    inputs_consumed: Dict[str, float] = field(default_factory=dict)
    production_cost: int = 0
    capital_depreciation: int = 0 # Pennies value to subtract
    automation_decay: float = 0.0 # Value to subtract
    error_message: Optional[str] = None

@runtime_checkable
class IProductionEngine(Protocol):
    def produce(self, input_dto: ProductionInputDTO) -> ProductionResultDTO:
        ...

# --- Brand Engine Protocols & DTOs ---

@dataclass(frozen=True)
class BrandUpdateInputDTO:
    current_adstock: float
    current_awareness: float
    current_perceived_quality: float
    marketing_spend: float
    actual_quality: float
    config: FirmConfigDTO

@dataclass(frozen=True)
class BrandMetricsResultDTO:
    new_adstock: float
    new_brand_awareness: float
    new_perceived_quality: float

@runtime_checkable
class IBrandEngine(Protocol):
    def calculate_brand_metrics(self, input_dto: BrandUpdateInputDTO) -> BrandMetricsResultDTO:
        """
        Pure function: Calculates new brand metrics based on spend and quality.
        """
        ...

# --- Sales Engine Protocols & DTOs ---

@dataclass(frozen=True)
class PricingContextDTO:
    orders: List[Order]
    current_time: int
    inventory_last_sale_tick: Dict[str, int]
    config: FirmConfigDTO
    unit_cost_estimator: Optional[Any] = None

@dataclass(frozen=True)
class PricingResultDTO:
    updated_orders: List[Order]
    updated_last_prices: Dict[str, int] # item_id -> price

@runtime_checkable
class ISalesEngine(Protocol):
    def post_ask(self, state: Any, context: Any) -> Order:
        ...
    def adjust_marketing_budget(self, state: Any, market_context: Any, revenue_this_turn: int, last_revenue: int, last_marketing_spend: int) -> Any:
        ...
    def calculate_dynamic_pricing(self, context: PricingContextDTO) -> PricingResultDTO:
        """
        Pure function: Applies dynamic pricing logic to orders.
        Returns modified orders and price updates.
        """
        ...
```

File: design\3_work_artifacts\specs\wave2_firm_architecture_spec.md
```markdown
# Spec: Wave 2 Firm Architecture Overhaul (SEO Pattern)

## 1. Overview
- **Goal**: Refactor `Firm` architecture to strictly adhere to the **Stateless Engine & Orchestrator (SEO)** pattern.
- **Problem**: Current engines (`BrandEngine`, `SalesEngine`, `HREngine`) mutate `FirmState` objects directly and implicitly rely on `self.parent` or nested state access.
- **Solution**: Convert all engine methods to Pure Functions that accept `InputDTOs` and return `ResultDTOs`. The `Firm` agent (Orchestrator) becomes the sole authority for state mutation.

## 2. Technical Debt Resolution
- **TD-ARCH-FIRM-COUP**: Removed all implicit parent/department references.
- **TD-ARCH-FIRM-MUTATION**: Engines no longer modify state in-place.
- **TD-CRIT-FLOAT-CORE**: Enforced integer math for all monetary values in new DTOs.

## 3. Detailed Design

### 3.1. BrandEngine Refactor
- **Current**: `update(state, ...)` modifies `state.adstock` etc.
- **New**: `calculate_brand_metrics(input_dto: BrandUpdateInputDTO) -> BrandMetricsResultDTO`
- **Logic**:
    1.  Read values from `BrandUpdateInputDTO`.
    2.  Calculate `new_adstock`, `new_awareness`, `new_perceived_quality`.
    3.  Return `BrandMetricsResultDTO`.
- **Orchestrator Action**:
    ```python
    # Firm.py
    brand_result = self.brand_engine.calculate_brand_metrics(...)
    self.state.sales.adstock = brand_result.new_adstock
    self.state.sales.brand_awareness = brand_result.new_brand_awareness
    self.state.sales.perceived_quality = brand_result.new_perceived_quality
    ```

### 3.2. SalesEngine Refactor
- **Current**: `check_and_apply_dynamic_pricing(..., orders, ...)` modifies `orders` list in-place and `state.last_prices`.
- **New**: `calculate_dynamic_pricing(context: PricingContextDTO) -> PricingResultDTO`
- **Logic**:
    1.  Create a deep copy of orders (or build new list).
    2.  Iterate and apply discount logic.
    3.  Track changed prices in a dict.
    4.  Return `PricingResultDTO(updated_orders=..., updated_last_prices=...)`.
- **Orchestrator Action**:
    ```python
    # Firm.py
    pricing_result = self.sales_engine.calculate_dynamic_pricing(...)
    final_orders = pricing_result.updated_orders
    self.state.sales.last_prices.update(pricing_result.updated_last_prices)
    ```

### 3.3. HREngine Refactor
- **Current**: `process_payroll` calls `self.remove_employee` (mutates state) and `_record_zombie_wage` (mutates state).
- **New**: `process_payroll(..., hr_state, ...) -> HRPayrollResultDTO`
- **Logic**:
    1.  Identify employees to remove (validation or firing). Add ID to `employees_to_remove` list in DTO.
    2.  Identify zombie wages. Add `ZombieWageEntryDTO` to `zombie_wages` list in DTO.
    3.  Calculate transactions and updates.
    4.  Return `HRPayrollResultDTO`.
- **Orchestrator Action**:
    ```python
    # Firm.py
    payroll_result = self.hr_engine.process_payroll(...)
    # Apply State Mutations
    for emp_id in payroll_result.employees_to_remove:
        self.state.hr.remove_employee_by_id(emp_id)
    for zombie_entry in payroll_result.zombie_wages:
        self.state.hr.add_zombie_wage(zombie_entry)
    ```

### 3.4. ProductionEngine Validation
- **Current**: `produce` returns `ProductionResultDTO`.
- **Refinement**: Ensure `ProductionState` is treated as read-only.
- **Orchestrator Action**:
    ```python
    # Firm.py
    prod_result = self.production_engine.produce(...)
    if prod_result.success:
        self.state.production.capital_stock -= prod_result.capital_depreciation
        self.state.production.automation_level -= prod_result.automation_decay
        # Update inventory...
    ```

## 4. Verification Plan

### 4.1. New Test Cases
- **Pure Function Tests**:
    - `test_brand_engine_pure_calculation`: Verify inputs -> expected outputs without side effects.
    - `test_sales_engine_dynamic_pricing_pure`: Verify order list transformation.
    - `test_hr_engine_payroll_result_structure`: Verify DTO contains correct removal/zombie instructions.

### 4.2. Regression Testing
- **Impact**: All tests mocking `Firm` and expecting side effects inside engine calls will fail.
- **Strategy**:
    - Update `tests/modules/firm/test_firm_agents.py` and `tests/simulation/components/engines/test_*.py`.
    - Refactor mocks to return expected DTOs instead of `None`.
    - Assert that the *Orchestrator* correctly applies these DTOs to the state.
- **Golden Data**: Use `golden_firms` fixture to provide realistic state snapshots for engine tests.

### 4.3. Audit & Reporting
- **Pre-Implementation**: Create `communications/insights/wave2-firm-architecture-spec.md`.
- **Content**:
    - Log the removal of `Department` classes (if any).
    - Document the specific fields moved to DTOs.
    - Confirm strict separation of concerns.

## 5. Risk Assessment
- **High Risk**: Missing a state update in the Orchestrator. If the Engine previously did X, Y, and Z, and the Orchestrator only implements X and Y from the DTO, Z is lost (Logic Gap).
- **Mitigation**: Comprehensive code review of original Engine logic vs. new DTO structure to ensure 1:1 mapping of all mutations.

## 6. Implementation Steps
1.  **Define DTOs**: Update `modules/firm/api.py`.
2.  **Refactor BrandEngine**: Implement pure `calculate_brand_metrics`.
3.  **Refactor SalesEngine**: Implement pure `calculate_dynamic_pricing`.
4.  **Refactor HREngine**: Implement pure `process_payroll` (handling side-effects via DTO).
5.  **Refactor Firm.py**: Update `_post_decision` and `_update` loops to consume DTOs and apply state changes.
6.  **Fix Tests**: Update unit tests to match new signatures and flows.
```