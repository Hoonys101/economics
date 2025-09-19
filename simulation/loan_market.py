from typing import List
import logging
import config

from simulation.models import Order, Transaction
from simulation.agents.bank import Bank # Bank 클래스 임포트

logger = logging.getLogger(__name__)

class LoanMarket:
    """대출 요청 및 상환을 처리하는 시장"""
    def __init__(self, market_id: str, bank: Bank):
        self.market_id = market_id
        self.bank = bank # 시장과 연결된 은행 인스턴스
        self.loan_requests: List[Order] = [] # 대출 요청 주문 큐
        self.repayment_requests: List[Order] = [] # 상환 요청 주문 큐
        logger.info(f"LoanMarket {market_id} initialized with bank: {bank.id}", extra={'tick': 0, 'market_id': self.market_id, 'agent_id': bank.id, 'tags': ['init', 'market']})

    def place_order(self, order: Order, current_tick: int) -> List[Transaction]:
        """대출 요청 또는 상환 주문을 시장에 제출합니다."""
        transactions: List[Transaction] = []
        log_extra = {'tick': current_tick, 'market_id': self.market_id, 'agent_id': order.agent_id, 'order_type': order.order_type, 'item_id': order.item_id, 'quantity': order.quantity, 'price': order.price}
        logger.info(f"Order placed: Type={order.order_type}, Item={order.item_id}, Agent={order.agent_id}, Amount={order.quantity}", extra=log_extra)

        if order.order_type == "LOAN_REQUEST":
            loan_amount = order.quantity
            interest_rate = order.price
            duration = config.DEFAULT_LOAN_DURATION # Use default duration from config
            
            loan_id, loan_details = self.bank.grant_loan(order.agent_id, loan_amount, interest_rate, duration)
            if loan_id:
                transactions.append(Transaction(item_id="loan_granted", quantity=loan_amount, price=interest_rate, buyer_id=self.bank.id, seller_id=order.agent_id, transaction_type="loan", time=current_tick, market_id=self.market_id))
                logger.info(f"Loan granted to {order.agent_id} for {loan_amount:.2f}. Loan ID: {loan_id}", extra={**log_extra, 'loan_id': loan_id})
            else:
                logger.warning(f"Loan denied for {order.agent_id} for {loan_amount:.2f}.", extra=log_extra)

        elif order.order_type == "REPAYMENT":
            loan_id = order.item_id
            repay_amount = order.quantity
            
            self.bank.process_repayment(loan_id, repay_amount)
            transactions.append(Transaction(item_id="loan_repaid", quantity=repay_amount, price=0, buyer_id=order.agent_id, seller_id=self.bank.id, transaction_type="loan", time=current_tick, market_id=self.market_id))
            logger.info(f"Repayment of {repay_amount:.2f} processed for loan {loan_id} by {order.agent_id}.", extra={**log_extra, 'loan_id': loan_id})
        else: # Handle unknown order types
            logger.warning(f"Unknown order type: {order.order_type}", extra=log_extra)
        
        return transactions

    def process_interest(self, current_tick: int) -> List[Transaction]:
        """은행의 이자 처리 로직을 호출합니다."""
        logger.info(f"Processing interest for outstanding loans at tick {current_tick}.", extra={'tick': current_tick, 'market_id': self.market_id, 'tags': ['loan', 'interest']})
        interest_transactions = []
        for loan_id, loan_details in list(self.bank.loans.items()): # Iterate over a copy since dict might change
            if loan_details["remaining_payments"] > 0:
                interest_amount = loan_details["amount"] * loan_details["interest_rate"]
                # 이자 지불 트랜잭션 생성 (차입자가 은행에 지불)
                interest_transactions.append(Transaction(item_id="interest_payment", quantity=interest_amount, price=1, buyer_id=self.bank.id, seller_id=loan_details["borrower_id"], transaction_type="loan", time=current_tick, market_id=self.market_id))
                logger.info(f"Interest payment of {interest_amount:.2f} for loan {loan_id} by {loan_details["borrower_id"]}.", extra={'tick': current_tick, 'market_id': self.market_id, 'loan_id': loan_id, 'borrower_id': loan_details["borrower_id"], 'amount': interest_amount})
                
                # 대출 잔액에서 이자만큼 차감 (간단화된 모델)
                # loan_details["amount"] -= interest_amount # 이자는 별도로 처리하고 원금은 상환 시에만 줄어든다고 가정
                loan_details["remaining_payments"] -= 1

        return interest_transactions