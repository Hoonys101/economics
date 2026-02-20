# Firm Refactor & AI Debt Awareness Hardening - Insight Report

## 1. Architectural Insights

### Debt Blindness in Firm AI
Prior to this hardening, the Firm's decision-making engines (`FinanceEngine`, `FirmSystem2Planner`) were effectively "debt blind" in their stateless operations.
*   **Root Cause:** `FinanceStateDTO` lacked `total_debt_pennies` and `average_interest_rate` fields. While the internal `FinanceState` tracked debt, the DTO boundary stripped this information before it reached the stateless engines.
*   **Impact:** The `FinanceEngine` defaulted to a 1% repayment heuristic (which evaluated to 0 if debt wasn't visible), and the `FirmSystem2Planner` calculated NPV without accounting for interest expenses, leading to overly optimistic valuations of leveraged projects.

### Protocol Purity & Circular Dependencies
*   **Challenge:** The `Firm` (Orchestrator) needs to query the `Bank` to get accurate debt status. However, `LoanMarket` is a concrete class, and the `ILoanMarket` interface is designed for Housing/Sagas and lacks `get_debt_status`.
*   **Resolution:** We enforced strict type checking using `isinstance` against `IBank` (Protocol) to access banking services safely. We avoided `hasattr` checks which are prone to runtime errors and mock drift. We used local imports to resolve circular dependencies between `Firm` and `LoanMarket`.

### Unit Consistency (The Penny Standard)
*   **Decision:** All financial values (debt, revenue, interest) are strictly maintained in integer pennies within the DTOs and Engine inputs.
*   **Clarification:** `FirmSystem2Planner` operates on these penny values (cast to float for NPV math). We verified that `revenue`, `wages`, and `interest_expense` are all consistently in pennies, ensuring the NPV calculation is dimensionally correct.

## 2. Regression Analysis

### Broken Tests
*   **`tests/unit/modules/firm/test_engines.py`**:
    *   **Reason:** The test used `MagicMock(spec=FinanceStateDTO)`. Since `altman_z_score` and `consecutive_loss_turns` were not explicitly set on the mock, the new logic in `FinanceEngine` (which checks distress status) raised an `AttributeError`.
    *   **Fix:** Updated the test fixture to explicitly initialize these fields on the mock, reflecting a "Healthy" firm state by default.
    *   **Logic Change:** The repayment logic changed from a hardcoded 1% to a strategic 0.5% (healthy) / 5.0% (distressed). Test assertions were updated to match this smarter behavior.

*   **`tests/integration/scenarios/phase21/test_firm_system2.py`**:
    *   **Reason:** Integration tests mocked `FirmStateDTO` but omitted the new `total_debt_pennies` and `average_interest_rate` fields. This caused `getattr` to return `MagicMock` objects instead of defaults in some contexts (or failure in comparisons).
    *   **Fix:** Updated mocks to include these fields with default values (0).

## 3. Test Evidence

**Command:** `python -m pytest tests/unit/modules/firm/test_engines.py tests/integration/scenarios/phase21/test_firm_system2.py tests/integration/scenarios/phase21/test_automation.py`

**Output:**
```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-8.3.4, pluggy-1.5.0
rootdir: /app
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.3, mock-3.14.0
asyncio: mode=Mode.STRICT, default_loop_scope=None
collected 12 items

tests/unit/modules/firm/test_engines.py::TestFinanceEngine::test_plan_budget_basics PASSED [  8%]
tests/unit/modules/firm/test_engines.py::TestFinanceEngine::test_plan_budget_with_debt_healthy PASSED [ 16%]
tests/unit/modules/firm/test_engines.py::TestFinanceEngine::test_plan_budget_with_debt_distressed PASSED [ 25%]
tests/unit/modules/firm/test_engines.py::TestFinanceEngine::test_plan_budget_returns_integers PASSED [ 33%]
tests/unit/modules/firm/test_engines.py::TestHREngine::test_manage_workforce_hiring PASSED [ 41%]
tests/unit/modules/firm/test_engines.py::TestHREngine::test_manage_workforce_firing PASSED [ 50%]
tests/unit/modules/firm/test_engines.py::TestHREngine::test_manage_workforce_wage_scaling PASSED [ 58%]
tests/integration/scenarios/phase21/test_firm_system2.py::test_system2_planner_guidance_automation_preference PASSED [ 66%]
tests/integration/scenarios/phase21/test_firm_system2.py::test_system2_planner_guidance_ma_preference PASSED [ 75%]
tests/integration/scenarios/phase21/test_firm_system2.py::test_system2_planner_with_debt PASSED [ 83%]
tests/integration/scenarios/phase21/test_automation.py::test_firm_automation_init PASSED [ 91%]
tests/integration/scenarios/phase21/test_automation.py::test_production_function_with_automation PASSED [100%]

============================== 12 passed in 0.42s ==============================
```
