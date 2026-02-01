# Technical Specification: Transaction Processor Refactoring (TD-191)

## 1. Overview & Goal

This document outlines the technical specification for refactoring the `TransactionProcessor` system. The current implementation (`simulation/systems/transaction_processor.py`) uses a monolithic `if/elif/else` chain within its `execute` method, making it difficult to maintain, test, and extend.

The primary goal of this refactoring is to replace this monolithic structure with a modular, handler-based dispatch system. This will improve code clarity, isolate transaction-specific logic, and facilitate future development.

## 2. Architectural Risks Addressed

This design directly addresses the risks identified in the **Pre-flight Audit (TD-191)**.

1.  **Constraint: The "Sacred Sequence" of Settlement & State Change**:
    *   **Resolution**: Each `ITransactionHandler` will encapsulate the entire logic for a transaction type. Within its `handle` method, it will first perform the financial settlement using the `SettlementSystem`. Only upon successful settlement will it proceed to apply stateful side-effects (inventory, employment changes). This preserves the critical sequence within a more modular boundary.

2.  **Risk: Propagation of God Class Dependencies**:
    *   **Resolution**: This refactoring acts as a **containment strategy**. While handlers will still depend on agent internals, this dependency is now explicitly confined to a small, single-purpose class instead of a massive, multi-purpose method. The `TransactionContext` object makes these dependencies explicit and consistent across all handlers.

3.  **Constraint: Atomic Multi-Party Settlements**:
    *   **Resolution**: The logic for constructing the `credits_list` for atomic settlements (e.g., `goods` and `labor` taxes) will be migrated directly into the dedicated `GoodsTransactionHandler` and `LaborTransactionHandler`. These handlers will be solely responsible for invoking `settlement.settle_atomic` correctly, ensuring economic integrity is maintained.

4.  **Risk: Circular Dependencies from Handler Dispatch**:
    *   **Resolution**: The refactored `TransactionProcessor` will implement a **runtime registration pattern**. Handlers will not be statically imported. Instead, they will be registered with the processor at initialization, decoupling the dispatcher from the concrete handler implementations and preventing circular import errors.

5.  **Constraint: Universal Context and State Access**:
    *   **Resolution**: A new `TransactionContext` DTO will be introduced. This object will be passed to every handler, providing a consistent and comprehensive interface to access all necessary simulation components (`agents`, `government`, `settlement_system`, `market_data`, etc.), including `inactive_agents`.

## 3. New Architecture

The new architecture consists of three main parts: the `TransactionContext` DTO, the `ITransactionHandler` interface, and the refactored `TransactionProcessor` dispatcher.

### 3.1. `TransactionContext` DTO

A `dataclass` will be created to bundle all state required by handlers. This simplifies the method signatures and ensures handlers have consistent access to the simulation world.

```python
# In: modules/simulation/systems/api.py

from dataclasses import dataclass
from typing import Dict, Any, List

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from simulation.agents.government import Government
    from simulation.systems.settlement_system import SettlementSystem
    # ... other necessary imports

@dataclass(frozen=True)
class TransactionContext:
    """
    Provides all necessary simulation state to a transaction handler.
    This is an immutable snapshot of state for a single transaction.
    """
    agents: Dict[int, Any]
    inactive_agents: Dict[int, Any]
    government: 'Government'
    settlement_system: 'SettlementSystem'
    taxation_system: 'TaxationSystem'
    stock_market: Any
    real_estate_units: List[Any]
    market_data: Dict[str, Any]
    config_module: Any
    logger: Any
    time: int
```

### 3.2. `ITransactionHandler` Interface

An abstract base class that defines the contract for all transaction handlers.

```python
# In: modules/simulation/systems/api.py

import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.models import Transaction

class ITransactionHandler(abc.ABC):
    """
    Interface for handling a specific type of transaction.
    """
    @abc.abstractmethod
    def handle(self, tx: 'Transaction', context: 'TransactionContext') -> bool:
        """
        Processes a single transaction.

        This method must enforce the "Sacred Sequence":
        1. Attempt financial settlement via the context.settlement_system.
        2. Only if settlement is successful, apply all other state changes
           (inventory, employment, etc.).

        Returns:
            bool: True if the transaction was successfully processed, False otherwise.
        """
        raise NotImplementedError
```

### 3.3. `TransactionProcessor` (Dispatcher)

