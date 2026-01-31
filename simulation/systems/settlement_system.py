from typing import Optional, Dict, Any, cast, TYPE_CHECKING
import logging

from simulation.finance.api import ISettlementSystem, ITransaction
from modules.finance.api import IFinancialEntity, InsufficientFundsError

if TYPE_CHECKING:
    from simulation.firms import Firm

class SettlementSystem(ISettlementSystem):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.

    ZERO-SUM PRINCIPLE:
    Every transfer MUST result in a net change of 0.0 across the system.
    Asset deduction from one agent must exactly equal asset addition to another.
    Money creation/destruction is ONLY allowed via the CentralBank (Minting Authority).
    """

    def __init__(self, logger: Optional[logging.Logger] = None, bank: Optional[Any] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bank = bank # TD-179: Reference to Bank for Seamless Payments
        self.total_liquidation_losses: float = 0.0

    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.
        """
        loss_amount = inventory_value + capital_value - recovered_cash
        if loss_amount < 0:
            loss_amount = 0.0

        self.total_liquidation_losses += loss_amount

        agent_id = agent.id if hasattr(agent, 'id') else "UNKNOWN"
        self.logger.info(
            f"LIQUIDATION: Agent {agent_id} liquidated. "
            f"Inventory: {inventory_value:.2f}, Capital: {capital_value:.2f}, Recovered: {recovered_cash:.2f}. "
            f"Net Destruction: {loss_amount:.2f}. Total Destroyed: {self.total_liquidation_losses:.2f}. "
            f"Reason: {reason}",
            extra={"tick": tick, "tags": ["liquidation", "bankruptcy", "ledger"]}
        )

    def transfer(
        self,
        debit_agent: IFinancialEntity,
        credit_agent: IFinancialEntity,
        amount: float,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0
    ) -> Optional[ITransaction]:
        """
        Executes an atomic transfer from debit_agent to credit_agent.
        Returns a Transaction object (truthy) on success, None (falsy) on failure.
        """
        if amount <= 0:
            self.logger.warning(f"Transfer of non-positive amount ({amount}) attempted. Memo: {memo}")
            # Consider this a success logic-wise (no-op) but log it.
            return self._create_transaction_record(
                debit_agent.id if hasattr(debit_agent, 'id') else 0,
                credit_agent.id if hasattr(credit_agent, 'id') else 0,
                amount, memo, tick
            )

        # 1. ATOMIC CHECK: Verify funds BEFORE any modification
        if debit_agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Debit agent is None. Memo: {memo}")
            return None

        if credit_agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Credit agent is None. Memo: {memo}")
            return None

        # Special Case: Central Bank (Minting Authority) can have negative assets (Fiat Issuer).
        is_central_bank = False
        if hasattr(debit_agent, "id") and str(debit_agent.id) == "CENTRAL_BANK":
             is_central_bank = True
        elif hasattr(debit_agent, "__class__") and debit_agent.__class__.__name__ == "CentralBank":
             is_central_bank = True

        if not is_central_bank:
            if hasattr(debit_agent, 'assets'):
                try:
                    current_cash = float(debit_agent.assets)
                    if current_cash < amount:
                        # TD-179: Seamless Payment (Auto-Withdrawal from Bank)
                        if self.bank:
                            needed_from_bank = amount - current_cash
                            bank_balance = self.bank.get_balance(str(debit_agent.id))
                            
                            if (current_cash + bank_balance) < amount:
                                self.logger.error(
                                    f"SETTLEMENT_FAIL | Insufficient total funds (Cash+Deposits) for {debit_agent.id}. "
                                    f"Cash: {current_cash:.2f}, Bank: {bank_balance:.2f}, Total: {(current_cash + bank_balance):.2f}. "
                                    f"Required: {amount:.2f}. Memo: {memo}",
                                    extra={"tags": ["settlement", "insufficient_funds"]}
                                )
                                return None
                            # Success: Will be handled in Phase 2 (Withdrawal)
                        else:
                            self.logger.error(
                                f"SETTLEMENT_FAIL | Insufficient cash for {debit_agent.id} AND Bank service is missing. "
                                f"Cash: {current_cash:.2f}, Required: {amount:.2f}. Memo: {memo}",
                                extra={"tags": ["settlement", "insufficient_funds"]}
                            )
                            return None
                except (TypeError, ValueError):
                    self.logger.warning(
                        f"SettlementSystem warning: Agent {debit_agent.id} assets property is not float compatible."
                    )
            else:
                 self.logger.warning(f"SettlementSystem warning: Agent {debit_agent.id} has no assets property.")

        # 2. EXECUTE: Perform the debit and credit
        try:
            # Phase 1: Debit (Seamless Support)
            if is_central_bank:
                # Central Bank has infinite fiat capacity or uses a dict for assets
                debit_agent.withdraw(amount)
            else:
                current_cash = float(debit_agent.assets)
                if current_cash >= amount:
                    # Standard cash withdrawal
                    debit_agent.withdraw(amount)
                else:
                    # Seamless Payment (TD-179)
                    needed_from_bank = amount - current_cash
                    
                    # 1. Exhaust all cash
                    if current_cash > 0:
                        debit_agent.withdraw(current_cash)
                    
                    # 2. Take the rest from the bank
                    success = self.bank.withdraw_for_customer(int(debit_agent.id), needed_from_bank)
                    if not success:
                        # This shouldn't happen if Phase 1 check passed, but for safety:
                        if current_cash > 0:
                            debit_agent.deposit(current_cash)
                        raise InsufficientFundsError(f"Bank withdrawal failed for {debit_agent.id} despite check.")
                    
                    self.logger.info(
                        f"SEAMLESS_PAYMENT | Agent {debit_agent.id} paid {amount:.2f} using {current_cash:.2f} cash and {needed_from_bank:.2f} from bank.",
                        extra={"tick": tick, "agent_id": debit_agent.id, "tags": ["settlement", "bank"]}
                    )

        except InsufficientFundsError as e:
            self.logger.critical(
                f"SETTLEMENT_CRITICAL | Race condition or logic error. InsufficientFundsError during transfer. "
                f"Initial check passed but withdrawal failed. Details: {e}",
                extra={"tags": ["settlement", "error"]}
            )
            return None
        except Exception as e:
            self.logger.exception(
                 f"SETTLEMENT_UNHANDLED_FAIL | An unexpected error occurred during withdrawal. Details: {e}"
            )
            return None

        try:
            # Phase 2: Credit
            credit_agent.deposit(amount)
        except Exception as e:
            # ROLLBACK: Credit failed, must reverse debit
            self.logger.error(
                f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back withdrawal of {amount:.2f} from {debit_agent.id}. Error: {e}"
            )
            try:
                debit_agent.deposit(amount)
                self.logger.info(f"SETTLEMENT_ROLLBACK_SUCCESS | Rolled back {amount:.2f} to {debit_agent.id}.")
            except Exception as rollback_error:
                self.logger.critical(
                    f"SETTLEMENT_FATAL | Rollback failed! Money {amount:.2f} lost from {debit_agent.id}. "
                    f"Original Error: {e}. Rollback Error: {rollback_error}",
                    extra={"tags": ["settlement", "fatal", "money_leak"]}
                )
            return None

        # Success
        self.logger.debug(
            f"SETTLEMENT_SUCCESS | Transferred {amount:.2f} from {debit_agent.id} to {credit_agent.id}. Memo: {memo}",
            extra={"tags": ["settlement"], "tick": tick}
        )
        return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)

    def create_and_transfer(
        self,
        source_authority: IFinancialEntity,
        destination: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        """
        if amount <= 0:
            return None

        is_central_bank = False
        if hasattr(source_authority, "__class__") and source_authority.__class__.__name__ == "CentralBank":
            is_central_bank = True
        elif hasattr(source_authority, "id") and str(source_authority.id) == "CENTRAL_BANK":
            is_central_bank = True

        if is_central_bank:
            # Minting logic: Just credit destination. Source (CB) is assumed to have infinite capacity.
            try:
                destination.deposit(amount)
                self.logger.info(
                    f"MINT_AND_TRANSFER | Created {amount:.2f} from {source_authority.id} to {destination.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                return self._create_transaction_record(source_authority.id, destination.id, amount, reason, tick)
            except Exception as e:
                self.logger.error(f"MINT_FAIL | {e}")
                return None
        else:
            # If not CB (e.g. Government), treat as regular transfer to enforce budget
            return self.transfer(source_authority, destination, amount, reason, tick=tick)

    def transfer_and_destroy(
        self,
        source: IFinancialEntity,
        sink_authority: IFinancialEntity,
        amount: float,
        reason: str,
        tick: int
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed.
        """
        if amount <= 0:
            return None

        is_central_bank = False
        if hasattr(sink_authority, "__class__") and sink_authority.__class__.__name__ == "CentralBank":
            is_central_bank = True
        elif hasattr(sink_authority, "id") and str(sink_authority.id) == "CENTRAL_BANK":
            is_central_bank = True

        if is_central_bank:
            # Burning logic: Just debit source. Sink (CB) absorbs it (removed from circulation).
            try:
                source.withdraw(amount)
                self.logger.info(
                    f"TRANSFER_AND_DESTROY | Destroyed {amount:.2f} from {source.id} to {sink_authority.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                return self._create_transaction_record(source.id, sink_authority.id, amount, reason, tick)
            except Exception as e:
                self.logger.error(f"BURN_FAIL | {e}")
                return None
        else:
            # If not CB, treat as regular transfer (e.g. tax to Gov)
            return self.transfer(source, sink_authority, amount, reason, tick=tick)

    def _create_transaction_record(self, buyer_id: int, seller_id: int, amount: float, memo: str, tick: int) -> ITransaction:
        return {
            "buyer_id": buyer_id,
            "seller_id": seller_id,
            "item_id": "currency",
            "quantity": amount,
            "price": 1.0,
            "market_id": "settlement",
            "transaction_type": "transfer",
            "time": tick,
            "metadata": {"memo": memo}
        }
