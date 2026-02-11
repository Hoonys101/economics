from typing import List, Dict, Optional, Any, Tuple, Union
import logging
import uuid
from modules.finance.api import (
    IFinanceSystem, BondDTO, BailoutLoanDTO, BailoutCovenant, IFinancialEntity,
    InsufficientFundsError, GrantBailoutCommand, BorrowerProfileDTO, LoanInfoDTO
)
from modules.finance.domain import AltmanZScoreCalculator
from modules.analysis.fiscal_monitor import FiscalMonitor
from modules.simulation.api import EconomicIndicatorsDTO, AgentID
from modules.system.api import DEFAULT_CURRENCY
from simulation.models import Transaction

# New Stateless Engine Imports
from modules.finance.engine_api import (
    FinancialLedgerDTO, TreasuryStateDTO, BankStateDTO, BondStateDTO,
    LoanApplicationDTO, LiquidationRequestDTO, LoanStateDTO, DepositStateDTO
)
from modules.finance.engines.loan_risk_engine import LoanRiskEngine
from modules.finance.engines.loan_booking_engine import LoanBookingEngine
from modules.finance.engines.liquidation_engine import LiquidationEngine
from modules.finance.engines.debt_servicing_engine import DebtServicingEngine
from modules.finance.engines.interest_rate_engine import InterestRateEngine

# Forward reference for type hinting
from simulation.firms import Firm

logger = logging.getLogger(__name__)

