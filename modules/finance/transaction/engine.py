import uuid
import logging
from typing import Optional, Callable

from modules.finance.transaction.api import (
    ITransactionEngine,
    ITransactionValidator,
    ITransactionExecutor,
    ITransactionLedger,
    IAccountAccessor,
    TransactionDTO,
    TransactionResultDTO,
    TransactionError,
    ValidationError,
    InsufficientFundsError,
    InvalidAccountError,
    NegativeAmountError,
    ExecutionError
)

# ==============================================================================
# DEFAULT IMPLEMENTATIONS
# ==============================================================================

class TransactionValidator(ITransactionValidator):
    def __init__(self, account_accessor: IAccountAccessor):
        self.account_accessor = account_accessor

    def validate(self, transaction: TransactionDTO) -> None:
        if transaction['amount'] <= 0:
            raise NegativeAmountError(f"Transaction amount must be positive. Got: {transaction['amount']}")

        if not self.account_accessor.exists(transaction['source_account_id']):
            raise InvalidAccountError(f"Source account does not exist: {transaction['source_account_id']}")

        if not self.account_accessor.exists(transaction['destination_account_id']):
            raise InvalidAccountError(f"Destination account does not exist: {transaction['destination_account_id']}")

        # Check sufficient funds
        try:
            wallet = self.account_accessor.get_wallet(transaction['source_account_id'])
            # Note: IWallet.get_balance might raise exception if currency not found,
            # but usually it returns 0.0 or we should handle it.
            # Assuming get_balance returns float.
            balance = wallet.get_balance(transaction['currency'])
            if balance < transaction['amount']:
                raise InsufficientFundsError(
                    f"Insufficient funds in source account {transaction['source_account_id']}. "
                    f"Required: {transaction['amount']}, Available: {balance}"
                )
        except Exception as e:
            if isinstance(e, TransactionError):
                raise e
            # Re-raise unexpected errors as InvalidAccountError or generic ValidationError if accessing wallet fails
            raise InvalidAccountError(f"Failed to access source wallet: {e}") from e


class TransactionExecutor(ITransactionExecutor):
    def __init__(self, account_accessor: IAccountAccessor):
        self.account_accessor = account_accessor

    def execute(self, transaction: TransactionDTO) -> None:
        try:
            source_wallet = self.account_accessor.get_wallet(transaction['source_account_id'])
            dest_wallet = self.account_accessor.get_wallet(transaction['destination_account_id'])

            # Atomic transfer is not natively supported by IWallet in one go between two wallets,
            # but we can do subtract then add.
            # If subtract fails, add is not reached.
            # If add fails, we have a problem (inconsistent state).
            # However, IWallet.add usually shouldn't fail for simple addition.
            # IWallet.subtract raises InsufficientFundsError, but we already validated.
            # But race conditions could happen if not single-threaded. Simulation is usually single-threaded.

            source_wallet.subtract(
                transaction['amount'],
                transaction['currency'],
                memo=f"Transfer to {transaction['destination_account_id']}: {transaction['description']}"
            )

            dest_wallet.add(
                transaction['amount'],
                transaction['currency'],
                memo=f"Transfer from {transaction['source_account_id']}: {transaction['description']}"
            )

        except Exception as e:
            raise ExecutionError(f"Transaction execution failed: {e}") from e


class SimpleTransactionLedger(ITransactionLedger):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def record(self, result: TransactionResultDTO) -> None:
        # In a real system, this would write to a DB.
        # For now, we log it.
        level = logging.INFO if result['status'] == 'COMPLETED' else logging.ERROR
        self.logger.log(
            level,
            f"Transaction Record: ID={result['transaction']['transaction_id']}, "
            f"Status={result['status']}, Message={result['message']}"
        )


class TransactionEngine(ITransactionEngine):
    def __init__(
        self,
        validator: ITransactionValidator,
        executor: ITransactionExecutor,
        ledger: ITransactionLedger,
        clock_callback: Optional[Callable[[], float]] = None # To get current time/tick
    ):
        self.validator = validator
        self.executor = executor
        self.ledger = ledger
        self.clock_callback = clock_callback

    def _get_timestamp(self) -> float:
        if self.clock_callback:
            return self.clock_callback()
        return 0.0

    def process_transaction(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: float,
        currency: str,
        description: str
    ) -> TransactionResultDTO:

        transaction_id = str(uuid.uuid4())
        transaction_dto = TransactionDTO(
            transaction_id=transaction_id,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            currency=currency,
            description=description
        )

        # 2. Validation Stage
        try:
            self.validator.validate(transaction_dto)
        except ValidationError as e:
            failed_result = TransactionResultDTO(
                transaction=transaction_dto,
                status='FAILED',
                message=str(e),
                timestamp=self._get_timestamp()
            )
            self.ledger.record(failed_result)
            return failed_result
        except Exception as e:
             # Unexpected error during validation
            failed_result = TransactionResultDTO(
                transaction=transaction_dto,
                status='FAILED',
                message=f"Unexpected validation error: {e}",
                timestamp=self._get_timestamp()
            )
            self.ledger.record(failed_result)
            return failed_result

        # 3. Execution Stage
        try:
            self.executor.execute(transaction_dto)
        except ExecutionError as e:
            critical_failure_result = TransactionResultDTO(
                transaction=transaction_dto,
                status='CRITICAL_FAILURE',
                message=str(e),
                timestamp=self._get_timestamp()
            )
            self.ledger.record(critical_failure_result)
            return critical_failure_result
        except Exception as e:
             # Unexpected error during execution
            critical_failure_result = TransactionResultDTO(
                transaction=transaction_dto,
                status='CRITICAL_FAILURE',
                message=f"Unexpected execution error: {e}",
                timestamp=self._get_timestamp()
            )
            self.ledger.record(critical_failure_result)
            return critical_failure_result

        # 4. Recording & Success
        successful_result = TransactionResultDTO(
            transaction=transaction_dto,
            status='COMPLETED',
            message='Transaction successful.',
            timestamp=self._get_timestamp()
        )
        self.ledger.record(successful_result)

        return successful_result
