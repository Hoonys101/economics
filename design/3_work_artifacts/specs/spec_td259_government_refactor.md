# Design Document: Government Agent Refactor (TD-259)

## 1. Introduction

- **Purpose**: This document outlines the architectural refactoring of the `Government` agent to resolve the technical debt item **TD-259**.
- **Scope**: The `Government` agent (`simulation/agents/government.py`) will be decomposed from a monolithic "God Class" into a state-managing **Orchestrator** and several stateless **Engines**, following the established pattern of the `Firm` agent.
- **Goals**:
  - Resolve `TD-259` by adhering to the Single Responsibility Principle (SRP).
  - Improve testability, maintainability, and extensibility of the government's logic.
  - Eliminate the "God Class" anti-pattern and reduce tight coupling.
  - Establish a clear, DTO-based contract for all government operations.

## 2. System Architecture (High-Level)

The refactored `Government` agent will follow an Orchestrator-Engine pattern.

```
+--------------------------+
|   Simulation Engine      |
| (e.g., main loop)        |
+--------------------------+
           |
           v
+--------------------------+      +---------------------------+
| Government (Orchestrator)|----->|  GovernmentDecisionEngine |
| - Holds State (DTO)      |      |  (Stateless)              |
| - Holds Dependencies     |      |  - Uses IGovernmentPolicy |
|   (SettlementSystem, etc)|<-----|  - Returns PolicyDecision |
+--------------------------+      +---------------------------+
           |
           v
+--------------------------+      +---------------------------+
| Government (Orchestrator)|----->|  PolicyExecutionEngine    |
| - Dispatches Commands    |      |  (Stateless)              |
|                          |<-----|  - Returns ExecutionResult|
+--------------------------+      +---------------------------+
                                             |
                                             v
                         +-------------------+-------------------+
                         |                   |                   |
               +-----------------+ +-----------------+ +-----------------------+
               |   TaxService    | | WelfareManager  | | InfrastructureManager |
               +-----------------+ +-----------------+ +-----------------------+

```

### Component Roles:

1.  **`Government` (Orchestrator)**:
    - **Responsibility**: Manages the agent's state via a `GovernmentStateDTO`. Holds references to external system dependencies (e.g., `SettlementSystem`, `FinanceSystem`).
    - **Execution Flow**: In its main `make_decision` cycle, it gathers state, calls the `DecisionEngine`, receives a `PolicyDecisionDTO`, passes it to the `ExecutionEngine`, receives an `ExecutionResultDTO`, and processes the results (e.g., executing payments via the `SettlementSystem`).

2.  **`GovernmentDecisionEngine` (Stateless Engine)**:
    - **Responsibility**: Contains the logic for *what* to do. It encapsulates the various policy strategies (`TaylorRulePolicy`, `AdaptiveGovPolicy`, etc.).
    - **Interface**: Receives the current `GovernmentStateDTO` and `MarketSnapshotDTO` and returns a `PolicyDecisionDTO` that represents a high-level strategic choice (e.g., "increase taxes," "provide bailouts").

3.  **`PolicyExecutionEngine` (Stateless Engine)**:
    - **Responsibility**: Contains the logic for *how* to implement a policy decision. It uses existing service components (`TaxService`, `WelfareManager`) to perform calculations.
    - **Interface**: Receives a `PolicyDecisionDTO` and a `GovernmentExecutionContext` (containing dependencies like `SettlementSystem`). It returns an `ExecutionResultDTO` containing concrete commands like `PaymentRequestDTO`s that the orchestrator will execute.

## 3. Detailed Design

### 3.1. DTO & Interface Definitions (`modules/government/api.py`)

