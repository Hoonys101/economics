# SPEC: TD-073 Firm Refactor (V2)

**Objective**: Liquidate technical debt TD-073 and TD-190 by refactoring the `Firm` class into a pure facade, removing state-delegating `@property` wrappers, and decomposing the `_execute_internal_order` method.

---

## 1. Problem Definition

-   **TD-073 (Firm "Split Brain")**: The `Firm` class violates the Single Responsibility Principle. It acts as both a facade and a state holder. Convenience `@property` wrappers (e.g., `firm.assets`) obscure the true location of state, which resides in departmental components (`firm.finance`, `firm.hr`). This makes the class difficult to reason about, test, and use for AI model training.
-   **TD-190 (Complex `if/elif` chain)**: The `_execute_internal_order` method in `firms.py` is a large procedural block that directly manipulates state, violating SRP and the facade pattern.

## 2. Implementation Plan

### Phase 1: Remove Property Wrappers

1.  **Targeted Removal**: Systematically delete all `@property` definitions from `simulation/firms.py` that delegate state access to a sub-component. This includes, but is not limited to:
    -   `assets` (delegates to `finance.balance`)
    -   `current_profit` (delegates to `finance.current_profit`)
    -   `revenue_this_turn` (delegates to `finance.revenue_this_turn`)
    -   `expenses_this_tick` (delegates to `finance.expenses_this_tick`)
    -   `sales_volume_this_tick`
    -   `last_sales_volume`
2.  **Update Call Sites**: Use `ripgrep` or a similar tool to find all usages of the removed properties throughout the codebase (in `modules/`, `simulation/`, and `tests/`).
3.  **Refactor Access Patterns**: Modify each call site to use the explicit, direct path to the state.
    -   `firm.assets` -> `firm.finance.balance`
    -   `firm.current_profit` -> `firm.finance.current_profit`
    -   `firm.hr.employees` (already correct, but serves as the pattern)

### Phase 2: Decompose `_execute_internal_order`

1.  **Create Departmental Methods**: Implement new public methods on the relevant department classes to handle specific internal orders. The logic from the `if/elif` block will be moved into these methods.

    -   **`ProductionDepartment` (`production_department.py`)**:
        -   `invest_in_automation(amount: float) -> bool`: Handles the logic for automation investment.
        -   `invest_in_rd(amount: float) -> bool`: Handles R&D investment and its probabilistic outcome.
        -   `invest_in_capex(amount: float) -> bool`: Handles capital expenditure.
        -   `set_production_target(quantity: float)`

    -   **`FinanceDepartment` (`finance_department.py`)**:
        -   `set_dividend_rate(rate: float)`
        -   `pay_ad_hoc_tax(amount: float, reason: str, government: Any, current_time: int) -> bool`

    -   **`SalesDepartment` (`sales_department.py`)**:
        -   `set_price(item_id: str, price: float)`

    -   **`HRDepartment` (`hr_department.py`)**:
        -   `fire_employee(employee_id: int, severance_pay: float) -> bool`

2.  **Refactor `Firm._execute_internal_order`**: The method in `firms.py` will be reduced to a simple router that calls the appropriate new departmental method.

    ```python
    # In simulation/firms.py
    def _execute_internal_order(self, order: Order, government: Optional[Any], current_time: int) -> None:
        """[REFACTORED] Routes internal orders to the correct department."""
        if order.order_type == "SET_TARGET":
            self.production.set_production_target(order.quantity)
        elif order.order_type == "INVEST_AUTOMATION":
            self.production.invest_in_automation(order.quantity, government)
        elif order.order_type == "SET_PRICE":
            self.sales.set_price(order.item_id, order.quantity)
        # ... etc.
    ```

### Phase 3: DTO Definitions (Composite State)

1.  **Departmental DTOs**: If they don't exist, create `FinanceStateDTO`, `HRStateDTO`, `ProductionStateDTO`, `SalesStateDTO` in a new `simulation/dtos/department_dtos.py` file. These will be dataclasses or TypedDicts representing the state of each department.
2.  **Composite `FirmStateDTO`**: Modify `FirmStateDTO` in `simulation/dtos/firm_state_dto.py` to be a composite of the departmental DTOs.

    ```python
    # In simulation/dtos/firm_state_dto.py
    from .department_dtos import FinanceStateDTO, HRStateDTO, ...

    @dataclass
    class FirmStateDTO:
        id: int
        is_active: bool
        # ... other core firm attributes
        finance: FinanceStateDTO
        hr: HRStateDTO
        production: ProductionStateDTO
        sales: SalesStateDTO
    ```
3.  **Update `Firm.get_state_dto()`**: Refactor this method to construct the new composite DTO from its departmental components.

## 3. Verification Plan

1.  **Static Analysis**: After refactoring, confirm no targeted `@property` definitions remain in `firms.py`.
2.  **Unit Tests**:
    -   All existing unit tests for `Firm` and `CorporateManager` must be updated to use the new access patterns (e.g., `firm.finance.balance`) and must pass.
    -   New unit tests must be created for the new methods on each department class (e.g., `test_production_invest_in_automation`).
3.  **Integration Tests**: The entire test suite must pass. Pay special attention to tests that run the full simulation loop to catch any cascading failures.
4.  **Golden Fixture Audit**:
    -   The `golden_firms` fixture in `tests/conftest.py` creates mocks. The generation script or the mock creation logic (`loader.create_firm_mocks()`) must be updated. The mocks must now have nested mock objects (e.g., `firm.finance.balance` must be a valid attribute).

## 4. Risk & Impact Audit

-   **Critical Risk**: **Widespread Test Failure**. Removing properties is a breaking change that will affect dozens of tests.
    -   **Mitigation**: This is an expected outcome. The verification plan explicitly requires a systematic search-and-replace operation on the `tests/` directory to update all failing tests. This is a mechanical task that must be completed thoroughly.
-   **Architectural Impact**: This change is **highly positive**. It resolves two major pieces of technical debt (TD-073, TD-190) and strictly enforces the project's desired Facade and SRP principles for the `Firm` agent, improving long-term maintainability.
