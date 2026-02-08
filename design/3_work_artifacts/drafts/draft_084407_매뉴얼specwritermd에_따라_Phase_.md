# Refactoring Specification: Phase 9.2 Interface Purity Sprint (Detailed Design)

**Status:** FINAL DRAFT
**Target Phase:** 9.2
**Primary Objective:** Enforce strict protocol boundaries to eliminate architectural drift, guarantee monetary integrity, and restore Separation of Concerns (SoC).

---

## 1. Problem Statement (현상 및 배경)

The 2026-02-09 audit and subsequent pre-flight analysis have confirmed a systemic degradation of the project's architecture. Key principles of encapsulation and SoC are being violated, leading to a fragile, unpredictable, and difficult-to-maintain codebase. This refactoring sprint is not a feature enhancement but a critical mission to restore architectural integrity.

### Key Failures (주요 결함):
1.  **Financial SSoT Violation**: The `SettlementSystem` is not the Single Source of Truth for financial transactions. Modules are directly accessing and mutating agent assets (`.cash`, `.assets`), making zero-sum validation impossible.
2.  **Encapsulation Breakage**: The `SensorySystem` and other analytics components directly access internal agent state (`_econ_state`, `_social_state`), creating tight coupling that causes cascading failures during refactoring.
3.  **DTO Fragmentation**: The coexistence of multiple `Order` DTOs (`simulation.models.Order`, `modules.market.api.OrderDTO`) creates architectural schism and non-determinism in market operations.
4.  **Ambiguous Dependencies**: Critical systems like `SettlementSystem` rely on untyped, ambiguous dependencies (`bank: Any`), obscuring logic and making testing unreliable.
5.  **Documentation Drift**: Key architecture documents (`ARCH_AGENTS.md`) do not reflect the reality of the current implementation (Stateless Engine vs. Stateful Pointer).

---

## 2. 세부 리팩토링 설계 (Refactoring Design)

This sprint is divided into four parallel tracks to address the core failures.

### 2.1 Track A: Financial SSoT Enforcement (금융 단일 진실 공급원 강제)
- **Objective**: To make the `SettlementSystem` the exclusive authority for all asset and currency transfers.
- **Design & Protocols**:
    1.  **`IBank` Protocol (`modules/finance/api.py`)**: A formal protocol will be introduced to define the contract for banking services, resolving the `Optional[Any]` dependency.
        -   `get_balance(agent_id: str) -> float`
        -   `withdraw_for_customer(agent_id: int, amount: float) -> bool`
    2.  **`IFinancialAgent` Protocol (`modules/finance/api.py`)**: All agents (Households, Firms, Government) must implement this protocol. This makes direct `.cash` or `.assets` access a clear protocol violation.
        -   `deposit(amount: float, currency: CurrencyCode) -> None`
        -   `withdraw(amount: float, currency: CurrencyCode) -> None`
        -   `get_balance(currency: CurrencyCode) -> float`
- **Implementation Pseudo-code**:
    ```python
    # In SettlementSystem.transfer:
    # OLD (VIOLATION):
    # debit_agent.assets -= amount 
    # credit_agent.assets += amount

    # NEW (REFACTORED):
    def transfer(debit_agent: IFinancialAgent, credit_agent: IFinancialAgent, ...):
        try:
            debit_agent.withdraw(amount, currency) # Raises InsufficientFundsError
            credit_agent.deposit(amount, currency)
        except InsufficientFundsError:
            # Handle failure
        except Exception as e:
            # Handle rollback
            debit_agent.deposit(amount, currency) # refund
    ```
- **Target Files**: `simulation/systems/settlement_system.py`, all agent implementations.

### 2.2 Track B: Sensory System & Observation Purity (관찰 계층 순수성 확보)
- **Objective**: Decouple observer systems from the internal state of agents.
- **Design & Protocols**:
    1.  **`AgentSensorySnapshotDTO` (`modules/agents/api.py`)**: A new TypedDict DTO to provide a stable, read-only view of an agent's state.
        -   `is_active: bool`, `approval_rating: float`, `total_wealth: float`
    2.  **`ISensoryDataProvider` Protocol (`modules/agents/api.py`)**: Agents will implement this to expose their state safely.
        -   `get_sensory_snapshot() -> AgentSensorySnapshotDTO`