```python
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field

# --- DTOs for State and Communication ---

@dataclass
class GovernmentStateDTO:
    """Immutable snapshot of the Government's state."""
    tick: int
    assets: Dict[str, float]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    fiscal_policy: 'FiscalPolicyDTO'
    # ... other state fields from the original Government class ...
    ruling_party: Any # e.g., PoliticalParty Enum
    approval_rating: float
    policy_lockouts: Dict[Any, int] # <PolicyActionTag, locked_until_tick>

@dataclass
class PolicyDecisionDTO:
    """High-level strategic decision from the DecisionEngine."""
    action_tag: Any # e.g., PolicyActionTag Enum
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GovernmentExecutionContext:
    """Injectable dependencies for the ExecutionEngine."""
    settlement_system: 'ISettlementSystem'
    finance_system: 'IFinanceSystem'
    tax_service: 'ITaxService'
    welfare_manager: 'WelfareManager'
    # ... any other required external systems ...

@dataclass
class ExecutionResultDTO:
    """Concrete commands resulting from policy execution."""
    payment_requests: List['PaymentRequestDTO'] = field(default_factory=list)
    bailout_results: List['BailoutResultDTO'] = field(default_factory=list)
    monetary_ledger_updates: Dict[str, float] = field(default_factory=dict)
    state_updates: Dict[str, Any] = field(default_factory=dict) # For Orchestrator to update its state

# --- Engine Interfaces ---

class IGovernmentDecisionEngine(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def decide(self, state: GovernmentStateDTO, market_snapshot: 'MarketSnapshotDTO', central_bank: 'CentralBank') -> PolicyDecisionDTO:
        """Decides on a policy action based on current state and market data."""
        ...

class IPolicyExecutionEngine(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def execute(self, decision: PolicyDecisionDTO, state: GovernmentStateDTO, agents: List[Any], context: GovernmentExecutionContext) -> ExecutionResultDTO:
        """Executes a policy decision and returns a list of concrete results."""
        ...
```

### 3.2. Logic Migration (Pseudo-code)

#### `Government` (Orchestrator) `make_decision` method

```python
# In class Government(IOrchestratorAgent):
def make_decision(self, market_data, agents, ...):
    # 1. Gather State
    current_state_dto = self.get_state_dto() # Create DTO from self attributes
    market_snapshot = MarketSnapshotDTO.from_market_data(market_data)

    # 2. Call Decision Engine
    policy_decision = self.decision_engine.decide(current_state_dto, market_snapshot, self.central_bank)

    # 3. Prepare Execution Context
    exec_context = GovernmentExecutionContext(
        settlement_system=self.settlement_system,
        finance_system=self.finance_system,
        tax_service=self.tax_service,
        welfare_manager=self.welfare_manager
    )

    # 4. Call Execution Engine
    execution_result = self.execution_engine.execute(
        policy_decision,
        current_state_dto,
        agents, # Pass agent list for checks
        exec_context
    )

    # 5. Process Results (Dispatch Commands)
    for req in execution_result.payment_requests:
        self.settlement_system.transfer(req.payer, req.payee, req.amount, req.memo)
    
    # ... process other results (bailouts, etc.)

    # 6. Update Internal State
    self.apply_state_updates(execution_result.state_updates)

```

#### `GovernmentDecisionEngine` `decide` method

```python
# In class GovernmentDecisionEngine(IGovernmentDecisionEngine):
def decide(self, state, market_snapshot, central_bank):
    # Re-implements logic from the old `government.make_policy_decision`
    # Uses the injected policy strategy (e.g., self.policy_strategy = TaylorRulePolicy())

    # 1. Determine fiscal stance (can be done here or in orchestrator)
    fiscal_policy = self.tax_service.determine_fiscal_stance(market_snapshot)
    
    # 2. Run the core policy logic (e.g., AdaptiveGovPolicy)
    decision = self.policy_strategy.decide(state, ...) # Pass DTOs
    
    # 3. Convert the output to a standardized PolicyDecisionDTO
    return PolicyDecisionDTO(
        action_tag=decision.get("action_taken"),
        parameters={"welfare_multiplier": decision.get("welfare_multiplier")}
    )
```

