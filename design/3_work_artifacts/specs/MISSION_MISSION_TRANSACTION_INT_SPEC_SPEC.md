File: modules\finance\transaction_integration\api.py
```python
from __future__ import annotations
from typing import Protocol, List, Dict, Any, Optional, Iterable, runtime_checkable, TypedDict
from dataclasses import dataclass
from enum import Enum

from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode
from modules.finance.api import IFinancialAgent, ISettlementSystem, IShareholderRegistry
from modules.simulation.api import EconomicIndicatorsDTO # Assuming availability or generic
from simulation.models import Transaction # Core model

# ==============================================================================
# DTOs
# ==============================================================================

class TransactionStatus(Enum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

@dataclass(frozen=True)
class TransactionExecutionResultDTO:
    """
    Standardized output from a Transaction Handler.
    Encapsulates the result of the business logic BEFORE final settlement recording.
    """
    transaction_id: str
    status: TransactionStatus
    amount_settled_pennies: int
    currency: CurrencyCode
    side_effects: Dict[str, Any] # Metadata for post-processing (e.g., inventory updates)
    error_message: Optional[str] = None

class TransactionContext(TypedDict):
    """
    Context passed to transaction handlers.
    Provides access to system services required for validation and execution.
    """
    agents: Dict[AgentID, Any] # Read-only access to agent registry
    settlement_system: ISettlementSystem
    shareholder_registry: Optional[IShareholderRegistry]
    market_data: Dict[str, Any]
    current_tick: int
    logger: Any

# ==============================================================================
# PROTOCOLS
# ==============================================================================

@runtime_checkable
class ITransactionHandler(Protocol):
    """
    Protocol for a specialized handler that processes specific transaction types.
    Implementing classes are responsible for Domain Validation and Business Logic.
    """
    
    @property
    def transaction_type(self) -> str:
        """The specific transaction type string this handler supports."""
        ...

    def validate(self, transaction: Transaction, context: TransactionContext) -> None:
        """
        Pure validation logic. Raises exceptions if invalid.
        Should NOT mutate state.
        """
        ...

    def handle(self, transaction: Transaction, buyer: Any, seller: Any, context: TransactionContext) -> bool:
        """
        Executes the business logic for the transaction.
        Responsible for calling SettlementSystem.transfer() if funds need to move.
        Returns True if successful, False otherwise.
        """
        ...

@runtime_checkable
class ITransactionDispatcher(Protocol):
    """
    Interface for the central processor that routes transactions to handlers.
    """

    def register_handler(self, handler: ITransactionHandler) -> None:
        """Registers a handler for a specific transaction type."""
        ...

    def process_batch(self, transactions: Iterable[Transaction], context: TransactionContext) -> List[TransactionExecutionResultDTO]:
        """
        Processes a batch of transactions via their registered handlers.
        """
        ...
```

File: design\3_work_artifacts\specs\transaction_integration_spec.md
```markdown
# Spec: Transaction Integration & Standardization

## 1. Introduction
This specification defines the architecture for the **Transaction Integration Layer**, aiming to unify the disparate transaction processing logic currently split between `TransactionProcessor` (Simulation System) and `TransactionEngine` (Finance Module). It establishes a strict **Dispatcher-Handler Pattern** to resolve technical debt regarding code duplication and floating-point precision leaks.

- **Primary Goal**: Standardize transaction processing interfaces.
- **Key Directive**: Enforce **Integer Pennies** for all settlement operations (Resolves `TD-CRIT-FLOAT-SETTLE`).
- **Scope**: `modules/finance/transaction_integration/`

## 2. Technical Debt Resolution

| Debt ID | Description | Resolution Strategy |
| :--- | :--- | :--- |
| **TD-PROC-TRANS-DUP** | Logic duplication between `TransactionManager` and `TransactionProcessor`. | Deprecate legacy `TransactionManager`. Designate `TransactionProcessor` (implementing `ITransactionDispatcher`) as SSoT. |
| **TD-CRIT-FLOAT-SETTLE** | `float` usage in settlement logic causing precision drift. | `TransactionExecutionResultDTO` and `ITransactionHandler` MUST explicitly use `amount_settled_pennies` (int). |
| **TD-INT-PENNIES-FRAGILITY** | `hasattr` checks for `xxx_pennies`. | Enforce `ISettlementSystem` usage which strictly requires `int` pennies. |

## 3. Architecture Overview

### 3.1. The Pipeline
The transaction lifecycle follows a strict pipeline:
1.  **Ingestion**: `Transaction` objects (DTOs) are submitted to the `ITransactionDispatcher`.
2.  **Routing**: Dispatcher identifies the correct `ITransactionHandler` based on `transaction.transaction_type`.
3.  **Context Assembly**: Dispatcher constructs a `TransactionContext` containing restricted system access (Settlement, Registries).
4.  **Validation**: Handler performs domain-specific checks (Inventory availability, Skill requirements).
5.  **Execution (Atomic)**: Handler executes the logic.
    - If financial transfer is involved, it **MUST** use `context.settlement_system.transfer()`.
    - **CRITICAL**: All amounts passed to `transfer()` must be `int`.
6.  **Reporting**: Handler returns `TransactionExecutionResultDTO`.

### 3.2. Interface Definitions (Pseudo-code)

#### Transaction Execution Result
```python
@dataclass
class TransactionExecutionResultDTO:
    status: str
    amount_settled_pennies: int  # STRICT INTEGER
    currency: str
    side_effects: Dict[str, Any] # e.g., {'inventory_moved': 'food', 'qty': 5.0}
