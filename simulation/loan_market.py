from typing import List, Any, Optional, override, TYPE_CHECKING
import logging

from simulation.models import Order, Transaction
from simulation.core_markets import Market
from modules.finance.api import IBankService, LoanNotFoundError, LoanRepaymentError
from modules.housing.dtos import MortgageApplicationDTO, MortgageApprovalDTO

if TYPE_CHECKING:
    from simulation.bank import Bank # For legacy casting if needed

logger = logging.getLogger(__name__)


class LoanMarket(Market):
    """
    Handles loan requests and repayments via the IBankService interface.
    Refactored to decouple from concrete Bank implementation.
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

    def request_mortgage(self, application: MortgageApplicationDTO, household_agent: Any = None, current_tick: int = 0) -> Optional[MortgageApprovalDTO]:
        """
        Specialized method for handling mortgage applications with LTV/DTI checks.
        Called by HousingTransactionSagaHandler.
        """
        # 1. LTV Check
        prop_value = application['property_value']
        principal = application['principal']
        if prop_value <= 0:
             return None
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
             return None

        # 2. DTI Check
        # Need income and existing debt
        applicant_id = application['applicant_id']

        # Calculate Monthly Payment
        # Get rate
        # Assuming bank.get_interest_rate() exists (it does in Bank implementation, but interface?)
        # IBankService doesn't explicitly mandate get_interest_rate, but Bank implements it.
        # We can default if missing.
        if hasattr(self.bank, 'get_interest_rate'):
             interest_rate = self.bank.get_interest_rate() # Annual
        else:
             interest_rate = getattr(self.config_module, 'DEFAULT_MORTGAGE_INTEREST_RATE', 0.05)

        ticks_per_year = getattr(self.config_module, 'TICKS_PER_YEAR', 100)

        # Mortgage term is usually in ticks or converted.
        # Spec DTO says loan_term (int). Assuming ticks.
        # Payment per tick
        r_tick = interest_rate / ticks_per_year
        n = application['loan_term']

        if r_tick == 0:
            payment_per_tick = principal / n
        else:
            payment_per_tick = principal * (r_tick * (1 + r_tick)**n) / ((1 + r_tick)**n - 1)

        # Income
        income = 0.0
        if household_agent and hasattr(household_agent, 'current_wage'):
             income = household_agent.current_wage

        # Existing Debt Service
        existing_debt_service = 0.0
        try:
            debt_status = self.bank.get_debt_status(str(applicant_id))
            if debt_status and debt_status['loans']:
                 for l in debt_status['loans']:
                     # approximate payment per tick (interest only usually in this sim)
                     rate_per_tick = l['interest_rate'] / ticks_per_year
                     existing_debt_service += l['outstanding_balance'] * rate_per_tick
        except Exception:
             pass

        total_obligation = existing_debt_service + payment_per_tick

        if income <= 0:
             dti = float('inf')
        else:
             dti = total_obligation / income

        if dti > max_dti:
             logger.info(f"LOAN_DENIED | DTI {dti:.2f} > {max_dti}")
             return None

        # 3. Approve
        due_tick = current_tick + application['loan_term']

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
                 loan_id_int = hash(loan_info['loan_id']) % 10000000 # Fallback

             return MortgageApprovalDTO(
                 loan_id=loan_id_int,
                 approved_principal=loan_info['original_amount'],
                 monthly_payment=payment_per_tick
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
            # Credit Jail check omitted as per legacy issues discussed (requires agent instance access)
            # Assuming Bank or Decision Engine handles it, or acceptable limitation for now.

            loan_amount = order.quantity
            interest_rate = order.price # Household's WTP or Market Rate? Bank decides usually.
            # Bank grant_loan uses this as 'interest_rate' param in new interface.

            # Duration (due_tick)
            duration = getattr(self.config_module, "DEFAULT_LOAN_TERM_TICKS", 50)
            due_tick = current_tick + duration

            # WO-078: Extract BorrowerProfile from metadata
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

                # WO-024: Record the credit creation transaction (Monetary)
                # This is the only transaction needed for auditable M2 tracking.
                # The commercial 'loan' transaction (cash transfer) is removed to prevent double-counting (TD-178).
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
            # Legacy Support: IBankService doesn't expose deposit_from_customer.
            # We assume self.bank is the concrete Bank or supports it dynamically.
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
            # Legacy Support
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
