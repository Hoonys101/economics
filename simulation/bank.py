import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import math
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import (
    InsufficientFundsError,
    IBankService,
    LoanInfoDTO,
    DebtStatusDTO,
    LoanNotFoundError,
    LoanRepaymentError,
    LoanRollbackError,
    ICreditScoringService,
    BorrowerProfileDTO,
    ILoanManager,
    IDepositManager,
    IShareholderRegistry,
    IPortfolioHandler,
    ICreditFrozen
)
from modules.simulation.api import IEducated
from modules.finance.managers.loan_manager import LoanManager
from modules.finance.managers.deposit_manager import DepositManager
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder
from modules.finance.wallet.wallet import Wallet
from modules.finance.wallet.api import IWallet
from simulation.models import Transaction
from simulation.portfolio import Portfolio
import config

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

TICKS_PER_YEAR = config.TICKS_PER_YEAR
INITIAL_BASE_ANNUAL_RATE = config.INITIAL_BASE_ANNUAL_RATE

from modules.finance.api import IFinancialEntity

class Bank(IBankService, ICurrencyHolder, IFinancialEntity):
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    WO-109: Refactored for Sacred Sequence (Transactions).
    TD-274: Decomposed into LoanManager and DepositManager Facade.
    """

    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager,
                 shareholder_registry: Optional[IShareholderRegistry] = None,
                 settlement_system: Optional["ISettlementSystem"] = None,
                 credit_scoring_service: Optional[ICreditScoringService] = None):
        self._id = id

        initial_balance_dict = {}
        if isinstance(initial_assets, dict):
            initial_balance_dict = initial_assets.copy()
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = float(initial_assets)

        self._wallet = Wallet(self.id, initial_balance_dict)

        self.config_manager = config_manager
        self.settlement_system = settlement_system
        self.credit_scoring_service = credit_scoring_service
        self.shareholder_registry = shareholder_registry
        self.government: Optional["Government"] = None

        # TD-274: Initialize Managers
        self.loan_manager: ILoanManager = LoanManager()
        self.deposit_manager: IDepositManager = DepositManager()

        self.base_rate = self._get_config("bank.initial_base_annual_rate", INITIAL_BASE_ANNUAL_RATE)

        # Current tick tracker (updated via run_tick usually)
        self.current_tick_tracker = 0

        # Compatibility
        self.value_orientation = "N/A"
        self.needs: Dict[str, float] = {}

        logger.info(f"Bank {self.id} initialized. Assets: {self.wallet.get_all_balances()}")

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = value

    @property
    def wallet(self) -> IWallet:
        return self._wallet

    @property
    def assets(self) -> float:
        """
        Returns the bank's liquid reserves in DEFAULT_CURRENCY, conforming to IFinancialEntity.
        """
        return self._wallet.get_balance(DEFAULT_CURRENCY)

    def get_assets_by_currency(self) -> Dict[CurrencyCode, float]:
        """Implementation of ICurrencyHolder."""
        return self._wallet.get_all_balances()

    def _internal_add_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """[INTERNAL ONLY] Increase assets. Do not call directly."""
        self._wallet.add(amount, currency, memo="Internal Add")

    def _internal_sub_assets(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        """[INTERNAL ONLY] Decrease assets. Do not call directly."""
        # Wallet checks funds
        self._wallet.subtract(amount, currency, memo="Internal Sub")

    def get_interest_rate(self) -> float:
        return self.base_rate

    def _get_config(self, key: str, default: Any) -> Any:
        return self.config_manager.get(key, default)

    def set_government(self, government: "Government") -> None:
        self.government = government

    def update_base_rate(self, new_rate: float):
        if abs(self.base_rate - new_rate) < 1e-6:
            return
        self.base_rate = new_rate
        logger.info(f"MONETARY_POLICY | Base Rate updated: {self.base_rate:.2%}")

    # --- IBankService Implementation ---

    def grant_loan(self, borrower_id: str, amount: float, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[Tuple[LoanInfoDTO, Transaction]]:
        """
        Grants a loan to a borrower.
        Returns LoanInfoDTO and a 'credit_creation' Transaction.
        Implements IBankService.grant_loan.
        """
        try:
            bid_int = int(borrower_id)
        except ValueError:
            logger.error(f"Bank.grant_loan: Invalid borrower_id {borrower_id}, expected int-convertible string.")
            return None

        # Delegate to LoanManager
        result = self.loan_manager.assess_and_create_loan(
            borrower_id=bid_int,
            amount=amount,
            interest_rate=interest_rate,
            due_tick=due_tick,
            borrower_profile=borrower_profile,
            credit_scoring_service=self.credit_scoring_service,
            lender_wallet=self.wallet,
            deposit_manager=self.deposit_manager,
            current_tick=self.current_tick_tracker,
            is_gold_standard=self._get_config("gold_standard_mode", False),
            reserve_req_ratio=self._get_config("reserve_req_ratio", 0.1),
            default_term_ticks=getattr(config, "DEFAULT_LOAN_TERM_TICKS", 50)
        )

        if not result:
            return None

        loan_dto, deposit_id = result

        credit_creation_tx = Transaction(
            buyer_id=self.id,
            seller_id=self.government.id if self.government else -1,
            item_id=f"credit_creation_{loan_dto['loan_id']}",
            quantity=1,
            price=amount,
            market_id="monetary_policy",
            transaction_type="credit_creation",
            time=self.current_tick_tracker
        )

        return loan_dto, credit_creation_tx

    def stage_loan(self, borrower_id: str, amount: float, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanInfoDTO]:
        try:
            bid_int = int(borrower_id)
        except ValueError:
            return None

        # Step 1: Credit Assessment
        if self.credit_scoring_service and borrower_profile:
             assessment = self.credit_scoring_service.assess_creditworthiness(borrower_profile, amount)
             if not assessment['is_approved']:
                 return None

        # Step 2: Liquidity Check
        usd_assets = self._wallet.get_balance(DEFAULT_CURRENCY)
        if usd_assets < amount:
            return None

        # Step 3: Book Loan
        start_tick = self.current_tick_tracker
        term_ticks = getattr(config, "DEFAULT_LOAN_TERM_TICKS", 50)
        if due_tick is not None:
             term_ticks = max(1, due_tick - start_tick)
        else:
             term_ticks = self._get_config("bank.default_loan_term_ticks", term_ticks)
             due_tick = start_tick + term_ticks

        loan_id = self.loan_manager.create_loan(
            borrower_id=bid_int,
            amount=amount,
            interest_rate=interest_rate,
            start_tick=start_tick,
            term_ticks=term_ticks,
            created_deposit_id=None
        )

        logger.info(f"LOAN_STAGED | Loan {loan_id} staged for {borrower_id}. Amount: {amount:.2f}")

        return LoanInfoDTO(
            loan_id=loan_id,
            borrower_id=borrower_id,
            original_amount=amount,
            outstanding_balance=amount,
            interest_rate=interest_rate,
            origination_tick=start_tick,
            due_tick=due_tick
        )

    def repay_loan(self, loan_id: str, amount: float) -> bool:
        if amount < 0:
            raise LoanRepaymentError("Repayment amount must be positive.")

        # Delegate to LoanManager (Protocol guaranteed)
        return self.loan_manager.repay_loan(loan_id, amount)

    def get_balance(self, account_id: str) -> float:
        try:
            aid_int = int(account_id)
            return self.deposit_manager.get_balance(aid_int)
        except ValueError:
            return 0.0

    def get_debt_status(self, borrower_id: str) -> DebtStatusDTO:
        try:
            bid_int = int(borrower_id)
        except ValueError:
            bid_int = -1

        loans_dto = self.loan_manager.get_loans_for_agent(bid_int)
        total_debt = sum(l['remaining_principal'] for l in loans_dto if l['remaining_principal'] > 0)

        loan_info_list = []
        for l in loans_dto:
            if l['remaining_principal'] <= 0: continue
            loan_info_list.append(LoanInfoDTO(
                loan_id=l['loan_id'],
                borrower_id=str(l['borrower_id']),
                original_amount=l['principal'],
                outstanding_balance=l['remaining_principal'],
                interest_rate=l['interest_rate'],
                origination_tick=l['origination_tick'],
                due_tick=l['due_tick']
            ))

        return DebtStatusDTO(
            borrower_id=borrower_id,
            total_outstanding_debt=total_debt,
            loans=loan_info_list,
            is_insolvent=False,
            next_payment_due=None,
            next_payment_due_tick=None
        )

    # --- Legacy / Internal Methods ---

    def deposit_from_customer(self, depositor_id: int, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> Optional[str]:
        margin = self._get_config("bank.deposit_margin", getattr(config, "BANK_DEPOSIT_MARGIN", 0.02))
        spread = self._get_config("bank.credit_spread_base", getattr(config, "BANK_CREDIT_SPREAD_BASE", 0.02))
        deposit_rate = max(0.0, self.base_rate + spread - margin)

        return self.deposit_manager.create_deposit(depositor_id, amount, deposit_rate, currency)

    def withdraw_for_customer(self, depositor_id: int, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> bool:
        # Check liquidity first
        try:
            self._wallet.subtract(amount, currency, memo=f"Customer Withdrawal {depositor_id}")
        except Exception:
            logger.error(f"BANK_LIQUIDITY_CRISIS | Bank {self.id} cannot fulfill withdrawal of {amount} for {depositor_id}. Insufficient Reserves.")
            return False

        # Delegate update to manager (Protocol guaranteed)
        success = self.deposit_manager.withdraw(depositor_id, amount)

        if not success:
            # Rollback wallet
            self._wallet.add(amount, currency, memo="Withdrawal Rollback")
            return False

        return True

    def deposit(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self._wallet.add(amount, currency, memo="Deposit")

    def withdraw(self, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        self._wallet.subtract(amount, currency, memo="Withdraw")

    def get_debt_summary(self, agent_id: int) -> Dict[str, float]:
        loans = self.loan_manager.get_loans_for_agent(agent_id)
        total_principal = sum(l['remaining_principal'] for l in loans)
        daily_interest_burden = sum((l['remaining_principal'] * l['interest_rate']) / TICKS_PER_YEAR for l in loans)
        return {"total_principal": total_principal, "daily_interest_burden": daily_interest_burden}

    def get_deposit_balance(self, agent_id: int) -> float:
        return self.deposit_manager.get_balance(agent_id)

    def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0) -> List[Transaction]:
        self.current_tick_tracker = current_tick
        generated_transactions: List[Transaction] = []

        gov_agent = None
        for a in agents_dict.values():
             if a.__class__.__name__ == 'Government':
                 gov_agent = a
                 break

        # --- Loan Servicing ---

        def payment_callback(borrower_id: int, amount: float) -> bool:
            borrower = agents_dict.get(borrower_id)
            if not borrower: return False

            # Use SettlementSystem if available
            if self.settlement_system:
                tx = self.settlement_system.transfer(borrower, self, amount, "Loan Interest Payment", tick=current_tick)
                return tx is not None
            else:
                # Fallback or Strict?
                # Using native withdraw/deposit if system missing (Legacy)
                try:
                    assets = 0.0
                    if hasattr(borrower, 'wallet'): assets = borrower.wallet.get_balance(DEFAULT_CURRENCY)
                    elif hasattr(borrower, 'assets'):
                        assets = borrower.assets.get(DEFAULT_CURRENCY, 0.0) if isinstance(borrower.assets, dict) else float(borrower.assets)

                    if assets >= amount:
                        borrower.withdraw(amount)
                        self.deposit(amount)
                        return True
                    return False
                except Exception:
                    return False

        loan_events = self.loan_manager.service_loans(current_tick, payment_callback)
        total_loan_interest = 0.0

        for event in loan_events:
            if event['type'] == 'interest_payment':
                total_loan_interest += event['amount']
                tx = Transaction(
                    buyer_id=event['borrower_id'],
                    seller_id=self.id,
                    item_id=event['loan_id'],
                    quantity=1.0,
                    price=event['amount'],
                    market_id="financial",
                    transaction_type="loan_interest",
                    time=current_tick
                )
                generated_transactions.append(tx)
            elif event['type'] == 'default':
                # Handle consequences via private helper
                default_txs = self._handle_default(event, agents_dict, current_tick)
                generated_transactions.extend(default_txs)

                # Check for any recovery income
                for tx in default_txs:
                    if tx.transaction_type == "loan_default_recovery":
                        total_loan_interest += tx.price

        # --- Deposit Interest ---

        interest_payments = self.deposit_manager.calculate_interest(current_tick)
        total_deposit_interest = 0.0

        for depositor_id, amount in interest_payments:
            agent = agents_dict.get(depositor_id)
            if not agent: continue

            # Bank pays interest
            # Check liquidity
            if self._wallet.get_balance(DEFAULT_CURRENCY) >= amount:
                success = False
                if self.settlement_system:
                    tx_int = self.settlement_system.transfer(self, agent, amount, "Deposit Interest", tick=current_tick)
                    success = tx_int is not None
                else:
                    try:
                        self.withdraw(amount)
                        agent.deposit(amount)
                        success = True
                    except: pass

                if success:
                    tx = Transaction(
                        buyer_id=self.id,
                        seller_id=agent.id,
                        item_id="deposit_interest", # Need generic ID or specific?
                        quantity=1.0,
                        price=amount,
                        market_id="financial",
                        transaction_type="deposit_interest",
                        time=current_tick
                    )
                    generated_transactions.append(tx)
                    total_deposit_interest += amount
                    if hasattr(agent, "capital_income_this_tick"):
                        agent.capital_income_this_tick += amount

        # --- Profit Remittance ---
        net_profit = total_loan_interest - total_deposit_interest
        if net_profit > 0 and gov_agent:
             success = False
             if self.settlement_system:
                 tx_prof = self.settlement_system.transfer(self, gov_agent, net_profit, "Bank Profit", tick=current_tick)
                 success = tx_prof is not None
             else:
                 try:
                     self.withdraw(net_profit)
                     gov_agent.deposit(net_profit)
                     success = True
                 except: pass

             if success:
                 tx = Transaction(
                     buyer_id=self.id,
                     seller_id=gov_agent.id,
                     item_id="bank_profit",
                     quantity=1.0,
                     price=net_profit,
                     market_id="financial",
                     transaction_type="bank_profit_remittance",
                     time=current_tick
                 )
                 generated_transactions.append(tx)

        return generated_transactions

    def _handle_default(self, event: Dict[str, Any], agents_dict: Dict[int, Any], current_tick: int) -> List[Transaction]:
        transactions = []
        borrower_id = event['borrower_id']
        agent = agents_dict.get(borrower_id)

        # 1. Credit Destruction
        if event['amount_defaulted'] > 0:
            transactions.append(Transaction(
                buyer_id=self.government.id if self.government else -1,
                seller_id=self.id,
                item_id=f"credit_destruction_default_{borrower_id}",
                quantity=1,
                price=event['amount_defaulted'],
                market_id="monetary_policy",
                transaction_type="credit_destruction",
                time=current_tick
            ))

        if not agent:
            return transactions

        # 2. Penalties (Protocol Purity)

        # Share Seizure
        if isinstance(agent, IPortfolioHandler):
            portfolio = agent.get_portfolio()
            for asset in portfolio.assets:
                if asset.asset_type == 'stock':
                    try:
                        firm_id = int(asset.asset_id)
                        # Remove from registry
                        if self.shareholder_registry:
                            self.shareholder_registry.register_shares(firm_id, borrower_id, 0)
                    except ValueError:
                        pass
            agent.clear_portfolio()

        # Credit Freeze (Jail)
        if isinstance(agent, ICreditFrozen):
            jail_ticks = self._get_config("bank.credit_recovery_ticks", getattr(config, "CREDIT_RECOVERY_TICKS", 100))
            agent.credit_frozen_until_tick = current_tick + jail_ticks

        # XP Penalty
        if isinstance(agent, IEducated):
            xp_penalty = self._get_config("bank.bankruptcy_xp_penalty", getattr(config, "BANKRUPTCY_XP_PENALTY", 0.2))
            agent.education_xp *= (1.0 - xp_penalty)

        # 3. Asset Recovery (Seize Cash)
        assets_val = 0.0
        # Use IFinancialEntity if possible
        if isinstance(agent, IFinancialEntity):
             assets_val = agent.assets
        # Fallback for legacy (should not happen if all are IFinancialEntity)
        elif hasattr(agent, 'wallet'):
             assets_val = agent.wallet.get_balance(DEFAULT_CURRENCY)

        if assets_val > 0:
             memo = f"Default Recovery {event['loan_id']}"
             success = False
             if self.settlement_system:
                 tx_rec = self.settlement_system.transfer(agent, self, assets_val, memo, tick=current_tick)
                 success = tx_rec is not None
             else:
                 try:
                     agent.withdraw(assets_val)
                     self.deposit(assets_val)
                     success = True
                 except: pass

             if success:
                 transactions.append(Transaction(
                    buyer_id=agent.id,
                    seller_id=self.id,
                    item_id=event['loan_id'],
                    quantity=1.0,
                    price=assets_val,
                    market_id="financial",
                    transaction_type="loan_default_recovery",
                    time=current_tick
                ))

        return transactions

    def generate_solvency_transactions(self, government: "Government") -> List[Transaction]:
        usd_assets = self._wallet.get_balance(DEFAULT_CURRENCY)
        if usd_assets < 0:
            solvency_buffer = self._get_config("bank.solvency_buffer", getattr(config, "BANK_SOLVENCY_BUFFER", 1000.0))
            borrow_amount = abs(usd_assets) + solvency_buffer

            tx = Transaction(
                buyer_id=government.id,
                seller_id=self.id,
                item_id="lender_of_last_resort",
                quantity=1,
                price=borrow_amount,
                market_id="system_stabilization",
                transaction_type="lender_of_last_resort",
                time=0
            )
            logger.warning(f"INSOLVENT: Generating Lender of Last Resort tx for {borrow_amount:.2f}")
            return [tx]

        return []

    def terminate_loan(self, loan_id: str) -> Optional[Transaction]:
        amount = self.loan_manager.terminate_loan(loan_id)
        if amount is not None and amount > 0:
             return Transaction(
                buyer_id=self.government.id if self.government else -1,
                seller_id=self.id,
                item_id=f"credit_destruction_term_{loan_id}",
                quantity=1,
                price=amount,
                market_id="monetary_policy",
                transaction_type="credit_destruction",
                time=self.current_tick_tracker
            )
        return None

    # Keeping void_loan for legacy support or atomic rollbacks
    def void_loan(self, loan_id: str) -> Optional[Transaction]:
        # Need to query loan before deleting to know principal?
        # LoanManager.terminate_loan returns remaining balance.
        # But void_loan needs principal to reverse deposit?
        # I need to access loan details.

        loan_dto = self.loan_manager.get_loan_by_id(loan_id)
        if not loan_dto:
            return None

        principal = loan_dto['principal'] # Or 'original_amount' in LoanInfoDTO? LoanDTO uses principal.

        # 1. Reverse Deposit
        borrower_id = int(loan_dto['borrower_id'])
        deposit_reversed = self.deposit_manager.remove_deposit_match(borrower_id, principal)

        if not deposit_reversed:
             logger.critical(f"VOID_LOAN_FAIL | Could not find deposit for loan {loan_id}. Cannot safely rollback.")
             raise LoanRollbackError(f"Critical: Could not find deposit to reverse for loan {loan_id}")

        # 2. Destroy Loan
        self.loan_manager.terminate_loan(loan_id) # Ignore return value (remaining balance)

        # 3. Transactional Credit Destruction
        tx = Transaction(
            buyer_id=self.government.id if self.government else -1,
            seller_id=self.id,
            item_id=f"credit_destruction_{loan_id}",
            quantity=1,
            price=principal,
            market_id="monetary_policy",
            transaction_type="credit_destruction",
            time=self.current_tick_tracker
        )

        logger.info(f"LOAN_VOIDED | Loan {loan_id} cancelled and deposit reversed.")
        return tx

    def get_outstanding_loans_for_agent(self, agent_id: int) -> List[Dict]:
        loans = self.loan_manager.get_loans_for_agent(agent_id)
        return [
            {
                "borrower_id": int(l['borrower_id']),
                "amount": l['remaining_principal'],
                "interest_rate": l['interest_rate'],
                "duration": l['term_months']
            }
            for l in loans
        ]

    def process_repayment(self, loan_id: str, amount: float):
        try:
            self.repay_loan(loan_id, amount)
        except Exception:
            pass

    def get_total_deposits(self) -> float:
        return self.deposit_manager.get_total_deposits()
