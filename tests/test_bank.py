import pytest
from unittest.mock import MagicMock, patch
from simulation.bank import Bank, Loan

@pytest.fixture(autouse=True)
def mock_logger():
    with patch("simulation.bank.logging.getLogger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance

@pytest.fixture
def bank_instance():
    # Initialize with enough assets for tests
    return Bank(id=1, initial_assets=10000.0)

class TestBank:
    def test_initialization(self, bank_instance):
        assert bank_instance.id == 1
        assert bank_instance.assets == 10000.0
        assert bank_instance.loans == {}
        assert bank_instance.next_loan_id == 0
        assert bank_instance.value_orientation == "N/A"
        assert bank_instance.needs == {}

    def test_grant_loan_successful(self, bank_instance):
        initial_assets = bank_instance.assets
        # Mock a borrower agent
        borrower = MagicMock()
        borrower.id = 101
        borrower.assets = 0.0

        loan_id = bank_instance.grant_loan(
            borrower_agent=borrower, amount=1000, term_ticks=50
        )

        assert loan_id == "loan_0"
        # Bank assets decreased, borrower assets increased
        assert bank_instance.assets == initial_assets - 1000
        assert borrower.assets == 1000

        loan = bank_instance.loans[loan_id]
        assert loan.borrower_id == 101
        assert loan.principal == 1000
        # Interest rate is base (0.05) + spread (0.02) = 0.07 by default config logic in Bank
        assert loan.annual_interest_rate == 0.07
        assert loan.term_ticks == 50
        assert bank_instance.next_loan_id == 1

    def test_grant_loan_insufficient_assets(self, bank_instance):
        initial_assets = bank_instance.assets
        borrower = MagicMock()
        borrower.id = 101
        borrower.assets = 0.0

        # Ask for more than available
        loan_id = bank_instance.grant_loan(
            borrower_agent=borrower, amount=20000, term_ticks=50
        )

        assert loan_id is None
        assert bank_instance.assets == initial_assets
        assert bank_instance.loans == {}
        assert bank_instance.next_loan_id == 0

    def test_grant_loan_multiple_loans(self, bank_instance):
        borrower1 = MagicMock(); borrower1.id = 101; borrower1.assets = 0
        borrower2 = MagicMock(); borrower2.id = 102; borrower2.assets = 0

        bank_instance.grant_loan(borrower1, 1000)
        bank_instance.grant_loan(borrower2, 500)

        assert len(bank_instance.loans) == 2
        assert "loan_0" in bank_instance.loans
        assert "loan_1" in bank_instance.loans
        assert bank_instance.next_loan_id == 2

    def test_get_outstanding_loans_for_agent_exists(self, bank_instance):
        borrower1 = MagicMock(); borrower1.id = 101; borrower1.assets = 0
        borrower2 = MagicMock(); borrower2.id = 102; borrower2.assets = 0

        bank_instance.grant_loan(borrower1, 1000)
        bank_instance.grant_loan(borrower2, 500)

        loans = bank_instance.get_outstanding_loans_for_agent(agent_id=101)
        assert len(loans) == 1
        assert loans[0]["borrower_id"] == 101
        assert loans[0]["amount"] == 1000

    def test_get_outstanding_loans_for_agent_none(self, bank_instance):
        borrower1 = MagicMock(); borrower1.id = 101; borrower1.assets = 0
        bank_instance.grant_loan(borrower1, 1000)

        loans = bank_instance.get_outstanding_loans_for_agent(agent_id=999)
        assert len(loans) == 0

    def test_get_outstanding_loans_for_agent_multiple(self, bank_instance):
        borrower1 = MagicMock(); borrower1.id = 101; borrower1.assets = 0
        bank_instance.grant_loan(borrower1, 1000)
        bank_instance.grant_loan(borrower1, 2000)

        borrower2 = MagicMock(); borrower2.id = 102; borrower2.assets = 0
        bank_instance.grant_loan(borrower2, 500)

        loans = bank_instance.get_outstanding_loans_for_agent(agent_id=101)
        assert len(loans) == 2
        assert loans[0]["borrower_id"] == 101
        assert loans[1]["borrower_id"] == 101
