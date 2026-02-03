import logging
from dataclasses import dataclass
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
    BorrowerProfileDTO
)
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio
import config

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

TICKS_PER_YEAR = config.TICKS_PER_YEAR
INITIAL_BASE_ANNUAL_RATE = config.INITIAL_BASE_ANNUAL_RATE

@dataclass
class Loan:
    borrower_id: int
    principal: float
    remaining_balance: float
    annual_interest_rate: float
    term_ticks: int
    start_tick: int
    origination_tick: int = 0
    created_deposit_id: Optional[str] = None # Link to the deposit created by this loan

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR

@dataclass
class Deposit:
    depositor_id: int
    amount: float
    annual_interest_rate: float

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR

class Bank(IBankService):
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    WO-109: Refactored for Sacred Sequence (Transactions).
    """

    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager, settlement_system: Optional["ISettlementSystem"] = None, credit_scoring_service: Optional[ICreditScoringService] = None):
        self._id = id
        self._assets = initial_assets
        self.config_manager = config_manager
        self.settlement_system = settlement_system
        self.credit_scoring_service = credit_scoring_service
        self.government: Optional["Government"] = None

        self.loans: Dict[str, Loan] = {}
        self.deposits: Dict[str, Deposit] = {}
        self.base_rate = self._get_config("bank.initial_base_annual_rate", INITIAL_BASE_ANNUAL_RATE)

        self.next_loan_id = 0
        self.next_deposit_id = 0

        # Compatibility
        self.value_orientation = "N/A"
        self.needs: Dict[str, float] = {}

        # Current tick tracker (updated via run_tick usually, but need it for grant_loan defaults if available)
        self.current_tick_tracker = 0

        logger.info(f"Bank {self.id} initialized. Assets: {self.assets:.2f}")

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = value

    @property
    def assets(self) -> float:
        return self._assets

    def _internal_add_assets(self, amount: float) -> None:
        """[INTERNAL ONLY] Increase assets. Do not call directly."""
        self._assets += amount

    def _internal_sub_assets(self, amount: float) -> None:
        """[INTERNAL ONLY] Decrease assets. Do not call directly."""
        self._assets -= amount

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

        # Step 1: Credit Assessment
        if self.credit_scoring_service and borrower_profile:
             assessment = self.credit_scoring_service.assess_creditworthiness(borrower_profile, amount)
             if not assessment['is_approved']:
                 logger.info(f"LOAN_DENIED | Borrower {borrower_id} denied. Reason: {assessment.get('reason')}")
                 return None

        # Step 2: Solvency Check (Reserve Requirement)
        gold_standard_mode = self._get_config("gold_standard_mode", False)
        if gold_standard_mode:
            if self.assets < amount:
                return None
        else:
            reserve_ratio = self._get_config("reserve_req_ratio", 0.1)
            # New deposit will be created, so total deposits increase by amount
            projected_deposits = sum(d.amount for d in self.deposits.values()) + amount
            required_reserves = projected_deposits * reserve_ratio

            if self.assets < required_reserves:
                logger.warning(f"LOAN_DENIED | Bank {self.id} insufficient reserves. Assets: {self.assets:.2f} < Req: {required_reserves:.2f}")
                return None

        # Step 3: Credit Creation (Book the Loan and Create Deposit)
        loan_id = f"loan_{self.next_loan_id}"
        self.next_loan_id += 1

        start_tick = self.current_tick_tracker
        term_ticks = getattr(config, "DEFAULT_LOAN_TERM_TICKS", 50) # Default
        if due_tick is not None:
             term_ticks = max(1, due_tick - start_tick)
        else:
             term_ticks = self._get_config("bank.default_loan_term_ticks", term_ticks)
             due_tick = start_tick + term_ticks

        # Create the new deposit (Money Creation)
        deposit_id = self.deposit_from_customer(bid_int, amount)

        new_loan = Loan(
            borrower_id=bid_int,
            principal=amount,
            remaining_balance=amount,
            annual_interest_rate=interest_rate,
            term_ticks=term_ticks,
            start_tick=start_tick,
            origination_tick=start_tick,
            created_deposit_id=deposit_id
        )
        self.loans[loan_id] = new_loan

        # WO-024: Transactional Credit Creation
        # No longer modifying government state directly.
        # Generating a symbolic transaction for M2 audit.
        credit_creation_tx = Transaction(
            buyer_id=self.id,
            seller_id=self.government.id if self.government else -1,
            item_id=f"credit_creation_{loan_id}",
            quantity=1,
            price=amount,
            market_id="monetary_policy",
            transaction_type="credit_creation",
            time=start_tick
        )

        dto = LoanInfoDTO(
            loan_id=loan_id,
            borrower_id=borrower_id,
            original_amount=amount,
            outstanding_balance=amount,
            interest_rate=interest_rate,
            origination_tick=start_tick,
            due_tick=due_tick
        )
        return dto, credit_creation_tx

    def repay_loan(self, loan_id: str, amount: float) -> bool:
        """
        Repays a portion or the full amount of a specific loan.
        Implements IBankService.repay_loan.
        """
        if loan_id not in self.loans:
            raise LoanNotFoundError(f"Loan {loan_id} not found.")

        if amount < 0:
            raise LoanRepaymentError("Repayment amount must be positive.")

        loan = self.loans[loan_id]

        # Check if amount exceeds balance?
        # The spec says "Repays a portion or the full amount".
        # If amount > balance, we cap it? Or raise error?
        # Let's cap it to be safe, or allow overpayment?
        # Typically we cap.
        actual_amount = min(amount, loan.remaining_balance)
        loan.remaining_balance -= actual_amount

        return True

    def get_balance(self, account_id: str) -> float:
        """
        Retrieves the current balance for a given account.
        Implements IBankService.get_balance.
        """
        try:
            aid_int = int(account_id)
            return self.get_deposit_balance(aid_int)
        except ValueError:
            return 0.0

    def get_debt_status(self, borrower_id: str) -> DebtStatusDTO:
        """
        Retrieves the comprehensive debt status for a given borrower.
        Implements IBankService.get_debt_status.
        """
        try:
            bid_int = int(borrower_id)
        except ValueError:
            bid_int = -1

        loans_dto_list: List[LoanInfoDTO] = []
        total_debt = 0.0

        ticks_per_year = TICKS_PER_YEAR

        for lid, loan in self.loans.items():
            if loan.borrower_id == bid_int and loan.remaining_balance > 0:
                total_debt += loan.remaining_balance
                loans_dto_list.append(LoanInfoDTO(
                    loan_id=lid,
                    borrower_id=borrower_id,
                    original_amount=loan.principal,
                    outstanding_balance=loan.remaining_balance,
                    interest_rate=loan.annual_interest_rate,
                    origination_tick=loan.origination_tick,
                    due_tick=loan.start_tick + loan.term_ticks
                ))

        return DebtStatusDTO(
            borrower_id=borrower_id,
            total_outstanding_debt=total_debt,
            loans=loans_dto_list,
            is_insolvent=False, # Basic check, more logic could be added
            next_payment_due=None, # Needs logic if we track payment schedule
            next_payment_due_tick=None
        )

    # --- Legacy / Internal Methods ---

    def deposit_from_customer(self, depositor_id: int, amount: float) -> Optional[str]:
        margin = self._get_config("bank.deposit_margin", getattr(config, "BANK_DEPOSIT_MARGIN", 0.02))
        spread = self._get_config("bank.credit_spread_base", getattr(config, "BANK_CREDIT_SPREAD_BASE", 0.02))
        deposit_rate = max(0.0, self.base_rate + spread - margin)

        deposit_id = f"dep_{self.next_deposit_id}"
        self.next_deposit_id += 1

        new_deposit = Deposit(
            depositor_id=depositor_id,
            amount=amount,
            annual_interest_rate=deposit_rate
        )
        self.deposits[deposit_id] = new_deposit
        return deposit_id

    def withdraw_for_customer(self, depositor_id: int, amount: float) -> bool:
        target_deposit = None
        target_dep_id = None
        for dep_id, deposit in self.deposits.items():
            if deposit.depositor_id == depositor_id:
                target_deposit = deposit
                target_dep_id = dep_id
                break

        if target_deposit is None or target_deposit.amount < amount:
            return False

        target_deposit.amount -= amount
        if target_deposit.amount <= 0 and target_dep_id:
            del self.deposits[target_dep_id]
        return True

    def deposit(self, amount: float) -> None:
        if amount > 0:
            self._internal_add_assets(amount)

    def withdraw(self, amount: float) -> None:
        if amount > 0:
            if self.assets < amount:
                 raise InsufficientFundsError(f"Insufficient funds")
            self._internal_sub_assets(amount)

    def get_debt_summary(self, agent_id: int) -> Dict[str, float]:
        """Legacy method used by TickScheduler etc. until refactored."""
        # Forward to new method if possible, or keep separate?
        # Keeping separate implementation for safety, but logic is same.
        total_principal = 0.0
        daily_interest_burden = 0.0
        ticks_per_year = TICKS_PER_YEAR
        for loan in self.loans.values():
            if loan.borrower_id == agent_id:
                total_principal += loan.remaining_balance
                daily_interest_burden += (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year
        return {"total_principal": total_principal, "daily_interest_burden": daily_interest_burden}

    def get_deposit_balance(self, agent_id: int) -> float:
        total_deposit = 0.0
        for deposit in self.deposits.values():
            if deposit.depositor_id == agent_id:
                total_deposit += deposit.amount
        return total_deposit

    def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0) -> List[Transaction]:
        self.current_tick_tracker = current_tick
        generated_transactions: List[Transaction] = []
        ticks_per_year = TICKS_PER_YEAR
        gov_agent = None
        for a in agents_dict.values():
             if a.__class__.__name__ == 'Government':
                 gov_agent = a
                 break

        total_loan_interest = 0.0
        # Create a list of loans to iterate over to allow modification (process_default deletes loan)
        for loan_id, loan in list(self.loans.items()):
            agent = agents_dict.get(loan.borrower_id)
            if not agent or not getattr(agent, 'is_active', True):
                continue

            interest_payment = (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year
            payment = interest_payment

            if agent.assets >= payment:
                tx = Transaction(
                    buyer_id=agent.id,
                    seller_id=self.id,
                    item_id=loan_id,
                    quantity=1.0,
                    price=payment,
                    market_id="financial",
                    transaction_type="loan_interest",
                    time=current_tick
                )
                generated_transactions.append(tx)
                total_loan_interest += payment
            else:
                # Capture credit destruction tx
                default_tx = self.process_default(agent, loan, current_tick, government=gov_agent)
                if default_tx:
                    generated_transactions.append(default_tx)

                partial = agent.assets
                if partial > 0:
                    tx = Transaction(
                        buyer_id=agent.id,
                        seller_id=self.id,
                        item_id=loan_id,
                        quantity=1.0,
                        price=partial,
                        market_id="financial",
                        transaction_type="loan_default_recovery",
                        time=current_tick
                    )
                    generated_transactions.append(tx)
                    total_loan_interest += partial

        total_deposit_interest = 0.0
        for dep_id, deposit in self.deposits.items():
            agent = agents_dict.get(deposit.depositor_id)
            if not agent:
                continue
            interest_payout = (deposit.amount * deposit.annual_interest_rate) / ticks_per_year
            if self.assets >= interest_payout:
                 tx = Transaction(
                    buyer_id=self.id,
                    seller_id=agent.id,
                    item_id=dep_id,
                    quantity=1.0,
                    price=interest_payout,
                    market_id="financial",
                    transaction_type="deposit_interest",
                    time=current_tick
                 )
                 generated_transactions.append(tx)
                 total_deposit_interest += interest_payout
                 if hasattr(agent, "capital_income_this_tick"):
                    agent.capital_income_this_tick += interest_payout

        net_profit = total_loan_interest - total_deposit_interest
        if net_profit > 0 and gov_agent:
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

    def generate_solvency_transactions(self, government: "Government") -> List[Transaction]:
        """
        WO-109: Generate 'lender_of_last_resort' transactions if insolvent.
        This replaces the old direct-modification `check_solvency`.
        """
        if self.assets < 0:
            solvency_buffer = self._get_config("bank.solvency_buffer", getattr(config, "BANK_SOLVENCY_BUFFER", 1000.0))
            borrow_amount = abs(self.assets) + solvency_buffer

            tx = Transaction(
                buyer_id=government.id, # Source of minting (symbolic)
                seller_id=self.id,      # Bank receives
                item_id="lender_of_last_resort",
                quantity=1,
                price=borrow_amount,
                market_id="system_stabilization",
                transaction_type="lender_of_last_resort",
                time=0 # Will be overridden or used by processor
            )
            logger.warning(f"INSOLVENT: Generating Lender of Last Resort tx for {borrow_amount:.2f}")
            return [tx]

        return []

    def process_default(self, agent: Any, loan: Loan, current_tick: int, government: Optional[Any] = None) -> Optional[Transaction]:
        if hasattr(agent, "shares_owned") and agent.shares_owned:
            agent.shares_owned.clear()

        destruction_tx = None
        amount = loan.remaining_balance

        if amount > 0:
             # WO-024: Transactional Credit Destruction
             destruction_tx = Transaction(
                buyer_id=government.id if government else -1,
                seller_id=self.id,
                item_id=f"credit_destruction_default_{loan.borrower_id}",
                quantity=1,
                price=amount,
                market_id="monetary_policy",
                transaction_type="credit_destruction",
                time=current_tick
            )

        loan.remaining_balance = 0.0

        jail_ticks = self._get_config("bank.credit_recovery_ticks", getattr(config, "CREDIT_RECOVERY_TICKS", 100))
        if hasattr(agent, "credit_frozen_until_tick"):
            agent.credit_frozen_until_tick = current_tick + jail_ticks

        xp_penalty = self._get_config("bank.bankruptcy_xp_penalty", getattr(config, "BANKRUPTCY_XP_PENALTY", 0.2))
        if hasattr(agent, "education_xp"):
             agent.education_xp *= (1.0 - xp_penalty)

        return destruction_tx

    def terminate_loan(self, loan_id: str) -> Optional[Transaction]:
        """
        Forcefully terminates a loan (e.g. foreclosure).
        Returns a credit_destruction transaction if balance was > 0.
        """
        if loan_id not in self.loans:
            return None

        loan = self.loans[loan_id]
        amount = loan.remaining_balance

        # Similar to void_loan but assumes deposit might not be reversible (spent), so just destroys credit asset.
        # This is essentially a write-off / destruction.

        del self.loans[loan_id]

        if amount > 0:
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

    # Legacy Stubs
    def get_outstanding_loans_for_agent(self, agent_id: int) -> List[Dict]:
        return [
            {
                "borrower_id": l.borrower_id,
                "amount": l.remaining_balance,
                "interest_rate": l.annual_interest_rate,
                "duration": l.term_ticks
            }
            for l in self.loans.values() if l.borrower_id == agent_id
        ]

    def process_repayment(self, loan_id: str, amount: float):
        """Legacy wrapper for repay_loan."""
        try:
            self.repay_loan(loan_id, amount)
        except (LoanNotFoundError, LoanRepaymentError):
            pass

    def void_loan(self, loan_id: str) -> Optional[Transaction]:
        """
        Cancels a loan and reverses the associated deposit creation.
        Returns a credit_destruction transaction.
        """
        if loan_id not in self.loans:
            return None

        loan = self.loans[loan_id]
        amount = loan.principal

        # 1. Reverse Deposit (Liability)
        target_dep_id = loan.created_deposit_id
        deposit_reversed = False

        if target_dep_id and target_dep_id in self.deposits:
            del self.deposits[target_dep_id]
            deposit_reversed = True
        else:
            borrower_id = loan.borrower_id
            for dep_id, deposit in self.deposits.items():
                if deposit.depositor_id == borrower_id and abs(deposit.amount - amount) < 1e-9:
                    del self.deposits[dep_id]
                    deposit_reversed = True
                    break

            if not deposit_reversed:
                logger.critical(f"VOID_LOAN_FAIL | Could not find deposit for loan {loan_id}. Cannot safely rollback.")
                raise LoanRollbackError(f"Critical: Could not find deposit to reverse for loan {loan_id}")

        # 2. Destroy Loan (Asset)
        if deposit_reversed:
            del self.loans[loan_id]

        # 3. Transactional Credit Destruction
        tx = Transaction(
            buyer_id=self.government.id if self.government else -1,
            seller_id=self.id,
            item_id=f"credit_destruction_{loan_id}",
            quantity=1,
            price=amount,
            market_id="monetary_policy",
            transaction_type="credit_destruction",
            time=self.current_tick_tracker
        )

        logger.info(f"LOAN_VOIDED | Loan {loan_id} cancelled and deposit reversed.")
        return tx
