from typing import List, Any, Optional, override, TYPE_CHECKING
import logging

from simulation.models import Order, Transaction
from simulation.core_markets import Market
from modules.finance.api import IBankService, LoanNotFoundError, LoanRepaymentError, BorrowerProfileDTO
from modules.housing.dtos import MortgageApprovalDTO
# Import from new API
from modules.market.housing_planner_api import ILoanMarket, MortgageApplicationDTO

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
        """
        # 1. LTV Check
        prop_value = application['property_value']
        principal = application['principal']
        if prop_value <= 0:
             return False

        ltv = principal / prop_value

        # Config access
        housing_config = getattr(self.config_module, 'housing', None)
        max_ltv = 0.8
        max_dti = 0.43

        if housing_config:
             if isinstance(housing_config, dict):
                 max_ltv = housing_config.get('max_ltv', 0.8)
                 max_dti = housing_config.get('max_dti', 0.43)
             else:
                 max_ltv = getattr(housing_config, 'max_ltv', 0.8)
                 max_dti = getattr(housing_config, 'max_dti', 0.43)

        if ltv > max_ltv:
             logger.info(f"LOAN_DENIED | LTV {ltv:.2f} > {max_ltv}")
             return False

        # 2. DTI Check
        applicant_id = application['applicant_id']
        annual_income = application.get('applicant_income', 0.0)
        existing_debt = application.get('applicant_existing_debt', 0.0)
        loan_term = application.get('loan_term', 360)

        # Get Interest Rate
        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate() # Annual
        else:
             interest_rate = getattr(self.config_module, 'DEFAULT_MORTGAGE_INTEREST_RATE', 0.05)

        # Calculate Payment
        # Monthly Payment for DTI
        monthly_rate = interest_rate / 12.0
        if monthly_rate == 0:
             new_payment = principal / loan_term
        else:
             new_payment = principal * (monthly_rate * (1 + monthly_rate)**loan_term) / ((1 + monthly_rate)**loan_term - 1)

        # Estimate Existing Debt Payment
        # Assuming existing debt is serviced at similar rate or we approximate.
        # Ideally we fetch exact debt status, but here we use passed DTO value if available.
        # But DTI is typically calculated on monthly gross income vs total monthly debt payments.
        # If 'applicant_existing_debt' is TOTAL principal, we need to estimate payment.

        # Use existing Bank query to get accurate debt payments if possible
        # But 'evaluate' is supposed to be fast/pure-ish.
        # Let's rely on Bank service for debt status if we want accuracy.

        existing_payment = 0.0
        try:
             debt_status = self.bank.get_debt_status(str(applicant_id))
             # We can sum up 'outstanding_balance' * interest?
             # LoanInfoDTO doesn't have monthly payment.
             # So we approximate.
             for l in debt_status['loans']:
                 r = l['interest_rate'] / 12.0
                 if r == 0:
                     payment = l['outstanding_balance'] / 360 # Assume 30y remaining
                 else:
                     payment = l['outstanding_balance'] * r # Interest Only approx?
                 existing_payment += payment
        except Exception:
             # Fallback to DTO passed value as principal estimate
             if monthly_rate == 0:
                  existing_payment = existing_debt / 360
             else:
                  existing_payment = existing_debt * monthly_rate

        total_monthly_obligation = existing_payment + new_payment
        monthly_income = annual_income / 12.0

        if monthly_income <= 0:
             dti = float('inf')
        else:
             dti = total_monthly_obligation / monthly_income

        if dti > max_dti:
             logger.info(f"LOAN_DENIED | DTI {dti:.2f} > {max_dti}")
             return False

        return True

    def stage_mortgage(self, application: MortgageApplicationDTO) -> Optional[int]:
        """
        Stages a mortgage (creates loan record) without disbursing funds.
        Returns loan_id if successful, None otherwise.
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

        due_tick = None # Let Bank decide or pass if needed. DTO has loan_term.
        # If DTO has loan_term, we can calculate due_tick if we knew current tick.
        # But we don't have current tick here easily unless passed.
        # Bank.stage_loan takes due_tick.
        # Bank.stage_loan uses current_tick_tracker if due_tick is None.

        loan_info = self.bank.stage_loan(
            borrower_id=str(application['applicant_id']),
            amount=application['principal'],
            interest_rate=interest_rate,
            due_tick=None, # Bank defaults using term
            borrower_profile=None # Could construct from application
        )

        if loan_info:
             # Extract int ID
             try:
                 loan_id_int = int(loan_info['loan_id'].split('_')[1])
             except (IndexError, ValueError):
                 loan_id_int = hash(loan_info['loan_id']) % 10000000
             return loan_id_int

        return None

    def request_mortgage(self, application: MortgageApplicationDTO, household_agent: Any = None, current_tick: int = 0) -> Optional[MortgageApprovalDTO]:
        """
        Legacy/Compat method.
        Calls evaluate, then Bank.grant_loan (Full execution).
        """
        if not self.evaluate_mortgage_application(application):
            return None

        # Execute
        principal = application['principal']
        applicant_id = application['applicant_id']
        loan_term = application.get('loan_term', 360)

        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate()
        else:
             interest_rate = 0.05

        due_tick = current_tick + loan_term

        grant_result = self.bank.grant_loan(
            borrower_id=str(applicant_id),
            amount=principal,
            interest_rate=interest_rate,
            due_tick=due_tick
        )

        if grant_result:
             loan_info, _ = grant_result

             try:
                 loan_id_int = int(loan_info['loan_id'].split('_')[1])
             except (IndexError, ValueError):
                 loan_id_int = hash(loan_info['loan_id']) % 10000000

             # Recalculate monthly payment for DTO
             monthly_rate = interest_rate / 12.0
             if monthly_rate == 0:
                 pmt = principal / loan_term
             else:
                 pmt = principal * (monthly_rate * (1 + monthly_rate)**loan_term) / ((1 + monthly_rate)**loan_term - 1)

             return MortgageApprovalDTO(
                 loan_id=loan_id_int,
                 approved_principal=loan_info['original_amount'],
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
                borrower_id=str(order.agent_id),
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
                    f"Loan granted to {order.agent_id} for {loan_amount:.2f}. Loan ID: {loan_info['loan_id']}",
                    extra={**log_extra, "loan_id": loan_info['loan_id']},
                )
            else:
                logger.warning(
                    f"Loan denied for {order.agent_id} for {loan_amount:.2f}.",
                    extra=log_extra,
                )

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount = order.quantity

            try:
                success = self.bank.repay_loan(loan_id, repay_amount)
                if success:
                    transactions.append(
                        Transaction(
                            item_id="loan_repaid",
                            quantity=repay_amount,
                            price=1.0,
                            buyer_id=order.agent_id,
                            seller_id=self.bank.id,
                            transaction_type="loan",
                            time=current_tick,
                            market_id=self.id,
                        )
                    )
                    logger.info(
                        f"Repayment of {repay_amount:.2f} processed for loan {loan_id} by {order.agent_id}.",
                        extra={**log_extra, "loan_id": loan_id},
                    )
            except (LoanNotFoundError, LoanRepaymentError) as e:
                logger.warning(f"Repayment failed for loan {loan_id}: {e}", extra=log_extra)

        elif order.order_type == "DEPOSIT":
            amount = order.quantity
            if hasattr(self.bank, "deposit_from_customer"):
                deposit_id = self.bank.deposit_from_customer(order.agent_id, amount) # type: ignore

                if deposit_id:
                    transactions.append(
                        Transaction(
                            item_id="deposit",
                            quantity=amount,
                            price=1.0,
                            buyer_id=order.agent_id,
                            seller_id=self.bank.id,
                            transaction_type="deposit",
                            time=current_tick,
                            market_id=self.id,
                        )
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
            amount = order.quantity
            if hasattr(self.bank, "withdraw_for_customer"):
                success = self.bank.withdraw_for_customer(order.agent_id, amount) # type: ignore

                if success:
                    transactions.append(
                        Transaction(
                            item_id="withdrawal",
                            quantity=amount,
                            price=1.0,
                            buyer_id=self.bank.id,
                            seller_id=order.agent_id,
                            transaction_type="withdrawal",
                            time=current_tick,
                            market_id=self.id,
                        )
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
