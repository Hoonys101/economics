# Technical Specification: TD-124 - Decomposing TransactionProcessor

## 1. Overview & Problem Statement

The `TransactionProcessor` class has become a "God Class," violating the Single Responsibility Principle (SRP) by managing financial settlements, tax calculations, and state registry updates for various entities (inventory, employment, assets). This tight coupling makes the code difficult to maintain, test, and extend. It also introduces significant risk, as any change can have unforeseen side effects.

This document outlines the plan to decompose `TransactionProcessor` into a set of coordinated, single-responsibility "Agencies" orchestrated by a `TransactionManager`. The primary goal is to improve modularity and maintainability while strictly preserving the simulation's zero-sum integrity through atomic operations.

**Reference Audit:** This plan directly addresses the findings in `Pre-flight Audit Report: Decomposing TransactionProcessor (TD-124)`.

## 2. Proposed Architecture

The existing monolithic process will be replaced by a coordinating manager and three specialized agencies:

1.  **`TransactionManager` (Orchestrator):** The new entry point that replaces the main loop of the old `TransactionProcessor`. It receives a `Transaction` and directs it to the appropriate agencies in a strict, atomic sequence.
2.  **`SettlementSystem` (Financial Layer):** Manages all financial transfers between agents. It is the sole authority for debiting and crediting agent assets. This will formalize and expand the pre-existing `settlement_system`.
3.  **`TaxAgency` (Fiscal Layer):** Calculates and collects all taxes (sales, income, etc.). It collaborates with the `SettlementSystem` to execute tax payments from agents to the government.
4.  **`Registry` (State Update Layer):** Updates non-financial agent state, such as inventory levels, employment status, and asset ownership. **Crucially, its methods are only ever called after a financial settlement is confirmed.**

```mermaid
graph TD
    subgraph TransactionManager
        A[execute_transaction(tx)]
    end

    A -- 1. Settle Funds & Taxes --> B{SettlementSystem};
    A -- also triggers --> C{TaxAgency};
    C -- uses --> B;
    A -- 2. If Settlement OK, commit state --> D{Registry};

    subgraph "Financial Layer"
        B;
        C;
    end

    subgraph "State Layer"
        D;
    end

    B -- Modifies --> E[Agent.assets];
    D -- Modifies --> F[Agent.inventory, Agent.is_employed, etc.];

    style B fill:#cce5ff,stroke:#333,stroke-width:2px
    style C fill:#cce5ff,stroke:#333,stroke-width:2px
    style D fill:#d4edda,stroke:#333,stroke-width:2px

```

## 3. Agency Interface Definitions (`api.py` Content)

### 3.1. DTOs (`simulation/dtos/transactions.py`)

```python
from typing import TypedDict, Any, Dict
from simulation.models import Transaction

class SettlementResult(TypedDict):
    success: bool
    error_message: str | None

class TaxResult(TypedDict):
    success: bool
    tax_amount: float
    error_message: str | None

class RegistryUpdateResult(TypedDict):
    success: bool
    error_message: str | None
```

### 3.2. Agency APIs (`simulation/systems/api.py`)

```python
from abc import ABC, abstractmethod
from simulation.models import Transaction
from simulation.dtos.api import SimulationState # Keep for now, but reduce usage
from simulation.dtos.transactions import SettlementResult, TaxResult, RegistryUpdateResult

# --- Interfaces ---

class ISettlementSystem(ABC):
    @abstractmethod
    def process_settlement(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        """Processes the financial aspect of a transaction."""
        ...

class ITaxAgency(ABC):
    @abstractmethod
    def process_tax(self, tx: Transaction, state: SimulationState) -> TaxResult:
        """Calculates and collects taxes related to a transaction."""
        ...

class IRegistry(ABC):
    @abstractmethod
    def update_state(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        """Updates non-financial state after a successful transaction."""
        ...

class ITransactionManager(ABC):
    @abstractmethod
    def execute_transaction(self, tx: Transaction, state: SimulationState) -> None:
        """Orchestrates the full, atomic lifecycle of a transaction."""
        ...
```

## 4. Atomic Execution Strategy (Zero-Sum Guarantee)

To address the atomicity risk identified in the audit, the `TransactionManager` will enforce a strict two-phase process for every transaction:

