import logging
from _typeshed import Incomplete
from modules.finance.api import ITransactionEngine as IHighLevelTransactionEngine, ITransactionHandler as ITransactionHandler, TransactionType as TransactionType
from modules.finance.transaction.api import ExecutionError as ExecutionError, IAccountAccessor as IAccountAccessor, ILedgerEngine as ILedgerEngine, ITransactionExecutor as ITransactionExecutor, ITransactionLedger as ITransactionLedger, ITransactionValidator as ITransactionValidator, InsufficientFundsError as InsufficientFundsError, InvalidAccountError as InvalidAccountError, NegativeAmountError as NegativeAmountError, TransactionDTO as TransactionDTO, TransactionError as TransactionError, TransactionResultDTO as TransactionResultDTO, ValidationError as ValidationError
from modules.system.api import CurrencyCode as CurrencyCode
from typing import Any, Callable

class SkipTransactionError(TransactionError):
    """Raised when a transaction should be skipped rather than failed (e.g. inactive agent)."""

class TransactionValidator(ITransactionValidator):
    account_accessor: Incomplete
    def __init__(self, account_accessor: IAccountAccessor) -> None: ...
    def validate(self, transaction: TransactionDTO) -> None: ...

class TransactionExecutor(ITransactionExecutor):
    account_accessor: Incomplete
    logger: Incomplete
    def __init__(self, account_accessor: IAccountAccessor) -> None: ...
    def execute(self, transaction: TransactionDTO) -> None: ...

class SimpleTransactionLedger(ITransactionLedger):
    logger: Incomplete
    def __init__(self, logger: logging.Logger | None = None) -> None: ...
    def record(self, result: TransactionResultDTO) -> None: ...

class TransactionEngine(IHighLevelTransactionEngine):
    """
    High-Level Transaction Engine implementing the Registry Pattern.
    Dispatches specialized transactions to registered handlers.
    """
    logger: Incomplete
    def __init__(self) -> None: ...
    def register_handler(self, tx_type: TransactionType, handler: ITransactionHandler) -> None: ...
    def process_transaction(self, tx_type: TransactionType, data: Any) -> Any: ...

class LedgerEngine(ILedgerEngine):
    """
    Low-level engine for processing financial transfers (Ledger operations).
    """
    validator: Incomplete
    executor: Incomplete
    ledger: Incomplete
    clock_callback: Incomplete
    logger: Incomplete
    def __init__(self, validator: ITransactionValidator, executor: ITransactionExecutor, ledger: ITransactionLedger, clock_callback: Callable[[], float] | None = None) -> None: ...
    def process_transaction(self, source_account_id: str, destination_account_id: str, amount: int, currency: CurrencyCode, description: str) -> TransactionResultDTO: ...
    def process_batch(self, transactions: list[TransactionDTO]) -> list[TransactionResultDTO]:
        """
        Processes a batch of transactions atomically.
        If any transaction fails (validation or execution), previous successful transactions are rolled back.
        Re-validates sequentially to prevent race condition overdrafts.
        """
