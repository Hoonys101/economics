# HR and Finance Department Decoupling Insight Report

## 1. Problem Phenomenon
The `HRDepartment` and `FinanceDepartment` were tightly coupled to the concrete `Household` agent class.
- `HRDepartment` stored `List[Household]` directly.
- `HRDepartment` methods (`hire`, `calculate_wage`, `process_payroll`, `fire_employee`) accepted `Household` objects and accessed attributes using `getattr` or direct attribute access, assuming specific implementation details (e.g., `_econ_state`).
- `FinanceDepartment.pay_severance` explicitly required a `Household` object.

This tight coupling meant that:
- Changes to `Household` structure could break HR and Finance logic.
- It was impossible to mock employees for testing without instantiating full `Household` agents (which are heavy, stateful objects).
- Circular dependencies were introduced (e.g., `HRDepartment` imports `Household` which imports `HRDepartment` transitively via `Firm`).

## 2. Root Cause Analysis
The root cause was the lack of an abstraction layer between the organizational components (`Firm`'s departments) and the agents they interact with (`Household`).
- **HR Domain:** Needs to know about skills, education, employment status, and wage history. It does not need to know about household consumption, political views, or biological state.
- **Finance Domain:** Needs to transfer money. It only requires a financial entity interface (`IFinancialEntity`).

## 3. Solution Implementation Details
We introduced the `IEmployeeDataProvider` protocol to decouple these components.

### 3.1. `IEmployeeDataProvider` Protocol
Defined in `modules/hr/api.py`, this protocol inherits from `IFinancialEntity` and specifies the exact interface required by HR operations:
- **Identity:** `id`, `employer_id`, `is_employed`.
- **Skills & Education:** `labor_skill`, `education_level`.
- **Compensation:** `labor_income_this_tick` (setter/getter).
- **Lifecycle:** `employment_start_tick`, `quit()`.

### 3.2. Household Enhancement
Updated `HouseholdPropertiesMixin` in `modules/household/mixins/_properties.py` to expose necessary fields (`labor_skill`, `education_level`, `labor_income_this_tick`, `employment_start_tick`) as properties, delegating to the internal `_econ_state` DTO.
Updated `Household` in `simulation/core_agents.py` to explicitly implement `IEmployeeDataProvider`.

### 3.3. HRDepartment Refactoring
Refactored `simulation/components/hr_department.py`:
- Replaced `List[Household]` with `List[IEmployeeDataProvider]`.
- Updated all method signatures to usage `IEmployeeDataProvider`.
- Replaced brittle `getattr` calls with typed property access guaranteed by the protocol.

### 3.4. FinanceDepartment Refactoring
Refactored `simulation/components/finance_department.py`:
- Updated `pay_severance` to accept `IFinancialEntity` instead of `Household`. This makes the method generic for any entity that can receive funds.

## 4. Lessons Learned & Technical Debt
- **Lesson:** Interface Segregation Principle (ISP) is crucial for large agent-based models. Agents like `Household` become "God Classes" if not accessed via narrow protocols.
- **Technical Debt:** `Household` still carries a lot of mixins and complexity. While we decoupled consumers, the provider (`Household`) is still monolithic. Future work could split `Household` into smaller composed entities, but for now, the facade pattern with protocols works well.
- **Insight:** Using `@property` in Mixins to expose internal DTO state is a powerful way to implement protocols without exposing the internal DTO structure (Purity Guard).
