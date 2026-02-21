# Insight: TD-ARCH-FIRM-COUP Resolution

## 1. Architectural Insights
- **Decoupling Strategy**: Successfully resolved `TD-ARCH-FIRM-COUP` by implementing the "Stateless Engine & Orchestrator" (SEO) pattern. `Firm` entities no longer pass `self` (or `firm_snapshot`) to `Production`, `HR`, and `Sales` engines for core logic.
- **Context/Intent Protocol**: Defined strict `ContextDTO` (Inputs) and `IntentDTO` (Outputs) for each department.
    - `ProductionEngine`: `ProductionContextDTO` -> `decide_production` -> `ProductionIntentDTO`
    - `HREngine`: `HRContextDTO` -> `decide_workforce` -> `HRIntentDTO`
    - `SalesEngine`: `SalesContextDTO` -> `decide_pricing` -> `SalesIntentDTO`
- **Component Hygiene**: Removed the `attach(self)` method from `IInventoryComponent` and `IFinancialComponent`, eliminating the risk of parent pointer pollution in these fundamental components.
- **Orchestration**: The `Firm` class now explicitly constructs contexts from its state, delegates decision-making to stateless engines, and applies the resulting intents. This centralizes state mutation within the `Firm` and keeps engines pure.

## 2. Regression Analysis
- **Test Adaptations**:
    - `tests/simulation/test_firm_refactor.py`: Updated to mock `decide_production` instead of `produce`, reflecting the `Firm`'s shift to the new API. This confirms that `Firm` is correctly using the decoupled path.
    - `tests/simulation/components/engines/test_production_engine.py`: Updated mocks for `FirmSnapshotDTO` to include `id` and `inventory` attributes, required by the new `_build_context` helper which bridges legacy DTOs to new Context DTOs.
- **Backward Compatibility**: Engines retain legacy methods (`produce`, `manage_workforce`, `post_ask`) as wrappers around the new logic, ensuring that any other systems relying on the old interface remain functional while transitioning.

## 3. Test Evidence
```text
tests/simulation/test_firm_refactor.py::test_firm_initialization_states PASSED [ 11%]
tests/simulation/test_firm_refactor.py::test_command_bus_internal_orders_delegation
-------------------------------- live log call ---------------------------------
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:88 INTERNAL_EXEC | Firm 1 invested 100.0 in INVEST_AUTOMATION.
INFO     modules.firm.orchestrators.firm_action_executor:firm_action_executor.py:112 INTERNAL_EXEC | Firm 1 R&D SUCCESS (Budget: 100.0)
PASSED                                                                   [ 22%]
tests/simulation/test_firm_refactor.py::test_produce_orchestration PASSED [ 33%]
tests/simulation/components/engines/test_production_engine.py::test_produce_success PASSED [ 44%]
tests/simulation/components/engines/test_production_engine.py::test_produce_input_constraint PASSED [ 55%]
tests/simulation/components/engines/test_production_engine.py::test_produce_no_employees PASSED [ 66%]
tests/simulation/components/engines/test_firm_decoupling.py::test_production_engine_decoupled PASSED [ 77%]
tests/simulation/components/engines/test_firm_decoupling.py::test_hr_engine_decoupled PASSED [ 88%]
tests/simulation/components/engines/test_firm_decoupling.py::test_sales_engine_decoupled PASSED [100%]
```
