import logging

logger = logging.getLogger(__name__)

class Bank:
    """은행의 역할을 하는 클래스. 대출을 관리하고 이자를 받습니다."""
    def __init__(self, id: int, initial_assets: float):
        self.id = id
        self.assets = initial_assets
        self.loans = {}
        self.next_loan_id = 0
        self.value_orientation = "N/A" # AI 훈련에서 제외하기 위한 더미 값
        self.needs = {} # Bank는 욕구가 없으므로 빈 딕셔너리 할당
        logger.info(f"Bank {self.id} initialized.", extra={'tick': 0, 'agent_id': self.id, 'tags': ['init', 'bank']})

    def grant_loan(self, borrower_id: int, amount: float, interest_rate: float, duration: int):
        if self.assets >= amount:
            self.assets -= amount
            loan_id = f"loan_{self.next_loan_id}"
            self.next_loan_id += 1
            self.loans[loan_id] = {
                "borrower_id": borrower_id,
                "amount": amount,
                "interest_rate": interest_rate,
                "duration": duration,
                "remaining_payments": duration
            }
            logger.info(f"Loan {loan_id} granted to {borrower_id} for {amount}", extra={'agent_id': self.id, 'tags': ['loan', 'grant']})
            return loan_id, self.loans[loan_id]
        return None, None

    def process_repayment(self, loan_id: str, amount: float):
        if loan_id in self.loans:
            self.assets += amount
            self.loans[loan_id]["amount"] -= amount
            logger.info(f"Repayment of {amount} for loan {loan_id}", extra={'agent_id': self.id, 'tags': ['loan', 'repayment']})
            if self.loans[loan_id]["amount"] <= 0:
                del self.loans[loan_id]
                logger.info(f"Loan {loan_id} fully repaid.", extra={'agent_id': self.id, 'tags': ['loan', 'repayment']})

    def get_outstanding_loans_for_agent(self, agent_id: int):
        return [loan for loan in self.loans.values() if loan['borrower_id'] == agent_id]