#### `PolicyExecutionEngine` `execute` method

```python
# In class PolicyExecutionEngine(IPolicyExecutionEngine):
def execute(self, decision, state, agents, context):
    
    if context.policy_lockout_manager.is_locked(decision.action_tag, state.tick):
        return ExecutionResultDTO() # Return empty result if locked

    # Route decision to the correct handler method
    if decision.action_tag == PolicyActionTag.SOCIAL_POLICY:
        return self._execute_social_policy(state, agents, context)
    elif decision.action_tag == PolicyActionTag.FIRM_BAILOUT:
        return self._execute_firm_bailout(decision.parameters, agents, context)
    # ... other handlers ...

def _execute_social_policy(self, state, agents, context):
    # Re-implements logic from old `government.execute_social_policy`
    # Uses services passed in via the context
    welfare_result = context.welfare_manager.run_welfare_check(...)
    tax_result = context.tax_service.collect_wealth_tax(...)

    # Aggregate results into a single DTO
    all_payment_requests = welfare_result.payment_requests + tax_result.payment_requests
    return ExecutionResultDTO(payment_requests=all_payment_requests)
```

## 4. Verification Plan (Test Strategy)

This refactor requires a careful, phased testing approach to prevent regressions.

1.  **Phase 1: Pre-Refactor (Behavioral Integration Tests)**
    *   Create a new test suite: `tests/integration/test_government_behavior.py`.
    *   These tests will run the simulation for a small number of ticks (e.g., 10-20) with a fixed seed and golden data fixtures (`golden_households`, `golden_firms`).
    *   They will **not** inspect the `Government` agent's internal state.
    *   Assertions will focus on high-level, observable outcomes:
        - `assert total_tax_revenue_collected == expected_value`
        - `assert total_welfare_paid == expected_value`
        - `assert government_final_assets == expected_final_assets`
    *   These tests establish the behavioral baseline that the refactored code must match.

2.  **Phase 2: During Refactor (Unit & Integration Testing)**
    *   **Unit Tests**: Write new, focused unit tests for `GovernmentDecisionEngine` and `PolicyExecutionEngine`. All external dependencies (services, DTOs) will be mocked. This validates the extracted logic in isolation.
    *   **Integration Test Migration**: Modify the tests from Phase 1 to instantiate the new `Government` orchestrator class. The core test logic and assertions will remain **unchanged**. These tests will initially fail. The refactor is considered successful when these behavioral tests pass again.

3.  **Phase 3: Post-Refactor (Cleanup)**
    *   The old, brittle unit tests that directly patched methods on the original `Government` class will be deleted. The new unit tests and the high-level behavioral integration tests provide superior coverage and stability.

## 5. Risk & Impact Audit

This design explicitly addresses the risks identified in the pre-flight audit.

-   **[RISK] God Class Decomposition**: **ADDRESSED**. The design mandates the extraction of all business logic from the `Government` orchestrator into stateless `Decision` and `Execution` engines, enforcing the Single Responsibility Principle.
-   **[RISK] Stateless Engines & DTO Contracts**: **ADDRESSED**. The architecture is built on stateless engines that communicate exclusively via immutable DTOs (`GovernmentStateDTO`, `PolicyDecisionDTO`, `ExecutionResultDTO`), preventing the "stateful component" anti-pattern seen in the `Firm` agent and avoiding hidden dependencies.
-   **[RISK] External System Dependency Injection**: **ADDRESSED**. Critical dependencies (`SettlementSystem`, `FinanceSystem`) are held by the orchestrator and passed to the `ExecutionEngine` via a dedicated `GovernmentExecutionContext` DTO, ensuring loose coupling and clear dependency management.
-   **[RISK] Integration of Existing Service Components**: **ADDRESSED**. The design reuses `TaxService`, `WelfareManager`, etc., as tools invoked by the `PolicyExecutionEngine`, preserving existing, well-factored code.
-   **[RISK] Major Test Suite Breakage**: **ADDRESSED**. The comprehensive, three-phase **Verification Plan** is designed to manage this risk by establishing a behavioral baseline *before* the refactor, ensuring the external functionality remains identical post-refactor.

