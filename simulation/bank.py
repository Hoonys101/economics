import logging
from typing import Dict, Any, List, Optional
import math
from simulation.models import Loan, Deposit, Order, RealEstateUnit

logger = logging.getLogger(__name__)

# Constants (Fallback if config is not passed, though it should be)
TICKS_PER_YEAR = 100
INITIAL_BASE_ANNUAL_RATE = 0.05
CREDIT_SPREAD_BASE = 0.02
BANK_MARGIN = 0.02

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

        # Mortgage Default Tracking
        # Map loan_id -> missed_payments count
        self.mortgage_default_counter: Dict[str, int] = {}

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

        # 2. Liquidity Check & Gold Standard
        if not self._check_liquidity(amount):
             return None

        # 3. Execution (Update Bank State Only)
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

    def grant_mortgage(
        self,
        borrower_id: int,
        property_id: int,
        principal: float,
        term_ticks: Optional[int] = None
    ) -> Optional[str]:
        """
        Grants a Mortgage Loan linked to a RealEstateUnit.
        Called by Engine during Real Estate Transaction.
        """
        if not term_ticks:
            # 30 years * 12 months = 360 months equivalent ticks?
            # Spec says "360 ticks (30 years equivalent)"
            term_ticks = 360

        credit_spread = self._get_config("MORTGAGE_SPREAD", 0.01) # Lower spread for secured loan
        annual_rate = self.base_rate + credit_spread

        # Check Liquidity
        if not self._check_liquidity(principal):
            return None

        loan_id = f"mortgage_{self.next_loan_id}"
        self.next_loan_id += 1

        new_loan = Loan(
            borrower_id=borrower_id,
            principal=principal,
            remaining_balance=principal,
            annual_interest_rate=annual_rate,
            term_ticks=term_ticks,
            start_tick=0,
            collateral_id=property_id
        )
        self.loans[loan_id] = new_loan
        self.mortgage_default_counter[loan_id] = 0

        logger.info(
            f"MORTGAGE_GRANTED | Loan {loan_id} for Unit {property_id} to Agent {borrower_id}. "
            f"Amt: {principal:.2f}, Rate: {annual_rate:.2%}, Term: {term_ticks}",
            extra={"agent_id": self.id, "tags": ["bank", "mortgage"]}
        )
        return loan_id

    def deposit(self, depositor_id: int, amount: float) -> Optional[str]:
        """
        Accepts a deposit from an agent.
        Does NOT transfer assets directly; returns deposit ID for Transaction creation.
        """
        margin = self._get_config("BANK_MARGIN", 0.02)
        deposit_rate = max(0.0, self.base_rate + self._get_config("CREDIT_SPREAD_BASE", 0.02) - margin)

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

    def _check_liquidity(self, amount: float) -> bool:
        if self._get_config("GOLD_STANDARD_MODE", False):
            if self.assets < amount:
                logger.warning(
                    f"LOAN_REJECTED | Insufficient reserves (Gold Standard) for {amount:.2f}. Reserves: {self.assets:.2f}",
                    extra={"agent_id": self.id, "tags": ["bank", "loan", "gold_standard"]}
                )
                return False
        elif self.assets < amount:
             logger.warning(
                f"LOAN_DENIED | Bank has insufficient liquidity for {amount:.2f}",
                extra={"agent_id": self.id, "tags": ["bank", "loan"]}
            )
             return False
        return True

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
        ticks_per_year = self._get_config("TICKS_PER_YEAR", TICKS_PER_YEAR)

        # 1. Collect Interest from Loans (and Principal for Mortgages?)
        total_loan_interest = 0.0

        # Copy keys to avoid modification during iteration if we remove loans (handled inside)
        for loan_id, loan in list(self.loans.items()):
            agent = agents_dict.get(loan.borrower_id)
            if not agent:
                continue

            # Calculate Payment
            # Default: Interest Only
            interest_payment = (loan.remaining_balance * loan.annual_interest_rate) / ticks_per_year

            # Amortization for Mortgage
            principal_payment = 0.0
            if loan.collateral_id is not None and loan.term_ticks > 0:
                # Simple straight-line amortization
                raw_principal_payment = loan.principal / loan.term_ticks
                # Correct Logic: Prevent overpayment
                principal_payment = min(raw_principal_payment, loan.remaining_balance)

            total_payment = interest_payment + principal_payment

            # Try to collect
            if agent.assets >= total_payment:
                agent.assets -= total_payment
                self.assets += total_payment

                # Apply payments
                loan.remaining_balance -= principal_payment

                total_loan_interest += interest_payment

                # Reset default counter on success
                if loan_id in self.mortgage_default_counter:
                    self.mortgage_default_counter[loan_id] = 0

                if loan.remaining_balance <= 0.0001: # Use epsilon
                    # Loan paid off
                    self.loans.pop(loan_id, None)
                    logger.info(f"LOAN_PAID_OFF | Loan {loan_id} fully repaid.", extra={"loan_id": loan_id})

            else:
                # Default Logic
                if loan.collateral_id is not None:
                     # Mortgage Default
                     current_misses = self.mortgage_default_counter.get(loan_id, 0) + 1
                     self.mortgage_default_counter[loan_id] = current_misses

                     logger.warning(
                         f"MORTGAGE_DEFAULT | Loan {loan_id} missed payment {current_misses}/3.",
                         extra={"agent_id": agent.id, "loan_id": loan_id}
                     )
                     # Foreclosure check happens in Engine or here?
                     # Engine coordinates, but Bank tracks data.
                     # We will expose a check method.
                else:
                    # Standard Loan Default (Unsecured)
                    self.process_default(agent, loan, current_tick)

                    # Partial recovery
                    partial = agent.assets
                    if partial > 0:
                         agent.assets = 0
                         self.assets += partial
                         total_loan_interest += partial # Treat all as interest/penalty

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

                # Track Capital Income (Interest)
                from simulation.core_agents import Household
                if isinstance(agent, Household) and hasattr(agent, "capital_income_this_tick"):
                    agent.capital_income_this_tick += interest_payout

                total_deposit_interest += interest_payout
            else:
                logger.error("BANK_LIQUIDITY_CRISIS | Cannot pay deposit interest!")

        # Phase 8-B: Capture Net Profit (Reflux)
        net_profit = total_loan_interest - total_deposit_interest
        if net_profit > 0 and reflux_system:
            self.assets -= net_profit
            reflux_system.capture(net_profit, "Bank", "net_profit")
            logger.info(f"BANK_PROFIT_CAPTURE | Transferred {net_profit:.2f} to Reflux System.")

        logger.info(
            f"BANK_TICK_SUMMARY | Collected Loan Int: {total_loan_interest:.2f}, Paid Deposit Int: {total_deposit_interest:.2f}, Net Profit: {net_profit:.2f}, Reserves: {self.assets:.2f}",
            extra={"agent_id": self.id, "tags": ["bank", "tick"]}
        )

    def check_mortgage_defaults(self) -> List[str]:
        """
        Returns list of loan_ids that have exceeded default threshold (e.g. 3 ticks).
        Called by Engine to trigger foreclosure.
        """
        defaults = []
        threshold = self._get_config("MORTGAGE_DEFAULT_THRESHOLD", 3)
        for loan_id, misses in self.mortgage_default_counter.items():
            if misses >= threshold:
                defaults.append(loan_id)
        return defaults

    def foreclose_property(self, loan_id: str, real_estate_units: List[RealEstateUnit], market: Any) -> bool:
        """
        Executes foreclosure:
        1. Seize property (Owner -> Bank, Evict Tenant)
        2. Cancel Loan (Collateral seized)
        3. List for Fire Sale
        """
        loan = self.loans.get(loan_id)
        if not loan or loan.collateral_id is None:
            return False

        unit_id = loan.collateral_id
        # Find unit
        unit = next((u for u in real_estate_units if u.id == unit_id), None)
        if not unit:
            return False

        old_owner_id = unit.owner_id

        # 1. Seize
        unit.owner_id = self.id # Bank owns it
        unit.occupant_id = None # Eviction
        unit.mortgage_id = None # Unlink mortgage from unit (it's being wiped)

        # 2. Cancel Loan
        # Write off remaining balance against Bank Assets?
        # Bank now owns asset (Property) worth X.
        # Loan Balance was Y.
        # If X > Y, Bank profits. If X < Y, Bank loses.
        # For now, just remove the loan.
        self.loans.pop(loan_id, None)
        self.mortgage_default_counter.pop(loan_id, None)

        # 3. Fire Sale
        # Price = 80% of Estimated Value
        fire_sale_price = unit.estimated_value * 0.8

        # Place Sell Order
        order = Order(
            agent_id=self.id,
            order_type="SELL",
            item_id=f"unit_{unit.id}",
            quantity=1.0,
            price=fire_sale_price,
            market_id="real_estate"
        )
        market.place_order(order, 0) # tick 0 or passed tick

        logger.info(
            f"FORECLOSURE_EXECUTED | Bank seized Unit {unit.id} from Agent {old_owner_id}. Loan {loan_id} cancelled. Listed for {fire_sale_price:.2f}",
            extra={"loan_id": loan_id, "unit_id": unit.id, "tags": ["foreclosure"]}
        )
        return True

    def withdraw(self, depositor_id: int, amount: float) -> bool:
        """
        Withdraws from depositor's account.
        Returns True if successful, False if insufficient balance.
        """
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

        if target_deposit.amount <= 0:
            if target_dep_id:
                del self.deposits[target_dep_id]

        logger.info(
            f"WITHDRAWAL_PROCESSED | Agent {depositor_id} withdrew {amount:.2f}",
            extra={"agent_id": self.id, "tags": ["bank", "withdrawal"]}
        )
        return True

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
        loan.remaining_balance = 0.0

        # 3. Penalty
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
