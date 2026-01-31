# TD-066: Refactoring make_decision Interface

## Context
The `make_decision` method in `Firm` and `Household` agents currently accepts a raw `Government` agent object. This violates encapsulation principles as it gives agents full access to the government's internal state and methods.

## Technical Debt
- **Direct Object Access**: `Firm.make_decision` passes the `Government` object down to `FinanceDepartment` and `_execute_internal_order`.
- **Method Coupling**: `FinanceDepartment` directly calls `government.collect_tax()`.
- **Interface Violation**: Agents should interact with the government via defined protocols (e.g., transactions, settlement system) rather than direct method calls on the agent instance.

## Solution
We introduce `GovernmentFiscalProxy` and `FiscalContext`.
- **GovernmentFiscalProxy**: A wrapper around the `Government` agent that exposes only the necessary financial interface (`IFinancialEntity`) and a restricted `collect_tax` method.
- **FiscalContext**: A DTO passed to `make_decision` containing the proxy.

This restricts what agents can do with the government object, enforcing a boundary.

## Impact
- **Firm**: `make_decision` signature changes. `FinanceDepartment` decoupled from raw `Government` class.
- **Household**: `make_decision` signature changes.
- **Orchestration**: `Phase1_Decision` creates the proxy and context.
- **Tests**: Unit tests mocking `make_decision` inputs need updates.
