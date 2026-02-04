# Design Document: Transaction Engine

## 1. Introduction

- **Purpose**: To design a robust, SRP-compliant engine for handling all financial transactions within the simulation.
- **Scope**: This design covers the validation and execution of transfers between any two accounts (e.g., household to firm, firm to government).
- **Goals**:
    - **Decoupling**: Strictly separate transaction validation from execution.
    - **Atomicity**: Ensure transactions are all-or-nothing.
    - **Extensibility**: Prepare for multi-currency support from the ground up.
    - **Testability**: Design for easy unit testing with clear dependencies.

## 2. System Architecture (High-Level)

The engine follows a pipeline architecture, ensuring Single Responsibility at each stage.

```
+-----------------------+      +-------------------------+      +------------------------+      +-----------------------+
|        Client         |----->|   ITransactionEngine    |----->|  ITransactionValidator |----->|   ITransactionExecutor  |
| (e.g., Market, Govt)  |      | (Orchestrator)          |      | (Pre-flight Checks)    |      | (Atomic Execution)    |
+-----------------------+      +-------------------------+      +------------------------+      +-----------+-----------+
                                                                                                              |
                                                                                                              v
                                                                                                   +-----------------------+
                                                                                                   |   IAccountServiceDAO  |
                                                                                                   | (Ledger Interaction)  |
                                                                                                   +-----------------------+
```

- **ITransactionEngine**: The public-facing entry point. It orchestrates the validation and execution process.
- **ITransactionValidator**: Performs all possible pre-flight checks that don't require locking resources (e.g., schema validation, account existence).
- **ITransactionExecutor**: Performs the atomic transfer, including the final balance check and updates. This is the only component that mutates state.
- **IAccountServiceDAO**: A Data Access Object responsible for abstracting the underlying ledger or account database.

## 3. Detailed Design

### 3.1. API/Interface (`api.py`)

#### **Data Transfer Objects (DTOs)**
```python
# In: modules/finance/dtos.py (or a new api.py)

from typing import TypedDict, Optional, Literal, List
from decimal import Decimal

class TransactionRequestDTO(TypedDict):
    """Data required to request a transaction."""
    sender_id: str
    receiver_id: str
    amount: Decimal
    currency: str
    memo: Optional[str]
    # To prevent double-spending in async scenarios
    idempotency_key: str 

class ValidationResultDTO(TypedDict):
    """Result of a pre-flight validation check."""
    is_valid: bool
    reasons: List[str]

class TransactionRecordDTO(TypedDict):
    """A record of a completed and committed transaction."""
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: Decimal
    currency: str
    timestamp: float # Unix timestamp
    memo: Optional[str]

class TransactionResultDTO(TypedDict):
    """Final result returned to the client."""
    status: Literal["SUCCESS", "FAILED"]
    message: str
    transaction_id: Optional[str]
```

#### **Interfaces (Protocols)**
```python
# In: modules/finance/api.py

from typing import Protocol
from decimal import Decimal
# from .dtos import ...

class InsufficientFundsError(Exception):
    pass

class AccountNotFoundError(Exception):
    pass

class InvalidCurrencyError(Exception):
    pass

class IAccountServiceDAO(Protocol):
    """Interface for accessing account data."""

    def get_balance(self, account_id: str, currency: str) -> Decimal:
        """Gets the current balance for a given account and currency."""
        ...

    def update_balance(self, account_id: str, delta: Decimal, currency: str) -> None:
        """Updates an account's balance by a delta amount. For atomicity."""
        ...
    
    def account_exists(self, account_id: str) -> bool:
        """Checks if an account exists."""
        ...

class ITransactionValidator(Protocol):
    """Validates a transaction request without mutating state."""

    def validate(self, request: TransactionRequestDTO, dao: IAccountServiceDAO) -> ValidationResultDTO:
        """Performs pre-flight checks."""
        ...

class ITransactionExecutor(Protocol):
    """Executes the transaction atomically."""

    def execute(self, request: TransactionRequestDTO, dao: IAccountServiceDAO) -> TransactionRecordDTO:
        """Performs the debit and credit operations."""
        ...

class ITransactionEngine(Protocol):
    """Orchestrates the entire transaction process."""

    def process_transaction(self, request: TransactionRequestDTO) -> TransactionResultDTO:
        """The main entry point for processing a transaction."""
        ...
```

### 3.2. Logic Steps (Pseudo-code)

