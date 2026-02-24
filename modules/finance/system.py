from typing import List, Dict, Optional, Any, Tuple, Union
import logging
import uuid
from modules.finance.api import (
    IFinanceSystem, BondDTO, BailoutLoanDTO, BailoutCovenant, IFinancialAgent, IFinancialFirm,
    InsufficientFundsError, GrantBailoutCommand, BorrowerProfileDTO, LoanDTO,
    IConfig, IBank, IGovernmentFinance, IMonetaryAuthority, IBankRegistry
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
from modules.finance.registry.bank_registry import BankRegistry

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from simulation.firms import Firm

logger = logging.getLogger(__name__)

# Constants
BAILOUT_CREDIT_SCORE = 850

class FinanceSystem(IFinanceSystem):
    """
    Manages sovereign debt, corporate bailouts, and solvency checks.
    Refactored to use Stateless Engines and FinancialLedgerDTO.
    MIGRATION: Uses integer pennies.
    """

    def __init__(self, government: IGovernmentFinance, central_bank: 'CentralBank', bank: IBank, config_module: IConfig, settlement_system: Optional[IMonetaryAuthority] = None, bank_registry: Optional[IBankRegistry] = None, monetary_authority: Optional[Any] = None):
        self.government = government
        self.central_bank = central_bank
        self.bank = bank
        self.config_module = config_module
        self.settlement_system = settlement_system
        self.monetary_authority = monetary_authority

        self.fiscal_monitor = FiscalMonitor()

        # --- STATELESS ARCHITECTURE ---
        # 1. Initialize Engines
        self.loan_risk_engine = LoanRiskEngine()
        self.loan_booking_engine = LoanBookingEngine()
        self.liquidation_engine = LiquidationEngine()
        self.debt_servicing_engine = DebtServicingEngine()
        self.interest_rate_engine = InterestRateEngine()

        # 2. Initialize Bank Registry
        self.bank_registry = bank_registry or BankRegistry()

        # Ensure initial bank is registered
        if not self.bank_registry.get_bank(bank.id):
            bank_state = BankStateDTO(
                bank_id=bank.id,
                base_rate=bank.base_rate,
                reserves={DEFAULT_CURRENCY: 0}
            )
            self.bank_registry.register_bank(bank_state)

        # 3. Initialize Ledger (Single Source of Truth)
        # We perform a basic sync from the legacy agents to the new ledger
        # The ledger shares the banks dictionary with the registry
        self.ledger = FinancialLedgerDTO(
            current_tick=0,
            treasury=TreasuryStateDTO(government_id=government.id),
            banks=self.bank_registry.banks_dict
        )

        # Sync Initial State (Optimistic) - REMOVED
        # We rely on SSoT (SettlementSystem) and sync on demand.

    def _sync_ledger_balances(self) -> None:
        """Syncs ledger reserves and treasury balance from SettlementSystem (SSoT)."""
        if not self.settlement_system:
            return

        # Sync Bank Reserves
        for bank_state in self.bank_registry.get_all_banks():
            balance = self.settlement_system.get_balance(bank_state.bank_id, DEFAULT_CURRENCY)
            bank_state.reserves[DEFAULT_CURRENCY] = balance

        # Sync Treasury
        gov_id = self.ledger.treasury.government_id
        gov_balance = self.settlement_system.get_balance(gov_id, DEFAULT_CURRENCY)
        self.ledger.treasury.balance[DEFAULT_CURRENCY] = gov_balance

    # --- ORCHESTRATOR METHODS ---

    def process_loan_application(
        self,
        borrower_id: AgentID,
        amount: int,
        borrower_profile: Union[Dict, BorrowerProfileDTO],
        current_tick: int
    ) -> Tuple[Optional[LoanDTO], List[Transaction]]:
        """
        Orchestrates the loan application process using Risk and Booking engines.
        """
        from dataclasses import asdict, is_dataclass
        # Sync SSoT
        self._sync_ledger_balances()

        # 1. Update Ledger Context
        self.ledger.current_tick = current_tick

        # 2. Construct Application DTO
        # Adapter: Convert DTO to Dict for internal engines if needed
        profile_dict = asdict(borrower_profile) if is_dataclass(borrower_profile) else borrower_profile

        # Determine lender (Default to self.bank for now as simpler orchestrator)
        lender_id = profile_dict.get("preferred_lender_id", self.bank.id)

        app_dto = LoanApplicationDTO(
            borrower_id=borrower_id,
            lender_id=lender_id,
            amount_pennies=amount,
            borrower_profile=profile_dict
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

        # Construct LoanDTO for the caller
        # lender_id was set in app_dto
        lender_id = app_dto.lender_id
        if not lender_id:
             # Fallback to first available bank
             all_banks = self.bank_registry.get_all_banks()
             if all_banks:
                 lender_id = all_banks[0].bank_id

        if not lender_id:
            return None, result.generated_transactions

        loan_state = self.bank_registry.get_loan(lender_id, loan_id)

        if not loan_state:
            return None, result.generated_transactions

        # TD-INT-STRESS-SCALE: Sync SettlementSystem Reverse Index
        if self.settlement_system:
             # Using register_account to ensure the borrower is tracked as a depositor
             # since loan creation triggers deposit creation (credit money).
             self.settlement_system.register_account(lender_id, borrower_id)

        # loan_state is already LoanDTO (LoanStateDTO alias)
        return loan_state, result.generated_transactions

    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        """Query the ledger for deposit balance."""
        deposit_id = f"DEP_{customer_id}_{bank_id}"
        deposit = self.bank_registry.get_deposit(bank_id, deposit_id)
        if deposit:
            return deposit.balance_pennies
        return 0

    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> List[LoanDTO]:
        """Query the ledger for loans."""
        loans = []
        bank_state = self.bank_registry.get_bank(bank_id)
        if bank_state:
            for loan in bank_state.loans.values():
                if loan.borrower_id == customer_id and loan.remaining_principal_pennies > 0:
                    loans.append(loan)
        return loans

    def close_deposit_account(self, bank_id: AgentID, agent_id: AgentID) -> int:
        bank_state = self.bank_registry.get_bank(bank_id)
        if bank_state:
            deposit_id = f"DEP_{agent_id}_{bank_id}"
            if deposit_id in bank_state.deposits:
                balance = bank_state.deposits[deposit_id].balance_pennies
                del bank_state.deposits[deposit_id]
                return balance
        return 0

    def record_loan_repayment(self, loan_id: str, amount: int) -> int:
        # Find loan in all banks
        for bank_state in self.bank_registry.get_all_banks():
            if loan_id in bank_state.loans:
                loan = bank_state.loans[loan_id]
                applied = min(amount, loan.remaining_principal_pennies)
                loan.remaining_principal_pennies -= applied
                if loan.remaining_principal_pennies <= 0:
                     loan.remaining_principal_pennies = 0
                return applied
        return 0

    def repay_any_debt(self, borrower_id: AgentID, amount: int) -> int:
        remaining = amount
        total_applied = 0

        loans_to_pay = []
        for bank_state in self.bank_registry.get_all_banks():
            for loan in bank_state.loans.values():
                # Ensure flexible ID matching (int vs str)
                if int(loan.borrower_id) == int(borrower_id) and loan.remaining_principal_pennies > 0:
                    loans_to_pay.append(loan)

        loans_to_pay.sort(key=lambda l: l.due_tick)

        for loan in loans_to_pay:
            if remaining <= 0: break
            applied = min(remaining, loan.remaining_principal_pennies)
            loan.remaining_principal_pennies -= applied
            remaining -= applied
            total_applied += applied

        return total_applied

    # --- IFinanceSystem Implementation ---

    def evaluate_solvency(self, firm: IFinancialFirm, current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
        startup_grace_period = self.config_module.get("economy_params.STARTUP_GRACE_PERIOD_TICKS", 24)
        z_score_threshold = self.config_module.get("economy_params.ALTMAN_Z_SCORE_THRESHOLD", 1.81)

        if firm.age < startup_grace_period:
            monthly_wage_bill = firm.monthly_wage_bill_pennies
            required_runway = monthly_wage_bill * 3
            return firm.balance_pennies >= required_runway
        else:
            # Altman Z-Score for established firms
            # All inputs should be int pennies. Ratios will be same.

            inventory_value_pennies = firm.inventory_value_pennies
            # Capital Stock Value (Estimate: 1 unit = 100 pennies)
            capital_stock_value = firm.capital_stock_units * 100

            # Total Assets = Cash + Inventory + Capital
            total_assets = firm.balance_pennies + capital_stock_value + inventory_value_pennies

            # Working Capital = Current Assets - Current Liabilities
            # Simplified: Cash + Inventory - Debt
            working_capital = (firm.balance_pennies + inventory_value_pennies) - firm.total_debt_pennies

            retained_earnings = firm.retained_earnings_pennies
            average_profit = firm.average_profit_pennies

            z_score = AltmanZScoreCalculator.calculate(
                total_assets=float(total_assets),
                working_capital=float(working_capital),
                retained_earnings=float(retained_earnings),
                average_profit=float(average_profit)
            )
            return z_score > z_score_threshold

    def register_bond(self, bond: BondDTO, owner_id: AgentID) -> None:
        """
        Registers a newly issued bond in the system ledger.
        This does NOT handle money transfer, only state tracking.
        """
        # Ensure ledger is ready
        if not self.ledger or not self.ledger.treasury:
            logger.error("LEDGER_NOT_READY | Cannot register bond.")
            return

        # Create BondStateDTO
        issue_tick = self.ledger.current_tick if self.ledger else 0

        bond_state = BondStateDTO(
            bond_id=bond.id,
            owner_id=owner_id,
            face_value_pennies=bond.face_value,
            yield_rate=bond.yield_rate,
            issue_tick=issue_tick,
            maturity_tick=bond.maturity_date
        )

        self.ledger.treasury.bonds[bond.id] = bond_state
        logger.info(f"BOND_REGISTERED | {bond.id} registered to {owner_id}")

    def issue_treasury_bonds(self, amount: int, current_tick: int) -> Tuple[List[BondDTO], List[Transaction]]:
        """
        Issues new treasury bonds using the new Ledger system (partially).
        NOW SYNCHRONOUS: Executes transfer via SettlementSystem to ensure Agent Wallets are updated.
        """
        # Sync SSoT
        self._sync_ledger_balances()

        # Updates self.ledger.treasury.bonds

        base_rate = self.config_module.get("economy_params.bank.base_rate", 0.03)
        all_banks = self.bank_registry.get_all_banks()
        if all_banks:
            base_rate = all_banks[0].base_rate

        yield_rate = base_rate + 0.01
        bond_maturity = 400

        bond_id = f"BOND_{current_tick}_{len(self.ledger.treasury.bonds)}"

        # Decide Buyer (QE Logic)
        buyer_agent = self.bank
        buyer_id = self.bank.id

        # QE Trigger Check
        qe_threshold = 1.5
        if self.config_module:
             qe_threshold = self.config_module.get("economy_params.QE_DEBT_TO_GDP_THRESHOLD", 1.5)

        current_gdp = 1.0
        if self.government.sensory_data and self.government.sensory_data.current_gdp > 0:
            current_gdp = self.government.sensory_data.current_gdp

        # Use Government's tracked debt or calculate from ledger
        total_debt = self.government.total_debt

        debt_to_gdp = total_debt / current_gdp

        if debt_to_gdp > qe_threshold:
            buyer_agent = self.central_bank
            buyer_id = self.central_bank.id
            logger.info(f"QE_ACTIVATED | Debt/GDP: {debt_to_gdp:.2f} > {qe_threshold}. Buyer: Central Bank")

        # Check funds in Ledger (only for Commercial Bank)
        if buyer_id == self.bank.id:
            bank_reserves = 0
            bank_state = self.bank_registry.get_bank(buyer_id)
            if bank_state:
                bank_reserves = bank_state.reserves.get(DEFAULT_CURRENCY, 0)

            # LLR Intervention Logic
            if bank_reserves < amount and self.monetary_authority:
                if hasattr(self.monetary_authority, 'check_and_provide_liquidity'):
                     # Request Liquidity
                     self.monetary_authority.check_and_provide_liquidity(self.bank, amount)

                     # Re-sync Ledger to reflect new reserves
                     self._sync_ledger_balances()

                     # Re-check Reserves
                     bank_state = self.bank_registry.get_bank(buyer_id)
                     if bank_state:
                         bank_reserves = bank_state.reserves.get(DEFAULT_CURRENCY, 0)

            if bank_reserves < amount:
                 logger.warning(f"BOND_ISSUANCE_SKIPPED | Bank {buyer_id} insufficient reserves: {bank_reserves} < {amount}")
                 return [], []

        # Execute Transfer via SettlementSystem (Synchronous Update of Agent Wallets)
        if self.settlement_system:
            # We must use the agent objects, not just IDs
            seller_agent = self.government

            success = self.settlement_system.transfer(
                buyer_agent,
                seller_agent,
                amount,
                memo=f"bond_purchase_{bond_id}",
                currency=DEFAULT_CURRENCY
            )

            if not success:
                logger.warning(f"BOND_ISSUANCE_FAILED | Settlement transfer failed for amount {amount}. Buyer: {buyer_id}")
                return [], []
        else:
             logger.warning("BOND_ISSUANCE_WARNING | No SettlementSystem attached. Wallet updates skipped.")

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

        # Manual ledger updates for reserves/treasury removed (Dual Write Elimination).
        # Balances are synced from SettlementSystem at start of next operation.

        # Generate Transaction
        tx = Transaction(
            buyer_id=buyer_id,
            seller_id=self.government.id,
            item_id=bond_id,
            quantity=1.0,
            price=amount / 100.0,
            market_id="financial",
            transaction_type="bond_purchase",
            time=current_tick,
            total_pennies=amount
        )

        # Map to BondDTO
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

    def grant_bailout_loan(self, firm: IFinancialFirm, amount: int, current_tick: int) -> Tuple[Optional[LoanDTO], List[Transaction]]:
        """
        Deprecated: Use request_bailout_loan.
        Provided for compatibility with legacy execution engines.
        """
        logger.warning("FinanceSystem.grant_bailout_loan is deprecated. Use request_bailout_loan.")

        command = self.request_bailout_loan(firm, amount)
        if not command:
            return None, []

        # Execute Command Logic (Simulated here since Orchestrator usually handles commands)
        # But we need to return the loan result.

        # 1. Create Loan Application
        # Deprecated flow: We construct a best-effort profile
        # Use new BorrowerProfileDTO with int pennies
        borrower_profile = BorrowerProfileDTO(
            borrower_id=firm.id,
            gross_income=0, # Unknown via IFinancialFirm
            existing_debt_payments=0,
            collateral_value=int(firm.capital_stock_units * 100),
            credit_score=float(BAILOUT_CREDIT_SCORE),
            employment_status="FIRM",
            preferred_lender_id=self.bank.id
        )

        # 2. Process Application
        loan_dto, txs = self.process_loan_application(
            borrower_id=firm.id,
            amount=amount,
            borrower_profile=borrower_profile,
            current_tick=current_tick
        )

        return loan_dto, txs

    def collect_corporate_tax(self, firm: IFinancialAgent, tax_amount: int) -> bool:
        logger.warning("FinanceSystem.collect_corporate_tax called. Should be using Transaction Generation.")
        return False

    def request_bailout_loan(self, firm: IFinancialFirm, amount: int) -> Optional[GrantBailoutCommand]:
        # Sync SSoT
        self._sync_ledger_balances()

        # Enforce Government Budget Constraint (Check Ledger)
        gov_bal = self.ledger.treasury.balance.get(DEFAULT_CURRENCY, 0)

        if gov_bal < amount:
            logger.warning(f"BAILOUT_DENIED | Government insufficient funds: {gov_bal} < {amount}")
            return None

        base_rate = self.config_module.get("economy_params.bank.base_rate", 0.03)
        all_banks = self.bank_registry.get_all_banks()
        if all_banks:
            base_rate = all_banks[0].base_rate

        penalty_premium = self.config_module.get("economy_params.BAILOUT_PENALTY_PREMIUM", 0.05)

        covenants = BailoutCovenant(
            dividends_allowed=False,
            executive_bonus_allowed=False,
            min_employment_level=None
        )

        return GrantBailoutCommand(
            firm_id=firm.id,
            amount=int(amount),
            interest_rate=base_rate + penalty_premium,
            covenants=covenants
        )

    def service_debt(self, current_tick: int) -> List[Transaction]:
        """
        Manages the servicing of outstanding government debt using DebtServicingEngine.
        """
        # Sync SSoT
        self._sync_ledger_balances()

        self.ledger.current_tick = current_tick
        result = self.debt_servicing_engine.service_all_debt(self.ledger)
        self.ledger = result.updated_ledger
        return result.generated_transactions

    @property
    def outstanding_bonds(self) -> List[BondDTO]:
        """
        Legacy compatibility property.
        Returns a list of BondDTOs derived from the ledger state.
        """
        bonds = []
        for bond_id, bond_state in self.ledger.treasury.bonds.items():
            bonds.append(BondDTO(
                id=bond_id,
                issuer="GOVERNMENT",
                face_value=bond_state.face_value_pennies,
                yield_rate=bond_state.yield_rate,
                maturity_date=bond_state.maturity_tick
            ))
        return bonds
