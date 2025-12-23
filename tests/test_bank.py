import pytest
from unittest.mock import MagicMock, patch

from simulation.agents.bank import Bank


# Mock Logger to prevent actual file writes during tests
@pytest.fixture(autouse=True)
def mock_logger():
    with patch("simulation.agents.bank.logging.getLogger") as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        yield mock_logger_instance


@pytest.fixture
def bank_instance():
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
        loan_id, loan_details = bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )

        assert loan_id == "loan_0"
        assert loan_details["borrower_id"] == 101
        assert loan_details["amount"] == 1000
        assert loan_details["interest_rate"] == 0.05
        assert loan_details["duration"] == 12
        assert loan_details["remaining_payments"] == 12
        assert bank_instance.assets == initial_assets - 1000
        assert bank_instance.loans[loan_id] == loan_details
        assert bank_instance.next_loan_id == 1

    def test_grant_loan_insufficient_assets(self, bank_instance):
        initial_assets = bank_instance.assets
        loan_id, loan_details = bank_instance.grant_loan(
            borrower_id=101, amount=20000, interest_rate=0.05, duration=12
        )

        assert loan_id is None
        assert loan_details is None
        assert bank_instance.assets == initial_assets
        assert bank_instance.loans == {}
        assert bank_instance.next_loan_id == 0

    def test_grant_loan_multiple_loans(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        bank_instance.grant_loan(
            borrower_id=102, amount=500, interest_rate=0.03, duration=6
        )

        assert len(bank_instance.loans) == 2
        assert "loan_0" in bank_instance.loans
        assert "loan_1" in bank_instance.loans
        assert bank_instance.next_loan_id == 2

    def test_process_repayment_full(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        initial_assets = bank_instance.assets

        bank_instance.process_repayment(loan_id="loan_0", amount=1000)

        assert bank_instance.assets == initial_assets + 1000
        assert "loan_0" not in bank_instance.loans

    def test_process_repayment_partial(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        initial_assets = bank_instance.assets

        bank_instance.process_repayment(loan_id="loan_0", amount=500)

        assert bank_instance.assets == initial_assets + 500
        assert bank_instance.loans["loan_0"]["amount"] == 500
        assert "loan_0" in bank_instance.loans

    def test_process_repayment_non_existent_loan(self, bank_instance):
        initial_assets = bank_instance.assets
        bank_instance.process_repayment(loan_id="non_existent_loan", amount=100)

        assert bank_instance.assets == initial_assets
        assert bank_instance.loans == {}

    def test_get_outstanding_loans_for_agent_exists(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        bank_instance.grant_loan(
            borrower_id=102, amount=500, interest_rate=0.03, duration=6
        )

        loans = bank_instance.get_outstanding_loans_for_agent(agent_id=101)
        assert len(loans) == 1
        assert loans[0]["borrower_id"] == 101

    def test_get_outstanding_loans_for_agent_none(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        loans = bank_instance.get_outstanding_loans_for_agent(
            agent_id=999
        )  # Non-existent agent
        assert len(loans) == 0

    def test_get_outstanding_loans_for_agent_multiple(self, bank_instance):
        bank_instance.grant_loan(
            borrower_id=101, amount=1000, interest_rate=0.05, duration=12
        )
        bank_instance.grant_loan(
            borrower_id=101, amount=2000, interest_rate=0.04, duration=24
        )
        bank_instance.grant_loan(
            borrower_id=102, amount=500, interest_rate=0.03, duration=6
        )

        loans = bank_instance.get_outstanding_loans_for_agent(agent_id=101)
        assert len(loans) == 2
        assert loans[0]["borrower_id"] == 101
        assert loans[1]["borrower_id"] == 101