#### **TransactionEngine (Default Implementation)**
```python
class TransactionEngine:
    def __init__(self, validator: ITransactionValidator, executor: ITransactionExecutor, dao: IAccountServiceDAO):
        self.validator = validator
        self.executor = executor
        self.dao = dao

    def process_transaction(self, request: TransactionRequestDTO) -> TransactionResultDTO:
        # 1. Validation
        validation_result = self.validator.validate(request, self.dao)
        if not validation_result['is_valid']:
            return {
                "status": "FAILED",
                "message": f"Validation failed: {'; '.join(validation_result['reasons'])}",
                "transaction_id": None
            }

        # 2. Execution
        try:
            # The DAO should handle atomicity (e.g., via DB transaction or lock)
            # This is where the core logic happens.
            record = self.executor.execute(request, self.dao)
            return {
                "status": "SUCCESS",
                "message": "Transaction successful.",
                "transaction_id": record['transaction_id']
            }
        except (InsufficientFundsError, AccountNotFoundError, InvalidCurrencyError) as e:
            # Executor failed, DAO should have rolled back.
            return {
                "status": "FAILED",
                "message": str(e),
                "transaction_id": None
            }
        except Exception as e:
            # Catch-all for unexpected errors
            # Log the full error here
            return {
                "status": "FAILED",
                "message": f"An unexpected error occurred: {e}",
                "transaction_id": None
            }
```

#### **TransactionExecutor (Default Implementation)**
```python
class TransactionExecutor:
    def execute(self, request: TransactionRequestDTO, dao: IAccountServiceDAO) -> TransactionRecordDTO:
        sender_balance = dao.get_balance(request['sender_id'], request['currency'])
        
        # Final, just-in-time check
        if sender_balance < request['amount']:
            raise InsufficientFundsError(f"Insufficient funds for sender {request['sender_id']}.")

        # Atomicity must be guaranteed by the DAO's implementation
        dao.update_balance(request['sender_id'], -request['amount'], request['currency'])
        dao.update_balance(request['receiver_id'], request['amount'], request['currency'])
        
        # Create and return the record
        # ... (generate id, timestamp)
        return transaction_record
```

## 4. Technical Considerations

- **Error Handling**: Custom, specific exceptions (`InsufficientFundsError`, `AccountNotFoundError`) are raised from the `Executor` to be caught by the `Engine`. The `Engine` is responsible for translating these into a user-friendly `TransactionResultDTO`.
- **Concurrency**: The `IAccountServiceDAO` implementation is responsible for guaranteeing atomicity. If it's a database, it should use `BEGIN TRANSACTION...COMMIT/ROLLBACK`. If it's in-memory, it must use locks (`threading.Lock`). An `idempotency_key` is included in the request DTO to prevent duplicate processing from retries.
- **Data Integrity**: Use of the `Decimal` type is mandatory for all currency amounts to prevent floating-point arithmetic errors.

## 5. Verification Plan

### Test Cases
- **Success**: A valid transaction between two existing accounts.
- **Failure (Validation)**:
    - Negative or zero transaction amount.
    - Non-existent sender or receiver account.
    - Request DTO missing required fields.
- **Failure (Execution)**:
    - Sender has insufficient funds (the most critical test).
    - An error during the receiver's credit after the sender's debit (requires rollback).
- **Concurrency Test**: Two simultaneous transactions from the same account that, combined, exceed its balance. Only one should succeed.

### Golden Sample
```python
# Used to test the transaction engine
golden_transaction_request = TransactionRequestDTO(
    sender_id='firm_1',      # From golden_firms fixture
    receiver_id='household_101', # From golden_households fixture
    amount=Decimal('150.75'),
    currency='USD',
    memo='Weekly salary payment.',
    idempotency_key='tx-20260204-abc-123'
)
```

## 6. Mocking Guide

- **DO NOT** use `unittest.mock.MagicMock` for the DAO. This breaks type safety and hides interface mismatches.
- **DO** create a dedicated `MockAccountServiceDAO` that implements the `IAccountServiceDAO` protocol.
- **Mechanism**: The mock DAO can be initialized with a dictionary representing the ledger.

```python
# In: tests/mocks/finance_mocks.py
class MockAccountServiceDAO:
    def __init__(self, initial_balances: dict[str, Decimal]):
        self._balances = initial_balances.copy()
        self._accounts = set(initial_balances.keys())

    def get_balance(self, account_id: str, currency: str) -> Decimal:
        # For simplicity, this mock ignores currency. A real one wouldn't.
        if not self.account_exists(account_id):
            raise AccountNotFoundError(f"Account {account_id} not found.")
        return self._balances.get(account_id, Decimal('0'))

    # ... implement other methods
```
- **Usage**: In `pytest`, create a fixture that provides an instance of this mock, populated with data from `golden_households` and `golden_firms`.

