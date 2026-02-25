import logging
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import math
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import (
    IBank,
    LoanDTO,
    DebtStatusDTO,
    BorrowerProfileDTO,
    IFinancialEntity,
    IFinancialAgent,
    IFinanceSystem,
    FloatIncursionError
)
from modules.simulation.api import AgentID
from modules.system.api import CurrencyCode, DEFAULT_CURRENCY, ICurrencyHolder
from modules.finance.wallet.wallet import Wallet # Keep for now as internal cache or legacy
from modules.finance.wallet.api import IWallet
from modules.system.event_bus.api import IEventBus
from modules.events.dtos import LoanDefaultedEvent
from simulation.models import Transaction
from dataclasses import replace, is_dataclass

if TYPE_CHECKING:
    from simulation.finance.api import ISettlementSystem
    from simulation.agents.government import Government

logger = logging.getLogger(__name__)

# Default fallbacks
_DEFAULT_TICKS_PER_YEAR = 365.0
_DEFAULT_INITIAL_BASE_ANNUAL_RATE = 0.03

class Bank(IBank, ICurrencyHolder, IFinancialEntity):
    """
    Refactored Bank Agent (Stateless Wrapper).
    Delegates all financial logic to FinanceSystem (FinancialLedgerDTO).
    """

    def __init__(self, id: AgentID, initial_assets: float, config_manager: ConfigManager,
                 shareholder_registry: Any = None,
                 settlement_system: Optional["ISettlementSystem"] = None,
                 credit_scoring_service: Any = None,
                 event_bus: Optional[IEventBus] = None):
        self._id = id
        self.config_manager = config_manager
        self.settlement_system = settlement_system
        self.credit_scoring_service = credit_scoring_service
        self.shareholder_registry = shareholder_registry
        self.event_bus = event_bus
        self.government: Optional["Government"] = None
        self.finance_system: Optional[IFinanceSystem] = None

        # internal wallet mostly for legacy interface compatibility until fully removed
        initial_balance_dict = {}
        if isinstance(initial_assets, dict):
            for k, v in initial_assets.items():
                initial_balance_dict[k] = int(v)
        else:
            initial_balance_dict[DEFAULT_CURRENCY] = int(initial_assets)
        self._wallet = Wallet(self.id, initial_balance_dict)

        self.ticks_per_year = self._get_config("finance.ticks_per_year", _DEFAULT_TICKS_PER_YEAR)
        initial_rate = self._get_config("finance.bank_defaults.initial_base_annual_rate", _DEFAULT_INITIAL_BASE_ANNUAL_RATE)
        self.base_rate = self._get_config("bank.initial_base_annual_rate", initial_rate)

        self.current_tick_tracker = 0
        self.value_orientation = "N/A"
        self.needs: Dict[str, float] = {}

        logger.info(f"Bank {self.id} initialized (Stateless Proxy).")

    @property
    def id(self) -> AgentID:
        return self._id

    @id.setter
    def id(self, value: AgentID):
        self._id = value

    @property
    def wallet(self) -> IWallet:
        # Warning: Direct wallet access is deprecated
        return self._wallet

    def set_finance_system(self, finance_system: IFinanceSystem) -> None:
        self.finance_system = finance_system

    # --- IFinancialEntity Implementation ---

    @property
    def balance_pennies(self) -> int:
        return self._wallet.get_balance(DEFAULT_CURRENCY)

    def deposit(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        # Bank's own funds
        self._wallet.add(amount_pennies, currency, memo="Deposit")

    def withdraw(self, amount_pennies: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._wallet.subtract(amount_pennies, currency, memo="Withdraw")

    # --- IFinancialAgent Implementation ---

    def _deposit(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        # Bank's own funds
        self._wallet.add(amount, currency, memo="Deposit")

    def _withdraw(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self._wallet.subtract(amount, currency, memo="Withdraw")

    def get_balance(self, currency: CurrencyCode = DEFAULT_CURRENCY) -> int:
        # SSoT is the Wallet
        return self._wallet.get_balance(currency)

    def get_all_balances(self) -> Dict[CurrencyCode, int]:
        return self._wallet.get_all_balances()

    @property
    def total_wealth(self) -> int:
        return sum(self._wallet.get_all_balances().values())

    def get_liquid_assets(self, currency: CurrencyCode = "USD") -> int:
        return self.get_balance(currency)

    def get_total_debt(self) -> int:
        return 0 # Banks usually have liabilities (deposits), not debt in this context

    # --- ICurrencyHolder Implementation ---

    def get_assets_by_currency(self) -> Dict[CurrencyCode, int]:
        return self.get_all_balances()

    def _internal_add_assets(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.deposit(amount, currency)

    def _internal_sub_assets(self, amount: int, currency: CurrencyCode = DEFAULT_CURRENCY) -> None:
        self.withdraw(amount, currency)

    def get_interest_rate(self) -> float:
        return self.base_rate

    def _get_config(self, key: str, default: Any) -> Any:
        return self.config_manager.get(key, default)

    def set_government(self, government: "Government") -> None:
        self.government = government

    def update_base_rate(self, new_rate: float):
        self.base_rate = new_rate

    # --- IBank Implementation ---

    def grant_loan(self, borrower_id: int, amount: int, interest_rate: float, due_tick: int = 0, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[Tuple[LoanDTO, Transaction]]:
        if isinstance(amount, float):
             raise FloatIncursionError(f"Bank.grant_loan requires integer amount (pennies). Got float: {amount}")
        if not isinstance(amount, int):
             raise TypeError(f"Bank.grant_loan requires integer amount (pennies). Got {type(amount)}: {amount}")

        # Resolve borrower object vs ID
        borrower_obj = None
        borrower_agent_id = borrower_id

        # Check if borrower_id is actually an agent object (duck typing or protocol check)
        if hasattr(borrower_id, 'id'):
             borrower_obj = borrower_id
             borrower_agent_id = borrower_id.id

        if not self.finance_system:
            logger.error("Bank: FinanceSystem not set. Cannot grant loan.")
            return None

        if not hasattr(self.finance_system, 'process_loan_application'):
            logger.error("Bank: FinanceSystem missing process_loan_application.")
            return None

        # Enhance profile with preferred lender (self)
        if borrower_profile and is_dataclass(borrower_profile):
            profile = borrower_profile
        elif isinstance(borrower_profile, dict):
            # Convert dict to BorrowerProfileDTO
            # Helper to safely extract int fields
            def safe_int(val):
                try:
                    return int(val) if val is not None else 0
                except (ValueError, TypeError):
                    return 0

            # MIGRATION: Updated to new BorrowerProfileDTO signature
            profile = BorrowerProfileDTO(
                borrower_id=AgentID(int(borrower_agent_id)), # Ensure AgentID
                gross_income=safe_int(borrower_profile.get('gross_income', 0)),
                existing_debt_payments=safe_int(borrower_profile.get('existing_debt_payments', 0)),
                collateral_value=safe_int(borrower_profile.get('collateral_value', 0)),
                credit_score=borrower_profile.get('credit_score'),
                employment_status=borrower_profile.get('employment_status', "UNKNOWN"),
                preferred_lender_id=borrower_profile.get('preferred_lender_id')
            )
        else:
            # Fallback: create empty/default DTO
            profile = BorrowerProfileDTO(
                borrower_id=AgentID(int(borrower_agent_id)),
                gross_income=0,
                existing_debt_payments=0,
                collateral_value=0,
                employment_status="UNKNOWN"
            )

        # Call FinanceSystem
        loan_dto, txs = self.finance_system.process_loan_application(
            borrower_id=borrower_agent_id,
            amount=amount,
            borrower_profile=profile,
            current_tick=self.current_tick_tracker
        )

        if not loan_dto:
            return None

        # Strict DTO enforcement: loan_dto must be an object (dataclass)
        if isinstance(loan_dto, dict):
             logger.error("FinanceSystem returned a dict instead of LoanDTO! This violates DTO purity.")
             return None

        # Extract credit creation tx and EXECUTE settlement
        credit_tx = None
        for tx in txs:
            if tx.transaction_type == "credit_creation":
                credit_tx = tx
                break

        # Execute the transfer (Wallet Update) to match Ledger Update
        # Bank transfers to Borrower. M2 increases (because Bank balance is subtracted from M2).
        if self.settlement_system:
             if borrower_obj:
                 # We use 'transfer' effectively swapping Reserves (Bank) for Deposit (Borrower).
                 # If Bank runs out of Reserves, it stops lending (Capital Constraint).
                 tx = self.settlement_system.transfer(
                     self,
                     borrower_obj, # Target Object
                     amount,
                     memo=f"loan_disbursement_{loan_dto.loan_id}",
                     currency=DEFAULT_CURRENCY
                 )

                 # Record M2 Expansion (Credit Creation)
                 # Only record if transfer succeeded (tx is not None)
                 if tx and self.settlement_system.monetary_ledger:
                     self.settlement_system.monetary_ledger.record_monetary_expansion(
                         amount,
                         source=f"credit_creation_loan_{loan_dto.loan_id}",
                         currency=DEFAULT_CURRENCY
                     )
             else:
                 logger.warning(f"Bank {self.id} cannot transfer loan funds: Borrower object not provided for ID {borrower_agent_id}")

        return loan_dto, credit_tx

    def stage_loan(self, borrower_id: AgentID, amount: int, interest_rate: float, due_tick: Optional[int] = None, borrower_profile: Optional[BorrowerProfileDTO] = None) -> Optional[LoanDTO]:
        # Implementation of stage_loan (without booking) is harder with pure stateless engines
        # skipping strictly "staging" or implementing as a Dry Run.
        # For now, return None or Mock it.
        logger.warning("Bank.stage_loan not fully supported in stateless mode yet.")
        return None

    def close_account(self, agent_id: AgentID) -> int:
        if self.finance_system:
             # Requires FinanceSystem update (Phase 4.1)
             try:
                 balance = self.finance_system.close_deposit_account(self.id, agent_id)
                 if self.settlement_system:
                     self.settlement_system.deregister_account(self.id, agent_id)
                 return balance
             except AttributeError:
                 logger.error("FinanceSystem missing close_deposit_account")
        return 0

    def repay_loan(self, loan_id: str, amount: int) -> int:
        # Updates ledger only. Money transfer assumed handled by caller.
        repaid_amount = 0
        if self.finance_system:
            try:
                repaid_amount = self.finance_system.record_loan_repayment(loan_id, amount)
            except AttributeError:
                logger.error("FinanceSystem missing record_loan_repayment")

        if repaid_amount > 0 and self.settlement_system and self.settlement_system.monetary_ledger:
             self.settlement_system.monetary_ledger.record_monetary_contraction(
                 repaid_amount,
                 source=f"credit_destruction_repayment_{loan_id}",
                 currency=DEFAULT_CURRENCY
             )

        return repaid_amount

    def receive_repayment(self, borrower_id: AgentID, amount: int) -> int:
        # Generic repayment application.
        repaid_amount = 0
        if self.finance_system:
            try:
                repaid_amount = self.finance_system.repay_any_debt(borrower_id, amount)
            except AttributeError:
                 logger.error("FinanceSystem missing repay_any_debt")

        if repaid_amount > 0 and self.settlement_system and self.settlement_system.monetary_ledger:
             # Contraction recorded here as well since repay_any_debt also reduces principal
             # Note: If repay_any_debt calls record_loan_repayment internally in FinanceSystem, we might double count
             # IF we added it there. But we removed it from FinanceSystem.
             # AND repay_any_debt iterates loans.
             # Wait, does repay_any_debt return total applied? Yes.
             # But if repay_any_debt just updates ledger, we should record contraction here.
             self.settlement_system.monetary_ledger.record_monetary_contraction(
                 repaid_amount,
                 source=f"credit_destruction_repayment_any_{borrower_id}",
                 currency=DEFAULT_CURRENCY
             )

        return repaid_amount

    def get_customer_balance(self, agent_id: AgentID) -> int:
        if self.finance_system:
            try:
                return self.finance_system.get_customer_balance(self.id, agent_id)
            except AttributeError:
                pass
        return 0

    def get_debt_status(self, borrower_id: AgentID) -> DebtStatusDTO:
        if self.finance_system:
            try:
                 loans = self.finance_system.get_customer_debt_status(self.id, borrower_id)
                 # UPDATED: Use outstanding_balance (float) per new DTO spec
                 total_debt = int(sum(l.outstanding_balance for l in loans) * 100) # Convert back to pennies for total? No, outstanding_balance is float.
                 # Wait, total_outstanding_pennies should be int.
                 # loans has remaining_principal_pennies.
                 total_debt_pennies = sum(l.remaining_principal_pennies for l in loans)

                 return DebtStatusDTO(
                     borrower_id=AgentID(int(borrower_id)),
                     total_outstanding_pennies=total_debt_pennies,
                     loans=loans,
                     is_insolvent=False,
                     next_payment_pennies=0,
                     next_payment_tick=0
                 )
            except AttributeError:
                pass
        return DebtStatusDTO(
            borrower_id=AgentID(int(borrower_id)),
            total_outstanding_pennies=0,
            loans=[],
            is_insolvent=False,
            next_payment_pennies=0,
            next_payment_tick=0
        )

    def terminate_loan(self, loan_id: str) -> Optional["Transaction"]:
        return None

    def withdraw_for_customer(self, agent_id: AgentID, amount: int) -> bool:
        if self.finance_system:
            try:
                 if self.id in self.finance_system.ledger.banks:
                     dep_id = f"DEP_{agent_id}_{self.id}"
                     bank_state = self.finance_system.ledger.banks[self.id]
                     if dep_id in bank_state.deposits:
                         if bank_state.deposits[dep_id].balance_pennies >= amount:
                             bank_state.deposits[dep_id].balance_pennies -= amount
                             return True
            except AttributeError:
                pass
        return False

    def get_total_deposits(self) -> int:
        # Sum from Ledger
        if self.finance_system:
            try:
                 if self.id in self.finance_system.ledger.banks:
                     deposits = self.finance_system.ledger.banks[self.id].deposits
                     return sum(d.balance_pennies for d in deposits.values())
            except AttributeError:
                pass
        return 0

    # --- Agent Lifecycle ---

    def run_tick(self, agents_dict: Dict[AgentID, Any], current_tick: int = 0) -> List[Transaction]:
        self.current_tick_tracker = current_tick

        # Trigger Finance System Service Debt
        # NOTE: If multiple banks exist, this might be called multiple times.
        # Assuming FinanceSystem handles idempotency or single bank scenario for now.

        txs = []
        if self.finance_system:
             try:
                 debt_txs = self.finance_system.service_debt(current_tick)
                 txs.extend(debt_txs)
             except AttributeError:
                 logger.error("FinanceSystem missing service_debt")

        return txs

    # --- Legacy Methods Wrappers ---
    def deposit_from_customer(self, depositor_id: AgentID, amount: float, currency: CurrencyCode = DEFAULT_CURRENCY) -> Optional[str]:
        # Used by tests mostly
        # We need to manually update Ledger to simulate deposit
        if self.finance_system:
            try:
                 if self.id in self.finance_system.ledger.banks:
                     dep_id = f"DEP_{depositor_id}_{self.id}"
                     bank_state = self.finance_system.ledger.banks[self.id]
                     from modules.finance.engine_api import DepositStateDTO
                     if dep_id not in bank_state.deposits:
                         # Correct instantiation for DepositDTO
                         bank_state.deposits[dep_id] = DepositStateDTO(
                             owner_id=depositor_id,
                             balance_pennies=0,
                             interest_rate=0.0,
                             deposit_id=dep_id,
                             currency=currency
                         )
                         # TD-INT-STRESS-SCALE: Sync SettlementSystem Reverse Index
                         if self.settlement_system:
                             self.settlement_system.register_account(self.id, depositor_id)
                     bank_state.deposits[dep_id].balance_pennies += int(amount)
                     return dep_id
            except AttributeError:
                pass
        return None