class FinanceSystem(IFinanceSystem):
    """
    Manages sovereign debt, corporate bailouts, and solvency checks.
    Refactored to use Stateless Engines and FinancialLedgerDTO.
    MIGRATION: Uses integer pennies.
    """

    def __init__(self, government: 'Government', central_bank: 'CentralBank', bank: 'Bank', config_module: Any, settlement_system: Any = None):
        self.government = government
        self.central_bank = central_bank
        self.bank = bank
        self.config_module = config_module
        self.settlement_system = settlement_system

        self.fiscal_monitor = FiscalMonitor()

        # --- STATELESS ARCHITECTURE ---
        # 1. Initialize Engines
        self.loan_risk_engine = LoanRiskEngine()
        self.loan_booking_engine = LoanBookingEngine()
        self.liquidation_engine = LiquidationEngine()
        self.debt_servicing_engine = DebtServicingEngine()
        self.interest_rate_engine = InterestRateEngine()

        # 2. Initialize Ledger (Single Source of Truth)
        # We perform a basic sync from the legacy agents to the new ledger
        self.ledger = FinancialLedgerDTO(
            current_tick=0,
            treasury=TreasuryStateDTO(government_id=government.id),
            banks={
                bank.id: BankStateDTO(
                    bank_id=bank.id,
                    base_rate=getattr(bank, 'base_rate', 0.03),
                    reserves={DEFAULT_CURRENCY: 0}
                )
            }
        )

        # Sync Initial State (Optimistic)
        if hasattr(bank, 'wallet'):
            bal = bank.wallet.get_balance(DEFAULT_CURRENCY)
            self.ledger.banks[bank.id].reserves[DEFAULT_CURRENCY] = bal

        if hasattr(government, 'wallet'):
             bal = government.wallet.get_balance(DEFAULT_CURRENCY)
             self.ledger.treasury.balance[DEFAULT_CURRENCY] = bal

    # --- ORCHESTRATOR METHODS ---

    def process_loan_application(
        self,
        borrower_id: AgentID,
        amount: int,
        borrower_profile: Dict,
        current_tick: int
    ) -> Tuple[Optional[LoanInfoDTO], List[Transaction]]:
        """
        Orchestrates the loan application process using Risk and Booking engines.
        """
        # 1. Update Ledger Context
        self.ledger.current_tick = current_tick

        # 2. Construct Application DTO
        # Determine lender (Default to self.bank for now as simpler orchestrator)
        lender_id = borrower_profile.get("preferred_lender_id", self.bank.id)

        app_dto = LoanApplicationDTO(
            borrower_id=borrower_id,
            lender_id=lender_id,
            amount_pennies=amount,
            borrower_profile=borrower_profile
        )

        # 3. Risk Assessment
        decision = self.loan_risk_engine.assess(app_dto, self.ledger)

        if not decision.is_approved:
            logger.info(f"LOAN_DENIED | {borrower_id} denied. Reason: {decision.rejection_reason}")
            return None, []

        # 4. Booking
        result = self.loan_booking_engine.grant_loan(app_dto, decision, self.ledger)

        # 5. Commit State
        self.ledger = result.updated_ledger

        # 6. Return Result
        loan_id = None
        for tx in result.generated_transactions:
            if tx.item_id.startswith("credit_creation_"):
                loan_id = tx.item_id.replace("credit_creation_", "")
                break

        if not loan_id:
            # Fallback/Error
            return None, result.generated_transactions

        # Construct LoanInfoDTO for the caller
        lender_id = app_dto.borrower_profile.get("preferred_lender_id")
        if not lender_id and self.ledger.banks:
             lender_id = next(iter(self.ledger.banks.keys()))

        loan_state = self.ledger.banks[lender_id].loans.get(loan_id)

        if not loan_state:
            return None, result.generated_transactions

        info_dto = LoanInfoDTO(
            loan_id=loan_state.loan_id,
            borrower_id=loan_state.borrower_id,
            original_amount=loan_state.principal_pennies,
            outstanding_balance=loan_state.remaining_principal_pennies,
            interest_rate=loan_state.interest_rate,
            origination_tick=loan_state.origination_tick,
            due_tick=loan_state.due_tick
        )

        return info_dto, result.generated_transactions

    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        """Query the ledger for deposit balance."""
        if bank_id in self.ledger.banks:
            deposit_id = f"DEP_{customer_id}_{bank_id}"
            if deposit_id in self.ledger.banks[bank_id].deposits:
                return self.ledger.banks[bank_id].deposits[deposit_id].balance_pennies
        return 0

    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> List[LoanInfoDTO]:
        """Query the ledger for loans."""
        loans = []
        if bank_id in self.ledger.banks:
            for loan in self.ledger.banks[bank_id].loans.values():
                if loan.borrower_id == customer_id and loan.remaining_principal_pennies > 0:
                    loans.append(LoanInfoDTO(
                        loan_id=loan.loan_id,
                        borrower_id=loan.borrower_id,
                        original_amount=loan.principal_pennies,
                        outstanding_balance=loan.remaining_principal_pennies,
                        interest_rate=loan.interest_rate,
                        origination_tick=loan.origination_tick,
                        due_tick=loan.due_tick
                    ))
        return loans

    # --- IFinanceSystem Implementation ---

    def evaluate_solvency(self, firm: 'Firm', current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        startup_grace_period = self.config_module.get("economy_params.STARTUP_GRACE_PERIOD_TICKS", 24)
        z_score_threshold = self.config_module.get("economy_params.ALTMAN_Z_SCORE_THRESHOLD", 1.81)

        if firm.age < startup_grace_period:
            if hasattr(firm, 'hr_state'):
                # Re-implement using state
                total_wages = sum(firm.hr_state.employee_wages.values())
                monthly_wage_bill = total_wages * 4
                required_runway = monthly_wage_bill * 3
                return firm.assets >= required_runway
            return True
        else:
            # Altman Z-Score for established firms
            # All inputs should be int pennies. Ratios will be same.
            # inventory_value: Firm.get_inventory_value() calculates qty * price. Price is float. So value is float dollars.
            # We need to convert inventory value to pennies.
            inventory_value = sum(firm.get_quantity(i) * firm.last_prices.get(i, 10.0) for i in firm.get_all_items())
            inventory_value_pennies = int(inventory_value * 100)

            capital_stock_pennies = int(firm.capital_stock * 100)

            total_assets = firm.assets + capital_stock_pennies + inventory_value_pennies
            working_capital = firm.assets - getattr(firm, 'total_debt', 0)

            retained_earnings = 0
            if hasattr(firm, 'finance_state'):
                retained_earnings = firm.finance_state.retained_earnings_pennies

            # Safe calculation of average profit
            average_profit = 0
            if hasattr(firm, 'finance_state') and firm.finance_state.profit_history:
                average_profit = sum(firm.finance_state.profit_history) / len(firm.finance_state.profit_history)

            z_score = AltmanZScoreCalculator.calculate(
                total_assets=float(total_assets),
                working_capital=float(working_capital),
                retained_earnings=float(retained_earnings),
                average_profit=float(average_profit)
            )
            return z_score > z_score_threshold

    def issue_treasury_bonds(self, amount: int, current_tick: int) -> Tuple[List[BondDTO], List[Transaction]]:
        """
        Issues new treasury bonds using the new Ledger system (partially).
        """
        # Updates self.ledger.treasury.bonds

        base_rate = 0.03
        if self.ledger.banks:
            base_rate = next(iter(self.ledger.banks.values())).base_rate

        yield_rate = base_rate + 0.01
        bond_maturity = 400

        bond_id = f"BOND_{current_tick}_{len(self.ledger.treasury.bonds)}"

        # Decide Buyer (Bank)
        buyer_id = self.bank.id

        # Check bank funds in Ledger
        bank_reserves = 0
        if buyer_id in self.ledger.banks:
            bank_reserves = self.ledger.banks[buyer_id].reserves.get(DEFAULT_CURRENCY, 0)

        if bank_reserves < amount:
            return [], []

        # Create Bond State
        bond_state = BondStateDTO(
            bond_id=bond_id,
            owner_id=buyer_id,
            face_value_pennies=amount,
            yield_rate=yield_rate,
            issue_tick=current_tick,
            maturity_tick=current_tick + bond_maturity
        )

        # Update Ledger
        self.ledger.treasury.bonds[bond_id] = bond_state

        # Deduct reserves (Payment)
        self.ledger.banks[buyer_id].reserves[DEFAULT_CURRENCY] -= amount

        # Add to Treasury Balance
        if DEFAULT_CURRENCY not in self.ledger.treasury.balance:
            self.ledger.treasury.balance[DEFAULT_CURRENCY] = 0
        self.ledger.treasury.balance[DEFAULT_CURRENCY] += amount

        # Generate Transaction
        tx = Transaction(
            buyer_id=buyer_id,
            seller_id=self.government.id,
            item_id=bond_id,
            quantity=1.0,
            price=amount,
            market_id="financial",
            transaction_type="bond_purchase",
            time=current_tick
        )

        # Map to legacy BondDTO for return signature compatibility
        bond_dto = BondDTO(
            id=bond_id,
            issuer="GOVERNMENT",
            face_value=amount,
            yield_rate=yield_rate,
            maturity_date=current_tick + bond_maturity
        )

        return [bond_dto], [tx]

    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: int, current_tick: int) -> Tuple[bool, List[Transaction]]:
        # Map to internal logic
        bonds, txs = self.issue_treasury_bonds(amount_to_raise, current_tick)
        return (len(bonds) > 0, txs)

    def collect_corporate_tax(self, firm: IFinancialEntity, tax_amount: int) -> bool:
        logger.warning("FinanceSystem.collect_corporate_tax called. Should be using Transaction Generation.")
        return False

    def request_bailout_loan(self, firm: 'Firm', amount: int) -> Optional[GrantBailoutCommand]:
        # Enforce Government Budget Constraint (Check Ledger)
        gov_bal = self.ledger.treasury.balance.get(DEFAULT_CURRENCY, 0)

        if gov_bal < amount:
            logger.warning(f"BAILOUT_DENIED | Government insufficient funds: {gov_bal} < {amount}")
            return None

        base_rate = 0.03 # Default
        if self.ledger.banks:
            base_rate = next(iter(self.ledger.banks.values())).base_rate

        penalty_premium = self.config_module.get("economy_params.BAILOUT_PENALTY_PREMIUM", 0.05)

        covenants = BailoutCovenant(
            dividends_allowed=False,
            executive_salary_freeze=True,
            mandatory_repayment=self.config_module.get("economy_params.BAILOUT_COVENANT_RATIO", 0.5)
        )

        return GrantBailoutCommand(
            firm_id=firm.id,
            amount=amount,
            interest_rate=base_rate + penalty_premium,
            covenants=covenants
        )

    def service_debt(self, current_tick: int) -> List[Transaction]:
        """
        Manages the servicing of outstanding government debt using DebtServicingEngine.
        """
        self.ledger.current_tick = current_tick
        result = self.debt_servicing_engine.service_all_debt(self.ledger)
        self.ledger = result.updated_ledger
        return result.generated_transactions
