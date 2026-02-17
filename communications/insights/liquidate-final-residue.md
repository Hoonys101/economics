# Mission: Liquidate 6 Residual Test Failures

## Architectural Insights

1.  **Strict Protocol Compliance in Mocks**:
    The `ISettlementSystem` and other components now strictly enforce `isinstance(agent, IFinancialAgent)` checks. Legacy mocks (like `MockGovernment`, `MockCentralBank`) that relied on duck typing (`hasattr`) failed because they did not inherit from the Protocol or implement all required methods (specifically `get_liquid_assets`, `get_total_debt`). This confirms the shift towards **Protocol Purity**. All mocks must now fully implement the Protocol contract, even if they are simple stubs.

2.  **DTO Purity and Valid Attributes**:
    The `BailoutCovenant` DTO strictly defines its attributes. Legacy code attempting to use deprecated attributes like `executive_salary_freeze` or non-existent ones like `mandatory_repayment` caused failures. This reinforces **DTO Purity**; we must adhere to the defined schema and not assume flexibility in Dataclasses.

3.  **Integer Math Purity (Pennies)**:
    The `FinanceEngine` operates strictly in pennies (integers). Configuration values provided as floats (e.g., `10.0` for maintenance fee) must be correctly typed as integers (e.g., `1000` pennies) in test setups if the engine does not perform internal conversion. This avoids "magic number" mismatches and ensures **Zero-Sum Integrity** by preventing floating-point drift.

4.  **Component Interaction & State Preconditions**:
    The `AIDrivenFirmDecisionEngine` integrates multiple logic layers (`CorporateManager`, `Pricing Logic`). The `Fire-Sale` logic acts as a safety override. Tests verifying standard pricing behavior (like `SalesAggressiveness`) must ensure the agent state (e.g., cash balance) does not trigger these emergency overrides, illustrating the importance of **State Preconditions** in unit testing complex decision engines.

## Test Evidence

```
=========================== short test summary info ============================
SKIPPED [1] tests/unit/decisions/test_household_integration_new.py:12: TODO: Fix integration test setup. BudgetEngine/ConsumptionEngine interaction results in empty orders.
================= 807 passed, 1 skipped, 10 warnings in 18.79s =================
```
