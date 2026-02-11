# Technical Specification: Stateless Policy Engines

## 1. Executive Summary

This document outlines the technical specification for refactoring the `Government` and `CentralBank` agents. Currently, these agents are monolithic "God Classes" that tightly couple state management, decision logic, and execution, leading to high maintenance costs and significant risk of unintended side effects.

The proposed solution is to extract the core decision-making logic into two new stateless engines: a `FiscalEngine` and a `MonetaryEngine`. These engines will operate on a purely functional basis, receiving all necessary information via Data Transfer Objects (DTOs) and returning decisions as DTOs. The agents (`Government`, `CentralBank`) will remain the sole owners of their state, responsible for orchestrating calls to the engines and applying the resulting decisions. This refactoring directly addresses the critical risks identified in the pre-flight audit, enforcing the Separation of Concerns (SoC) and creating a more robust, testable, and maintainable architecture.

## 2. High-Level Architecture: Agent-Engine Model

The new architecture follows a strict, one-way data flow that prevents the engines from holding state or causing side effects.

```
+----------------+      1. Collects State & Market Data      +---------------------+
| Agent          | ---------------------------------------> | Stateless Engine    |
| (e.g.          |      (FiscalStateDTO, MarketSnapshotDTO) | (e.g. FiscalEngine) |
| Government)    |                                          +---------------------+
| [Stateful]     |                                                    |
+----------------+                                                    | 2. Computes Decision
       ^                                                               |  (Pure Function)
       |                                                               V
       | 4. Applies changes                                  +--------------------+
       |   (self.tax_rate = result.new_tax_rate)              | Decision DTO       |
       +-----------------------------------------------------| (e.g.              |
                     3. Receives Decision                    | FiscalDecisionDTO) |
                                                             +--------------------+
```

1.  **Agent Collects State**: The `Government` agent gathers its internal state (`income_tax_rate`, `total_debt`, etc.) and relevant market data into DTOs.
2.  **Engine Computes Decision**: The agent calls the stateless `FiscalEngine`, passing the DTOs. The engine performs its calculations without modifying any state.
3.  **Engine Returns Decision**: The engine returns a `FiscalDecisionDTO` containing the *proposed changes* (e.g., a new tax rate), not the full new state.
4.  **Agent Applies Changes**: The `Government` agent receives the decision and is responsible for applying the changes to its own internal state variables, following the pattern already established by `_apply_state_updates`.

## 3. Detailed Design: `IFiscalEngine`

The `FiscalEngine` will encapsulate the fiscal policy logic currently embedded within the `Government` agent.

-   **Location**: `modules/government/engines/fiscal_engine.py`
-   **Interface**: `modules/government/engines/api.py`

### 3.1. Responsibilities

-   Determining the overall fiscal stance (e.g., expansionary, contractionary).
-   Calculating tax policy adjustments.
-   Calculating welfare and subsidy amounts based on policy.
-   Evaluating eligibility and terms for firm bailouts.

### 3.2. API & Logic

The engine's primary method will be `decide`.

```python
# modules/government/engines/api.py

class IFiscalEngine:
    def decide(
        self,
        state: FiscalStateDTO,
        market: MarketSnapshotDTO,
        requests: List[FiscalRequestDTO]
    ) -> FiscalDecisionDTO:
        """
        Calculates the next set of fiscal actions based on current state.
        """
        ...
```

### 3.3. Addressing Abstraction Leaks

The current design suffers from abstraction leaks where raw agent handles are passed into methods. This will be replaced with a DTO-based contract.

**BEFORE (Leaky Abstraction):**

```python
# simulation/agents/government.py
def provide_firm_bailout(self, firm: Any, amount: float, current_tick: int) -> ...:
    # Engine can access firm.id, firm.assets, firm.history, etc.
    # This is an unstable, implicit contract.
    ...
```

**AFTER (DTO Contract):**

The process will be split between the agent and the engine.

1.  The `Government` agent creates a request DTO.
2.  The `FiscalEngine` evaluates this request and returns a decision.
3.  The `Government` agent executes the transfer based on the decision.

```python
# In Government Agent
bailout_request = FirmBailoutRequestDTO(
    firm_id=firm.id,
    requested_amount=amount,
    firm_financials=firm.get_financial_snapshot() # Snapshot DTO, not the object
)
decision = self.fiscal_engine.decide(..., requests=[bailout_request])

if decision.bailouts_to_grant:
     grant = decision.bailouts_to_grant[0]
     self.settlement_system.transfer(self, firm, grant.amount, ...)
```

The engine only sees the `FirmBailoutRequestDTO`, preventing it from accessing the live `firm` object.

## 4. Detailed Design: `IMonetaryEngine`

The `MonetaryEngine` will encapsulate the interest rate logic currently in `CentralBank`.

-   **Location**: `modules/finance/engines/monetary_engine.py`
-   **Interface**: `modules/finance/engines/api.py`

### 4.1. Responsibilities

-   Calculating the target base interest rate using the Taylor Rule or other models.
-   Applying smoothing and respecting the Zero Lower Bound (ZLB).

### 4.2. API & Logic

```python
# modules/finance/engines/api.py

class IMonetaryEngine:
    def calculate_rate(
        self,
        state: MonetaryStateDTO,
        market: MarketSnapshotDTO
    ) -> MonetaryDecisionDTO:
        """
        Calculates the new target base interest rate.
        """
        ...
```

