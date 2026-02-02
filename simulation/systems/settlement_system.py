from typing import Optional, Dict, Any, cast, TYPE_CHECKING, Tuple, List
import logging

from simulation.finance.api import ISettlementSystem, ITransaction
from modules.finance.api import IFinancialEntity, InsufficientFundsError
from simulation.dtos.settlement_dtos import LegacySettlementAccount

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
        self.settlement_accounts: Dict[int, LegacySettlementAccount] = {} # TD-160

    def create_settlement(
        self,
        agent_id: int,
        cash_assets: float,
        portfolio_assets: Dict[str, Any],
        real_estate_assets: List[Any],
        tick: int
    ) -> LegacySettlementAccount:
        """
        TD-160: Initiates the settlement process by creating an escrow account.
        In a real implementation, this would involve moving assets.
        Here we assume assets are 'logically' moved by the caller clearing them from the agent.
        """
        account = LegacySettlementAccount(
            deceased_agent_id=agent_id,
            escrow_cash=cash_assets,
            escrow_portfolio=portfolio_assets,
            escrow_real_estate=real_estate_assets,
            status="OPEN",
            created_at=tick
        )
        self.settlement_accounts[agent_id] = account
        self.logger.info(
            f"SETTLEMENT_CREATED | Escrow account created for Agent {agent_id}. Cash: {cash_assets:.2f}",
            extra={"tick": tick, "agent_id": agent_id, "tags": ["settlement", "inheritance"]}
        )
        return account

    def execute_settlement(
        self,
        account_id: int,
        distribution_plan: List[Tuple[Any, float, str, str]], # (Recipient, Amount, Memo, TxType)
        tick: int
    ) -> List[ITransaction]:
        """
        TD-160: Executes the distribution of assets from the escrow account.
        Returns a list of executed transactions (receipts).
        """
        if account_id not in self.settlement_accounts:
            self.logger.error(f"SETTLEMENT_FAIL | Account {account_id} not found.")
            return []

        account = self.settlement_accounts[account_id]
        if account.status != "OPEN":
            self.logger.error(f"SETTLEMENT_FAIL | Account {account_id} is not OPEN. Status: {account.status}")
            return []

        account.status = "PROCESSING"
        transactions: List[ITransaction] = []

        # We need a dummy 'escrow' entity for the source of transfer
        # or we assume the money is 'floating' in this system and we just deposit to recipients.
        # To maintain zero-sum, we must ensure the total distributed <= escrow_cash.
        # But wait, where is the cash?
        # Ideally, we should have transferred it to a concrete 'EscrowAgent' in the simulation.
        # But `SettlementSystem` holds the account virtually.
        # If we didn't transfer to a real agent, the cash effectively vanished from the system when we cleared the deceased agent.
        # So creating it here (depositing to heir) is technically 'creating' it back.
        # Zero-Sum: Deceased Assets -> 0 -> Heir Assets. Net change 0 (if amounts match).

        total_distributed = 0.0

        for recipient, amount, memo, tx_type in distribution_plan:
            if amount <= 0:
                continue

            if total_distributed + amount > account.escrow_cash + 0.01: # Tolerance
                 self.logger.critical(
                     f"SETTLEMENT_OVERDRAFT | Attempted to distribute more than escrow! "
                     f"Escrow: {account.escrow_cash:.2f}, Distributed: {total_distributed:.2f}, Requested: {amount:.2f}",
                     extra={"tick": tick, "agent_id": account_id}
                 )
                 continue # Skip or abort? Skip for now to save what we can.

            try:
                # Direct Deposit (Logic: The cash is coming from the void where we put it when clearing deceased)
                recipient.deposit(amount)
                total_distributed += amount

                # Create Receipt
                tx = self._create_transaction_record(
                    buyer_id=recipient.id if hasattr(recipient, 'id') else 0, # Recipient is Buyer (Receiver)
                    seller_id=account.deceased_agent_id, # Deceased is Seller (Source)
                    amount=amount,
                    memo=memo,
                    tick=tick
                )
                tx["transaction_type"] = tx_type
                tx["metadata"]["executed"] = True # Mark as executed
                transactions.append(tx)

            except Exception as e:
                self.logger.error(f"SETTLEMENT_DISTRIBUTION_FAIL | Failed to pay {recipient.id}. {e}")

        # Update Account
        account.escrow_cash -= total_distributed
        # Rounding check
        if abs(account.escrow_cash) < 0.01:
            account.escrow_cash = 0.0

        return transactions

    def verify_and_close(self, account_id: int, tick: int) -> bool:
        """
        TD-160: Verifies zero balance and closes the account.
        """
        if account_id not in self.settlement_accounts:
            return False

        account = self.settlement_accounts[account_id]

        # Check integrity
        # We assume Portfolio and Real Estate are handled separately or in same batch (not implemented in execute_settlement yet for brevity, assuming cash conversion or direct transfer handling elsewhere).
        # For this task, we focus on Cash integrity.

        if account.escrow_cash > 0.01:
            self.logger.warning(
                f"SETTLEMENT_LEAK | Account {account_id} closed with remaining cash: {account.escrow_cash:.2f}. Burning it.",
                extra={"tick": tick, "agent_id": account_id}
            )
            # Burn remaining (it's already in void, just update record)
            account.escrow_cash = 0.0
            account.status = "CLOSED_WITH_LEAK"
            return False

        account.status = "CLOSED"
        self.logger.info(
            f"SETTLEMENT_CLOSED | Account {account_id} closed successfully.",
            extra={"tick": tick, "agent_id": account_id}
        )
        # Optional: Remove from dict to save memory, or keep for audit?
        # self.settlement_accounts.pop(account_id)
        return True

    def record_liquidation(
        self,
        agent: IFinancialEntity,
        inventory_value: float,
        capital_value: float,
        recovered_cash: float,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialEntity] = None
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.
        If government_agent is provided, transfers residual assets to it (Escheatment).
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

        # WO-178: Escheatment Logic
        if government_agent:
            try:
                # TD-073: Check finance.balance first for Firms
                if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
                    current_assets = agent.finance.balance
                else:
                    current_assets = float(agent.assets) if hasattr(agent, 'assets') else 0.0
            except (TypeError, ValueError):
                current_assets = 0.0

            if current_assets > 0:
                self.transfer(
                    debit_agent=agent,
                    credit_agent=government_agent,
                    amount=current_assets,
                    memo="liquidation_escheatment",
                    tick=tick
                )

    def _execute_withdrawal(self, agent: IFinancialEntity, amount: float, memo: str, tick: int) -> bool:
        """
        Executes withdrawal with checks and seamless payment (Bank) support.
        Returns True on success, False on failure.
        """
        # 1. Checks
        if agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Debit agent is None. Memo: {memo}")
            return False

        is_central_bank = False
        if hasattr(agent, "id") and str(agent.id) == "CENTRAL_BANK":
             is_central_bank = True
        elif hasattr(agent, "__class__") and agent.__class__.__name__ == "CentralBank":
             is_central_bank = True

        if is_central_bank:
             try:
                 agent.withdraw(amount)
                 return True
             except Exception as e:
                 self.logger.error(f"SETTLEMENT_FAIL | Central Bank withdrawal failed. {e}")
                 return False

        # 2. Standard Agent Checks (Compatible with TD-073 Firm Refactor)
        current_cash = 0.0

        # Check for Firm's finance component first
        if hasattr(agent, 'finance') and hasattr(agent.finance, 'balance'):
             current_cash = agent.finance.balance
        # Check for Household's EconComponent state
        elif hasattr(agent, '_econ_state') and hasattr(agent._econ_state, 'assets'):
             current_cash = agent._econ_state.assets
        else:
             if not hasattr(agent, 'assets'):
                  self.logger.warning(f"SettlementSystem warning: Agent {agent.id} has no assets property.")
                  pass
             try:
                 current_cash = float(agent.assets) if hasattr(agent, 'assets') else 0.0
             except (TypeError, ValueError):
                  current_cash = 0.0

        if current_cash < amount:
            # Seamless Check
            if self.bank:
                needed_from_bank = amount - current_cash
                bank_balance = self.bank.get_balance(str(agent.id))
                if (current_cash + bank_balance) < amount:
                    self.logger.error(
                        f"SETTLEMENT_FAIL | Insufficient total funds (Cash+Deposits) for {agent.id}. "
                        f"Cash: {current_cash:.2f}, Bank: {bank_balance:.2f}, Total: {(current_cash + bank_balance):.2f}. "
                        f"Required: {amount:.2f}. Memo: {memo}",
                        extra={"tags": ["settlement", "insufficient_funds"]}
                    )
                    return False
            else:
                self.logger.error(
                    f"SETTLEMENT_FAIL | Insufficient cash for {agent.id} AND Bank service is missing. "
                    f"Cash: {current_cash:.2f}, Required: {amount:.2f}. Memo: {memo}",
                    extra={"tags": ["settlement", "insufficient_funds"]}
                )
                return False

        # 3. Execution
        try:
            if current_cash >= amount:
                agent.withdraw(amount)
            else:
                # Seamless
                needed_from_bank = amount - current_cash
                if current_cash > 0:
                    agent.withdraw(current_cash)

                success = self.bank.withdraw_for_customer(int(agent.id), needed_from_bank)
                if not success:
                    # Rollback cash
                    if current_cash > 0:
                         agent.deposit(current_cash)
                    raise InsufficientFundsError(f"Bank withdrawal failed for {agent.id} despite check.")

                self.logger.info(
                    f"SEAMLESS_PAYMENT | Agent {agent.id} paid {amount:.2f} using {current_cash:.2f} cash and {needed_from_bank:.2f} from bank.",
                    extra={"tick": tick, "agent_id": agent.id, "tags": ["settlement", "bank"]}
                )
            return True
        except InsufficientFundsError as e:
             self.logger.critical(f"SETTLEMENT_CRITICAL | InsufficientFundsError. {e}")
             return False
        except Exception as e:
             self.logger.exception(f"SETTLEMENT_UNHANDLED_FAIL | {e}")
             return False

    def settle_atomic(
        self,
        debit_agent: IFinancialEntity,
        credits_list: List[Tuple[IFinancialEntity, float, str]],
        tick: int
    ) -> bool:
        """
        Executes a one-to-many atomic settlement.
        All credits are summed to determine the total debit amount.
        If the debit fails, the entire transaction is aborted.
        If any credit fails, previous credits in this batch are rolled back.
        """
        if not credits_list:
            return True

        # 0. Validate Credits (No negative transfers allowed in this atomic mode)
        for _, amount, memo in credits_list:
             if amount < 0:
                 self.logger.error(f"SETTLEMENT_FAIL | Negative credit amount {amount} in atomic batch. Memo: {memo}")
                 return False

        # 1. Calculate Total Debit
        total_debit = sum(amount for _, amount, _ in credits_list)
        if total_debit <= 0:
             return True

        # 2. Debit Check & Withdrawal
        memo = f"atomic_batch_{len(credits_list)}_txs"
        success = self._execute_withdrawal(debit_agent, total_debit, memo, tick)
        if not success:
            return False

        # 3. Execute Credits
        completed_credits = []
        for credit_agent, amount, credit_memo in credits_list:
            if amount <= 0:
                continue
            try:
                credit_agent.deposit(amount)
                completed_credits.append((credit_agent, amount))
            except Exception as e:
                self.logger.error(
                    f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back atomic batch. Error: {e}"
                )
                # ROLLBACK
                # 1. Reverse completed credits
                for ca, amt in completed_credits:
                    try:
                        ca.withdraw(amt)
                    except Exception as rb_err:
                        self.logger.critical(f"SETTLEMENT_FATAL | Credit Rollback failed for {ca.id}. {rb_err}")

                # 2. Refund debit agent
                try:
                    debit_agent.deposit(total_debit)
                except Exception as rb_err:
                    self.logger.critical(f"SETTLEMENT_FATAL | Debit Refund failed for {debit_agent.id}. {rb_err}")

                return False

        return True

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

        if debit_agent is None or credit_agent is None:
             self.logger.error(f"SETTLEMENT_FAIL | Debit or Credit agent is None. Memo: {memo}")
             return None

        # EXECUTE
        success = self._execute_withdrawal(debit_agent, amount, memo, tick)
        if not success:
            return None

        try:
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
