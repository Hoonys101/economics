# Structural Audit Report

## Executive Summary
This report documents the findings of a structural audit performed on the codebase. The audit focused on identifying "God Classes" (classes exceeding 800 lines of code) and "Abstraction Leaks" (instances where raw agent objects are passed into decision engines or other stateless components).

## God Class Detection
Classes exceeding 800 lines of code were identified as potential "God Classes". These classes often violate the Single Responsibility Principle and become difficult to maintain.

### Findings
1.  **`simulation/firms.py`**: `Firm` class (1164 lines)
    *   **Responsibilities**: Implements `ILearningAgent`, `IFinancialEntity`, `IFinancialAgent`, `ILiquidatable`, `IOrchestratorAgent`, `ICreditFrozen`, `IInventoryHandler`, `ICurrencyHolder`, `ISensoryDataProvider`, `IConfigurable`, `IPropertyOwner`, `IFirmStateProvider`.
    *   **Description**: The `Firm` class acts as an orchestrator for firm operations but contains significant logic related to state management, inventory handling, and coordination of multiple engines (HR, Finance, Production, Sales). Despite delegation to engines, the class remains overly complex.

2.  **`simulation/core_agents.py`**: `Household` class (1121 lines)
    *   **Responsibilities**: Implements `ILearningAgent`, `IEmployeeDataProvider`, `IEducated`, `IFinancialEntity`, `IFinancialAgent`, `IOrchestratorAgent`, `ICreditFrozen`, `IInventoryHandler`, `ISensoryDataProvider`, `IPropertyOwner`, `IInvestor`.
    *   **Description**: Similar to `Firm`, the `Household` class orchestrates household behavior but handles too many concerns directly, including lifecycle management, needs assessment, and financial operations.

## Abstraction Leak Detection
Abstraction leaks occur when raw agent objects (stateful entities) are passed directly into stateless engines or decision components, violating the Orchestrator-Engine pattern and creating tight coupling.

### Findings
1.  **`Firm.produce` -> `ProductionEngine`**
    *   **Location**: `simulation/firms.py`
    *   **Leak**: The `Firm` instance (`self`) is passed to `self.production_engine.produce`.
    *   **Interface**: It is passed as `inventory_handler: IInventoryHandler`.
    *   **Impact**: While typed as an interface, the engine still depends on the agent object which implements the interface. Ideally, a separate `Inventory` component or DTO should be passed to fully decouple the engine from the agent implementation.

2.  **`Firm.generate_transactions` -> `HREngine`**
    *   **Location**: `simulation/firms.py`
    *   **Leak**: The `Government` agent (`government`) is passed directly to `self.hr_engine.process_payroll`.
    *   **Interface**: Passed as `government: Optional[Any]`.
    *   **Impact**: `HREngine` (in `simulation/components/engines/hr_engine.py`) calls methods on the raw `Government` agent (e.g., `calculate_income_tax`, `get_survival_cost`). This creates a direct dependency between the HR Engine and the Government Agent, violating the stateless engine principle.

3.  **`Government.make_policy_decision` -> `GovernmentDecisionEngine`**
    *   **Location**: `simulation/agents/government.py`
    *   **Leak**: The `CentralBank` agent (`central_bank`) is passed to `self.decision_engine.decide`.
    *   **Interface**: Passed as `central_bank: Any`.
    *   **Impact**: Although potentially unused in current logic (e.g., `_decide_taylor_rule`), the signature allows for direct interaction with the Central Bank agent, which is an abstraction leak.

4.  **`Government.provide_firm_bailout` -> `PolicyExecutionEngine`**
    *   **Location**: `simulation/agents/government.py`
    *   **Leak**: The raw `Firm` agent (`firm`) is passed in a list to `self.execution_engine.execute`.
    *   **Interface**: Passed as `agents: List[Any]`.
    *   **Impact**: `PolicyExecutionEngine` (in `modules/government/engines/execution_engine.py`) retrieves the firm and passes it to `context.finance_system.evaluate_solvency`, `context.welfare_manager.provide_firm_bailout`, and `context.finance_system.grant_bailout_loan`. This propagates the leak deep into the execution layer.

## Recommendations
*   **Refactor God Classes**: Further decompose `Firm` and `Household` by extracting logic into dedicated components or services. Move state management strictly to DTOs and logic to engines.
*   **Fix Abstraction Leaks**:
    *   Replace `IInventoryHandler` passing in `ProductionEngine` with an `InventoryDTO` or a dedicated `InventoryService`.
    *   Pass `TaxService` or `FiscalPolicyDTO` to `HREngine` instead of the raw `Government` agent.
    *   Remove `central_bank` from `GovernmentDecisionEngine` signature or replace with `CentralBankStateDTO`.
    *   Refactor `PolicyExecutionEngine` to operate on `AgentID` and use a `Registry` or `Service` to look up necessary data, or pass required DTOs instead of raw agents.