from typing import Optional, Dict, Any, cast
import logging

from simulation.finance.api import ISettlementSystem
from modules.finance.api import IFinancialEntity, InsufficientFundsError


class SettlementSystem(ISettlementSystem):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger if logger else logging.getLogger(__name__)

    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Executes an atomic transfer from debit_agent to credit_agent.
        """
        # 1. Validation
        if amount <= 0:
            self.logger.warning(
                f"TRANSFER_INVALID_AMOUNT | Amount must be positive. Given: {amount} | Memo: {memo}",
                extra={"tags": ["settlement", "error"]},
            )
            return False

        if debit_agent.id == credit_agent.id:
            self.logger.warning(
                f"TRANSFER_SELF | Agent {debit_agent.id} attempted self-transfer. | Memo: {memo}",
                extra={"tags": ["settlement", "warning"]},
            )
            return False

        # 2. Solvency Check & Atomic Operation
        try:
            # Withdraw first (this performs solvency check inside for BaseAgent)
            # For agents that allow negative balance (if any), withdraw implementation should handle it.
            debit_agent.withdraw(amount)
        except InsufficientFundsError:
            self.logger.error(
                f"INSUFFICIENT_FUNDS | Agent {debit_agent.id} (Assets: {debit_agent.assets:.2f}) "
                f"cannot pay {amount:.2f} to Agent {credit_agent.id}. | Memo: {memo}",
                extra={
                    "debit_agent_id": debit_agent.id,
                    "credit_agent_id": credit_agent.id,
                    "amount": amount,
                    "tags": ["settlement", "insolvency"],
                },
            )
            return False
        except Exception as e:
            self.logger.critical(
                f"WITHDRAW_FAILURE | Agent {debit_agent.id} failed to withdraw {amount}. Error: {e}",
                extra={"tags": ["settlement", "error"]},
            )
            return False

        try:
            credit_agent.deposit(amount)
        except Exception as e:
            self.logger.critical(
                f"DEPOSIT_FAILURE | Rolled back transfer of {amount} from {debit_agent.id} to {credit_agent.id}. Error: {e}",
                extra={"tags": ["settlement", "critical"]},
            )
            # Rollback: Try to add back to debit_agent
            try:
                debit_agent.deposit(amount)
            except Exception as rollback_error:
                self.logger.critical(
                    f"ROLLBACK_FAILED | SYSTEM CORRUPTED. Agent {debit_agent.id} lost {amount}. Error: {rollback_error}",
                    extra={"tags": ["settlement", "fatal"]},
                )
            return False

        # 4. Success Logging
        self.logger.info(
            f"TRANSFER | {debit_agent.id} -> {credit_agent.id} : {amount:.2f} | {memo}",
            extra={
                "debit_agent_id": debit_agent.id,
                "credit_agent_id": credit_agent.id,
                "amount": amount,
                "memo": memo,
                "tags": ["settlement", "transfer"],
            },
        )
        return True