1.  **Phase 1: Financial Settlement:**
    *   The `TransactionManager` calls the `SettlementSystem` to attempt the primary financial transfer.
    *   If the transfer is tax-related, the `SettlementSystem` will in turn call the `TaxAgency` to calculate the tax, and then settle both the main transfer and the tax transfer.
    *   **If any financial operation in this phase fails, the entire transaction is aborted. No state changes are made.**

2.  **Phase 2: State Commitment:**
    *   **Only if Phase 1 succeeds,** the `TransactionManager` calls the `Registry` to update the non-financial state (inventory, employment, etc.).
    *   Failures in this phase are considered critical system errors and should be logged as such, as the financial state and world state are now inconsistent. However, the design minimizes this risk by performing all possible checks during Phase 1.

This sequence ensures that a change in physical/abstract state (like owning a new item) can **never** occur without the corresponding financial transaction completing successfully.

## 5. Detailed Logic (Pseudo-code)

### 5.1. `TransactionManager`

```python
class TransactionManager(ITransactionManager):
    def __init__(self, settlement_system: ISettlementSystem, registry: IRegistry):
        self.settlement_system = settlement_system
        self.registry = registry

    def execute_transaction(self, tx: Transaction, state: SimulationState) -> None:
        # Phase 1: Financial Settlement
        settlement_result = self.settlement_system.process_settlement(tx, state)

        if not settlement_result['success']:
            # Log failure, maybe trigger agent solvency checks etc.
            # No state is changed, atomicity is preserved.
            return

        # Phase 2: Commit State
        registry_result = self.registry.update_state(tx, state)

        if not registry_result['success']:
            # CRITICAL ERROR: Financials and World State are inconsistent.
            # Log this as a high-priority error.
            # This should ideally never happen.
            logger.critical(f"ATOMICITY VIOLATION on TX {tx.id}")

        # Optional: Add successful TX to effects queue
        if tx.metadata and tx.metadata.get("triggers_effect"):
             state.effects_queue.append(tx.metadata)
```

### 5.2. `SettlementSystem` (Refactored)

```python
class SettlementSystem(ISettlementSystem):
    def __init__(self, tax_agency: ITaxAgency):
        self.tax_agency = tax_agency

    def process_settlement(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        # This method acts as a router, calling specific handlers
        # It replaces the giant `if/elif` block in the old processor.

        handlers = {
            "goods": self._settle_goods_trade,
            "labor": self._settle_labor_wage,
            "stock": self._settle_asset_trade,
            "asset_transfer": self._settle_asset_trade,
            "tax": self._settle_tax_payment,
            # ... add all other transaction types
        }
        handler = handlers.get(tx.transaction_type, self._settle_generic)
        return handler(tx, state)

    def _settle_goods_trade(self, tx, state) -> SettlementResult:
        buyer, seller = self._get_agents(tx, state)
        trade_value = tx.price * tx.quantity

        # 1. Collect Sales Tax first
        tax_result = self.tax_agency.process_tax(tx, state)
        if not tax_result['success']:
            return SettlementResult(success=False, error_message=tax_result['error_message'])

        # 2. Settle the primary trade
        # The old `settlement.transfer` logic is moved here.
        if buyer.assets < trade_value:
            return SettlementResult(success=False, error_message="Insufficient funds")

        buyer.assets -= trade_value
        seller.assets += trade_value
        # Record financial event
        return SettlementResult(success=True, error_message=None)

    # ... Implement other _settle_* methods
```

### 5.3. `TaxAgency`

```python
class TaxAgency(ITaxAgency):
    def process_tax(self, tx: Transaction, state: SimulationState) -> TaxResult:
        # Router for different tax types
        if tx.transaction_type == "goods":
            return self._process_sales_tax(tx, state)
        elif tx.transaction_type == "labor":
            return self._process_income_tax(tx, state)
        return TaxResult(success=True, tax_amount=0.0, error_message=None) # No tax for this tx type

    def _process_sales_tax(self, tx, state) -> TaxResult:
        government = state.government
        buyer = state.agents[tx.buyer_id]
        trade_value = tx.price * tx.quantity
        tax_rate = self.config_module.SALES_TAX_RATE
        tax_amount = trade_value * tax_rate

        # Use government.collect_tax which handles the transfer internally
        result = government.collect_tax(tax_amount, "sales_tax", buyer, state.time)
        return TaxResult(success=result['success'], tax_amount=tax_amount, error_message=result.get('error'))

    # ... Implement other _process_* methods
```

