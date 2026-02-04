# Spec: Transaction Engine

## 1. Overview

This document specifies the design for a Transaction Engine module. The primary goal is to create a robust, maintainable, and testable system for handling all financial transactions within the simulation.

The design adheres strictly to the Single Responsibility Principle (SRP) by decoupling the core stages of a transaction: Validation, Execution, and Recording. This architecture prepares the system for future enhancements, such as multi-currency support and transaction fees, without requiring major refactoring.

## 2. Logic Steps (Pseudo-code)

The `TransactionEngine` will orchestrate the process, delegating tasks to specialized components.

```python
# Inside TransactionEngine.process_transaction method:

# 1. Initialization & DTO Creation
transaction_id = self.id_generator.generate()
transaction_dto = TransactionDTO(
    transaction_id=transaction_id,
    source_account_id=source_account_id,
    destination_account_id=destination_account_id,
    amount=amount,
    currency=currency,
    description=description
)

# 2. Validation Stage (Guard Clause)
try:
    # The validator checks rules like account existence, sufficient funds, etc.
    self.validator.validate(transaction_dto)
except ValidationError as e:
    # If validation fails, create a failed result and exit immediately.
    failed_result = TransactionResultDTO(
        transaction=transaction_dto,
        status='FAILED',
        message=str(e),
        timestamp=self.clock.get_time()
    )
    # The ledger may optionally record failed attempts for auditing.
    self.ledger.record(failed_result)
    return failed_result

# 3. Execution Stage
try:
    # The executor performs the actual state change (debit/credit).
    # This component trusts that the transaction is valid.
    self.executor.execute(transaction_dto)
except ExecutionError as e:
    # This indicates a critical, unexpected error during state change.
    # A potential rollback mechanism would be triggered here in a more complex system.
    critical_failure_result = TransactionResultDTO(
        transaction=transaction_dto,
        status='CRITICAL_FAILURE',
        message=f"Execution failed post-validation: {e}",
        timestamp=self.clock.get_time()
    )
    self.ledger.record(critical_failure_result)
    # This case requires special monitoring.
    return critical_failure_result

# 4. Recording & Success
successful_result = TransactionResultDTO(
    transaction=transaction_dto,
    status='COMPLETED',
    message='Transaction successful.',
    timestamp=self.clock.get_time()
)
# The ledger records the successful transaction.
self.ledger.record(successful_result)

# 5. Return successful result object
return successful_result
```

## 3. Exception Handling

The engine will use a hierarchy of custom exceptions to provide clear error contexts.

-   `TransactionError` (Base Exception)
    -   `ValidationError(TransactionError)`: Raised by the Validator component for any business rule violation.
        -   `InsufficientFundsError(ValidationError)`: Source account balance is too low.
        -   `InvalidAccountError(ValidationError)`: Source or destination account does not exist or is inactive.
        -   `NegativeAmountError(ValidationError)`: Transaction amount is zero or negative.
    -   `ExecutionError(TransactionError)`: Raised by the Executor if the state change fails for an unexpected reason after validation has passed. This signals a potentially inconsistent state.

## 4. Interface 명세 (DTOs)

Data will be passed between components using strictly-defined Data Transfer Objects.

```python
# In modules/finance/transaction/api.py

from typing import TypedDict, Literal

# The core data describing a transaction request.
class TransactionDTO(TypedDict):
    transaction_id: str
    source_account_id: str
    destination_account_id: str
    amount: float
    currency: str  # e.g., "GOLD", "USD"
    description: str

# The object returned by the engine after processing is complete.
class TransactionResultDTO(TypedDict):
    transaction: TransactionDTO
    status: Literal['COMPLETED', 'FAILED', 'CRITICAL_FAILURE']
    message: str
    timestamp: float # Simulation timestamp
```

## 5. 검증 계획 (Verification Plan)

-   **Unit Test `validator`**:
    -   Test case for sufficient funds (should pass).
    -   Test case for insufficient funds (should raise `InsufficientFundsError`).
    -   Test case for invalid source account (should raise `InvalidAccountError`).
    -   Test case for zero or negative amount (should raise `NegativeAmountError`).
-   **Unit Test `executor`**:
    -   Given a valid `TransactionDTO`, verify that `source.balance` is debited and `destination.balance` is credited correctly.
    -   Mock the account objects to simulate `update_balance` methods.
-   **Integration Test `TransactionEngine`**:
    -   **Happy Path**: A valid transfer from one household to another. Verify a `COMPLETED` `TransactionResultDTO` is returned and balances are updated.
    -   **Failure Path**: An invalid transfer (e.g., insufficient funds). Verify a `FAILED` `TransactionResultDTO` is returned and balances remain unchanged.
    -   Verify the `ITransactionLedger.record` method is called exactly once in all scenarios with the correct result object.

## 6. Mocking 가이드

-   **Data Source**: All tests involving accounts **MUST** use the `golden_households` and `golden_firms` fixtures from `tests/conftest.py`. These provide realistic, schema-compliant data. Do **NOT** create agents manually with `MagicMock`.

    ```python
    # Correct usage of fixtures
    def test_firm_pays_household(golden_firms, golden_households):
        firm = golden_firms[0]
        household = golden_households[0]
        # ... proceed with test using these agent instances
    ```

