from typing import List, Any, Optional, override, TYPE_CHECKING, Literal
import logging

from simulation.models import Order, Transaction
from simulation.core_markets import Market
from modules.finance.api import IBankService, LoanNotFoundError, LoanRepaymentError, BorrowerProfileDTO
from modules.housing.dtos import MortgageApprovalDTO
# Import from new API
from modules.market.housing_planner_api import ILoanMarket
from modules.finance.api import MortgageApplicationDTO
from modules.finance.api import LoanInfoDTO
from modules.simulation.api import AgentID

if TYPE_CHECKING:
    from simulation.bank import Bank # For legacy casting if needed

logger = logging.getLogger(__name__)


class LoanMarket(Market, ILoanMarket):
    """
    Handles loan requests and repayments via the IBankService interface.
    Refactored to decouple from concrete Bank implementation.
    Implements ILoanMarket for housing pipeline (Phase 32).
    """

    def __init__(self, market_id: str, bank: IBankService, config_module: Any):
        super().__init__(market_id=market_id)
        self.id = market_id
        self.bank = bank  # Interface dependency
        self.config_module = config_module
        self.loan_requests: List[Order] = []
        self.repayment_requests: List[Order] = []

        logger.info(
            f"LoanMarket {market_id} initialized with bank service: {bank.id}",
            extra={
                "tick": 0,
                "market_id": self.id,
                "agent_id": bank.id,
                "tags": ["init", "market"],
            },
        )

    def evaluate_mortgage_application(self, application: MortgageApplicationDTO) -> bool:
        """
        Performs hard LTV/DTI checks. Returns True if approved, False if rejected.
        Implements ILoanMarket.evaluate_mortgage_application.
        Uses [TD-206] MortgageApplicationDTO for precise DTI calculation.
        """
        # Canonical Keys from loan_api:
        # requested_principal, property_value, applicant_monthly_income, existing_monthly_debt_payments

        principal = application.requested_principal
        prop_value = application.property_value

        if prop_value <= 0:
             logger.warning(f"LOAN_DENIED | Invalid property value {prop_value}")
             return False

        # 1. LTV Check
        ltv = principal / prop_value

        # Config access (support both object and dict)
        max_ltv = 0.8
        max_dti = 0.43

        # Check 'regulations' section first (New Spec)
        regulations = getattr(self.config_module, 'regulations', None)
        if regulations:
             if isinstance(regulations, dict):
                 max_ltv = regulations.get('max_ltv_ratio', max_ltv)
                 max_dti = regulations.get('max_dti_ratio', max_dti)
             else:
                 max_ltv = getattr(regulations, 'max_ltv_ratio', max_ltv)
                 max_dti = getattr(regulations, 'max_dti_ratio', max_dti)
        else:
             # Fallback to 'housing' section (Legacy)
             housing_config = getattr(self.config_module, 'housing', None)
             if housing_config:
                 if isinstance(housing_config, dict):
                     max_ltv = housing_config.get('max_ltv', max_ltv)
                     max_dti = housing_config.get('max_dti', max_dti)
                 else:
                     max_ltv = getattr(housing_config, 'max_ltv', max_ltv)
                     max_dti = getattr(housing_config, 'max_dti', max_dti)

        if ltv > max_ltv:
             logger.info(f"LOAN_DENIED | LTV {ltv:.2f} > {max_ltv}")
             return False

        # 2. DTI Check
        applicant_id = application.applicant_id

        # TD-206: Use precise monthly income and existing payments
        monthly_income = application.applicant_monthly_income
        existing_payment = application.existing_monthly_debt_payments

        loan_term = application.loan_term

        # Get Interest Rate
        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate() # Annual
        else:
             interest_rate = getattr(self.config_module, 'DEFAULT_MORTGAGE_INTEREST_RATE', 0.05)

        # Calculate Payment for NEW loan
        monthly_rate = interest_rate / 12.0
        if monthly_rate == 0:
             new_payment = principal / loan_term
        else:
             new_payment = principal * (monthly_rate * (1 + monthly_rate)**loan_term) / ((1 + monthly_rate)**loan_term - 1)

        total_monthly_obligation = existing_payment + new_payment

        if monthly_income <= 0:
             dti = float('inf')
        else:
             dti = total_monthly_obligation / monthly_income

        if dti > max_dti:
             logger.info(f"LOAN_DENIED | DTI {dti:.2f} > {max_dti}")
             return False

        return True

    def apply_for_mortgage(self, application: MortgageApplicationDTO) -> Optional[LoanInfoDTO]:
        """
        Processes a mortgage application with regulatory checks.
        Returns LoanInfoDTO if approved, None otherwise.
        """
        return self.stage_mortgage(application)

    def stage_mortgage_application(self, application: MortgageApplicationDTO) -> Optional[str]:
        """
        Submits an application for asynchronous credit check.
        Returns a unique `staged_loan_id` for tracking, or None if invalid.
        Implements ILoanMarket (Saga) interface.
        """
        # 1. Evaluate
        if not self.evaluate_mortgage_application(application):
            return None

        # 2. Stage Loan via Bank
        # Get Interest Rate
        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate() # Annual
        else:
             interest_rate = getattr(self.config_module, 'DEFAULT_MORTGAGE_INTEREST_RATE', 0.05)

        principal = application.requested_principal

        loan_info = self.bank.stage_loan(
            borrower_id=application.applicant_id,
            amount=principal,
            interest_rate=interest_rate,
            due_tick=None, # Bank defaults using term
            borrower_profile=None # Could construct from application
        )

        if loan_info:
            return loan_info.loan_id
        return None

    def stage_mortgage(self, application: MortgageApplicationDTO) -> Optional[LoanInfoDTO]:
        """
        Legacy/Compat method.
        Stages a mortgage (creates loan record) without disbursing funds.
        Returns LoanInfoDTO if successful, None otherwise.
        """
        loan_id = self.stage_mortgage_application(application)
        if loan_id:
            return self.convert_staged_to_loan(loan_id)
        return None

    def check_staged_application_status(self, staged_loan_id: str) -> Literal["PENDING", "APPROVED", "REJECTED"]:
        """Checks the status of a pending mortgage application."""
        # Check if loan exists in Bank
        if hasattr(self.bank, 'loans') and staged_loan_id in self.bank.loans:
             return "APPROVED"
        return "REJECTED"

    def convert_staged_to_loan(self, staged_loan_id: str) -> Optional[LoanInfoDTO]:
        """
        Finalizes an approved application.
        Returns LoanInfoDTO object.
        """
        if hasattr(self.bank, 'loans') and staged_loan_id in self.bank.loans:
             loan = self.bank.loans[staged_loan_id]
             # MIGRATION: Ensure DTO purity by returning object.
             # loan is LoanStateDTO (pennies). LoanInfoDTO expects Dollars (float).
             return LoanInfoDTO(
                 loan_id=staged_loan_id,
                 borrower_id=int(loan.borrower_id),
                 original_amount=float(loan.principal_pennies) / 100.0,
                 outstanding_balance=float(loan.remaining_principal_pennies) / 100.0,
                 interest_rate=float(loan.interest_rate),
                 origination_tick=int(loan.origination_tick),
                 due_tick=int(loan.start_tick + loan.term_ticks),
                 lender_id=int(self.bank.id) if hasattr(self.bank, 'id') else None,
                 term_ticks=int(loan.term_ticks)
             )
        return None

    def void_staged_application(self, staged_loan_id: str) -> bool:
        """Cancels a pending or approved application."""
        if hasattr(self.bank, 'terminate_loan'):
             self.bank.terminate_loan(staged_loan_id)
             return True
        return False

    def request_mortgage(self, application: MortgageApplicationDTO, household_agent: Any = None, current_tick: int = 0) -> Optional[MortgageApprovalDTO]:
        """
        Legacy/Compat method.
        Calls evaluate, then Bank.grant_loan (Full execution).
        """
        if not self.evaluate_mortgage_application(application):
            return None

        # Execute
        principal = application.requested_principal
        applicant_id = application.applicant_id
        loan_term = application.loan_term

        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate()
        else:
             interest_rate = 0.05

        due_tick = current_tick + loan_term

        grant_result = self.bank.grant_loan(
            borrower_id=applicant_id,
            amount=principal,
            interest_rate=interest_rate,
            due_tick=due_tick
        )

        if grant_result:
             loan_info, _ = grant_result

             try:
                 loan_id_int = int(loan_info.loan_id.split('_')[1])
             except (IndexError, ValueError):
                 loan_id_int = hash(loan_info.loan_id) % 10000000

             # Recalculate monthly payment for DTO
             monthly_rate = interest_rate / 12.0
             if monthly_rate == 0:
                 pmt = principal / loan_term
             else:
                 pmt = principal * (monthly_rate * (1 + monthly_rate)**loan_term) / ((1 + monthly_rate)**loan_term - 1)

             return MortgageApprovalDTO(
                 loan_id=loan_id_int,
                 approved_principal=loan_info.original_amount,
                 monthly_payment=pmt
             )

        return None

    def place_order(self, order: Order, current_tick: int) -> List[Transaction]:
        """Submits a loan request or repayment order to the bank service."""
        transactions: List[Transaction] = []
        log_extra = {
            "tick": current_tick,
            "market_id": self.id,
            "agent_id": order.agent_id,
            "order_type": order.order_type,
            "item_id": order.item_id,
            "quantity": order.quantity,
            "price": order.price,
        }
        logger.info(
            f"Order placed: Type={order.order_type}, Item={order.item_id}, Agent={order.agent_id}, Amount={order.quantity}",
            extra=log_extra,
        )

        if order.order_type == "LOAN_REQUEST":
            # Direct loan request via Order (Legacy or different path)
            # Use grant_loan directly as this bypasses the detailed MortgageApplication DTO usually.

            loan_amount = order.quantity
            interest_rate = order.price

            duration = getattr(self.config_module, "DEFAULT_LOAN_TERM_TICKS", 50)
            due_tick = current_tick + duration

            borrower_profile = None
            if order.metadata and "borrower_profile" in order.metadata:
                borrower_profile = order.metadata["borrower_profile"]

            grant_result = self.bank.grant_loan(
                borrower_id=AgentID(order.agent_id),
                amount=loan_amount,
                interest_rate=interest_rate,
                due_tick=due_tick,
                borrower_profile=borrower_profile
            )

            if grant_result:
                loan_info, credit_tx = grant_result
                if credit_tx:
                    transactions.append(credit_tx)

                logger.info(
                    f"Loan granted to {order.agent_id} for {loan_amount:.2f}. Loan ID: {loan_info.loan_id}",
                    extra={**log_extra, "loan_id": loan_info.loan_id},
                )
            else:
                logger.warning(
                    f"Loan denied for {order.agent_id} for {loan_amount:.2f}.",
                    extra=log_extra,
                )

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount_pennies = int(order.quantity * 100) # Assuming Order.quantity is Dollars

            try:
                success = self.bank.repay_loan(loan_id, repay_amount_pennies)
                if success:
                    transactions.append(
                        Transaction(
                            item_id="loan_repaid",
                            quantity=order.quantity,
                            price=1.0,
                            buyer_id=order.agent_id,
                            seller_id=self.bank.id,
                            transaction_type="loan",
                            time=current_tick,
                            market_id=self.id,
                         total_pennies=repay_amount_pennies)
                    )
                    logger.info(
                        f"Repayment of {order.quantity:.2f} processed for loan {loan_id} by {order.agent_id}.",
                        extra={**log_extra, "loan_id": loan_id},
                    )
            except (LoanNotFoundError, LoanRepaymentError) as e:
                logger.warning(f"Repayment failed for loan {loan_id}: {e}", extra=log_extra)

        elif order.order_type == "DEPOSIT":
            amount_pennies = int(order.quantity * 100)
            if hasattr(self.bank, "deposit_from_customer"):
                deposit_id = self.bank.deposit_from_customer(order.agent_id, amount_pennies) # type: ignore

                if deposit_id:
                    transactions.append(
                        Transaction(
                            item_id="deposit",
                            quantity=order.quantity,
                            price=1.0,
                            buyer_id=order.agent_id,
                            seller_id=self.bank.id,
                            transaction_type="deposit",
                            time=current_tick,
                            market_id=self.id,
                         total_pennies=amount_pennies)
                    )
                    logger.info(
                        f"Deposit accepted from {order.agent_id} for {amount:.2f}. Deposit ID: {deposit_id}",
                        extra={**log_extra, "deposit_id": deposit_id},
                    )
                else:
                    logger.warning(f"Deposit failed for {order.agent_id}", extra=log_extra)
            else:
                logger.error("Bank service does not support 'deposit_from_customer'.")

        elif order.order_type == "WITHDRAW":
            amount_pennies = int(order.quantity * 100)
            if hasattr(self.bank, "withdraw_for_customer"):
                success = self.bank.withdraw_for_customer(order.agent_id, amount_pennies) # type: ignore

                if success:
                    transactions.append(
                        Transaction(
                            item_id="withdrawal",
                            quantity=order.quantity,
                            price=1.0,
                            buyer_id=self.bank.id,
                            seller_id=order.agent_id,
                            transaction_type="withdrawal",
                            time=current_tick,
                            market_id=self.id,
                         total_pennies=amount_pennies)
                    )
                    logger.info(
                        f"Withdrawal accepted for {order.agent_id} for {amount:.2f}.",
                        extra=log_extra,
                    )
                else:
                    logger.warning(f"Withdrawal failed for {order.agent_id}", extra=log_extra)
            else:
                 logger.error("Bank service does not support 'withdraw_for_customer'.")

        else:
            logger.warning(f"Unknown order type: {order.order_type}", extra=log_extra)

        return transactions

    def get_total_demand(self) -> float:
        return 0.0

    def get_total_supply(self) -> float:
        return 0.0

    def match_orders(self, current_time: int) -> List[Transaction]:
        return []

    def get_daily_avg_price(self) -> float:
        return 0.0

    def get_daily_volume(self) -> float:
        return 0.0

    @override
    def clear_orders(self) -> None:
        self.matched_transactions = []
