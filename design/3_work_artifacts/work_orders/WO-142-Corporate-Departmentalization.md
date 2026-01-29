# Work Order: WO-142 - CorporateManager Departmentalization

## 🎯 Objective
Refactor the monolithic `CorporateManager` (629+ LOC) in `simulation/decisions/corporate_manager.py` into a set of specialized, departmental managers (HR, Finance, Operations, Sales). This transition will transform the `CorporateManager` from a "God Class" that does everything into an "Orchestrator" that coordinates specialized agents.

---

## 🛠️ Tasks

### 1. Define API & DTOs
- Create `simulation/decisions/firm/api.py` (or similar) based on the specification.
- Implement the following DTOs: `DecisionContextDTO`, `FinancialPlanDTO`, `HRPlanDTO`, `OperationsPlanDTO`, `SalesPlanDTO`.
- Define Protocol interfaces for `FinanceManager`, `HRManager`, `OperationsManager`, and `SalesManager`.

### 2. Implement Departmental Managers
Create the following specialized modules in `simulation/decisions/firm/`:
- `finance_manager.py`: Handles budgets, debt, and dividends.
- `hr_manager.py`: Handles hiring, firing, and wage setting.
- `operations_manager.py`: Handles production targets and **R&D investment (Preserve WO-136 logic)**.
- `sales_manager.py`: Handles pricing strategy and marketing.

### 3. Refactor CorporateManager (The Orchestrator)
- Update `simulation/decisions/corporate_manager.py`:
    - Inject departmental managers into `__init__`.
    - Refactor `realize_ceo_actions` (or the main decision loop) to:
        1. Gather state into `DecisionContextDTO`.
        2. Call managers in the specified sequence (Finance -> HR -> Operations -> Sales).
        3. Apply the resulting plans to the simulation state.
- Strictly adhere to the **Unidirectional Data Flow** (Orchestrator -> Departments).

### 4. Test Suite Reconstruction
- **Deprecate** `tests/unit/test_corporate_manager.py`.
- Create focused unit tests for each new manager in `tests/unit/corporate/`.
- Create an integration test `tests/integration/test_corporate_orchestrator.py`.

---

## 🏗️ Technical Constraints
- **Preservation of WO-136**: The new Endogenous R&D logic must be correctly migrated to `OperationsManager`.
- **DTO Purity**: No manager should have direct access to `WorldState` or `Firm` objects; only DTOs.
- **No Circular Dependencies**: Departments must not know about each other; only the Orchestrator knows all.

---

## 🏁 Success Sign-off
- [ ] `CorporateManager` LOC reduced significantly (target < 200 lines for the orchestrator).
- [ ] All corporate logic successfully delegated to specialized modules.
- [ ] New test suite passes with 100% coverage for departmental logic.
- [ ] Endogenous R&D (WO-136) remains functional in the Industrial Revolution scenario.