The `TransactionProcessor` will be refactored to act as a dispatcher. It will maintain a registry of handlers and delegate the processing of each transaction to the appropriate handler.

```python
# In: simulation/systems/transaction_processor.py (Refactored)

from typing import Dict, Type
from simulation.systems.api import ITransactionHandler, TransactionContext

class TransactionProcessor(SystemInterface):
    def __init__(self, config_module: Any):
        self.config_module = config_module
        self._handlers: Dict[str, ITransactionHandler] = {}
        # The settlement and taxation systems are now part of the context
        # and will be instantiated at a higher level (e.g., in Simulation).

    def register_handler(self, transaction_type: str, handler: ITransactionHandler):
        """Registers a handler for a specific transaction type."""
        self._handlers[transaction_type] = handler

    def execute(self, state: SimulationState) -> None:
        """
        Dispatches transactions to registered handlers.
        """
        context = TransactionContext(
            agents=state.agents,
            inactive_agents=getattr(state, "inactive_agents", {}),
            government=state.government,
            settlement_system=state.settlement_system,
            taxation_system=state.taxation_system, # Assumes this is created alongside
            stock_market=state.stock_market,
            real_estate_units=state.real_estate_units,
            market_data=state.market_data,
            config_module=self.config_module,
            logger=state.logger,
            time=state.time
        )
        
        default_handler = self._handlers.get("default")

        for tx in state.transactions:
            handler = self._handlers.get(tx.transaction_type)

            # Fallback for symbolic transactions or unhandled types
            if handler is None:
                 if tx.transaction_type in ["credit_creation", "credit_destruction"]:
                     continue # These are symbolic, no handler needed.
                 if default_handler:
                     handler = default_handler
                 else:
                     context.logger.warning(f"No handler for tx type: {tx.transaction_type}")
                     continue

            # Find buyer and seller
            buyer = context.agents.get(tx.buyer_id) or context.inactive_agents.get(tx.buyer_id)
            seller = context.agents.get(tx.seller_id) or context.inactive_agents.get(tx.seller_id)

            if not buyer or not seller:
                continue

            # Delegate to the handler
            success = handler.handle(tx, buyer, seller, context)

            # Post-processing (e.g., effects queue)
            if success and tx.metadata and tx.metadata.get("triggers_effect"):
                state.effects_queue.append(tx.metadata)
```

## 4. Concrete Handler Implementations

New handlers will be created in a new directory: `simulation/systems/handlers/`. Below are examples for `Goods` and `Stock` transactions.

### 4.1. `GoodsTransactionHandler`

This handler demonstrates the preservation of atomic, multi-party settlement.

```python
# In: simulation/systems/handlers/goods_handler.py

from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

class GoodsTransactionHandler(ITransactionHandler):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = tx.quantity * tx.price

        # 1. Prepare Settlement (Calculate tax intents)
        intents = context.taxation_system.calculate_tax_intents(tx, buyer, seller, context.government, context.market_data)

        credits = [(seller, trade_value, f"goods_trade:{tx.item_id}")]
        total_cost = trade_value
        for intent in intents:
            credits.append((context.government, intent.amount, intent.reason))
            if intent.payer_id == buyer.id:
                total_cost += intent.amount
        
        # 2. Execute Settlement (Atomic)
        settlement_success = context.settlement_system.settle_atomic(buyer, credits, context.time)

        # 3. Apply Side-Effects (Only on success)
        if settlement_success:
            # Record revenue for tax purposes
            for intent in intents:
                context.government.record_revenue({
                     "success": True, "amount_collected": intent.amount,
                     "tax_type": intent.reason, "payer_id": intent.payer_id,
                     "payee_id": intent.payee_id, "error_message": None
                })
            
            # Update inventories, consumption, etc. (Migrated from _handle_goods_transaction)
            good_info = context.config_module.GOODS.get(tx.item_id, {})
            # ... (rest of the logic from the original _handle_goods_transaction)

        return settlement_success
```

### 4.2. `StockTransactionHandler`

This handler shows a simpler, direct transfer.