### 5.4. `Registry`

```python
class Registry(IRegistry):
    def update_state(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        # Router similar to SettlementSystem
        handlers = {
            "goods": self._update_goods_state,
            "labor": self._update_labor_state,
            "stock": self._update_stock_ownership,
            "real_estate": self._update_real_estate_ownership,
        }
        handler = handlers.get(tx.transaction_type, lambda tx, state: RegistryUpdateResult(success=True, error_message=None))
        return handler(tx, state)

    def _update_goods_state(self, tx, state) -> RegistryUpdateResult:
        # Logic from _handle_goods_transaction moved here
        buyer, seller = self._get_agents(tx, state)
        seller.inventory[tx.item_id] -= tx.quantity
        buyer.inventory[tx.item_id] += tx.quantity
        # ... update quality, firm revenue, etc.
        return RegistryUpdateResult(success=True, error_message=None)

    def _update_labor_state(self, tx, state) -> RegistryUpdateResult:
        # Logic from _handle_labor_transaction moved here
        firm, household = self._get_agents(tx, state)
        firm.hr.hire(household, tx.price)
        household.is_employed = True
        # ...
        return RegistryUpdateResult(success=True, error_message=None)

    # ... Implement other _update_* methods
```

## 6. Verification & Test Plan

Acknowledging the "Inevitable Test Breakage" risk, the refactoring will proceed with a parallel test suite update.

1.  **Unit Tests:**
    *   New test files will be created for `TaxAgency`, `SettlementSystem`, and `Registry`.
    *   These tests will mock the other agencies and verify the logic of the target agency in isolation.
    *   **Example:** `test_tax_agency.py` will test `calculate_income_tax` with various incomes without needing a real `SettlementSystem`.

2.  **Integration Tests:**
    *   A new test file, `test_transaction_manager.py`, will be created.
    *   These tests will initialize all three new agencies and the manager.
    *   They will verify end-to-end transaction outcomes by calling `TransactionManager.execute_transaction` and asserting the final state of all involved agents (financial and non-financial).
    *   These tests will effectively replace the old `test_transaction_processor.py`.

3.  **Golden Data & Mocks:**
    *   Existing fixtures (`golden_households`, etc.) will be heavily relied upon to ensure test inputs are realistic.
    *   Mocks will be required for dependencies like the `Government` agent during unit tests.

## 7. Risk & Impact Audit (Addressing Pre-flight Report)

-   **[Mitigated] God Class & SRP:** The proposed architecture directly resolves this by splitting responsibilities into `SettlementSystem`, `TaxAgency`, and `Registry`. Interfaces are defined to minimize data exposure, although initial implementations may still pass the `SimulationState` DTO for expediency, with a follow-up task (TD-XXX) to narrow them further.
-   **[Mitigated] Zero-Sum Integrity:** The `TransactionManager`'s two-phase `Settle -> Commit` process is explicitly designed to enforce atomicity and prevent state divergence.
-   **[Acknowledged] Test Breakage:** The verification plan allocates specific work to rewrite unit and integration tests in parallel with the refactoring, acknowledging this is a significant part of the task.
-   **[Addressed] Pre-existing `SettlementSystem`:** The new `SettlementSystem` is designed as a formalization and replacement of the old one. The core logic of `settlement.transfer` will be migrated into the new `_settle_*` private methods, ensuring functionality is preserved and enhanced.

## 8. Implementation Guidance for Jules

-   **[Routine] Mandatory Reporting**: During implementation, you are required to document any non-obvious design choices, performance trade-offs, or newly discovered technical debt. Create a new file in `communications/insights/TD-124-Jules-Observations.md` and detail your findings. This is critical for future maintenance.
-   **[Task] Incremental Refactoring:** Implement one agency at a time. It is recommended to start with the `Registry`, then `TaxAgency`, then `SettlementSystem`, and finally the `TransactionManager`. Use feature flags or separate entry points to switch between the old and new processors during development.
-   **[Test] Refactor Tests First:** Before changing the implementation, consider copying the existing tests for `TransactionProcessor` and adapting them for the `TransactionManager`. This will provide a clear target for the refactored code to aim for.
