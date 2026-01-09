from typing import List, Any, Optional, override
import logging

from simulation.models import Order, Transaction, Loan # Import Loan
from simulation.bank import Bank
from simulation.core_markets import Market

logger = logging.getLogger(__name__)


class LoanMarket(Market):
    """대출 요청 및 상환을 처리하는 시장"""

    def __init__(self, market_id: str, bank: Bank, config_module: Any):
        super().__init__(market_id=market_id)
        self.id = market_id
        self.bank = bank  # 시장과 연결된 은행 인스턴스
        self.config_module = config_module  # Store config_module
        self.loan_requests: List[Order] = []  # 대출 요청 주문 큐
        self.repayment_requests: List[Order] = []  # 상환 요청 주문 큐
        logger.info(
            f"LoanMarket {market_id} initialized with bank: {bank.id}",
            extra={
                "tick": 0,
                "market_id": self.id,
                "agent_id": bank.id,
                "tags": ["init", "market"],
            },
        )

    def place_order(self, order: Order, current_tick: int) -> List[Transaction]:
        """대출 요청 또는 상환 주문을 시장에 제출합니다."""
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
            # Phase 4: Credit Jail Check via Agent Lookup
            borrower_id = order.agent_id
            is_jailed = False

            if hasattr(self, "agents_ref") and self.agents_ref:
                agent = self.agents_ref.get(borrower_id)
                if agent and hasattr(agent, "credit_frozen_until_tick"):
                    if current_tick < agent.credit_frozen_until_tick:
                        is_jailed = True

            if is_jailed:
                logger.warning(
                    f"LOAN_DENIED | Agent {borrower_id} is in Credit Jail.",
                    extra=log_extra,
                )
                loan_id = None
            else:
                loan_amount = order.quantity
                interest_rate = order.price
                duration = (
                    self.config_module.DEFAULT_LOAN_DURATION
                )
                loan_id = self.bank.grant_loan(
                    borrower_id=order.agent_id,
                    amount=loan_amount,
                    term_ticks=duration
                )

            if loan_id:
                transactions.append(
                    Transaction(
                        item_id="loan_granted",
                        quantity=order.quantity,
                        price=order.price,
                        buyer_id=self.bank.id,
                        seller_id=order.agent_id,
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Loan granted to {order.agent_id} for {order.quantity:.2f}. Loan ID: {loan_id}",
                    extra={**log_extra, "loan_id": loan_id},
                )
            else:
                logger.warning(
                    f"Loan denied for {order.agent_id} for {order.quantity:.2f}.",
                    extra=log_extra,
                )

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount = order.quantity

            # Update Bank State (Principal Reduction) is handled via Transaction normally?
            # Or explicit method?
            # Bank.run_tick handles interest.
            # Repayment logic usually reduces balance.
            # Let's check Bank class for process_repayment method (legacy check)
            # The previous version had `process_repayment`.
            if hasattr(self.bank, "process_repayment"):
                 self.bank.process_repayment(loan_id, repay_amount) # Legacy method if exists
            elif loan_id in self.bank.loans:
                 # Direct update if method missing
                 self.bank.loans[loan_id].remaining_balance -= repay_amount

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

        elif order.order_type == "DEPOSIT":
            amount = order.quantity
            deposit_id = self.bank.deposit(order.agent_id, amount)

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

        elif order.order_type == "WITHDRAW":
            amount = order.quantity
            success = self.bank.withdraw(order.agent_id, amount)

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
            logger.warning(f"Unknown order type: {order.order_type}", extra=log_extra)

        return transactions

    def process_interest(self, current_tick: int) -> List[Transaction]:
        """은행의 이자 처리 로직을 호출합니다."""
        logger.info(
            f"Processing interest for outstanding loans at tick {current_tick}.",
            extra={
                "tick": current_tick,
                "market_id": self.id,
                "tags": ["loan", "interest"],
            },
        )
        interest_transactions = []
        # Updated to use Loan object attributes
        for loan_id, loan in list(self.bank.loans.items()):
            if loan.remaining_balance > 0: # Check balance instead of payments count
                interest_amount = loan.remaining_balance * loan.tick_interest_rate

                interest_transactions.append(
                    Transaction(
                        item_id="interest_payment",
                        quantity=interest_amount,
                        price=1,
                        buyer_id=self.bank.id,
                        seller_id=loan.borrower_id,
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.id,
                    )
                )
                logger.info(
                    f"Interest payment of {interest_amount:.2f} for loan {loan_id} by {loan.borrower_id}.",
                    extra={
                        "tick": current_tick,
                        "market_id": self.id,
                        "loan_id": loan_id,
                        "borrower_id": loan.borrower_id,
                        "amount": interest_amount,
                    },
                )
                # Note: Principal reduction handled via run_tick or repayments

        return interest_transactions

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
