# Report: Architectural Analysis of Household and Finance Modules

## Executive Summary
The refactoring effort has successfully implemented the stateless engine and orchestrator pattern in the `Household` module, which adheres well to architectural guidelines. However, the `Finance` module exhibits significant deviations: the `Bank` agent retains state, and several finance engines improperly mutate input DTOs directly instead of operating as pure functions.

## Detailed Analysis

### 1. Household Module (`simulation/core_agents.py`, `modules/household/engines/`)
- **Status**: ✅ Implemented
- **Evidence**:
  - **Orchestrator Pattern**: The `Household` agent acts as a proper orchestrator. For example, in `make_decision` (`core_agents.py:L822-L885`), it calls the `budget_engine` and `consumption_engine`, then applies the state changes from their output DTOs to its own state (`self._econ_state = budget_output.econ_state`).
  - **Stateless Engines**: All five household engines (`Lifecycle`, `Needs`, `Social`, `Budget`, `Consumption`) are stateless. They do not contain agent-specific state and operate on input DTOs, returning output DTOs. For instance, `LifecycleEngine.process_tick` (`lifecycle.py:L18-L62`) takes a `LifecycleInputDTO`, creates a copy of the state to work on, and returns a `LifecycleOutputDTO` without modifying any `self` attributes.
  - **DTO Usage**: Communication is handled via DTOs (e.g., `LifecycleInputDTO`, `NeedsInputDTO`). The engines do not receive direct handles to the `Household` agent.
- **Notes**:
  - A minor architectural smell was noted in `BudgetEngine._plan_housing` (`budget.py:L86-L119`). It uses a `StateWrapper` class to mimic an agent structure for a legacy planner. While it doesn't pass the live agent instance, this workaround deviates slightly from pure DTO communication.

### 2. Finance Engines (`modules/finance/engines/`)
- **Status**: ⚠️ Partial
- **Evidence**:
  - **Correct Engines**: `LoanRiskEngine` (`loan_risk_engine.py`) and `MonetaryEngine` (`monetary_engine.py`) are implemented correctly. They are stateless, take DTOs as input, and return a new DTO without modifying the inputs.
  - **Incorrect Engines (State Mutation)**: Multiple engines mutate the input `FinancialLedgerDTO` directly instead of returning a modified copy. This violates the "Pure Function" principle for engines.
    - **`DebtServicingEngine.service_all_debt`** (`debt_servicing_engine.py:L13-L126`): Modifies `deposit.balance`, `loan.remaining_principal`, and `bank.retained_earnings` on the input `ledger` object.
    - **`LiquidationEngine.liquidate`** (`liquidation_engine.py:L14-L113`): Modifies `loan.remaining_principal` and `loan.is_defaulted` on the input `ledger`.
    - **`LoanBookingEngine.grant_loan`** (`loan_booking_engine.py:L20-L80`): Directly adds new loans and deposits to the input `ledger` (`bank_state.deposits[deposit_id] = deposit`).
    - **`InterestRateEngine.update_rates`** (`interest_rate_engine.py:L13-L24`): Directly modifies `bank.base_rate` on the input `ledger`.
- **Notes**: These engines are stateless themselves (no `self.state`), but their implementation is impure, leading to side effects on the calling orchestrator's state.

### 3. Bank Agent (`simulation/bank.py`)
- **Status**: ❌ Missing
- **Evidence**:
  - **Stateful Proxy**: The `Bank` agent is not a fully stateless proxy. It maintains its own state via `self._wallet` (`bank.py:L60`) in parallel to the `FinanceSystem`'s central ledger.
  - **Dual State Management**: Methods like `deposit` (`bank.py:L94-L101`) and `withdraw` (`bank.py:L103-L110`) attempt to update both the central `FinanceSystem` ledger and the internal `self._wallet`, creating two sources of truth and violating the design principle.
- **Notes**: The agent's role as a pure orchestrator is compromised by its residual state-holding responsibilities.

## Risk Assessment
- **Data Integrity**: The direct mutation of the `FinancialLedgerDTO` by multiple finance engines creates a risk of unpredictable side effects and makes debugging difficult. The "single source of truth" principle is violated.
- **Technical Debt**: The `Bank` agent's dual state management (`_wallet` and `FinanceSystem`) is a significant source of technical debt that will complicate future development and bug-fixing.
- **Inconsistent Implementation**: The contrast between the compliant `Household` module and the non-compliant `Finance` module will lead to confusion and errors as the project grows.

## Conclusion
The refactoring to a stateless engine architecture has been successful for the `Household` module, which serves as a good model for the rest of the system. However, the `Finance` module requires significant rework to align with the project's architectural guardrails. The primary action items are to make the finance engines pure functions by having them return a modified copy of the ledger DTO and to refactor the `Bank` agent into a truly stateless proxy that relies exclusively on the `FinanceSystem` for state.
