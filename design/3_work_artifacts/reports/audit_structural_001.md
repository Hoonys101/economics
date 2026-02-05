# Structural Audit Report: God Class & Abstraction Leak

**Task ID:** AUDIT-STRUCTURAL-001
**Date:** 2024-05-22
**Auditor:** Jules (AI Agent)

## 1. Executive Summary
This audit identified significant structural issues in the `simulation/systems/settlement_system.py` and `modules/finance/saga_handler.py` files. The `SettlementSystem` class is approaching the "God Class" threshold and exhibits severe abstraction leaks, knowing too much about the internal implementation of various agent types. Additionally, the `HousingTransactionSagaHandler` demonstrates raw agent leaks, bypassing DTO boundaries and directly accessing agent instances and their internal properties.

## 2. Findings

### 2.1. God Class Candidate: `SettlementSystem`
*   **File:** `simulation/systems/settlement_system.py`
*   **Lines:** 785 (Approaching the 800-line saturation limit)
*   **Responsibilities:**
    *   Saga Orchestration (Housing)
    *   Atomic Settlements (Transfers, Withdrawals, Deposits)
    *   Legacy Settlement Account Management (Escrow)
    *   Liquidation & Bankruptcy Recording
    *   Money Creation (Minting) & Destruction (Burning)
    *   Agent Liveness Checks
*   **Analysis:** The class is overloaded. It mixes low-level financial transaction logic with high-level process orchestration (Sagas) and lifecycle management (Liquidation). It acts as a central hub that is becoming a bottleneck for maintenance and extension.

### 2.2. Abstraction Leaks (Dependency Hell)
*   **Location:** `SettlementSystem.create_settlement`, `SettlementSystem._execute_withdrawal`, `SettlementSystem.record_liquidation`
*   **Issue:** The system inspects agent internals using `hasattr` and `isinstance` checks for `wallet`, `finance`, `_econ_state`, and `assets`.
*   **Evidence:**
    ```python
    # simulation/systems/settlement_system.py

    if hasattr(agent, 'wallet'):
        cash_balance = agent.wallet.get_balance(DEFAULT_CURRENCY)
    elif hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
        # ... logic for Firm ...
    elif hasattr(agent, '_econ_state'):
        # ... logic for Household ...
    ```
*   **Impact:** `SettlementSystem` is tightly coupled to the specific implementations of `Firm`, `Household`, and `Government`. Adding a new agent type requires modifying this core system class, violating the Open/Closed Principle.

### 2.3. Raw Agent Leaks in Decision Engines
*   **Location:** `modules/finance/saga_handler.py` (`HousingTransactionSagaHandler`)
*   **Issue:** The handler retrieves raw agent objects from `simulation.agents` and accesses their internal properties directly, bypassing DTOs.
*   **Evidence:**
    ```python
    # modules/finance/saga_handler.py

    buyer = self.simulation.agents.get(saga['buyer_id'])
    # ...
    if buyer and hasattr(buyer, 'current_wage'):
         monthly_income = calculate_monthly_income(buyer.current_wage, ticks_per_year)
    ```
*   **Impact:** The decision logic (Saga Handler) depends on the raw agent object structure (`current_wage`). Changes to the `Agent` class (e.g., moving `current_wage` to a component) will break the Saga Handler. This violates the "DTO Purity Gate" principle.

### 2.4. Sequence Exceptions
*   **Location:** `HousingTransactionSagaHandler.execute_step`
*   **Issue:** The handler modifies agent state (e.g., `housing_service.transfer_ownership`) and triggers settlements directly within the `Phase_HousingSaga`. While this is part of the saga logic, it bypasses the standard `TransactionProcessor` for side effects, making it harder to track and replay the simulation state deterministically if not carefully logged.

## 3. Recommendations

### 3.1. Decompose `SettlementSystem`
*   **Refactor:** Split `SettlementSystem` into smaller, focused services:
    *   `SettlementService`: Core atomic transfers and withdrawals.
    *   `EscrowService`: Management of settlement accounts and inheritance logic.
    *   `LiquidationService`: Handling of bankruptcy and asset liquidation.
    *   `SagaManager`: Generic saga orchestration (or keep in `SettlementSystem` but delegate to specific handlers).

### 3.2. Introduce `ISettlementEntity` Interface
*   **Refactor:** Create a unified interface `ISettlementEntity` (or extend `IFinancialEntity`) that all agents must implement.
    *   Methods: `get_liquid_assets(currency)`, `withdraw(amount, currency)`, `deposit(amount, currency)`.
*   **Benefit:** `SettlementSystem` will interact only with this interface, removing the need for `hasattr` checks and decoupling it from specific agent implementations.

### 3.3. Enforce DTO Purity in Saga Handlers
*   **Refactor:** `HousingTransactionSagaHandler` should receive a context object containing necessary data as DTOs (e.g., `BuyerFinancialDTO`) instead of accessing `simulation.agents` directly. Or, strictly use interfaces (`IFinancialEntity`, `IWageEarner`) if direct object access is necessary for performance, but never raw property access.

## 4. Conclusion
Immediate refactoring is recommended for `SettlementSystem` to prevent further accumulation of technical debt and to facilitate the addition of new agent types and financial instruments. The abstraction leaks pose a significant risk to the stability of the simulation.
