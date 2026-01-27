# Refinement Report: TD-124 - Decomposing TransactionProcessor (Audit-Revised)

## 1. Executive Summary

This document refines the original `TD-124` specification based on the findings of the "Pre-flight Audit Report." The proposed architecture is updated to address critical risks, including the handling of non-zero-sum (money minting) transactions, Single Responsibility Principle (SRP) violations in the proposed `Registry`, and over-simplification of complex transaction logic. This revised plan ensures a more robust, modular, and zero-sum-safe decomposition.

## 2. Revised Architecture

The architecture is expanded to include specialized systems for money creation and financial ledgering, preventing architectural decay into new "God Classes."

1.  **`TransactionManager` (Orchestrator):** The entry point. Now routes transactions to the appropriate system: `CentralBank` for money creation, a specialized `Handler` for complex sagas, or the standard `SettlementSystem`.
2.  **`CentralBank` (Minting Authority):** A new, dedicated system that handles non-zero-sum transactions (`lender_of_last_resort`, `asset_liquidation`). It is the sole authority for creating money.
3.  **`SettlementSystem` (Financial Layer):** Its role is now strictly limited to facilitating **zero-sum** asset transfers between agents.
4.  **`TaxAgency` (Fiscal Layer):** Unchanged. Calculates taxes and uses the `SettlementSystem` to execute the collection.
5.  **`Registry` (Ownership State Layer):** Its role is narrowed to updating **only** non-financial, physical/ownership state (inventory, employment ID, property ownership).
6.  **`AccountingSystem` (Ledgering Layer):** A new system responsible for updating agents' internal financial ledgers (e.g., recording revenue, expenses, capital income). This is part of the "Commit" phase.
7.  **Specialized Handlers (e.g., `InheritanceHandler`):** For complex, multi-step transactions, these handlers orchestrate a sequence of operations, using other systems like the `SettlementSystem` to perform atomic steps.

```mermaid
graph TD
    subgraph TransactionManager
        A[execute_transaction(tx)]
    end

    A -- "tx.type == 'lender_of_last_resort'" --> CB[CentralBank];
    A -- "tx.type == 'inheritance_distribution'" --> IH[InheritanceHandler];
    A -- "Standard Trade" -- 1. Settle Funds & Taxes --> B[SettlementSystem];
    
    B -- collaborates with --> C[TaxAgency];
    IH -- uses --> B;

    A -- 2. If Settlement OK, commit state --> D{Registry};
    A -- 2. If Settlement OK, commit state --> AS[AccountingSystem];

    subgraph "Minting Authority"
        style CB fill:#fffacd,stroke:#333,stroke-width:2px
        CB;
    end
    
    subgraph "Financial Layer (Zero-Sum)"
        style B fill:#cce5ff,stroke:#333,stroke-width:2px
        style C fill:#cce5ff,stroke:#333,stroke-width:2px
        B;
        C;
    end

    subgraph "Complex Sagas"
        style IH fill:#e6ccff,stroke:#333,stroke-width:2px
        IH;
    end

    subgraph "State Commitment Layer"
        style D fill:#d4edda,stroke:#333,stroke-width:2px
        style AS fill:#d4edda,stroke:#333,stroke-width:2px
        D[Registry (Ownership)];
        AS[AccountingSystem (Ledgers)];
    end

    CB -- Modifies --> Agent.assets;
    B -- Modifies --> Agent.assets;
    D -- Modifies --> Agent.inventory, Agent.employer_id;
    AS -- Modifies --> Agent.finance.revenue, Agent.capital_income_this_tick;
```

## 3. Revised Agency Interface Definitions (`api.py`)

### 3.1. DTOs (`simulation/dtos/transactions.py`)
(No changes from original `TD-124` spec)

### 3.2. Agency APIs (`simulation/systems/api.py`)

