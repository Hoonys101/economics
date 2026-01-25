import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, TYPE_CHECKING
import math
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import InsufficientFundsError, IFinancialEntity
from simulation.models import Order, Transaction
from simulation.portfolio import Portfolio

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

TICKS_PER_YEAR = 100
INITIAL_BASE_ANNUAL_RATE = 0.05

@dataclass
class Loan:
    borrower_id: int
    principal: float
    remaining_balance: float
    annual_interest_rate: float
    term_ticks: int
    start_tick: int

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

class Bank(IFinancialEntity):
    """
    Phase 3: Central & Commercial Bank Hybrid System.
    WO-109: Refactored for Sacred Sequence (Transactions).
    """

    def __init__(self, id: int, initial_assets: float, config_manager: ConfigManager, settlement_system: Optional["ISettlementSystem"] = None):
        self._id = id
        self._assets = initial_assets
        self.config_manager = config_manager
        self.settlement_system = settlement_system
        self.government: Optional["Government"] = None

        self.loans: Dict[str, Loan] = {}
        self.deposits: Dict[str, Deposit] = {}
        self.base_rate = self._get_config("bank_defaults.initial_base_annual_rate", INITIAL_BASE_ANNUAL_RATE)

        self.next_loan_id = 0
        self.next_deposit_id = 0

        # Compatibility
        self.value_orientation = "N/A"
        self.needs: Dict[str, float] = {}

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

    def _add_assets(self, amount: float) -> None:
        self._assets += amount

    def _sub_assets(self, amount: float) -> None:
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

    def grant_loan(self, borrower_id: int, amount: float, term_ticks: Optional[int] = None, interest_rate: Optional[float] = None) -> Optional[str]:
        if not term_ticks:
            term_ticks = self._get_config("loan.default_term", 50)

        if interest_rate is not None:
            annual_rate = interest_rate
        else:
            credit_spread = self._get_config("bank_defaults.credit_spread_base", 0.02)
            annual_rate = self.base_rate + credit_spread

        gold_standard_mode = self._get_config("gold_standard_mode", False)
        if gold_standard_mode:
            if self.assets < amount:
                return None
        else:
            reserve_ratio = self._get_config("reserve_req_ratio", 0.1)
            total_deposits = sum(d.amount for d in self.deposits.values())
            required_reserves = (total_deposits + amount) * reserve_ratio
            if self.assets < required_reserves:
                return None

            if self.assets < amount:
                shortfall = amount - self.assets
                if self.government and hasattr(self.government, "total_money_issued"):
                    self.government.total_money_issued += shortfall
                    self.deposit(shortfall)

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
        return loan_id

    def deposit_from_customer(self, depositor_id: int, amount: float) -> Optional[str]:
        margin = self._get_config("bank_defaults.bank_margin", 0.02)
        deposit_rate = max(0.0, self.base_rate + self._get_config("bank_defaults.credit_spread_base", 0.02) - margin)

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
            self._assets += amount

    def withdraw(self, amount: float) -> None:
        if amount > 0:
            if self.assets < amount:
                 raise InsufficientFundsError(f"Insufficient funds")
            self._assets -= amount

    def get_debt_summary(self, agent_id: int) -> Dict[str, float]:
        total_principal = 0.0
        daily_interest_burden = 0.0
        ticks_per_year = self._get_config("bank_defaults.ticks_per_year", TICKS_PER_YEAR)
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

    def run_tick(self, agents_dict: Dict[int, Any], current_tick: int = 0, reflux_system: Optional[Any] = None) -> List[Transaction]:
        generated_transactions: List[Transaction] = []
        ticks_per_year = self._get_config("bank_defaults.ticks_per_year", TICKS_PER_YEAR)
        gov_agent = None
        for a in agents_dict.values():
             if a.__class__.__name__ == 'Government':
                 gov_agent = a
                 break

        total_loan_interest = 0.0
        for loan_id, loan in self.loans.items():
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
                self.process_default(agent, loan, current_tick, government=gov_agent)
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
                 transaction_type="reflux_capture",
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
            solvency_buffer = self._get_config("bank_defaults.solvency_buffer", 1000.0)
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

    def process_default(self, agent: Any, loan: Loan, current_tick: int, government: Optional[Any] = None):
        if hasattr(agent, "shares_owned") and agent.shares_owned:
            agent.shares_owned.clear()

        if government and loan.remaining_balance > 0:
            government.total_money_destroyed += loan.remaining_balance

        loan.remaining_balance = 0.0

        jail_ticks = self._get_config("credit_recovery_ticks", 100)
        if hasattr(agent, "credit_frozen_until_tick"):
            agent.credit_frozen_until_tick = current_tick + jail_ticks

        xp_penalty = self._get_config("bankruptcy_xp_penalty", 0.2)
        if hasattr(agent, "education_xp"):
             agent.education_xp *= (1.0 - xp_penalty)

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
        if loan_id in self.loans:
            self.loans[loan_id].remaining_balance -= amount