- **🚨 Schema Change Notice**: If `TransactionRequestDTO` or other DTOs are modified, the `golden_transaction_request` sample and any related fixtures **MUST** be updated. The `fixture_harvester.py` script may need to be run to regenerate snapshots if the underlying agent schemas change.

## 7. 🚨 Risk & Impact Audit

- **Circular Dependency**: High Risk. The `finance` module is a low-level service. The `TransactionEngine` and its `DAO` MUST NOT import from higher-level business logic modules (like `household` or `market`). All dependencies must flow downwards. The `Client -> Engine` direction must be respected.
- **Test Impact**: Medium Risk. Any existing tests that directly manipulate agent balances (e.g., `test_household_consumption`) will need to be refactored to use the `TransactionEngine` or a mock that correctly simulates its behavior. Direct balance manipulation in tests should be deprecated.
- **Configuration Dependency**: Low Risk. The engine may require a list of supported currencies. This should be added to `config/finance.yaml` and loaded via the `SimulationConfig` object, not hardcoded.
- **Pre-requisite Work**:
    1.  **TD-L-01 (Ledger Abstraction)**: A concrete `IAccountServiceDAO` implementation is a blocker. An interface must be finalized and a default implementation (e.g., `SQLiteAccountServiceDAO`) must be created before this engine can be fully implemented.
    2.  **Refactor Agent Initialization**: All agents (`Household`, `Firm`, etc.) must be guaranteed to have an account created via the `IAccountServiceDAO` upon their creation.

---
---

```python
# In: modules/finance/api.py

from typing import Protocol, TypedDict, Optional, Literal, List
from decimal import Decimal

# DTOs
# =================================================================

class TransactionRequestDTO(TypedDict):
    """Data required to request a transaction."""
    sender_id: str
    receiver_id: str
    amount: Decimal
    currency: str
    memo: Optional[str]
    idempotency_key: str

class ValidationResultDTO(TypedDict):
    """Result of a pre-flight validation check."""
    is_valid: bool
    reasons: List[str]

class TransactionRecordDTO(TypedDict):
    """A record of a completed and committed transaction."""
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: Decimal
    currency: str
    timestamp: float # Unix timestamp
    memo: Optional[str]

class TransactionResultDTO(TypedDict):
    """Final result returned to the client."""
    status: Literal["SUCCESS", "FAILED"]
    message: str
    transaction_id: Optional[str]


# Exceptions
# =================================================================

class InsufficientFundsError(Exception):
    """Raised when an account has insufficient funds for a debit."""
    pass

class AccountNotFoundError(Exception):
    """Raised when a requested account does not exist."""
    pass

class InvalidCurrencyError(Exception):
    """Raised when a transaction involves an unsupported currency."""
    pass


# Interfaces (Protocols)
# =================================================================

class IAccountServiceDAO(Protocol):
    """
    Interface for accessing and modifying account data in the ledger.
    Implementations of this protocol are responsible for ensuring atomicity.
    """

    def get_balance(self, account_id: str, currency: str) -> Decimal:
        """Gets the current balance for a given account and currency."""
        ...

    def update_balance(self, account_id: str, delta: Decimal, currency: str) -> None:
        """
        Updates an account's balance by a delta amount.
        Should be part of an atomic operation managed by the DAO.
        """
        ...
    
    def account_exists(self, account_id: str) -> bool:
        """Checks if an account exists in the ledger."""
        ...


class ITransactionValidator(Protocol):
    """Interface for validating a transaction request without mutating state."""

    def validate(self, request: TransactionRequestDTO, dao: IAccountServiceDAO) -> ValidationResultDTO:
        """
        Performs pre-flight checks, such as schema validation,
        account existence, and non-negative amounts.
        """
        ...


class ITransactionExecutor(Protocol):
    """Interface for executing the transaction atomically."""

    def execute(self, request: TransactionRequestDTO, dao: IAccountServiceDAO) -> TransactionRecordDTO:
        """
        Performs the debit and credit operations. This is the only
        component that should cause state mutation in the ledger.
        It must raise specific errors on failure.
        """
        ...


class ITransactionEngine(Protocol):
    """Interface for orchestrating the entire transaction process."""

    def process_transaction(self, request: TransactionRequestDTO) -> TransactionResultDTO:
        """
        The main public entry point for processing a transaction.
        Coordinates the validator and executor.
        """
        ...

```