-   **Component Mocking**: The engine's dependencies (`validator`, `executor`, `ledger`) **SHOULD** be mocked during the engine's unit tests using `pytest-mock`'s `mocker` fixture. This isolates the engine's orchestration logic for testing.

    ```python
    def test_engine_calls_validator(mocker):
        mock_validator = mocker.patch('modules.finance.transaction.api.ITransactionValidator')
        # ... setup engine with mock_validator
        # ... run engine and assert mock_validator.validate.assert_called_once()
    ```

-   **🚨 Schema Change Notice**: If the `TransactionDTO` or related agent schemas change, the "Golden" data snapshots in `design/_archive/snapshots/` may become outdated. A "Harvesting" step using `scripts/fixture_harvester.py` **MUST** be included in the implementation plan to regenerate these fixtures and ensure test validity.

## 7. 🚨 Risk & Impact Audit (기술적 위험 분석)

-   **순환 참조 위험 (Medium)**: The `TransactionValidator` will need access to account data (e.g., from `household` or `government` modules). Those modules might, in turn, need to use the `TransactionEngine`. This creates a high risk of circular imports.
    -   **Mitigation**: Employ strict Dependency Injection. The engine and its components should receive interfaces to data accessors (e.g., an `IAccountAccessor` protocol) in their constructors, rather than importing concrete modules directly.

-   **테스트 영향도 (High)**: This engine centralizes all value transfers. Existing tests that manually manipulate agent balances (`agent.balance += 100`) will become invalid as they bypass the official transaction logic and ledger.
    -   **Mitigation**: A significant, project-wide refactoring effort will be required to replace all manual balance adjustments with calls to the new `TransactionEngine`. This task should be logged in the `TECH_DEBT_LEDGER.md` and planned accordingly.

-   **설정 의존성 (Low)**: The initial design has no direct config dependencies. However, future features like transaction fees or currency conversion rates will require additions to `finance.yaml` or `economy_params.yaml`.

-   **선행 작업 권고 (High)**: Due to the high impact on testing and existing code, the implementation of this Transaction Engine should be considered a foundational task. It is recommended to pause development on new features that involve monetary transfers until this engine is implemented and integrated. A task should be created to audit the codebase for all instances of manual balance manipulation.

---

```python
# Path: modules/finance/transaction/api.py
from typing import Protocol, TypedDict, Literal

# ==============================================================================
# DATA TRANSFER OBJECTS (DTOs)
# ==============================================================================

class TransactionDTO(TypedDict):
    """
    A pure data container describing a single transaction request.
    This object is immutable once created and is passed between components.
    """
    transaction_id: str
    source_account_id: str
    destination_account_id: str
    amount: float
    currency: str  # e.g., "GOLD", "USD"
    description: str


class TransactionResultDTO(TypedDict):
    """
    A data container representing the final outcome of a transaction attempt.
    This is what the TransactionEngine returns to the caller.
    """
    transaction: TransactionDTO
    status: Literal['COMPLETED', 'FAILED', 'CRITICAL_FAILURE']
    message: str
    timestamp: float # Simulation timestamp


# ==============================================================================
# EXCEPTIONS
# ==============================================================================

class TransactionError(Exception):
    """Base exception for all transaction-related errors."""
    pass


class ValidationError(TransactionError):
    """Raised by the validator when a business rule is violated."""
    pass


class InsufficientFundsError(ValidationError):
    """Raised when the source account has an insufficient balance."""
    pass


class InvalidAccountError(ValidationError):
    """Raised when the source or destination account is invalid or inactive."""
    pass


class NegativeAmountError(ValidationError):
    """Raised when the transaction amount is not a positive number."""
    pass


class ExecutionError(TransactionError):
    """
    Raised by the executor for critical failures after validation has passed.
    This may indicate an inconsistent state.
    """
    pass


# ==============================================================================
# COMPONENT INTERFACES (Protocols)
# ==============================================================================

class ITransactionValidator(Protocol):
    """
    Interface for a component that validates a transaction against business rules.
    It should not modify any state.
    """
    def validate(self, transaction: TransactionDTO) -> None:
        """
        Checks if the transaction is valid.
        
        Args:
            transaction: The transaction data to validate.
            
        Raises:
            ValidationError or its subclasses if the transaction is invalid.
        """
        ...


class ITransactionExecutor(Protocol):
    """
    Interface for a component that executes a transaction.
    It assumes the transaction has already been validated.
    """
    def execute(self, transaction: TransactionDTO) -> None:
        """
        Performs the state change for the transaction (e.g., debit/credit).
        
        Args:
            transaction: The validated transaction data to execute.
            
        Raises:
            ExecutionError if the state change fails unexpectedly.
        """
        ...


class ITransactionLedger(Protocol):
    """
    Interface for a Data Access Object (DAO) that records transaction results.
    This is the persistence layer.
    """
    def record(self, result: TransactionResultDTO) -> None:
        """
        Saves the result of a transaction to a persistent store.
        
        Args:
            result: The final result object of the transaction.
        """
        ...


class ITransactionEngine(Protocol):
    """
    Interface for the main engine that orchestrates the entire transaction process.
    This is the primary entry point for external modules.
    """
    def process_transaction(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: float,
        currency: str,
        description: str
    ) -> TransactionResultDTO:
        """
        Processes a complete financial transaction from validation to recording.
        
        Args:
            source_account_id: The ID of the account to debit.
            destination_account_id: The ID of the account to credit.
            amount: The amount to transfer.
            currency: The currency of the transaction.
            description: A human-readable description of the transaction.
            
        Returns:
            A DTO containing the full transaction details and its final status.
        """
        ...

```