```python
# In: simulation/systems/handlers/stock_handler.py

from simulation.systems.api import ITransactionHandler, TransactionContext
from simulation.models import Transaction

class StockTransactionHandler(ITransactionHandler):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        trade_value = tx.quantity * tx.price

        # 1. Execute Settlement
        settlement_success = context.settlement_system.transfer(buyer, seller, trade_value, f"stock_trade:{tx.item_id}")

        # 2. Apply Side-Effects (Only on success)
        if settlement_success:
            # Update portfolios, share registries, etc.
            # (Logic migrated from the original _handle_stock_transaction)
            firm_id = int(tx.item_id.split("_")[1])
            # ... (rest of the logic)

        return settlement_success
```

## 5. Migration Plan & Verification

1.  **Create API**: Implement `TransactionContext` and `ITransactionHandler` in `modules/simulation/systems/api.py`.
2.  **Refactor `TransactionProcessor`**: Modify `TransactionProcessor` to become a dispatcher as specified above. Implement the `register_handler` method.
3.  **Create Handlers Directory**: Create the `simulation/systems/handlers/` directory.
4.  **Migrate Logic (One by One)**:
    *   For each `elif` block in the original `execute` method:
        *   Create a new `..._handler.py` file.
        *   Create a class implementing `ITransactionHandler`.
        *   Copy the logic from the `elif` block and its corresponding private helper method (e.g., `_handle_labor_transaction`) into the new `handle` method.
        *   Update the logic to use the `context` object instead of direct state access.
        *   Instantiate and register the new handler in the main `Simulation` class where `TransactionProcessor` is created.
5.  **Verification**:
    *   Existing tests for the simulation should continue to pass, as the external behavior is unchanged.
    *   New unit tests should be written for each individual handler to test its logic in isolation. These tests can use mock `TransactionContext` objects to provide specific scenarios.
    *   Zero-sum and money-leak audit scripts must be run after the refactoring to ensure economic integrity has been preserved.

---

# API Definition File (`api.py`)
```python
# Path: modules/simulation/systems/api.py
from __future__ import annotations
import abc
from dataclasses import dataclass
from typing import Dict, Any, List, TYPE_CHECKING

# Forward references to avoid circular imports at runtime.
# These are crucial for type hinting without causing import loops.
if TYPE_CHECKING:
    from simulation.models import Transaction
    from simulation.agents.government import Government
    from simulation.systems.settlement_system import SettlementSystem
    from modules.government.taxation.system import TaxationSystem
    from logging import Logger

@dataclass(frozen=True)
class TransactionContext:
    """
    Provides all necessary simulation state to a transaction handler.
    This is an immutable snapshot of state for a single transaction,
    ensuring that handlers have a consistent view of the world.
    """
    agents: Dict[int, Any]
    inactive_agents: Dict[int, Any]
    government: 'Government'
    settlement_system: 'SettlementSystem'
    taxation_system: 'TaxationSystem'
    stock_market: Any
    real_estate_units: List[Any]
    market_data: Dict[str, Any]
    config_module: Any
    logger: 'Logger'
    time: int

class ITransactionHandler(abc.ABC):
    """
    Abstract Base Class defining the interface for handling a specific
    type of transaction. Each concrete handler will implement the logic
    for one transaction type (e.g., 'goods', 'labor', 'stock').
    """
    @abc.abstractmethod
    def handle(self, tx: 'Transaction', buyer: Any, seller: Any, context: 'TransactionContext') -> bool:
        """
        Processes a single transaction, enforcing the "Sacred Sequence".

        The implementation of this method MUST strictly follow this order:
        1. Perform all necessary calculations (e.g., taxes, net amounts).
        2. Attempt the financial settlement using the context.settlement_system.
           This is the point of no return for the financial part.
        3. ONLY if the settlement call returns a success status, proceed to apply
           all other stateful side-effects (e.g., updating inventories, changing
           employment status, updating share registries).

        Args:
            tx: The Transaction object to be processed.
            buyer: The hydrated buyer agent object.
            seller: The hydrated seller agent object.
            context: An immutable context object providing access to simulation state.

        Returns:
            bool: True if the transaction was successfully processed in its entirety
                  (both settlement and side-effects), False otherwise. A False return
                  indicates a failure at some point, and the system should consider
                  the transaction aborted.
        """
        raise NotImplementedError

class SystemInterface(abc.ABC):
    """
    A more generic interface for simulation systems that are called once per tick.
    """
    @abc.abstractmethod
    def execute(self, state: 'SimulationState') -> None:
        """
        Executes the system's logic for a single simulation tick.
        """
        raise NotImplementedError

```
