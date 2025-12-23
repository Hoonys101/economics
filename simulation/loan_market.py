from typing import List, Any
import logging

from simulation.models import Order, Transaction
from simulation.agents.bank import Bank  # Bank 클래스 임포트
from simulation.core_markets import Market # Import Market

logger = logging.getLogger(__name__)


class LoanMarket(Market):
    """대출 요청 및 상환을 처리하는 시장"""

    def __init__(self, market_id: str, bank: Bank, config_module: Any):
        super().__init__(market_id)
        self.market_id = market_id
        self.bank = bank  # 시장과 연결된 은행 인스턴스
        self.config_module = config_module  # Store config_module
        self.loan_requests: List[Order] = []  # 대출 요청 주문 큐
        self.repayment_requests: List[Order] = []  # 상환 요청 주문 큐
        logger.info(
            f"LoanMarket {market_id} initialized with bank: {bank.id}",
            extra={
                "tick": 0,
                "market_id": self.market_id,
                "agent_id": bank.id,
                "tags": ["init", "market"],
            },
        )

    def place_order(self, order: Order, current_tick: int) -> List[Transaction]:
        """대출 요청 또는 상환 주문을 시장에 제출합니다."""
        transactions: List[Transaction] = []
        log_extra = {
            "tick": current_tick,
            "market_id": self.market_id,
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
            loan_amount = order.quantity
            interest_rate = order.price
            duration = (
                self.config_module.DEFAULT_LOAN_DURATION
            )  # Use default duration from config

            loan_id, loan_details = self.bank.grant_loan(
                order.agent_id, loan_amount, interest_rate, duration
            )
            if loan_id:
                transactions.append(
                    Transaction(
                        item_id="loan_granted",
                        quantity=loan_amount,
                        price=interest_rate,
                        buyer_id=self.bank.id,
                        seller_id=order.agent_id,
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.market_id,
                    )
                )
                logger.info(
                    f"Loan granted to {order.agent_id} for {loan_amount:.2f}. Loan ID: {loan_id}",
                    extra={**log_extra, "loan_id": loan_id},
                )
            else:
                logger.warning(
                    f"Loan denied for {order.agent_id} for {loan_amount:.2f}.",
                    extra=log_extra,
                )

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount = order.quantity

            self.bank.process_repayment(loan_id, repay_amount)
            transactions.append(
                Transaction(
                    item_id="loan_repaid",
                    quantity=repay_amount,
                    price=0,
                    buyer_id=order.agent_id,
                    seller_id=self.bank.id,
                    transaction_type="loan",
                    time=current_tick,
                    market_id=self.market_id,
                )
            )
            logger.info(
                f"Repayment of {repay_amount:.2f} processed for loan {loan_id} by {order.agent_id}.",
                extra={**log_extra, "loan_id": loan_id},
            )
        else:  # Handle unknown order types
            logger.warning(f"Unknown order type: {order.order_type}", extra=log_extra)

        return transactions

    def process_interest(self, current_tick: int) -> List[Transaction]:
        """은행의 이자 처리 로직을 호출합니다."""
        logger.info(
            f"Processing interest for outstanding loans at tick {current_tick}.",
            extra={
                "tick": current_tick,
                "market_id": self.market_id,
                "tags": ["loan", "interest"],
            },
        )
        interest_transactions = []
        for loan_id, loan_details in list(
            self.bank.loans.items()
        ):  # Iterate over a copy since dict might change
            if loan_details["remaining_payments"] > 0:
                interest_amount = loan_details["amount"] * loan_details["interest_rate"]
                # 이자 지불 트랜잭션 생성 (차입자가 은행에 지불)
                interest_transactions.append(
                    Transaction(
                        item_id="interest_payment",
                        quantity=interest_amount,
                        price=1,
                        buyer_id=self.bank.id,
                        seller_id=loan_details["borrower_id"],
                        transaction_type="loan",
                        time=current_tick,
                        market_id=self.market_id,
                    )
                )
                logger.info(
                    f"Interest payment of {interest_amount:.2f} for loan {loan_id} by {loan_details['borrower_id']}.",
                    extra={
                        "tick": current_tick,
                        "market_id": self.market_id,
                        "loan_id": loan_id,
                        "borrower_id": loan_details["borrower_id"],
                        "amount": interest_amount,
                    },
                )

                # 대출 잔액에서 이자만큼 차감 (간단화된 모델)
                # loan_details["amount"] -= interest_amount # 이자는 별도로 처리하고 원금은 상환 시에만 줄어든다고 가정
                loan_details["remaining_payments"] -= 1

        return interest_transactions

    def get_total_demand(self) -> float:
        """총 수요를 반환합니다. LoanMarket의 경우 0을 반환합니다."""
        return 0.0

    def get_total_supply(self) -> float:
        """총 공급을 반환합니다. LoanMarket의 경우 0을 반환합니다."""
        return 0.0

    def match_orders(self, current_time: int) -> List[Transaction]:
        """LoanMarket에서는 별도의 주문 매칭 로직이 없습니다. 대출/상환은 place_order에서 즉시 처리됩니다."""
        return []

    def get_daily_avg_price(self) -> float:
        """LoanMarket의 일일 평균 가격은 의미가 없으므로 0을 반환합니다."""
        return 0.0

    def get_daily_volume(self) -> float:
        """LoanMarket의 일일 거래량은 의미가 없으므로 0을 반환합니다."""
        return 0.0

    def clear_market_for_next_tick(self) -> None:
        """LoanMarket은 매 틱 초기화할 내부 상태가 없습니다."""
        pass

