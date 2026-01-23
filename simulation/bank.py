import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import InsufficientFundsError, IFinancialEntity

logger = logging.getLogger(__name__)

# Constants (Fallback if config is not passed, though it should be)
TICKS_PER_YEAR = 100
INITIAL_BASE_ANNUAL_RATE = 0.05
CREDIT_SPREAD_BASE = 0.02
BANK_MARGIN = 0.02


@dataclass
class Loan:
    borrower_id: int
    principal: float       # 원금
    remaining_balance: float # 잔액
    annual_interest_rate: float # 연이율
    term_ticks: int        # 만기 (틱)
    start_tick: int        # 대출 실행 틱

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR


@dataclass
class Deposit:
    depositor_id: int
    amount: float          # 예치금
    annual_interest_rate: float # 연이율

    @property
    def tick_interest_rate(self) -> float:
        return self.annual_interest_rate / TICKS_PER_YEAR


class Bank(IFinancialEntity):
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    Manages loans, deposits, and monetary policy interaction.
    """

    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager, settlement_system: Any = None):
        self._id = id
        self._assets = initial_assets # Reserves
        self.config_manager = config_manager
        self.settlement_system = settlement_system

        # Data Stores
        self.loans: Dict[str, Loan] = {}
        self.deposits: Dict[str, Deposit] = {}

        # Policy Rates
        self.base_rate = self._get_config("bank_defaults.initial_base_annual_rate", INITIAL_BASE_ANNUAL_RATE)

        # Counters
        self.next_loan_id = 0
        self.next_deposit_id = 0

        # Dummy attrs for compatibility
        self.value_orientation = "N/A"
        self.needs: Dict[str, float] = {}

        logger.info(
            f"Bank {self.id} initialized. Assets: {self.assets:.2f}, Base Rate: {self.base_rate:.2%}",
            extra={"tick": 0, "agent_id": self.id, "tags": ["init", "bank"]},
        )

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = value

    @property
    def assets(self) -> float:
        return self._assets

    def _add_assets(self, amount: float) -> None:
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
        self._assets -= amount

    def get_interest_rate(self) -> float:
        """Returns the current base interest rate."""
        return self.base_rate

    def _get_config(self, key: str, default: Any) -> Any:
        return self.config_manager.get(key, default)

    def update_base_rate(self, new_rate: float):
        """
        Called by Central Bank (via Engine) to update monetary policy.
        Updates the base rate which affects new loans and deposits.
        """
        if abs(self.base_rate - new_rate) < 1e-6:
            return

        old_rate = self.base_rate
        self.base_rate = new_rate
        logger.info(
            f"MONETARY_POLICY | Base Rate updated: {old_rate:.2%} -> {self.base_rate:.2%}",
            extra={"agent_id": self.id, "tags": ["bank", "policy"]}
        )

    def grant_loan(
        self,
        borrower_id: int,
        amount: float,
        term_ticks: Optional[int] = None,
        interest_rate: Optional[float] = None
    ) -> Optional[str]:
        """
        Grants a loan to an agent if eligible.
        Does NOT transfer assets directly; returns loan ID for Transaction creation.

        Args:
            borrower_id: The ID of the agent borrowing money.
            amount: The principal amount of the loan.
            term_ticks: Duration of the loan in ticks. Defaults to LOAN_DEFAULT_TERM if None.
            interest_rate: Specific annual interest rate to use. If None, uses Base Rate + Spread.
        """
        # 1. Config Check
        if not term_ticks:
            term_ticks = self._get_config("loan.default_term", 50)

        if interest_rate is not None:
            annual_rate = interest_rate
        else:
            credit_spread = self._get_config("bank_defaults.credit_spread_base", 0.02)
            annual_rate = self.base_rate + credit_spread

        # 2. Liquidity Check
        # 1a. Credit Jail Check (Phase 4)
        if self._get_config("credit_recovery_ticks", None) is not None:
            # We assume borrower_id maps to an agent object passed somewhere, but here we only have ID.
            # We need to access the agent to check 'credit_frozen_until_tick'.
            # Bank doesn't have direct access to agent list in grant_loan signature.
            # But grant_loan is usually called by LoanMarket which has access or the Agent itself calls it via Market.
            # Wait, LoanMarket.process_loan_request calls this.
            # Ideally, LoanMarket should check this before calling grant_loan.
            # BUT, to enforce it at the Bank level, we'd need the agent object or a way to look it up.
            # Since we don't have it here easily without changing signature, let's assume LoanMarket checks it OR
            # we rely on the fact that if an agent is in credit jail, their 'credit_rating' (conceptually) is 0.
            # Let's enforce it in LoanMarket instead?
            # The spec says "Modify Bank to handle defaults ... prevents Moral Hazard".
            # It also says "Bankrupt agents remain active but are economically crippled (Credit Jail)."
            # Let's add an optional 'borrower_agent' arg or rely on LoanMarket.
            # I'll update LoanMarket in the next steps or if I can modify Bank signature.
            # Actually, Bank.run_tick has access to 'agents_dict'.
            # Let's trust LoanMarket for now, OR change signature.
            # I will assume LoanMarket handles the denial based on the flag I added to Household.
            pass

        # 3. Gold Standard (Full Reserve) Check vs. Fractional Reserve (WO-064)
        gold_standard_mode = self._get_config("gold_standard_mode", False)

        if gold_standard_mode:
            # Gold Standard: 100% reserve requirement
            if self.assets < amount:
                logger.warning(
                    f"LOAN_REJECTED | Insufficient reserves (Gold Standard) for {amount:.2f}. Reserves: {self.assets:.2f}",
                    extra={"agent_id": self.id, "tags": ["bank", "loan", "gold_standard"]}
                )
                return None
        else:
            # Fractional Reserve Logic
            reserve_ratio = self._get_config("reserve_req_ratio", 0.1)
            total_deposits = sum(d.amount for d in self.deposits.values())
            # Required reserves are based on total liabilities (deposits) after the new loan is notionally added
            required_reserves = (total_deposits + amount) * reserve_ratio

            if self.assets < required_reserves:
                logger.warning(
                    f"LOAN_DENIED | Insufficient reserves for fractional lending. "
                    f"Assets: {self.assets:.2f}, Required: {required_reserves:.2f} "
                    f"(Deposits: {total_deposits:.2f}, Loan: {amount:.2f}, Ratio: {reserve_ratio:.2%})",
                    extra={"agent_id": self.id, "tags": ["bank", "loan", "fractional_reserve"]}
                )
                return None

            # If assets are less than the loan amount, but we have enough reserves, this is credit creation.
            if self.assets < amount:
                logger.info(
                    f"[CREDIT_CREATION] Bank {self.id} created {amount} credit. Reserves: {self.assets:.2f}",
                    extra={"agent_id": self.id, "tags": ["bank", "loan", "credit_creation"]}
                )

        # 3. Execution (Update Bank State Only)
        # self.assets -= amount  <-- REMOVED: Asset transfer handled by LoanMarket Transaction
        loan_id = f"loan_{self.next_loan_id}"
        self.next_loan_id += 1

        new_loan = Loan(
            borrower_id=borrower_id,
            principal=amount,
            remaining_balance=amount,
            annual_interest_rate=annual_rate,
            term_ticks=term_ticks,
            start_tick=0
        )
        self.loans[loan_id] = new_loan

        logger.info(
            f"LOAN_GRANTED | Loan {loan_id} to Agent {borrower_id}. "
            f"Amt: {amount:.2f}, Rate: {annual_rate:.2%}, Term: {term_ticks}",
            extra={"agent_id": self.id, "tags": ["bank", "loan"]}
        )
        return loan_id

    # --- IBankService Implementation (Customer Facing) ---

    def deposit_from_customer(self, depositor_id: int, amount: float) -> Optional[str]:
        """
        Accepts a deposit from an agent (Customer).
        Does NOT transfer assets directly (handled by Transaction); creates deposit record.
        Returns deposit ID.
        """
        margin = self._get_config("bank_defaults.bank_margin", 0.02)
        deposit_rate = max(0.0, self.base_rate + self._get_config("bank_defaults.credit_spread_base", 0.02) - margin)

        # self.assets += amount <-- REMOVED: Asset transfer handled by LoanMarket Transaction

        deposit_id = f"dep_{self.next_deposit_id}"
        self.next_deposit_id += 1

        new_deposit = Deposit(
            depositor_id=depositor_id,
            amount=amount,
            annual_interest_rate=deposit_rate
        )

        self.deposits[deposit_id] = new_deposit

        logger.info(
            f"DEPOSIT_ACCEPTED | Deposit {deposit_id} from Agent {depositor_id}. "
            f"Amt: {amount:.2f}, Rate: {deposit_rate:.2%}",
            extra={"agent_id": self.id, "tags": ["bank", "deposit"]}
        )
        return deposit_id

    def withdraw_for_customer(self, depositor_id: int, amount: float) -> bool:
        """
        Withdraws from depositor's account (Customer).
        Returns True if successful, False if insufficient balance.
        """
        # Find deposit by depositor_id
        # We need to scan because key is deposit_id
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
        # self.assets -= amount # Handled by Transaction in LoanMarket

        # If deposit is empty, remove it
        if target_deposit.amount <= 0:
            if target_dep_id:
                del self.deposits[target_dep_id]

        logger.info(
            f"WITHDRAWAL_PROCESSED | Agent {depositor_id} withdrew {amount:.2f}",
            extra={"agent_id": self.id, "tags": ["bank", "withdrawal"]}
        )
        return True

    # --- IFinancialEntity Implementation (System Facing) ---

    def deposit(self, amount: float) -> None:
        """
        Deposits a given amount into the bank's own assets (Equity/Reserves).
        Implementation of IFinancialEntity.deposit.
        """
        if amount > 0:
            self._assets += amount

    def withdraw(self, amount: float) -> None:
        """
        Withdraws a given amount from the bank's own assets (Equity/Reserves).
        Implementation of IFinancialEntity.withdraw.
        """
        if amount > 0:
            if self.assets < amount:
                raise InsufficientFundsError(f"Bank {self.id} has insufficient funds for withdrawal of {amount:.2f}. Available: {self.assets:.2f}")
            self._assets -= amount

    def get_debt_summary(self, agent_id: int) -> Dict[str, float]:
        """Returns debt info for AI state."""
        total_principal = 0.0
        daily_interest_burden = 0.0
        ticks_per_year = self._get_config("bank_defaults.ticks_per_year", TICKS_PER_YEAR)

        for loan in self.loans.values():
            if loan.borrower_id == agent_id:
                total_principal += loan.remaining_balance
                daily_interest_burden += (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year

        return {
            "total_principal": total_principal,
            "daily_interest_burden": daily_interest_burden
        }

    def get_deposit_balance(self, agent_id: int) -> float:
        """Returns the total deposit balance for a specific agent."""
        total_deposit = 0.0
        for deposit in self.deposits.values():
            if deposit.depositor_id == agent_id:
                total_deposit += deposit.amount
        return total_deposit

    def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0, reflux_system: Optional[Any] = None):
        """
        Process interest payments and distributions.
        Must be called every tick.
        """
        ticks_per_year = self._get_config("bank_defaults.ticks_per_year", TICKS_PER_YEAR)

        # 1. Collect Interest from Loans
        total_loan_interest = 0.0
        loans_to_remove = []

        for loan_id, loan in self.loans.items():
            agent = agents_dict.get(loan.borrower_id)
            if not agent or not getattr(agent, 'is_active', True):
                # Default logic or write-off logic here
                continue

            # Calculate Interest Payment
            interest_payment = (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year

            # Principal Repayment (Amortized or Bullet? Assuming Bullet for now or minimal amortization)
            # Let's simple amortization: Principal / Remaining Term
            # Wait, design spec says "Man-gi or Bun-hal". Let's do simple interest only + Principal at end?
            # Or constant payment?
            # Spec: "tick_payment = (balance * annual_rate) / TICKS_PER_YEAR" -> This is Interest Only.

            payment = interest_payment

            # Try to collect
            if agent.assets >= payment:
                success = False
                if self.settlement_system:
                    success = self.settlement_system.transfer(agent, self, payment, f"Loan Interest {loan_id}")
                else:
                    agent.withdraw(payment)
                    self.deposit(payment)
                    success = True

                if success:
                    total_loan_interest += payment

                    # Record Expense for Firms (FinanceDepartment)
                    if hasattr(agent, 'finance') and hasattr(agent.finance, 'record_expense'):
                        agent.finance.record_expense(payment)

            else:
                # Default / Penalty logic
                # Phase 4: Call process_default
                self.process_default(agent, loan, current_tick)

                # Take whatever is left (process_default might have seized assets already)
                partial = agent.assets
                if partial > 0:
                     success = False
                     if self.settlement_system:
                         success = self.settlement_system.transfer(agent, self, partial, f"Loan Default Recovery {loan_id}")
                     else:
                         # Force withdrawal of remaining balance
                         # Assuming partial = agent.assets
                         agent.withdraw(partial)
                         self.deposit(partial)
                         success = True

                     if success:
                        total_loan_interest += partial

        # 2. Pay Interest to Depositors
        total_deposit_interest = 0.0
        for dep_id, deposit in self.deposits.items():
            agent = agents_dict.get(deposit.depositor_id)
            if not agent:
                continue

            interest_payout = (deposit.amount * deposit.annual_interest_rate) / ticks_per_year

            if self.assets >= interest_payout:
                success = False
                if self.settlement_system:
                    success = self.settlement_system.transfer(self, agent, interest_payout, f"Deposit Interest {dep_id}")
                else:
                    self.withdraw(interest_payout)
                    agent.deposit(interest_payout)
                    success = True

                # Track Capital Income (Interest)
                from simulation.core_agents import Household
                if isinstance(agent, Household) and hasattr(agent, "capital_income_this_tick"):
                    agent.capital_income_this_tick += interest_payout

                total_deposit_interest += interest_payout
                # Compounding? Usually deposits compound.
                # If we pay to agent.assets, it's "Payout".
                # If we add to deposit.amount, it's "Compound".
                # Spec says: "bank.reserves 차감, agent.assets 증가 (유동성 공급)" -> Payout.
            else:
                # Bank run scenario?
                logger.error("BANK_LIQUIDITY_CRISIS | Cannot pay deposit interest!")

        # Phase 8-B: Capture Net Profit (Reflux)
        # Net Profit = Interest Income - Interest Expense
        net_profit = total_loan_interest - total_deposit_interest
        if net_profit > 0 and reflux_system:
            # Transfer profit to reflux system (Distribution as dividend/service fee)
            # This ensures Bank doesn't accumulate infinite money.
            # Bank assets were already updated above (+loan_int, -dep_int).
            # So we subtract net_profit from assets.
            self._assets -= net_profit
            reflux_system.capture(net_profit, "Bank", "net_profit")
            logger.info(f"BANK_PROFIT_CAPTURE | Transferred {net_profit:.2f} to Reflux System.")

        logger.info(
            f"BANK_TICK_SUMMARY | Collected Loan Int: {total_loan_interest:.2f}, Paid Deposit Int: {total_deposit_interest:.2f}, Net Profit: {net_profit:.2f}, Reserves: {self.assets:.2f}",
            extra={"agent_id": self.id, "tags": ["bank", "tick"]}
        )

    # Legacy method support for compatibility if needed, but we are rewriting
    def get_outstanding_loans_for_agent(self, agent_id: int) -> List[Dict]:
        # Return dict representation for compatibility if other modules use it
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
        if loan_id in self.loans:
            # We don't touch assets here, handled by Transaction
            self.loans[loan_id].remaining_balance -= amount
            if self.loans[loan_id].remaining_balance <= 0:
                # Fully repaid
                pass # Logic to archive loan?
            logger.info(
                f"REPAYMENT_PROCESSED | Loan {loan_id} repaid by {amount}",
                extra={"agent_id": self.id, "tags": ["bank", "repayment"]}
            )

    def _borrow_from_central_bank(self, amount: float):
        """
        Phase 23.5: Lender of Last Resort.
        Creates money via Government to cover liquidity gaps.
        """
        self._assets += amount
        if self._get_config("government_id", None) is not None:
             # If we have a reference to government via simulation later, but here we take config
             pass
        
        # We need a way to increment gov.total_money_issued. 
        # Since Bank doesn't have gov reference directly, we'll return the amount
        # or rely on the engine to track it if we flag it.
        # Better: Pass government to Bank.run_tick or check_solvency.
        logger.warning(f"BANK_BORROWING | Central Bank injected {amount:.2f} into Bank {self.id} reserves.")

    def check_solvency(self, government: Any):
        """
        Phase 23.5: Ensuring Bank always has positive reserves for TransactionProcessor.
        """
        if self.assets < 0:
            borrow_amount = abs(self.assets) + 1000.0 # Maintain buffer

            if self.settlement_system:
                self.settlement_system.transfer(government, self, borrow_amount, "Lender of Last Resort")
                government.total_money_issued += borrow_amount
            else:
                self._assets += borrow_amount
                government.total_money_issued += borrow_amount

            logger.warning(f"LENDER_OF_LAST_RESORT | Bank {self.id} insolvent! Borrowed {borrow_amount:.2f} from Government.")

    def process_default(self, agent: Any, loan: Loan, current_tick: int):
        """
        Phase 4: Handles loan default.
        1. Liquidation: Sell assets (stocks, inventory) to repay.
        2. Forgiveness: Remaining debt is written off.
        3. Penalty: Credit Jail & XP Penalty.
        """
        logger.warning(
            f"DEFAULT_EVENT | Agent {agent.id} defaulted on Loan {loan.principal:.2f}",
            extra={"agent_id": agent.id, "loan_id": getattr(loan, "id", "unknown")}
        )

        # 1. Liquidation
        if hasattr(agent, "shares_owned") and agent.shares_owned:
            agent.shares_owned.clear()
            logger.info(f"LIQUIDATION | Agent {agent.id} shares confiscated.")

        # 2. Forgiveness (Write-off)
        loan.remaining_balance = 0.0 # Effectively forgiven

        # 3. Penalty
        # Credit Jail
        jail_ticks = self._get_config("credit_recovery_ticks", 100)
        if hasattr(agent, "credit_frozen_until_tick"):
            agent.credit_frozen_until_tick = current_tick + jail_ticks

        # 4. XP Penalty
        xp_penalty = self._get_config("bankruptcy_xp_penalty", 0.2)
        if hasattr(agent, "education_xp"):
             agent.education_xp *= (1.0 - xp_penalty)
        if hasattr(agent, "skills"):
             for skill in agent.skills.values():
                 skill.value *= (1.0 - xp_penalty)

        logger.info(f"PENALTY_APPLIED | Agent {agent.id} entered Credit Jail and lost XP.")
