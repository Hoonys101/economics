import uuid
import logging
from typing import Optional, Callable, List

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
from modules.system.api import CurrencyCode

# ==============================================================================
# DEFAULT IMPLEMENTATIONS
# ==============================================================================

class TransactionValidator(ITransactionValidator):
    def __init__(self, account_accessor: IAccountAccessor):
        self.account_accessor = account_accessor

    def validate(self, transaction: TransactionDTO) -> None:
        # Strict Type Check
        if not isinstance(transaction.amount, int):
             raise ValidationError(f"Transaction amount must be integer (pennies). Got: {type(transaction.amount)}")

        if transaction.amount <= 0:
            raise NegativeAmountError(f"Transaction amount must be positive. Got: {transaction.amount}")

        # Account Existence Checks
        if not self.account_accessor.exists(transaction.source_account_id):
            raise InvalidAccountError(f"Source account does not exist: {transaction.source_account_id}")

        if not self.account_accessor.exists(transaction.destination_account_id):
            raise InvalidAccountError(f"Destination account does not exist: {transaction.destination_account_id}")

        # Check sufficient funds
        try:
            participant = self.account_accessor.get_participant(transaction.source_account_id)
            balance = participant.get_balance(transaction.currency)
            if balance < transaction.amount and not participant.allows_overdraft:
                raise InsufficientFundsError(
                    f"Insufficient funds in source account {transaction.source_account_id}. "
                    f"Required: {transaction.amount}, Available: {balance}"
                )
        except Exception as e:
            if isinstance(e, TransactionError):
                raise e
            # Re-raise unexpected errors as InvalidAccountError or generic ValidationError if accessing participant fails
            raise InvalidAccountError(f"Failed to access source participant: {e}") from e


class TransactionExecutor(ITransactionExecutor):
    def __init__(self, account_accessor: IAccountAccessor):
        self.account_accessor = account_accessor
        self.logger = logging.getLogger(__name__)

    def execute(self, transaction: TransactionDTO) -> None:
        try:
            source_participant = self.account_accessor.get_participant(transaction.source_account_id)
            dest_participant = self.account_accessor.get_participant(transaction.destination_account_id)

            # Atomic transfer: Withdraw then Deposit
            # Step 1: Withdraw
            try:
                source_participant.withdraw(
                    transaction.amount,
                    transaction.currency,
                    memo=f"Transfer to {transaction.destination_account_id}: {transaction.description}"
                )
            except Exception as e:
                 raise ExecutionError(f"Withdrawal failed from {transaction.source_account_id}: {e}") from e

            # Step 2: Deposit
            try:
                dest_participant.deposit(
                    transaction.amount,
                    transaction.currency,
                    memo=f"Transfer from {transaction.source_account_id}: {transaction.description}"
                )
            except Exception as e:
                # ROLLBACK: Attempt to return funds to source
                self.logger.warning(
                    f"Deposit failed for {transaction.destination_account_id}. Rolling back withdrawal from {transaction.source_account_id}. Error: {e}"
                )
                try:
                    source_participant.deposit(
                        transaction.amount,
                        transaction.currency,
                        memo=f"ROLLBACK: Failed transfer to {transaction.destination_account_id}"
                    )
                except Exception as rb_error:
                    # CRITICAL: Money destroyed (Withdrawn but not Returned)
                    msg = (
                        f"CRITICAL: Rollback failed! {transaction.amount} {transaction.currency} lost from {transaction.source_account_id}. "
                        f"Original Error: {e}. Rollback Error: {rb_error}"
                    )
                    self.logger.critical(msg)
                    raise ExecutionError(msg) from rb_error

                # Re-raise original error wrapped in ExecutionError (since transaction failed)
                raise ExecutionError(f"Deposit failed: {e}. Rollback successful.") from e

        except Exception as e:
             if isinstance(e, ExecutionError):
                 raise e
             raise ExecutionError(f"Transaction execution failed: {e}") from e


class SimpleTransactionLedger(ITransactionLedger):
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def record(self, result: TransactionResultDTO) -> None:
        # In a real system, this would write to a DB.
        # For now, we log it.
        level = logging.INFO if result.status == 'COMPLETED' else logging.ERROR
        self.logger.log(
            level,
            f"Transaction Record: ID={result.transaction.transaction_id}, "
            f"Status={result.status}, Message={result.message}"
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
        amount: int,
        currency: CurrencyCode,
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

        return self._process_single(transaction_dto)

    def _process_single(self, transaction_dto: TransactionDTO) -> TransactionResultDTO:
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

    def process_batch(self, transactions: List[TransactionDTO]) -> List[TransactionResultDTO]:
        """
        Processes a batch of transactions atomically.
        If any transaction fails, previous successful transactions in the batch are rolled back.
        """
        results: List[TransactionResultDTO] = []
        successful_transactions: List[TransactionDTO] = []

        # 1. Validation Phase (All must pass)
        for tx in transactions:
            try:
                self.validator.validate(tx)
            except Exception as e:
                 # If one fails validation, fail all
                 fail_msg = f"Batch Validation Failed on {tx.transaction_id}: {e}"
                 failed_results = [
                     TransactionResultDTO(
                         transaction=t,
                         status='FAILED',
                         message=fail_msg,
                         timestamp=self._get_timestamp()
                     ) for t in transactions
                 ]
                 # Record all failures
                 for fr in failed_results:
                     self.ledger.record(fr)
                 return failed_results

        # 2. Execution Phase
        for tx in transactions:
            try:
                self.executor.execute(tx)
                successful_transactions.append(tx)
                results.append(TransactionResultDTO(
                    transaction=tx,
                    status='COMPLETED',
                    message='Transaction successful (Batch)',
                    timestamp=self._get_timestamp()
                ))
            except Exception as e:
                # Failure encountered! Initiate Batch Rollback
                fail_msg = f"Batch Execution Failed on {tx.transaction_id}: {e}"

                # Rollback successful ones (reverse order)
                self._rollback_batch(successful_transactions)

                # Return failure for all
                # Mark executed ones as failed (rolled back) and the failing one as failed.
                failed_results = []
                for t in transactions:
                    msg = fail_msg
                    status = 'FAILED'
                    if t == tx:
                        status = 'CRITICAL_FAILURE' # Execution failed
                    elif t in successful_transactions:
                         msg = f"Rolled back due to batch failure: {fail_msg}"

                    failed_results.append(TransactionResultDTO(
                         transaction=t,
                         status=status,
                         message=msg,
                         timestamp=self._get_timestamp()
                     ))

                for fr in failed_results:
                     self.ledger.record(fr)
                return failed_results

        # 3. Recording (if all successful)
        for res in results:
            self.ledger.record(res)

        return results

    def _rollback_batch(self, transactions: List[TransactionDTO]) -> None:
        """
        Rolls back a list of successfully executed transactions.
        Attempts to rollback ALL transactions even if some fail, to maximize consistency.
        """
        for tx in reversed(transactions):
            try:
                # Reverse Logic: Swap Source/Dest
                reverse_tx = TransactionDTO(
                    transaction_id=f"rollback_{tx.transaction_id}",
                    source_account_id=tx.destination_account_id,
                    destination_account_id=tx.source_account_id,
                    amount=tx.amount,
                    currency=tx.currency,
                    description=f"ROLLBACK of {tx.transaction_id}"
                )
                self.executor.execute(reverse_tx)
            except Exception as e:
                 # CRITICAL: Rollback failed. Money is effectively created/destroyed or trapped.
                 logging.critical(f"BATCH ROLLBACK FAILED for {tx.transaction_id}. System State Inconsistent! Error: {e}")
                 # Continue to try rolling back others