```

#### Generic Handler Interface
```python
class ITransactionHandler(Protocol):
    def handle(self, tx: Transaction, buyer: Any, seller: Any, ctx: TransactionContext) -> bool:
        # 1. Validate (Inventory, Rights, etc.)
        # 2. Calculate Amount (Price * Qty) -> Convert to Pennies
        # 3. SettlementSystem.transfer(...)
        # 4. Update Domain State (Inventory deduction, etc.)
        # 5. Return Success/Fail
        ...
```

## 4. Implementation Details

### 4.1. Goods Transaction Handler (Example)
- **Type**: `'goods'`
- **Validation**:
    - Seller has `inventory[item_id] >= quantity`.
    - Buyer has sufficient funds (checked by Settlement, but pre-check allowed).
- **Execution**:
    - `total_pennies = int(tx.price * tx.quantity * 100)` (if price is float dollars) OR `tx.total_pennies`.
    - Call `settlement.transfer(buyer, seller, total_pennies)`.
    - Decrement Seller Inventory / Increment Buyer Inventory.

### 4.2. Labor Transaction Handler (Example)
- **Type**: `'labor'`
- **Validation**:
    - Employer (Buyer) has budget.
    - Employee (Seller) has available `time_budget`.
- **Execution**:
    - Transfer Wages (`wage_pennies`).
    - Update `Employee.time_worked`.
    - Update `Employer.labor_hours_received`.

## 5. Verification Plan

### 5.1. Test Cases
- **Case 1: Precision Enforcement**: Create a transaction with `price=10.001` and verify that settlement logic handles rounding/truncation deterministically according to the Penny Standard.
- **Case 2: Handler Routing**: Register mock handlers for 'type_A' and 'type_B'. Submit a batch mixed with both types. Verify correct routing.
- **Case 3: Atomic Failure**: Simulate a Settlement failure (Insufficient Funds). Verify that Domain State (e.g., Inventory) is **NOT** updated (Rollback/Atomic Check).

### 5.2. Integration Check
- The `TransactionProcessor` in `simulation/systems` must be refactored to implement the `ITransactionDispatcher` protocol defined in this spec.
- **Mocking**: Tests must use `MagicMock(spec=ISettlementSystem)` to ensure arguments are checked against the protocol (especially `amount: int`).

## 6. Risk Assessment
- **Migration Risk**: Existing agents might still be generating `Transaction` objects with `price` as float without `total_pennies` set.
    - **Mitigation**: The Handler's `validate` method must normalize the transaction data (calculate pennies) before execution.
- **Performance**: Dispatching overhead for thousands of transactions per tick.
    - **Mitigation**: Use dictionary lookups for handlers (O(1)). Pre-warm handler registry.

## 7. Mandatory Reporting
> **[!] ACTION REQUIRED**:
> Upon creating this spec, create/update `communications/insights/MISSION_TRANSACTION_INT_SPEC.md` with:
> 1. Confirmation that `TD-CRIT-FLOAT-SETTLE` is addressed by the `int` requirement in `TransactionExecutionResultDTO`.
> 2. List of existing Transaction Types found in the codebase that need Handlers created.
```