```python
from abc import ABC, abstractmethod
from simulation.models import Transaction
from simulation.dtos.api import SimulationState
from simulation.dtos.transactions import SettlementResult, TaxResult, RegistryUpdateResult

# --- NEW Interfaces ---

class IMintingAuthority(ABC):
    @abstractmethod
    def process_minting(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        """Processes a non-zero-sum transaction where money is created."""
        ...

class IAccountingSystem(ABC):
    @abstractmethod
    def update_ledgers(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        """Updates internal financial ledgers of agents (revenue, expense, etc.)."""
        ...
        
class ISpecializedTransactionHandler(ABC):
    @abstractmethod
    def execute(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        """Handles a complex, multi-step transaction saga."""
        ...

# --- Existing Interfaces ---

class ISettlementSystem(ABC):
    @abstractmethod
    def process_settlement(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        """Processes the ZERO-SUM financial aspect of a transaction."""
        ...

class ITaxAgency(ABC):
    @abstractmethod
    def process_tax(self, tx: Transaction, state: SimulationState) -> TaxResult:
        """Calculates and collects taxes related to a transaction."""
        ...

class IRegistry(ABC):
    @abstractmethod
    def update_ownership_state(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        """Updates non-financial ownership/physical state after a successful transaction."""
        ...

class ITransactionManager(ABC):
    @abstractmethod
    def execute_transaction(self, tx: Transaction, state: SimulationState) -> None:
        """Orchestrates the full, atomic lifecycle of a transaction."""
        ...
```

## 4. Revised Atomic Execution Strategy

The `TransactionManager` now functions as a more intelligent router, preserving the two-phase commit model where applicable.

1.  **Phase 1: Financial Operation (Routing):**
    *   The `TransactionManager` first checks the transaction type.
    *   **If `tx.type` is a minting type:** Route to `IMintingAuthority.process_minting`.
    *   **If `tx.type` is a complex saga type:** Route to the appropriate `ISpecializedTransactionHandler`.
    *   **Otherwise (standard zero-sum trade):** Route to `ISettlementSystem.process_settlement`.
    *   If the operation fails at any point, the transaction is aborted.

2.  **Phase 2: State Commitment:**
    *   **Only if Phase 1 succeeds,** the `TransactionManager` calls **both**:
        *   `IRegistry.update_ownership_state` to update inventories, employment, etc.
        *   `IAccountingSystem.update_ledgers` to record revenue, expenses, etc.
    *   This ensures financial records and physical state are updated atomically post-settlement.

## 5. Revised Detailed Logic (Pseudo-code)

### 5.1. `TransactionManager`

```python
class TransactionManager(ITransactionManager):
    def __init__(self, minting_authority: IMintingAuthority, settlement_system: ISettlementSystem, registry: IRegistry, accounting_system: IAccountingSystem, handlers: Dict[str, ISpecializedTransactionHandler]):
        self.minting_authority = minting_authority
        self.settlement_system = settlement_system
        self.registry = registry
        self.accounting_system = accounting_system
        self.special_handlers = handlers
        self.minting_tx_types = {"lender_of_last_resort", "asset_liquidation"}

    def execute_transaction(self, tx: Transaction, state: SimulationState) -> None:
        settlement_result: SettlementResult

        # Phase 1: Financial Operation (with routing)
        if tx.transaction_type in self.minting_tx_types:
            settlement_result = self.minting_authority.process_minting(tx, state)
        elif tx.transaction_type in self.special_handlers:
            handler = self.special_handlers[tx.transaction_type]
            settlement_result = handler.execute(tx, state)
        else:
            settlement_result = self.settlement_system.process_settlement(tx, state)

        if not settlement_result['success']:
            # Log failure. Atomicity is preserved.
            return

        # Phase 2: Commit State (Registry and Accounting)
        registry_result = self.registry.update_ownership_state(tx, state)
        accounting_result = self.accounting_system.update_ledgers(tx, state)

        if not registry_result['success'] or not accounting_result['success']:
            # CRITICAL ERROR: Financials and World State are inconsistent.
            logger.critical(f"ATOMICITY VIOLATION on TX {tx.id}")
```

### 5.2. `CentralBank` (New)

```python
class CentralBank(IMintingAuthority):
    def process_minting(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        buyer, seller = self._get_agents(tx, state)
        trade_value = tx.price * tx.quantity
        
        # Money is created. No debit from buyer.
        seller.deposit(trade_value)
        
        # Track total money supply if buyer is government
        if hasattr(buyer, "total_money_issued"):
            buyer.total_money_issued += trade_value
            
        return SettlementResult(success=True, error_message=None)
```

### 5.3. `InheritanceHandler` (New)