- **Implementation Pseudo-code**:
    ```python
    # In SensorySystem.generate_government_sensory_dto:
    # OLD (VIOLATION):
    # for h in households:
    #     val = h._econ_state.assets.get(DEFAULT_CURRENCY, 0.0)
    #     approval = h._social_state.approval_rating
    
    # NEW (REFACTORED):
    # households: List[ISensoryDataProvider] = context.get("households")
    # for agent in households:
    #     snapshot = agent.get_sensory_snapshot()
    #     if snapshot['is_active']:
    #         wealth_values.append(snapshot['total_wealth'])
    #         approval_ratings.append(snapshot['approval_rating'])
    ```
- **Target Files**: `simulation/systems/sensory_system.py`, all analytics/reporting modules, all agent implementations.

### 2.3 Track C: Market DTO Unification (마켓 DTO 단일화)
- **Objective**: Establish a single, canonical `OrderDTO` for all market interactions.
- **Design & Protocols**:
    1.  **`CanonicalOrderDTO` (`modules/market/api.py`)**: A new `dataclass(frozen=True)` will be the single source of truth for all orders. It will include all necessary fields for all market types (e.g., `agent_id`, `item_id`, `quantity`, `side`, `price_limit`, `order_id`).
- **Migration Strategy**: An **Adapter Pattern** will be used to minimize disruption.
    - Create an adapter function `convert_legacy_order_to_canonical(legacy_order) -> CanonicalOrderDTO`.
    - Market `place_order` methods will be immediately updated to accept only `CanonicalOrderDTO`.
    - Legacy calling code will wrap its calls: `market.place_order(convert_legacy_order_to_canonical(old_order))`.
    - This allows for incremental refactoring of agent logic without breaking the market system.
- **Target Files**: `simulation/markets/stock_market.py`, `simulation/markets/order_book_market.py`, all other market implementations, all agents that place orders.

### 2.4 Track D: Architectural Sync (설계 문서 동기화)
- **Objective**: Ensure design documents reflect the implemented reality.
- **Action**: The `design/1_governance/architecture/ARCH_AGENTS.md` document will be rewritten to remove the outdated "Stateful Parent Pointer" concept and accurately describe the current "Stateless Engine + State DTO" architecture.

---

## 3. Risk & Impact Audit (기술적 위험 분석)

This refactoring addresses critical risks but also introduces its own. The design is tailored to mitigate them.

1.  **Risk: Invasive Financial Changes.**
    -   **Finding**: The `SettlementSystem` itself contains workarounds for direct asset access, indicating the violation is deeply embedded.
    -   **Mitigation**: The `IFinancialAgent` protocol provides a clear, unavoidable contract. All financial logic will be centralized. The refactoring will be invasive, but confining it to a single, well-defined API (`deposit`/`withdraw`/`get_balance`) makes the scope manageable and verifiable.
2.  **Risk: Cascading Failures from Agent Refactoring.**
    -   **Finding**: `SensorySystem`'s deep introspection is likely repeated elsewhere.
    -   **Mitigation**: The `ISensoryDataProvider` protocol and `AgentSensorySnapshotDTO` act as a firewall. Agent internal models can be refactored freely without breaking any external observer, as long as they can still produce the snapshot DTO. This contains the impact.
3.  **Risk: Design Conflicts from DTO Unification.**
    -   **Finding**: DTO fragmentation points to deeper architectural schisms.
    -   **Mitigation**: The `CanonicalOrderDTO` forces a resolution. The **Adapter Pattern** is the key mitigation strategy here, allowing the old and new systems to coexist during a transition period, reducing the risk of a "big bang" failure.
4.  **Risk: Ambiguous `Bank` Dependency.**
    -   **Finding**: `SettlementSystem`'s logic is dependent on an unknown, untyped collaborator.
    -   **Mitigation**: The `IBank` protocol eliminates ambiguity. It creates a formal, testable contract, making `SettlementSystem`'s logic explicit and verifiable. This also provides a clear path for resolving `TD-261 (Bank Domain Purification)`.

---

## 4. Verification Plan & Mocking Guide

- **Testing Philosophy**: We will move away from `MagicMock` and brittle patching. Tests will rely on injecting mock objects that correctly implement the new protocols.
- **Golden Data Strategy**:
    - Existing fixtures like `golden_households` and `golden_firms` from `tests/conftest.py` are the **preferred source for test agents**.
    - These fixtures **must be updated** to implement `IFinancialAgent` and `ISensoryDataProvider` as part of this sprint.
    - **Usage**: `def test_my_feature(golden_firms): ...`
    - **Schema Change**: Any change to a DTO schema requires updating the corresponding golden data and fixtures. The `scripts/fixture_harvester.py` script must be used to regenerate snapshots if needed.
