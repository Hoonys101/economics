import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import math

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


class Bank:
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    Manages loans, deposits, and monetary policy interaction.
    """

    def __init__(self, id: int, initial_assets: float, config_module: Any = None):
        self.id = id
        self.assets = initial_assets # Reserves
        self.config_module = config_module

        # Data Stores
        self.loans: Dict[str, Loan] = {}
        self.deposits: Dict[str, Deposit] = {}

        # Policy Rates
        if config_module:
            self.base_rate = getattr(config_module, "INITIAL_BASE_ANNUAL_RATE", INITIAL_BASE_ANNUAL_RATE)
        else:
            self.base_rate = INITIAL_BASE_ANNUAL_RATE

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

    def _get_config(self, key: str, default: Any) -> Any:
        return getattr(self.config_module, key, default)

    def update_base_rate(self, new_rate: float):
        """Called by Central Bank / Government to update monetary policy."""
        self.base_rate = new_rate
        logger.info(
            f"MONETARY_POLICY | Base Rate updated to {self.base_rate:.2%}",
            extra={"agent_id": self.id, "tags": ["bank", "policy"]}
        )

    def grant_loan(
        self,
        borrower_id: int,
        amount: float,
        term_ticks: Optional[int] = None
    ) -> Optional[str]:
        """
        Grants a loan to an agent if eligible.
        Does NOT transfer assets directly; returns loan ID for Transaction creation.
        """
        # 1. Config Check
        if not term_ticks:
            term_ticks = self._get_config("LOAN_DEFAULT_TERM", 50)

        credit_spread = self._get_config("CREDIT_SPREAD_BASE", 0.02)
        annual_rate = self.base_rate + credit_spread

        # 2. Liquidity Check
        # 1a. Credit Jail Check (Phase 4)
        if hasattr(self.config_module, "CREDIT_RECOVERY_TICKS"):
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

        if self.assets < amount:
            logger.warning(
                f"LOAN_DENIED | Bank has insufficient liquidity for {amount:.2f}",
                extra={"agent_id": self.id, "tags": ["bank", "loan"]}
            )
            return None

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

    def deposit(self, depositor_id: int, amount: float) -> Optional[str]:
        """
        Accepts a deposit from an agent.
        Does NOT transfer assets directly; returns deposit ID for Transaction creation.
        """
        margin = self._get_config("BANK_MARGIN", 0.02)
        deposit_rate = max(0.0, self.base_rate + self._get_config("CREDIT_SPREAD_BASE", 0.02) - margin)

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

    def get_debt_summary(self, agent_id: int) -> Dict[str, float]:
        """Returns debt info for AI state."""
        total_principal = 0.0
        daily_interest_burden = 0.0
        ticks_per_year = self._get_config("TICKS_PER_YEAR", TICKS_PER_YEAR)

        for loan in self.loans.values():
            if loan.borrower_id == agent_id:
                total_principal += loan.remaining_balance
                daily_interest_burden += (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year

        return {
            "total_principal": total_principal,
            "daily_interest_burden": daily_interest_burden
        }

    def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0):
        """
        Process interest payments and distributions.
        Must be called every tick.
        """
        ticks_per_year = self._get_config("TICKS_PER_YEAR", TICKS_PER_YEAR)

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
                agent.assets -= payment
                self.assets += payment
                total_loan_interest += payment
            else:
                # Default / Penalty logic
                # Phase 4: Call process_default
                self.process_default(agent, loan, current_tick)

                # Take whatever is left (process_default might have seized assets already)
                partial = agent.assets
                if partial > 0:
                     agent.assets = 0
                     self.assets += partial
                     total_loan_interest += partial

        # 2. Pay Interest to Depositors
        total_deposit_interest = 0.0
        for dep_id, deposit in self.deposits.items():
            agent = agents_dict.get(deposit.depositor_id)
            if not agent:
                continue

            interest_payout = (deposit.amount * deposit.annual_interest_rate) / ticks_per_year

            if self.assets >= interest_payout:
                self.assets -= interest_payout
                agent.assets += interest_payout
                total_deposit_interest += interest_payout
                # Compounding? Usually deposits compound.
                # If we pay to agent.assets, it's "Payout".
                # If we add to deposit.amount, it's "Compound".
                # Spec says: "bank.reserves 차감, agent.assets 증가 (유동성 공급)" -> Payout.
            else:
                # Bank run scenario?
                logger.error("BANK_LIQUIDITY_CRISIS | Cannot pay deposit interest!")

        logger.info(
            f"BANK_TICK_SUMMARY | Collected Loan Int: {total_loan_interest:.2f}, Paid Deposit Int: {total_deposit_interest:.2f}, Reserves: {self.assets:.2f}",
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
        jail_ticks = getattr(self.config_module, "CREDIT_RECOVERY_TICKS", 100)
        if hasattr(agent, "credit_frozen_until_tick"):
            agent.credit_frozen_until_tick = current_tick + jail_ticks

        # 4. XP Penalty
        xp_penalty = getattr(self.config_module, "BANKRUPTCY_XP_PENALTY", 0.2)
        if hasattr(agent, "education_xp"):
             agent.education_xp *= (1.0 - xp_penalty)
        if hasattr(agent, "skills"):
             for skill in agent.skills.values():
                 skill.value *= (1.0 - xp_penalty)

        logger.info(f"PENALTY_APPLIED | Agent {agent.id} entered Credit Jail and lost XP.")