```python
class InheritanceHandler(ISpecializedTransactionHandler):
    def __init__(self, settlement_system: ISettlementSystem):
        self.settlement_system = settlement_system # Uses the settlement system for atomic transfers

    def execute(self, tx: Transaction, state: SimulationState) -> SettlementResult:
        # Encapsulates the complex looping logic from the old processor
        deceased, _ = self._get_agents(tx, state) # Buyer is the deceased agent
        heir_ids = tx.metadata.get("heir_ids", [])
        total_cash = deceased.assets
        
        if not heir_ids or total_cash <= 0:
            return SettlementResult(success=True, error_message="No heirs or no assets to distribute.")

        # ... complex logic with math.floor to calculate per-heir amounts ...
        # ... loop through heirs, creating a new temporary Transaction for each ...
        # ... and use self.settlement_system.process_settlement for each one. ...
        
        all_success = True
        for heir_tx in generated_heir_transactions:
            result = self.settlement_system.process_settlement(heir_tx, state)
            if not result['success']:
                all_success = False
                # Handle failure: what to do if one heir's transfer fails?
                # For now, log and continue.
                
        return SettlementResult(success=all_success, error_message=None)
```

### 5.4. `Registry` (Refined Role)

```python
class Registry(IRegistry):
    def update_ownership_state(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        # ... router logic ...
    
    def _update_labor_state(self, tx, state) -> RegistryUpdateResult:
        # Logic from _handle_labor_transaction is refined
        firm, household = self._get_agents(tx, state)
        
        # PRINCIPLE: Update only primitive state. Do NOT call agent methods.
        household.is_employed = True
        household.employer_id = firm.id
        household.current_wage = tx.price
        household.needs["labor_need"] = 0.0
        
        # The firm's HR department should react to these changes, not be called by the registry.
        # This can be done via post-transaction hooks or an event bus.
        
        return RegistryUpdateResult(success=True, error_message=None)

    # ... other _update_* methods for inventory, property, etc.
```

### 5.5. `AccountingSystem` (New)

```python
class AccountingSystem(IAccountingSystem):
    def update_ledgers(self, tx: Transaction, state: SimulationState) -> RegistryUpdateResult:
        # This method acts as a router for different ledger updates
        handlers = {
            "goods": self._update_trade_ledgers,
            "labor": self._update_labor_ledgers,
            "dividend": self._update_dividend_ledgers,
        }
        handler = handlers.get(tx.transaction_type, lambda tx, state: RegistryUpdateResult(success=True, error_message=None))
        return handler(tx, state)

    def _update_trade_ledgers(self, tx, state) -> RegistryUpdateResult:
        buyer, seller = self._get_agents(tx, state)
        trade_value = tx.quantity * tx.price

        if isinstance(seller, Firm):
            seller.finance.record_revenue(trade_value)
            seller.finance.sales_volume_this_tick += tx.quantity
        return RegistryUpdateResult(success=True, error_message=None)

    def _update_labor_ledgers(self, tx, state) -> RegistryUpdateResult:
        firm, household = self._get_agents(tx, state)
        trade_value = tx.quantity * tx.price
        
        firm.finance.record_expense(trade_value)
        if hasattr(household, "labor_income_this_tick"):
            # Net income would be calculated after tax, this records the gross event
            household.labor_income_this_tick += trade_value
        return RegistryUpdateResult(success=True, error_message=None)

    def _update_dividend_ledgers(self, tx, state) -> RegistryUpdateResult:
        _, household = self._get_agents(tx, state) # seller=firm, buyer=household
        trade_value = tx.quantity * tx.price
        
        if hasattr(household, "capital_income_this_tick"):
            household.capital_income_this_tick += trade_value
        return RegistryUpdateResult(success=True, error_message=None)
```

## 6. Implementation Guidance for Jules (Revised)

-   **[Task] Incremental Refactoring Order:**
    1.  Implement the new interfaces and DTOs in `api.py`.
    2.  Implement the `Registry` and `AccountingSystem` with their narrowed responsibilities.
    3.  Implement the `CentralBank` for minting transactions.
    4.  Refactor the existing `SettlementSystem` to handle only zero-sum logic.
    5.  Implement the `TransactionManager` to orchestrate all the new components. Start by routing only a few transaction types and falling back to the old processor for the rest.
-   **[Principle] Looser Coupling:** When implementing the `Registry`, strictly adhere to the principle of only modifying primitive agent attributes. Do not call complex methods on agents (e.g., `firm.hr.hire()`). Log this as a follow-up task to implement an event/hook system if one does not exist.
