from typing import Optional, Dict, Any, cast, TYPE_CHECKING, Tuple, List, Set
import logging
from uuid import UUID
from collections import defaultdict

from simulation.finance.api import ITransaction
from modules.finance.api import (
    IFinancialAgent, IFinancialEntity, IBank, InsufficientFundsError,
    IPortfolioHandler, PortfolioDTO, PortfolioAsset, IHeirProvider, LienDTO, AgentID,
    IMonetaryAuthority
)
from simulation.dtos.settlement_dtos import LegacySettlementAccount
from modules.system.api import DEFAULT_CURRENCY, CurrencyCode, ICurrencyHolder
from modules.system.constants import ID_CENTRAL_BANK
from modules.market.housing_planner_api import MortgageApplicationDTO
from simulation.models import Transaction
from modules.simulation.api import IGovernment, ICentralBank
from modules.common.protocol import enforce_purity

if TYPE_CHECKING:
    from simulation.firms import Firm

class SettlementSystem(IMonetaryAuthority):
    """
    Centralized system for handling all financial transfers between entities.
    Enforces atomicity and zero-sum integrity.
    MIGRATION: Uses integer pennies for all monetary values.

    ZERO-SUM PRINCIPLE:
    Every transfer MUST result in a net change of 0 across the system.
    Asset deduction from one agent must exactly equal asset addition to another.
    Money creation/destruction is ONLY allowed via the CentralBank (Minting Authority).
    """

    def __init__(self, logger: Optional[logging.Logger] = None, bank: Optional[IBank] = None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.bank = bank # TD-179: Reference to Bank for Seamless Payments
        self.total_liquidation_losses: int = 0
        self.settlement_accounts: Dict[int, LegacySettlementAccount] = {} # TD-160
        self.agent_registry: Optional[Any] = None # Injected by SimulationInitializer

        # TD-INT-STRESS-SCALE: Reverse Index for Bank Accounts
        # BankID -> Set[AgentID]
        self._bank_depositors: Dict[int, Set[int]] = defaultdict(set)
        # AgentID -> Set[BankID] (for fast removal)
        self._agent_banks: Dict[int, Set[int]] = defaultdict(set)

    def register_account(self, bank_id: int, agent_id: int) -> None:
        """
        Registers an account link between a bank and an agent.
        Used to maintain the reverse index for bank runs.
        """
        self._bank_depositors[bank_id].add(agent_id)
        self._agent_banks[agent_id].add(bank_id)

    def deregister_account(self, bank_id: int, agent_id: int) -> None:
        """
        Removes an account link between a bank and an agent.
        """
        if bank_id in self._bank_depositors:
            self._bank_depositors[bank_id].discard(agent_id)
            if not self._bank_depositors[bank_id]:
                del self._bank_depositors[bank_id]

        if agent_id in self._agent_banks:
            self._agent_banks[agent_id].discard(bank_id)
            if not self._agent_banks[agent_id]:
                del self._agent_banks[agent_id]

    def get_account_holders(self, bank_id: int) -> List[int]:
        """
        Returns a list of all agents holding accounts at the specified bank.
        This provides O(1) access to depositors for bank run simulation.
        """
        if bank_id in self._bank_depositors:
            return list(self._bank_depositors[bank_id])
        return []

    def remove_agent_from_all_accounts(self, agent_id: int) -> None:
        """
        Removes an agent from all bank account indices.
        Called upon agent liquidation/deletion.
        """
        if agent_id in self._agent_banks:
            # Copy to avoid modification during iteration
            banks = list(self._agent_banks[agent_id])
            for bank_id in banks:
                self.deregister_account(bank_id, agent_id)

    def get_balance(self, agent_id: AgentID, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        """
        Queries the Single Source of Truth for an agent's current balance.
        This is the ONLY permissible way to check another agent's funds.
        """
        if self.agent_registry:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                # Prefer IFinancialEntity for standard "pennies" check if default currency
                if currency == DEFAULT_CURRENCY and isinstance(agent, IFinancialEntity):
                    return agent.balance_pennies

                # Fallback to IFinancialAgent for multi-currency or legacy
                if isinstance(agent, IFinancialAgent):
                    return agent.get_balance(currency)

        self.logger.warning(f"get_balance: Agent {agent_id} not found or Registry not linked or Agent not IFinancialAgent.")
        return 0

    def create_settlement(
        self,
        agent: Any, # IPortfolioHandler & IHeirProvider & IFinancialAgent
        tick: int
    ) -> LegacySettlementAccount:
        """
        TD-160: Initiates the settlement process by creating an escrow account.
        Atomically transfers all assets (Cash + Portfolio) from the agent to the escrow.
        """
        agent_id = agent.id

        # 1. Atomic Transfer: Portfolio
        if isinstance(agent, IPortfolioHandler):
            portfolio_dto = agent.get_portfolio()
            agent.clear_portfolio()
        else:
            # Fallback for non-compliant agents (should not happen with new Households)
            portfolio_dto = PortfolioDTO(assets=[])
            self.logger.warning(f"Agent {agent_id} does not implement IPortfolioHandler. Portfolio not captured.")

        # 2. Atomic Transfer: Cash
        # IFinancialAgent protocol enforcement (was agent.assets)
        cash_balance = 0
        if isinstance(agent, IFinancialEntity):
            cash_balance = agent.balance_pennies
        elif isinstance(agent, IFinancialAgent):
            cash_balance = agent.get_balance(DEFAULT_CURRENCY)

        if cash_balance > 0:
            if isinstance(agent, IFinancialEntity):
                agent.withdraw(cash_balance, currency=DEFAULT_CURRENCY)
            elif isinstance(agent, IFinancialAgent):
                agent._withdraw(cash_balance)

        # 3. Determine Heir / Escheatment
        heir_id = None
        is_escheatment = True

        if isinstance(agent, IHeirProvider):
            heir_id = agent.get_heir()
            if heir_id is not None:
                is_escheatment = False

        account = LegacySettlementAccount(
            deceased_agent_id=agent_id,
            escrow_cash=cash_balance,
            escrow_portfolio=portfolio_dto,
            escrow_real_estate=[], # Placeholder
            status="OPEN",
            created_at=tick,
            heir_id=heir_id,
            is_escheatment=is_escheatment
        )
        self.settlement_accounts[agent_id] = account

        self.logger.info(
            f"SETTLEMENT_CREATED | Escrow account created for Agent {agent_id}. Cash: {cash_balance}. Portfolio items: {len(portfolio_dto.assets)}. Heir: {heir_id if heir_id else 'NONE (Escheatment)'}",
            extra={"tick": tick, "agent_id": agent_id, "tags": ["settlement", "inheritance", "atomic"]}
        )
        return account

    def execute_settlement(
        self,
        account_id: int,
        distribution_plan: List[Tuple[Any, int, str, str]], # (Recipient, Amount, Memo, TxType)
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

        # --- 1. Portfolio Distribution (Priority) ---
        portfolio_transferred = False
        if account.escrow_portfolio.assets:
            # Attempt to find the correct recipient in the plan
            # If escheatment -> Government
            # If inheritance -> Heir (heir_id)

            recipient_candidate = None

            for recipient, _, _, _ in distribution_plan:
                # Check for Government (Escheatment)
                if account.is_escheatment:
                    # Heuristic: Check for Government protocol
                    if isinstance(recipient, IGovernment):
                        recipient_candidate = recipient
                        break

                # Check for Heir
                else:
                    if recipient.id == account.heir_id:
                        recipient_candidate = recipient
                        break

            if recipient_candidate and isinstance(recipient_candidate, IPortfolioHandler):
                recipient_candidate.receive_portfolio(account.escrow_portfolio)
                # Clear from escrow to prevent leak/duplication (Reassign to empty DTO to preserve passed reference)
                account.escrow_portfolio = PortfolioDTO(assets=[])
                portfolio_transferred = True
                self.logger.info(
                    f"PORTFOLIO_TRANSFER | Transferred portfolio to {recipient_candidate.id}",
                    extra={"tick": tick, "agent_id": account.deceased_agent_id}
                )
            else:
                self.logger.error(
                    f"PORTFOLIO_TRANSFER_FAIL | Could not find valid IPortfolioHandler recipient for {'Escheatment' if account.is_escheatment else f'Heir {account.heir_id}'}",
                    extra={"tick": tick, "agent_id": account.deceased_agent_id}
                )

        # --- 2. Cash Distribution ---
        total_distributed = 0

        for recipient, amount, memo, tx_type in distribution_plan:
            if not isinstance(amount, int):
                 raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)} in distribution plan.")

            if amount <= 0:
                continue

            # Strict Integer Check
            if total_distributed + amount > account.escrow_cash:
                 self.logger.critical(
                     f"SETTLEMENT_OVERDRAFT | Attempted to distribute more than escrow! "
                     f"Escrow: {account.escrow_cash}, Distributed: {total_distributed}, Requested: {amount}",
                     extra={"tick": tick, "agent_id": account_id}
                 )
                 continue

            try:
                # Direct Deposit (Source is Void/Escrow)
                if isinstance(recipient, IFinancialEntity):
                    recipient.deposit(amount)
                elif isinstance(recipient, IFinancialAgent):
                    recipient._deposit(amount)
                else:
                     raise TypeError(f"Recipient {recipient.id} is not a valid financial agent.")

                total_distributed += amount

                # Create Receipt
                tx = self._create_transaction_record(
                    buyer_id=recipient.id, # Recipient
                    seller_id=account.deceased_agent_id, # Deceased
                    amount=amount,
                    memo=memo,
                    tick=tick
                )
                tx.transaction_type = tx_type
                if tx.metadata is None:
                    tx.metadata = {}
                tx.metadata["executed"] = True
                transactions.append(tx)

            except Exception as e:
                self.logger.error(f"SETTLEMENT_DISTRIBUTION_FAIL | Failed to pay {recipient.id}. {e}")

        # Update Account
        account.escrow_cash -= total_distributed
        # No float tolerance needed for int

        return transactions

    def get_assets_by_currency(self) -> Dict[str, int]:
        """
        Implements ICurrencyHolder for M2 verification.
        Returns total cash held in escrow accounts.
        """
        total = 0
        for acc in self.settlement_accounts.values():
            # Count all cash in the system regardless of status, as it is withdrawn from circulation
            total += acc.escrow_cash
        return {DEFAULT_CURRENCY: total}

    def verify_and_close(self, account_id: int, tick: int) -> bool:
        """
        TD-160: Verifies zero balance and closes the account.
        """
        if account_id not in self.settlement_accounts:
            return False

        account = self.settlement_accounts[account_id]

        has_error = False

        # 1. Cash Check
        if account.escrow_cash != 0:
            self.logger.warning(
                f"SETTLEMENT_LEAK | Account {account_id} closed with remaining cash: {account.escrow_cash}. Burning it.",
                extra={"tick": tick, "agent_id": account_id}
            )
            account.escrow_cash = 0
            has_error = True

        # 2. Portfolio Check (TD-160)
        if account.escrow_portfolio and account.escrow_portfolio.assets:
             self.logger.warning(
                f"SETTLEMENT_LEAK | Account {account_id} closed with remaining PORTFOLIO ASSETS: {len(account.escrow_portfolio.assets)} items.",
                extra={"tick": tick, "agent_id": account_id}
             )
             # Logic to burn/destroy portfolio assets? Just log for now.
             has_error = True

        if has_error:
            account.status = "CLOSED_WITH_LEAK"
            return False

        account.status = "CLOSED"
        self.logger.info(
            f"SETTLEMENT_CLOSED | Account {account_id} closed successfully.",
            extra={"tick": tick, "agent_id": account_id}
        )
        return True

    def record_liquidation(
        self,
        agent: IFinancialAgent,
        inventory_value: int,
        capital_value: int,
        recovered_cash: int,
        reason: str,
        tick: int,
        government_agent: Optional[IFinancialAgent] = None
    ) -> None:
        """
        Records the value destroyed during a firm's bankruptcy and liquidation.
        This ensures the value is accounted for in the simulation's total wealth.
        If government_agent is provided, transfers residual assets to it (Escheatment).
        MIGRATION: All inputs are int pennies.
        """
        # Loss = Book Value (Inventory + Capital) - Recovered Cash
        loss_amount = inventory_value + capital_value - recovered_cash
        if loss_amount < 0:
            loss_amount = 0

        self.total_liquidation_losses += loss_amount

        agent_id = agent.id
        self.logger.info(
            f"LIQUIDATION: Agent {agent_id} liquidated. "
            f"Inventory: {inventory_value}, Capital: {capital_value}, Recovered: {recovered_cash}. "
            f"Net Destruction: {loss_amount}. Total Destroyed: {self.total_liquidation_losses}. "
            f"Reason: {reason}",
            extra={"tick": tick, "tags": ["liquidation", "bankruptcy", "ledger"]}
        )

        # WO-178: Escheatment Logic
        if government_agent:
            # IFinancialAgent usage
            current_assets_val = agent.get_balance(DEFAULT_CURRENCY)

            if current_assets_val > 0:
                self.transfer(
                    debit_agent=agent,
                    credit_agent=government_agent,
                    amount=current_assets_val,
                    memo="liquidation_escheatment",
                    tick=tick,
                    currency=DEFAULT_CURRENCY
                )

    def _execute_withdrawal(self, agent: IFinancialAgent, amount: int, memo: str, tick: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> bool:
        """
        Executes withdrawal with checks and seamless payment (Bank) support.
        Returns True on success, False on failure.
        """
        # 1. Checks
        if agent is None:
            self.logger.error(f"SETTLEMENT_FAIL | Debit agent is None. Memo: {memo}")
            return False

        if not isinstance(amount, int):
             raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}. Memo: {memo}")

        is_central_bank = isinstance(agent, ICentralBank) or (agent.id == ID_CENTRAL_BANK)

        if is_central_bank:
             try:
                 # Central Bank might still use withdraw if it tracks money supply?
                 # Usually CB has infinite money, so withdraw should just work or be a no-op on validation but decrement M0.
                 if isinstance(agent, IFinancialAgent):
                    agent._withdraw(amount, currency=currency)
                 return True
             except Exception as e:
                 self.logger.error(f"SETTLEMENT_FAIL | Central Bank withdrawal failed. {e}")
                 return False

        # 2. Standard Agent Checks (IFinancialEntity / IFinancialAgent Interface)
        current_cash = 0
        if isinstance(agent, IFinancialEntity) and currency == DEFAULT_CURRENCY:
            current_cash = agent.balance_pennies
        elif isinstance(agent, IFinancialAgent):
            current_cash = agent.get_balance(currency)
        elif isinstance(agent, ICurrencyHolder):
             # Fallback if agent is ICurrencyHolder but not IFinancialAgent (unlikely now)
             current_cash = agent.get_assets_by_currency().get(currency, 0)

        if current_cash < amount:
            # Seamless Check (Only for DEFAULT_CURRENCY for now, assume Bank uses DEFAULT_CURRENCY)
            if self.bank and currency == DEFAULT_CURRENCY:
                needed_from_bank = amount - current_cash
                # Bank balance check using str(agent.id)
                agent_id_str = str(agent.id)
                bank_balance = self.bank.get_customer_balance(agent_id_str)

                if (current_cash + bank_balance) < amount:
                    self.logger.error(
                        f"SETTLEMENT_FAIL | Insufficient total funds (Cash+Deposits) for {agent.id}. "
                        f"Cash: {current_cash}, Bank: {bank_balance}, Total: {(current_cash + bank_balance)}. "
                        f"Required: {amount}. Memo: {memo}",
                        extra={"tags": ["settlement", "insufficient_funds"]}
                    )
                    return False
            else:
                self.logger.error(
                    f"SETTLEMENT_FAIL | Insufficient cash for {agent.id} AND Bank service is missing/incompatible. "
                    f"Cash: {current_cash}, Required: {amount}. Memo: {memo}",
                    extra={"tags": ["settlement", "insufficient_funds"]}
                )
                return False

        # 3. Execution
        try:
            if current_cash >= amount:
                # Use standard withdraw
                if isinstance(agent, IFinancialEntity):
                    agent.withdraw(amount, currency=currency)
                elif isinstance(agent, IFinancialAgent):
                    agent._withdraw(amount, currency=currency)
                self.logger.debug(f"DEBUG_WITHDRAW | Agent {agent.id} withdrew {amount}. Memo: {memo}")
            else:
                # Seamless (Only for DEFAULT_CURRENCY)
                if currency != DEFAULT_CURRENCY:
                     self.logger.error(f"SETTLEMENT_FAIL | Seamless payment not supported for {currency}")
                     return False

                needed_from_bank = amount - current_cash
                if current_cash > 0:
                    if isinstance(agent, IFinancialEntity):
                        agent.withdraw(current_cash, currency=currency)
                    elif isinstance(agent, IFinancialAgent):
                        agent._withdraw(current_cash, currency=currency)

                success = self.bank.withdraw_for_customer(int(agent.id), needed_from_bank)
                if not success:
                    # Rollback cash
                    if current_cash > 0:
                         if isinstance(agent, IFinancialEntity):
                            agent.deposit(current_cash, currency=currency)
                         elif isinstance(agent, IFinancialAgent):
                            agent._deposit(current_cash, currency=currency)
                    raise InsufficientFundsError(f"Bank withdrawal failed for {agent.id} despite check.")

                self.logger.info(
                    f"SEAMLESS_PAYMENT | Agent {agent.id} paid {amount} using {current_cash} cash and {needed_from_bank} from bank.",
                    extra={"tick": tick, "agent_id": agent.id, "tags": ["settlement", "bank"]}
                )
            return True
        except InsufficientFundsError as e:
             self.logger.critical(f"SETTLEMENT_CRITICAL | InsufficientFundsError. {e}")
             return False
        except Exception as e:
             self.logger.exception(f"SETTLEMENT_UNHANDLED_FAIL | {e}")
             return False

    def execute_multiparty_settlement(
        self,
        transfers: List[Tuple[IFinancialAgent, IFinancialAgent, int]],
        tick: int
    ) -> bool:
        """
        Executes a batch of transfers atomically.
        Format: (DebitAgent, CreditAgent, Amount)
        If any transfer fails, all are rolled back.
        """
        if not transfers:
            return True

        completed_transfers = [] # List of (Debit, Credit, Amount)

        for i, (debit, credit, amount) in enumerate(transfers):
            memo = f"multiparty_seq_{i}"

            # Execute individual transfer safely
            tx = self.transfer(debit, credit, amount, memo, tick=tick)
            if tx:
                completed_transfers.append((debit, credit, amount))
            else:
                d_id = debit.id
                c_id = credit.id
                self.logger.warning(
                    f"MULTIPARTY_FAIL | Transfer {i} failed ({d_id} -> {c_id}). Rolling back {len(completed_transfers)} previous transfers."
                )

                # ROLLBACK
                for r_debit, r_credit, r_amount in reversed(completed_transfers):
                    # Reverse: r_credit pays back r_debit
                    rb_tx = self.transfer(r_credit, r_debit, r_amount, f"rollback_multiparty_{i}", tick=tick)
                    if not rb_tx:
                         rc_id = r_credit.id
                         rd_id = r_debit.id
                         self.logger.critical(
                             f"MULTIPARTY_FATAL | Rollback failed for {r_amount} from {rc_id} to {rd_id}."
                         )
                return False

        return True

    def settle_atomic(
        self,
        debit_agent: IFinancialAgent,
        credits_list: List[Tuple[IFinancialAgent, int, str]],
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
             if not isinstance(amount, int):
                 raise TypeError(f"Settlement integrity violation: Amount must be int in atomic batch. Memo: {memo}")
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
                if isinstance(credit_agent, IFinancialEntity):
                    credit_agent.deposit(amount)
                elif isinstance(credit_agent, IFinancialAgent):
                    credit_agent._deposit(amount)
                completed_credits.append((credit_agent, amount))
            except Exception as e:
                self.logger.error(
                    f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back atomic batch. Error: {e}"
                )
                # ROLLBACK
                # 1. Reverse completed credits
                for ca, amt in completed_credits:
                    try:
                        if isinstance(ca, IFinancialEntity):
                            ca.withdraw(amt)
                        elif isinstance(ca, IFinancialAgent):
                            ca._withdraw(amt)
                    except Exception as rb_err:
                        self.logger.critical(f"SETTLEMENT_FATAL | Credit Rollback failed for {ca.id}. {rb_err}")

                # 2. Refund debit agent
                try:
                    if isinstance(debit_agent, IFinancialEntity):
                        debit_agent.deposit(total_debit)
                    elif isinstance(debit_agent, IFinancialAgent):
                        debit_agent._deposit(total_debit)
                except Exception as rb_err:
                    self.logger.critical(f"SETTLEMENT_FATAL | Debit Refund failed for {debit_agent.id}. {rb_err}")

                return False

        return True

    @enforce_purity()
    def transfer(
        self,
        debit_agent: IFinancialAgent,
        credit_agent: IFinancialAgent,
        amount: int,
        memo: str,
        debit_context: Optional[Dict[str, Any]] = None,
        credit_context: Optional[Dict[str, Any]] = None,
        tick: int = 0,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Executes an atomic transfer from debit_agent to credit_agent.
        Returns a Transaction object (truthy) on success, None (falsy) on failure.
        """
        if not isinstance(amount, int):
             raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}. Memo: {memo}")

        if amount <= 0:
            self.logger.warning(f"Transfer of non-positive amount ({amount}) attempted. Memo: {memo}")
            # Consider this a success logic-wise (no-op) but log it.
            return self._create_transaction_record(
                debit_agent.id,
                credit_agent.id,
                amount, memo, tick
            )

        if debit_agent is None or credit_agent is None:
             self.logger.error(f"SETTLEMENT_FAIL | Debit or Credit agent is None. Memo: {memo}")
             return None

        # VALIDATION (Tech Debt Fix: Null IDs)
        debit_id = getattr(debit_agent, 'id', None)
        credit_id = getattr(credit_agent, 'id', None)

        if debit_id is None or credit_id is None:
             self.logger.critical(
                 f"SETTLEMENT_FATAL | Transfer attempted with NULL agent IDs! "
                 f"Debit ID: {debit_id}, Credit ID: {credit_id}. Memo: {memo}. "
                 f"Aborting to prevent DB Integrity Error.",
                 extra={"tick": tick, "tags": ["settlement", "integrity_error"]}
             )
             return None

        # EXECUTE
        success = self._execute_withdrawal(debit_agent, amount, memo, tick, currency=currency)
        if not success:
            return None

        try:
            if isinstance(credit_agent, IFinancialEntity):
                credit_agent.deposit(amount, currency=currency)
            elif isinstance(credit_agent, IFinancialAgent):
                credit_agent._deposit(amount, currency=currency)
        except Exception as e:
            # ROLLBACK: Credit failed, must reverse debit
            self.logger.error(
                f"SETTLEMENT_ROLLBACK | Deposit failed for {credit_agent.id}. Rolling back withdrawal of {amount} from {debit_agent.id}. Error: {e}"
            )
            try:
                if isinstance(debit_agent, IFinancialEntity):
                    debit_agent.deposit(amount, currency=currency)
                elif isinstance(debit_agent, IFinancialAgent):
                    debit_agent._deposit(amount, currency=currency)
                self.logger.info(f"SETTLEMENT_ROLLBACK_SUCCESS | Rolled back {amount} to {debit_agent.id}.")
            except Exception as rollback_error:
                self.logger.critical(
                    f"SETTLEMENT_FATAL | Rollback failed! Money {amount} lost from {debit_agent.id}. "
                    f"Original Error: {e}. Rollback Error: {rollback_error}",
                    extra={"tags": ["settlement", "fatal", "money_leak"]}
                )
            return None

        # Success
        self.logger.debug(
            f"SETTLEMENT_SUCCESS | Transferred {amount} from {debit_agent.id} to {credit_agent.id}. Memo: {memo}",
            extra={"tags": ["settlement"], "tick": tick}
        )
        return self._create_transaction_record(debit_agent.id, credit_agent.id, amount, memo, tick)

    def create_and_transfer(
        self,
        source_authority: IFinancialAgent,
        destination: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Creates new money (or grants) and transfers it to an agent.
        """
        if not isinstance(amount, int):
             raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}.")

        if amount <= 0:
            return None

        is_central_bank = isinstance(source_authority, ICentralBank) or (source_authority.id == ID_CENTRAL_BANK)

        if is_central_bank:
            # Minting logic: Just credit destination. Source (CB) is assumed to have infinite capacity.
            try:
                if isinstance(destination, IFinancialEntity):
                    destination.deposit(amount, currency=currency)
                elif isinstance(destination, IFinancialAgent):
                    destination._deposit(amount, currency=currency)

                self.logger.info(
                    f"MINT_AND_TRANSFER | Created {amount} {currency} from {source_authority.id} to {destination.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                tx = self._create_transaction_record(source_authority.id, destination.id, amount, reason, tick)
                tx.transaction_type = "money_creation"
                return tx
            except Exception as e:
                self.logger.error(f"MINT_FAIL | {e}")
                return None
        else:
            # If not CB (e.g. Government), treat as regular transfer to enforce budget
            return self.transfer(source_authority, destination, amount, reason, tick=tick, currency=currency)

    def transfer_and_destroy(
        self,
        source: IFinancialAgent,
        sink_authority: IFinancialAgent,
        amount: int,
        reason: str,
        tick: int,
        currency: CurrencyCode = DEFAULT_CURRENCY
    ) -> Optional[ITransaction]:
        """
        Transfers money from an agent to an authority to be destroyed.
        """
        if not isinstance(amount, int):
             raise TypeError(f"Settlement integrity violation: amount must be int, got {type(amount)}.")

        if amount <= 0:
            return None

        is_central_bank = isinstance(sink_authority, ICentralBank) or (sink_authority.id == ID_CENTRAL_BANK)

        if is_central_bank:
            # Burning logic: Just debit source. Sink (CB) absorbs it (removed from circulation).
            try:
                if isinstance(source, IFinancialEntity):
                    source.withdraw(amount, currency=currency)
                elif isinstance(source, IFinancialAgent):
                    source._withdraw(amount, currency=currency)

                self.logger.info(
                    f"TRANSFER_AND_DESTROY | Destroyed {amount} {currency} from {source.id} to {sink_authority.id}. Reason: {reason}",
                    extra={"tick": tick}
                )
                tx = self._create_transaction_record(source.id, sink_authority.id, amount, reason, tick)
                tx.transaction_type = "money_destruction"
                return tx
            except Exception as e:
                self.logger.error(f"BURN_FAIL | {e}")
                return None
        else:
            # If not CB, treat as regular transfer (e.g. tax to Gov)
            return self.transfer(source, sink_authority, amount, reason, tick=tick, currency=currency)

    def _create_transaction_record(self, buyer_id: int, seller_id: int, amount: int, memo: str, tick: int) -> Optional[Transaction]:
        if buyer_id is None or seller_id is None:
             self.logger.critical(
                 f"SETTLEMENT_INTEGRITY_FAIL | Attempted to create transaction with NULL ID. "
                 f"Buyer: {buyer_id}, Seller: {seller_id}, Memo: {memo}. Skipping record creation.",
                 extra={"tick": tick, "tags": ["integrity_error"]}
             )
             return None

        return Transaction(
            buyer_id=buyer_id,
            seller_id=seller_id,
            item_id="currency",
            quantity=amount, # Int amount as quantity
            price=1, # Nominal price 1 for currency transfer (Int)
            market_id="settlement",
            transaction_type="transfer",
            time=tick,
            metadata={"memo": memo}
        )

    def mint_and_distribute(self, target_agent_id: int, amount: int, tick: int = 0, reason: str = "god_mode_injection") -> bool:
        """
        FOUND-03: Phase 0 Intercept - Special transaction for God Mode injection.
        Uses Central Bank as the source to ensure authorized money creation.
        """
        if not self.agent_registry:
            self.logger.critical("MINT_FAIL | Agent registry not linked.")
            return False

        central_bank = self.agent_registry.get_agent(ID_CENTRAL_BANK)
        if not central_bank:
             # Try fallback to string ID if registry keys are strings
             central_bank = self.agent_registry.get_agent(str(ID_CENTRAL_BANK))

        if not central_bank:
            self.logger.critical("MINT_FAIL | Central Bank not found.")
            return False

        target_agent = self.agent_registry.get_agent(target_agent_id)
        if not target_agent:
            self.logger.critical(f"MINT_FAIL | Target agent {target_agent_id} not found.")
            return False

        if not isinstance(central_bank, IFinancialAgent) or not isinstance(target_agent, IFinancialAgent):
            self.logger.critical("MINT_FAIL | Agents must implement IFinancialAgent.")
            return False

        tx = self.create_and_transfer(
            source_authority=central_bank,
            destination=target_agent,
            amount=amount,
            reason=reason,
            tick=tick
        )
        return tx is not None

    def audit_total_m2(self, expected_total: Optional[int] = None) -> bool:
        """
        FOUND-03: Phase 0 Intercept - M2 Integrity Audit.
        Sums up all cash in the system and compares with expected total.
        If expected_total is None, it just logs the current total (Passive Mode).
        """
        if not self.agent_registry:
             self.logger.critical("AUDIT_FAIL | Agent registry not linked.")
             return False

        # Use the enhanced registry method
        if not hasattr(self.agent_registry, "get_all_financial_agents"):
             self.logger.critical("AUDIT_FAIL | Agent registry does not support get_all_financial_agents.")
             return False

        agents = self.agent_registry.get_all_financial_agents()
        total_cash = 0
        bank_reserves = 0
        total_deposits = 0

        for agent in agents:
            # Exclude Central Bank from M2 calculation to align with WorldState.calculate_total_money
            # M2 is money in circulation, not held by the issuer.
            # IFinancialAgent requires 'id'.
            agent_id = getattr(agent, 'id', None)
            if agent_id == ID_CENTRAL_BANK or str(agent_id) == str(ID_CENTRAL_BANK):
                continue

            current_balance = 0
            if isinstance(agent, IFinancialEntity):
                current_balance = agent.balance_pennies
            elif isinstance(agent, IFinancialAgent):
                current_balance = agent.get_balance(DEFAULT_CURRENCY)
            elif hasattr(agent, "get_assets_by_currency"):
                assets = agent.get_assets_by_currency()
                current_balance = assets.get(DEFAULT_CURRENCY, 0)

            total_cash += current_balance

            # Bank Logic: Reserves and Deposits
            # Identify if agent is a Bank to adjust for M2 (Fractional Reserve)
            if isinstance(agent, IBank):
                bank_reserves += current_balance
                total_deposits += agent.get_total_deposits()
            elif hasattr(agent, '__class__') and agent.__class__.__name__ == "Bank":
                # Fallback for legacy bank not implementing IBank properly
                bank_reserves += current_balance
                if hasattr(agent, 'get_total_deposits'):
                    total_deposits += agent.get_total_deposits()
                elif hasattr(agent, 'deposits') and isinstance(agent.deposits, dict):
                     # Legacy Bank support
                     total_deposits += sum(d.amount for d in agent.deposits.values() if hasattr(d, 'amount'))

        # Include escrow accounts (considered removed from circulation until settled, but part of system total)
        # Escrow is effectively "Cash in Limbo".
        escrow_cash = sum(acc.escrow_cash for acc in self.settlement_accounts.values())

        # M2 = (Total Cash - Bank Reserves) + Total Deposits + Escrow
        # Currency in Circulation = Total Cash - Bank Reserves
        total_m2 = (total_cash - bank_reserves) + total_deposits + escrow_cash

        if expected_total is not None:
            if total_m2 != expected_total:
                self.logger.critical(
                    f"AUDIT_INTEGRITY_FAILURE | M2 Mismatch! Expected: {expected_total}, Actual: {total_m2}, Diff: {total_m2 - expected_total}",
                    extra={"expected": expected_total, "actual": total_m2, "diff": total_m2 - expected_total}
                )
                return False
            else:
                self.logger.info(f"AUDIT_PASS | M2 Verified: {total_m2}")
                return True
        else:
             self.logger.info(f"AUDIT_PASS | M2 Current: {total_m2} (No expectation set)")
             return True