### 4.3. Handling Stateful Logic

The `CentralBank` currently calculates and updates a smoothed `potential_gdp` estimate internally. This stateful operation will be owned by the agent, while the engine remains stateless.

1.  **Agent (pre-call)**: `CentralBank` updates `self.potential_gdp` using its EMA logic.
2.  **Agent (call)**: `CentralBank` packages `self.potential_gdp` into the `MonetaryStateDTO` and sends it to the engine.
3.  **Engine**: The `MonetaryEngine` uses the `potential_gdp` value from the DTO to calculate the output gap and the Taylor Rule rate. It has no memory of past values.
4.  **Agent (post-call)**: `CentralBank` receives the `MonetaryDecisionDTO` and updates `self.base_rate`.

## 5. Data Contracts (DTOs)

The following DTOs will be defined in `modules/government/engines/api.py` and `modules/finance/engines/api.py`.

```python
# --- Fiscal DTOs ---
from typing import TypedDict, List, Dict, Optional
from modules.system.api import CurrencyCode

class FiscalStateDTO(TypedDict):
    """Input state from Government agent."""
    tick: int
    assets: Dict[CurrencyCode, float]
    total_debt: float
    income_tax_rate: float
    corporate_tax_rate: float
    approval_rating: float
    welfare_budget_multiplier: float
    potential_gdp: float

class FirmFinancialsDTO(TypedDict):
    """A snapshot of a firm's health, NOT the live object."""
    assets: float
    profit: float
    is_solvent: bool

class FirmBailoutRequestDTO(TypedDict):
    firm_id: int
    requested_amount: float
    firm_financials: FirmFinancialsDTO

class FiscalRequestDTO(TypedDict): # Union of all possible requests
    bailout_request: Optional[FirmBailoutRequestDTO]
    # ... other request types in the future

class GrantedBailoutDTO(TypedDict):
    firm_id: int
    amount: float
    interest_rate: float
    term: int

class FiscalDecisionDTO(TypedDict):
    """Output decisions from the FiscalEngine."""
    new_income_tax_rate: Optional[float]
    new_corporate_tax_rate: Optional[float]
    new_welfare_budget_multiplier: Optional[float]
    bailouts_to_grant: List[GrantedBailoutDTO]


# --- Monetary DTOs ---
class MonetaryStateDTO(TypedDict):
    """Input state from CentralBank agent."""
    tick: int
    current_base_rate: float
    potential_gdp: float # Calculated and owned by the agent
    inflation_target: float

class MarketSnapshotDTO(TypedDict):
    """Shared market data for both engines."""
    tick: int
    inflation_rate_annual: float
    current_gdp: float

class MonetaryDecisionDTO(TypedDict):
    """Output decision from the MonetaryEngine."""
    new_base_rate: float
```

## 6. Verification & Testing Strategy

-   **New Unit Tests**: The stateless nature of the engines makes them highly suitable for unit testing. We will create dedicated test files (`tests/modules/government/engines/test_fiscal_engine.py`) that test the `decide` and `calculate_rate` methods with a variety of input DTOs, verifying the output DTOs are correct. No mocking of agent objects is required.
-   **Existing Test Impact**: A significant number of integration tests that rely on the internal stateful behavior of `Government.make_policy_decision` and `CentralBank.step` will fail. These tests must be refactored to verify the new orchestration flow: check that the agent correctly calls the engine and correctly applies the returned decision.
-   **Integration Check**: Key scenario tests (e.g., `scenario_stress_100.py`) must be run to ensure the new architecture produces behavior consistent with the old one, preventing macroeconomic regressions.
-   **Mocking Guide**: Existing fixtures like `golden_households` remain valid for testing agents. The key change is that tests for agent *logic* will now involve checking the DTOs passed to a mocked Engine, rather than checking the final state directly.
-   **Schema Change Notice**: The introduction of these DTOs will require verification that any systems that serialize agent data are updated if these DTOs become part of the agent's state. `scripts/fixture_harvester.py` may need to be updated to correctly snapshot and restore agent state if these DTOs are embedded.

## 7. Risk & Impact Audit Mitigation

This design directly mitigates the risks identified in the pre-flight audit:

-   **God Class Entanglement**: Logic is physically separated into different files (`fiscal_engine.py`, `government.py`), enforcing the Single Responsibility Principle at the file level. The `Government` agent is demoted to an orchestrator.
-   **Abstraction Leaks**: The mandatory use of DTOs as the sole communication mechanism severs the dangerous coupling created by passing live agent handles. The `FirmBailoutRequestDTO` is a prime example of this enforcement.
-   **Stateful Logic**: State management (like the `potential_gdp` EMA) remains explicitly within the agent. The engines are purely functional, receiving state, computing, and returning a result without side effects, making them predictable and testable.
-   **Circular Dependencies**: Engines are designed to be independent and cannot import each other. All coordination occurs at the agent level (e.g., `Government` can get the interest rate from `CentralBank` and pass it into the `FiscalEngine` via a DTO), ensuring a top-down, acyclic dependency graph.

## 8. Mandatory Reporting Verification

All insights, design trade-offs, and identified technical debt during the implementation of this specification will be documented and saved to `communications/insights/REF-001_Stateless_Policy_Engines.md`. This ensures a transparent record of the architectural evolution.