## 6. Mandatory Reporting Verification

All insights, challenges, and minor technical debt discovered during the implementation of this refactor will be logged in a dedicated insight report: `communications/insights/TD-259_Government_Refactor.md`. This ensures knowledge capture and informs future architectural decisions.

---
```python
import abc
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field

# --- DTOs for State and Communication ---

# Forward-declare DTOs that might have circular dependencies in type hints
# In a real scenario, these would be imported from their respective API files.
class FiscalPolicyDTO: pass
class MarketSnapshotDTO: pass
class PaymentRequestDTO: pass
class BailoutResultDTO: pass
class ISettlementSystem: pass
class IFinanceSystem: pass
class ITaxService: pass
class WelfareManager: pass
class CentralBank: pass

# Enums would be imported from a central `enums.py`
class PolicyActionTag: pass
class PoliticalParty: pass


@dataclass
class GovernmentStateDTO:
    """Immutable snapshot of the Government's state for decision-making."""
    tick: int
    assets: Dict[str, float]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    fiscal_policy: 'FiscalPolicyDTO'
    ruling_party: 'PoliticalParty'
    approval_rating: float
    policy_lockouts: Dict['PolicyActionTag', int] = field(default_factory=dict)
    sensory_data: Optional[Dict[str, Any]] = None # Simplified representation of sensory DTO
    gdp_history: List[float] = field(default_factory=list)
    welfare_budget_multiplier: float = 1.0


@dataclass
class PolicyDecisionDTO:
    """Represents a high-level strategic decision from the DecisionEngine."""
    action_tag: 'PolicyActionTag'
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "OK"


@dataclass
class GovernmentExecutionContext:
    """
    Provides the necessary external systems (dependencies) for the ExecutionEngine.
    These are injected by the Orchestrator at execution time.
    """
    settlement_system: 'ISettlementSystem'
    finance_system: 'IFinanceSystem'
    tax_service: 'ITaxService'
    welfare_manager: 'WelfareManager'


@dataclass
class ExecutionResultDTO:
    """Contains the concrete commands and state changes from the ExecutionEngine."""
    payment_requests: List['PaymentRequestDTO'] = field(default_factory=list)
    bailout_results: List['BailoutResultDTO'] = field(default_factory=list)
    monetary_ledger_updates: Dict[str, float] = field(default_factory=dict)
    state_updates: Dict[str, Any] = field(default_factory=dict)
    transactions: List[Any] = field(default_factory=list) # For legacy compatibility if needed


# --- Engine Interfaces ---

class IGovernmentDecisionEngine(metaclass=abc.ABCMeta):
    """
    Interface for the stateless decision-making engine.
    Determines *what* policy action to take.
    """
    @abc.abstractmethod
    def decide(
        self,
        state: GovernmentStateDTO,
        market_snapshot: 'MarketSnapshotDTO',
        central_bank: 'CentralBank'
    ) -> PolicyDecisionDTO:
        """
        Decides on a policy action based on current state and market data.
        This method encapsulates the logic of choosing a strategy (e.g., Taylor Rule, AI).
        """
        ...


class IPolicyExecutionEngine(metaclass=abc.ABCMeta):
    """
    Interface for the stateless policy execution engine.
    Determines *how* to implement a decided action.
    """
    @abc.abstractmethod
    def execute(
        self,
        decision: PolicyDecisionDTO,
        current_state: GovernmentStateDTO,
        agents: List[Any],
        market_data: Dict[str, Any],
        context: GovernmentExecutionContext
    ) -> ExecutionResultDTO:
        """
        Takes a high-level policy decision and translates it into concrete,
        executable results by orchestrating various services (Tax, Welfare, etc.).
        """
        ...

```
