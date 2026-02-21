from typing import Protocol, List, Literal, runtime_checkable, Any
from dataclasses import dataclass
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY

# ==============================================================================
# DATA TRANSFER OBJECTS (DTOs)
# ==============================================================================

@dataclass
class TransactionDTO:
    """
    A pure data container describing a single transaction request.
    This object is immutable once created and is passed between components.
    MIGRATION: Uses integer pennies for amount.
    """
    transaction_id: str
    source_account_id: str
    destination_account_id: str
    amount: int
    currency: CurrencyCode  # e.g., "GOLD", "USD"
    description: str

@dataclass
class TransactionResultDTO:
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

@runtime_checkable
class ITransactionParticipant(Protocol):
    """
    A standardized interface for any entity (Agent, Firm, Wallet wrapper)
    that can participate in financial transactions.
    """
    def deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        """Deposits funds into the participant's account."""
        ...

    def withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY, memo: str = "") -> None:
        """Withdraws funds from the participant's account."""
        ...

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """Returns the current balance for the specified currency."""
        ...

    @property
    def allows_overdraft(self) -> bool:
        """Returns True if this participant is allowed to have a negative balance (e.g., Central Bank)."""
        ...


@runtime_checkable
class IAccountAccessor(Protocol):
    """
    Interface for accessing account information and performing operations.
    Decouples the transaction system from the agent registry.
    """
    def get_participant(self, account_id: str) -> ITransactionParticipant:
        """
        Retrieves the transaction participant for the given account ID.
        Raises InvalidAccountError if the account does not exist or is incompatible.
        """
        ...

    def exists(self, account_id: str) -> bool:
        """Checks if an account exists."""
        ...


@runtime_checkable
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


@runtime_checkable
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


@runtime_checkable
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


@runtime_checkable
class ILedgerEngine(Protocol):
    """
    Interface for the ledger engine that orchestrates financial transfers (debit/credit).
    Renamed from ITransactionEngine to avoid conflict with the High-Level Transaction Engine.
    """
    def process_transaction(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: int,
        currency: CurrencyCode,
        description: str
    ) -> TransactionResultDTO:
        """
        Processes a complete financial transaction from validation to recording.

        Args:
            source_account_id: The ID of the account to debit.
            destination_account_id: The ID of the account to credit.
            amount: The amount to transfer (in pennies).
            currency: The currency of the transaction.
            description: A human-readable description of the transaction.

        Returns:
            A DTO containing the full transaction details and its final status.
        """
        ...

    def process_batch(self, transactions: List[TransactionDTO]) -> List[TransactionResultDTO]:
        """
        Processes a batch of transactions atomically.
        If any transaction fails, the entire batch is rolled back (implementation dependent,
        but interface supports returning results for all).
        """
        ...