- **Verification Cases**:
    - **Track A**: Write a test for `SettlementSystem` that injects a mock `IFinancialAgent` and a mock `IBank`. Verify that `transfer` calls `withdraw` and `deposit` on the mock agent, and that `_execute_withdrawal` calls `get_balance` and `withdraw_for_customer` on the mock bank. A codebase-wide `grep` for `.cash =` and `.assets =` must return zero results outside of wallet implementations.
    - **Track B**: Test `SensorySystem` by injecting a list of mock agents implementing `ISensoryDataProvider`. Verify that the system correctly calculates its indicators based *only* on the data returned by `get_sensory_snapshot()`.
    - **Track C**: Write unit tests for the `convert_legacy_order_to_canonical` adapter. Test that `StockMarket` and other markets now reject legacy order types and function correctly with `CanonicalOrderDTO`.

---

## 5. Mandatory Reporting Verification

All technical debt, architectural insights, and design decisions discovered during the implementation of this specification **will be logged** in separate markdown files within the `communications/insights/` directory, prefixed with `PH9.2_`. This is a non-negotiable step to ensure knowledge is captured and fed back into the `TECH_DEBT_LEDGER.md`.

---
```python
#
# file: modules/market/api.py
#
"""API definitions for the Market domain."""
from typing import Literal, TypedDict, Optional
from uuid import UUID
from dataclasses import dataclass

# [Track C] CanonicalOrderDTO to unify market interactions.
# This replaces fragmented Order objects.
@dataclass(frozen=True)
class CanonicalOrderDTO:
    """A unified, immutable data transfer object for all market orders."""
    agent_id: int
    item_id: str  # e.g., "goods_1", "stock_5"
    quantity: float
    side: Literal["BUY", "SELL"]
    price_limit: float
    order_id: UUID # Unique identifier for the order
    tick_created: int
    # Optional field for specific market implementations (e.g., housing)
    metadata: Optional[TypedDict] = None

# ... other existing API elements in this file ...
```
```python
#
# file: modules/finance/api.py
#
"""API definitions for the Finance domain, including protocols for purity."""
from typing import Protocol, Dict, Optional
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

class InsufficientFundsError(Exception):
    """Custom exception for failed withdrawals."""
    pass

# [Track A] Protocol to abstract bank interactions away from SettlementSystem
class IBank(Protocol):
    """
    Defines the contract for a banking institution that can hold customer
    deposits and facilitate payments.
    """
    def get_balance(self, agent_id: str) -> float:
        """Returns the deposit balance for a given agent."""
        ...

    def withdraw_for_customer(self, agent_id: int, amount: float) -> bool:
        """
        Withdraws an amount from a customer's account for a seamless payment.
        Returns True on success, False on failure.
        """
        ...

# [Track A] Protocol to enforce strict financial interaction with agents
class IFinancialAgent(Protocol):
    """
    Defines the contract for any agent participating in the economy.
    This enforces that all cash/asset changes go through a controlled interface,
    preventing direct mutation of state.
    """
    @property
    def id(self) -> int:
        ...

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """Deposits a given amount of currency into the agent's wallet."""
        ...

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """
        Withdraws a given amount of currency from the agent's wallet.
        Raises InsufficientFundsError if the balance is too low.
        """
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> float:
        """Returns the current balance for a specific currency."""
        ...

# ... other existing API elements like IPortfolioHandler ...
```
```python
#
# file: modules/agents/api.py
#
"""API definitions for the Agent domain."""
from typing import Protocol, TypedDict

# [Track B] DTO for providing sensory data to observer systems.
class AgentSensorySnapshotDTO(TypedDict):
    """
    A snapshot of an agent's state for consumption by sensory/analytics systems.
    This prevents direct access to internal agent state.
    """
    is_active: bool
    approval_rating: float
    total_wealth: float # Combines cash and other assets into a single value
    # Add other key indicators as needed by analytics systems
    # e.g., 'age', 'social_class', etc.

# [Track B] Protocol for agents to provide sensory data.
class ISensoryDataProvider(Protocol):
    """
    Defines the contract for an agent to provide its state in a structured,
    read-only format to observer systems like SensorySystem.
    """
    @property
    def id(self) -> int:
        ...

    def get_sensory_snapshot(self) -> AgentSensorySnapshotDTO:
        """Returns a DTO containing the agent's current state for observation."""
        ...
```
