from _typeshed import Incomplete
from modules.analysis.fiscal_monitor import FiscalMonitor as FiscalMonitor
from modules.finance.api import BailoutCovenant as BailoutCovenant, BailoutLoanDTO as BailoutLoanDTO, BondDTO as BondDTO, BorrowerProfileDTO as BorrowerProfileDTO, GrantBailoutCommand as GrantBailoutCommand, IBank as IBank, IBankRegistry as IBankRegistry, IConfig as IConfig, IFinanceSystem as IFinanceSystem, IFinancialAgent as IFinancialAgent, IFinancialFirm as IFinancialFirm, IGovernmentFinance as IGovernmentFinance, IMonetaryAuthority as IMonetaryAuthority, InsufficientFundsError as InsufficientFundsError, LoanDTO as LoanDTO
from modules.finance.domain import AltmanZScoreCalculator as AltmanZScoreCalculator
from modules.finance.engine_api import BankStateDTO as BankStateDTO, BondStateDTO as BondStateDTO, DepositStateDTO as DepositStateDTO, FinancialLedgerDTO as FinancialLedgerDTO, LiquidationRequestDTO as LiquidationRequestDTO, LoanApplicationDTO as LoanApplicationDTO, LoanStateDTO as LoanStateDTO, TreasuryStateDTO as TreasuryStateDTO
from modules.finance.engines.debt_servicing_engine import DebtServicingEngine as DebtServicingEngine
from modules.finance.engines.interest_rate_engine import InterestRateEngine as InterestRateEngine
from modules.finance.engines.liquidation_engine import LiquidationEngine as LiquidationEngine
from modules.finance.engines.loan_booking_engine import LoanBookingEngine as LoanBookingEngine
from modules.finance.engines.loan_risk_engine import LoanRiskEngine as LoanRiskEngine
from modules.finance.registry.bank_registry import BankRegistry as BankRegistry
from modules.simulation.api import AgentID as AgentID, EconomicIndicatorsDTO as EconomicIndicatorsDTO
from modules.system.api import DEFAULT_CURRENCY as DEFAULT_CURRENCY
from simulation.firms import Firm as Firm
from simulation.models import Transaction
from typing import Any

logger: Incomplete
BAILOUT_CREDIT_SCORE: int

class FinanceSystem(IFinanceSystem):
    """
    Manages sovereign debt, corporate bailouts, and solvency checks.
    Refactored to use Stateless Engines and FinancialLedgerDTO.
    MIGRATION: Uses integer pennies.
    """
    government: Incomplete
    central_bank: Incomplete
    bank: Incomplete
    config_module: Incomplete
    settlement_system: Incomplete
    fiscal_monitor: Incomplete
    loan_risk_engine: Incomplete
    loan_booking_engine: Incomplete
    liquidation_engine: Incomplete
    debt_servicing_engine: Incomplete
    interest_rate_engine: Incomplete
    bank_registry: Incomplete
    ledger: Incomplete
    def __init__(self, government: IGovernmentFinance, central_bank: CentralBank, bank: IBank, config_module: IConfig, settlement_system: IMonetaryAuthority | None = None, bank_registry: IBankRegistry | None = None) -> None: ...
    def process_loan_application(self, borrower_id: AgentID, amount: int, borrower_profile: dict | BorrowerProfileDTO, current_tick: int) -> tuple[LoanDTO | None, list[Transaction]]:
        """
        Orchestrates the loan application process using Risk and Booking engines.
        """
    def get_customer_balance(self, bank_id: AgentID, customer_id: AgentID) -> int:
        """Query the ledger for deposit balance."""
    def get_customer_debt_status(self, bank_id: AgentID, customer_id: AgentID) -> list[LoanDTO]:
        """Query the ledger for loans."""
    def close_deposit_account(self, bank_id: AgentID, agent_id: AgentID) -> int: ...
    def record_loan_repayment(self, loan_id: str, amount: int) -> int: ...
    def repay_any_debt(self, borrower_id: AgentID, amount: int) -> int: ...
    def evaluate_solvency(self, firm: IFinancialFirm, current_tick: int) -> bool:
        """Evaluates a firm's solvency to determine bailout eligibility."""
    def register_bond(self, bond: BondDTO, owner_id: AgentID) -> None:
        """
        Registers a newly issued bond in the system ledger.
        This does NOT handle money transfer, only state tracking.
        """
    def issue_treasury_bonds(self, amount: int, current_tick: int) -> tuple[list[BondDTO], list[Transaction]]:
        """
        Issues new treasury bonds using the new Ledger system (partially).
        NOW SYNCHRONOUS: Executes transfer via SettlementSystem to ensure Agent Wallets are updated.
        """
    def issue_treasury_bonds_synchronous(self, issuer: Any, amount_to_raise: int, current_tick: int) -> tuple[bool, list[Transaction]]: ...
    def grant_bailout_loan(self, firm: IFinancialFirm, amount: int, current_tick: int) -> tuple[LoanDTO | None, list[Transaction]]:
        """
        Deprecated: Use request_bailout_loan.
        Provided for compatibility with legacy execution engines.
        """
    def collect_corporate_tax(self, firm: IFinancialAgent, tax_amount: int) -> bool: ...
    def request_bailout_loan(self, firm: IFinancialFirm, amount: int) -> GrantBailoutCommand | None: ...
    def service_debt(self, current_tick: int) -> list[Transaction]:
        """
        Manages the servicing of outstanding government debt using DebtServicingEngine.
        """
    @property
    def outstanding_bonds(self) -> list[BondDTO]:
        """
        Legacy compatibility property.
        Returns a list of BondDTOs derived from the ledger state.
        """
