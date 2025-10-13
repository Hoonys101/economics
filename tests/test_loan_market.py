import pytest
from unittest.mock import Mock, MagicMock, patch

from simulation.models import Order
from simulation.loan_market import LoanMarket
from simulation.agents.bank import Bank
import config # Import config for DEFAULT_LOAN_DURATION

@pytest.fixture
def mock_bank():
    bank = Mock(spec=Bank)
    bank.id = 0
    bank.assets = 1000000.0
    bank.loans = {}
    bank.grant_loan.return_value = ("loan_id_123", {"amount": 100, "interest_rate": 0.05, "duration": 10})
    bank.process_repayment.return_value = None
    return bank

@pytest.fixture
def loan_market_instance(mock_bank):
    return LoanMarket(market_id="test_loan_market", bank=mock_bank, config_module=config)

@pytest.fixture(autouse=True)
def mock_logger():
    with patch('simulation.loan_market.logger') as mock_loan_market_logger:
        mock_loan_market_logger.info = MagicMock()
        mock_loan_market_logger.warning = MagicMock()
        yield mock_loan_market_logger

class TestLoanMarket:

    def test_initialization(self, loan_market_instance, mock_bank):
        assert loan_market_instance.market_id == "test_loan_market"
        assert loan_market_instance.bank == mock_bank
        assert isinstance(loan_market_instance.loan_requests, list)
        assert isinstance(loan_market_instance.repayment_requests, list)

    def test_place_loan_request_grants_loan(self, loan_market_instance, mock_bank, mock_logger):
        order = Order(agent_id=1, order_type="LOAN_REQUEST", item_id="loan_item", quantity=100, price=0.05, market_id="test_loan_market")
        transactions = loan_market_instance.place_order(order, 1)

        mock_bank.grant_loan.assert_called_once_with(1, 100, 0.05, config.DEFAULT_LOAN_DURATION)
        assert len(transactions) == 1
        assert transactions[0].item_id == "loan_granted"
        mock_logger.info.assert_any_call(
            f"Loan granted to {order.agent_id} for {order.quantity:.2f}. Loan ID: loan_id_123",
            extra={'tick': 1, 'market_id': 'test_loan_market', 'agent_id': 1, 'order_type': 'LOAN_REQUEST', 'item_id': 'loan_item', 'quantity': 100, 'price': 0.05, 'loan_id': 'loan_id_123'}
        )

    def test_place_loan_request_denies_loan(self, loan_market_instance, mock_bank, mock_logger):
        mock_bank.grant_loan.return_value = (None, None) # Simulate loan denial
        order = Order(agent_id=1, order_type="LOAN_REQUEST", item_id="loan_item", quantity=100, price=0.05, market_id="test_loan_market")
        transactions = loan_market_instance.place_order(order, 1)

        mock_bank.grant_loan.assert_called_once()
        assert len(transactions) == 0
        mock_logger.warning.assert_called_once_with(
            f"Loan denied for {order.agent_id} for {order.quantity:.2f}.",
            extra={'tick': 1, 'market_id': 'test_loan_market', 'agent_id': 1, 'order_type': 'LOAN_REQUEST', 'item_id': 'loan_item', 'quantity': 100, 'price': 0.05}
        )

    def test_place_repayment_processes_repayment(self, loan_market_instance, mock_bank, mock_logger):
        order = Order(agent_id=1, order_type="REPAYMENT", item_id="loan_id_456", quantity=50, price=0, market_id="test_loan_market")
        transactions = loan_market_instance.place_order(order, 1)

        mock_bank.process_repayment.assert_called_once_with("loan_id_456", 50)
        assert len(transactions) == 1
        assert transactions[0].item_id == "loan_repaid"

    def test_place_order_unknown_type_logs_warning(self, loan_market_instance, mock_logger):
        order = Order(agent_id=1, order_type="UNKNOWN_TYPE", item_id="item", quantity=1, price=1, market_id="test_loan_market")
        transactions = loan_market_instance.place_order(order, 1)

        mock_logger.warning.assert_called_once_with(
            "Unknown order type: UNKNOWN_TYPE", # Corrected expected message
            extra={'tick': 1, 'market_id': 'test_loan_market', 'agent_id': 1, 'order_type': 'UNKNOWN_TYPE', 'item_id': 'item', 'quantity': 1, 'price': 1}
        )
        assert len(transactions) == 0

    def test_process_interest_calls_bank_method(self, loan_market_instance, mock_bank, mock_logger):
        # Mock bank.loans to simulate existing loans
        mock_bank.loans = {
            "loan_id_1": {"borrower_id": 1, "amount": 100, "interest_rate": 0.05, "remaining_payments": 2},
            "loan_id_2": {"borrower_id": 2, "amount": 200, "interest_rate": 0.03, "remaining_payments": 1}
        }
        transactions = loan_market_instance.process_interest(1)

        assert len(transactions) == 2 # Expecting 2 interest payment transactions
        assert transactions[0].item_id == "interest_payment"
        assert transactions[1].item_id == "interest_payment"
        mock_logger.info.assert_any_call(
            "Processing interest for outstanding loans at tick 1.",
            extra={'tick': 1, 'market_id': 'test_loan_market', 'tags': ['loan', 'interest']}
        )
        # Verify that remaining_payments are decremented
        assert mock_bank.loans["loan_id_1"]["remaining_payments"] == 1
        assert mock_bank.loans["loan_id_2"]["remaining_payments"] == 0
