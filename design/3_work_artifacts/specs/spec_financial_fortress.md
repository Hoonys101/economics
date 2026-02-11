```markdown
# Spec: Financial Fortress Protocol

## 1. Introduction

- **Purpose**: This document outlines the architectural changes required to enforce the `SettlementSystem` as the exclusive Single Source of Truth (SSoT) for all monetary state and transfers, as mandated by `FINANCIAL_INTEGRITY.md`.
- **Scope**: This spec covers modifications to `Household` and `Firm` agents, the `FinanceSystem`, and related testing strategies.
- **Goals**:
    - Eliminate all direct wallet mutations (`deposit`, `withdraw`, `load_state`) from agent APIs.
    - Eradicate unaudited money creation during agent instantiation (`clone`).
    - Resolve the state inconsistency ("schizophrenia") in the `FinanceSystem`'s internal ledger.
    - Establish a robust, auditable, and command-based financial transaction pipeline.

---

## 2. Detailed Design: Protocol Enforcement

### 2.1. Agent Wallet Lockdown

The core of the protocol is to make agent wallets immutable from the outside. All state changes will be orchestrated via the `SettlementSystem`.

#### 2.1.1. Removal of Direct Wallet Access

- **Action**: The public methods `deposit(self, ...)` and `withdraw(self, ...)` will be **removed** from `simulation.core_agents.Household` and `simulation.firms.Firm`.
- **Action**: The `load_state(self, ...)` method in both agents will be modified to **no longer load financial asset data**. It will be used exclusively for non-monetary state restoration.
- **Impact**: This is a breaking change that intentionally makes it impossible for any external module to directly mutate an agent's financial balance.

#### 2.1.2. The `SettlementOrder` Command

- **Mechanism**: All monetary transfers will be modeled as `SettlementOrder` commands. Agents and systems will generate these commands instead of performing direct transfers. A central orchestrator will execute these orders via the `SettlementSystem` at the end of a tick or sub-tick sequence.
- **DTO Definition** (`modules/finance/api.py`):

  ```python
  class SettlementOrder(TypedDict):
      """A command to execute a monetary transfer via the SettlementSystem."""
      sender_id: AgentID
      receiver_id: AgentID
      amount_pennies: int
      currency: CurrencyCode
      memo: str
      transaction_type: str # e.g., 'WAGE', 'TAX', 'PURCHASE', 'ASSET_ENDOWMENT'
  ```

#### 2.1.3. Agent Creation and Asset Endowment (`clone` Deprecation)

- **Problem**: The `clone()` methods are a primary source of untraceable money creation.
- **Solution**: The `clone()` methods will be deprecated and replaced by a centralized `AgentFactory`.
- **`AgentFactory` Workflow**:
    1.  The factory receives a request to create a new agent (e.g., a `Household` child).
    2.  It instantiates the agent object with **zero initial assets**.
    3.  It generates a `SettlementOrder` to transfer initial assets from the parent agent (or a designated "Genesis" system account) to the new child agent.
    4.  The `transaction_type` will be `ASSET_ENDOWMENT`.
    5.  This makes the birth of a new agent and its initial wealth an explicit, auditable financial event.

### 2.2. `FinanceSystem` Ledger Synchronization

- **Problem**: The `FinanceSystem` maintains its own parallel ledger (`self.ledger`), which creates a dangerous second source of truth.
- **Solution**: The `FinanceSystem` will be refactored into a **stateless orchestrator** regarding external agent balances. Its internal ledger will only track state for which it is the true owner (e.g., the list of outstanding treasury bonds).

#### 2.2.1. Eliminating the Parallel Ledger

- **Action**: The `__init__` method of `FinanceSystem` will **no longer read initial balances** from `bank.wallet` or `government.wallet`. The `self.ledger.banks[bank.id].reserves` and `self.ledger.treasury.balance` fields will be removed or repurposed.
- **Action**: In methods like `issue_treasury_bonds`, all balance checks will be performed by querying the SSoT in real-time. This will be done by calling `self.settlement_system.get_balance(agent_id)`.
- **Action**: The dual-write pattern in `issue_treasury_bonds` will be eliminated. The method will call `self.settlement_system.transfer()`, and that action will be the sole record of the state change. The manual decrements/increments to `self.ledger` reserves and balances will be **deleted**.

#### 2.2.2. New `ISettlementSystem` Interface

- **`modules/finance/api.py`**: The settlement system interface will be expanded to support the new stateless query pattern.

  ```python
  class ISettlementSystem(Protocol):
      # ... existing methods ...

      def transfer(self, sender: IFinancialAgent, receiver: IFinancialAgent, amount_pennies: int, memo: str, currency: CurrencyCode = DEFAULT_CURRENCY) -> bool:
          """Executes an immediate, single transfer. Returns success."""
          ...

      def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
          """
          Queries the Single Source of Truth for an agent's current balance.
          This is the ONLY permissible way to check another agent's funds.
          """
          ...
  ```

---

## 3. Testing & Verification Strategy

The removal of `deposit`/`withdraw` invalidates the setup phase for a majority of existing tests. A new testing strategy is required.

- **`TestSettlementSystem`**: A mock implementation of `ISettlementSystem` will be created for testing purposes. It will be injectable via `pytest` fixtures.
- **Key Features**:
    - `setup_balance(agent_id: AgentID, amount_pennies: int, currency: CurrencyCode)`: Allows test arrangements to declaratively set an agent's starting balance.
    - `get_recorded_transfers() -> List[SettlementOrder]`: Stores all transfer requests it receives, allowing tests to assert that the correct financial commands were issued.
    - `get_balance()`: Will return balances set via `setup_balance`.
- **Migration Path**:
    1.  Tests that previously used `agent.deposit(...)` in the setup will be refactored to use `mock_settlement_system.setup_balance(agent.id, ...)`.
    2.  Tests that asserted a change in balance will be refactored to assert that the correct `SettlementOrder` was recorded by the mock system.

---

## 4. Risk & Impact Audit

This design directly addresses the risks identified in the pre-flight audit.

- **1. Agent Lifecycle & Money Creation**: **Mitigated.** The `AgentFactory` pattern replaces `clone()` and uses auditable `SettlementOrder`s for initial asset endowment, closing the "ghost money" loophole.
- **2. Widespread API Breakage & Test Suite Failure**: **Mitigated.** The proposed `TestSettlementSystem` provides a clear, robust, and systematic path for migrating the entire test suite, preventing a wholesale loss of test coverage.
- **3. `FinanceSystem` State Schizophrenia**: **Mitigated.** By making the `FinanceSystem` a stateless orchestrator that queries the SSoT for balances, we eliminate the parallel ledger and the risk of state drift entirely. The dual-write pattern is removed.
- **4. Dependency & SRP Violation**: **Mitigated.** By removing direct wallet access and forcing the use of `SettlementOrder`s or an injected `ISettlementSystem` interface, the design enforces Dependency Inversion and a clean separation of concerns, making the system more modular and robust.

---

## 5. Mandatory Reporting Verification

- **Insight Logging**: All insights, technical debt discoveries, and architectural decisions made during the implementation of this specification will be logged to `communications/insights/FI-001_Financial_Fortress_Implementation.md`. This ensures compliance with mandatory reporting protocols.
```
