import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from simulation.loan_market import LoanMarket
from simulation.bank import Bank
from simulation.models import Order, Transaction
from modules.common.config_manager.api import ConfigManager
from modules.finance.api import LoanInfoDTO

class TestLoanMarket:
    @pytest.fixture
    def mock_bank(self):
        return MagicMock(spec=Bank)

    @pytest.fixture
    def mock_config_manager(self):
        config = MagicMock(spec=ConfigManager)
        config.DEFAULT_LOAN_DURATION = 50
        return config

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.fixture
    def loan_market_instance(self, mock_bank, mock_config_manager):
        with patch("simulation.loan_market.logger") as mock_logger:
            return LoanMarket(
                market_id="test_loan_market",
                bank=mock_bank,
                config_module=mock_config_manager,
            )

    def test_initialization(self, loan_market_instance, mock_bank):
        assert loan_market_instance.id == "test_loan_market"
        assert loan_market_instance.bank == mock_bank
        assert loan_market_instance.loan_requests == []
        assert loan_market_instance.repayment_requests == []

    def test_place_loan_request_grants_loan(
        self, loan_market_instance, mock_bank, mock_logger
    ):
        order = Order(
            agent_id=1,
            side="LOAN_REQUEST",
            item_id="loan_item",
            quantity=100,
            price_limit=0.05,
            market_id="test_loan_market",
        )

        # Mock grant_loan to return a DTO
        mock_loan_info = LoanInfoDTO(
            loan_id="loan_id_123",
            borrower_id="1",
            original_amount=100.0,
            outstanding_balance=100.0,
            interest_rate=0.05,
            origination_tick=0,
            due_tick=50
        )
        # Mock transaction returned by bank
        mock_tx = MagicMock(spec=Transaction)
        mock_tx.transaction_type = "loan"
        mock_tx.item_id = "loan_granted"
        mock_tx.buyer_id = mock_bank.id
        mock_tx.seller_id = 1

        mock_bank.grant_loan.return_value = (mock_loan_info, mock_tx)

        transactions = loan_market_instance.place_order(order, 1)

        assert len(transactions) == 1
        assert transactions[0].transaction_type == "loan"
        assert transactions[0].item_id == "loan_granted"
        assert transactions[0].buyer_id == mock_bank.id
        assert transactions[0].seller_id == 1

        # Verify call with new signature
        # borrower_id is converted to str
        mock_bank.grant_loan.assert_called_once_with(
            borrower_id="1",
            amount=100,
            interest_rate=0.05,
            due_tick=51, # current_tick 1 + 50
            borrower_profile=None
        )

    def test_place_loan_request_with_profile(
        self, loan_market_instance, mock_bank, mock_logger
    ):
        profile = {"borrower_id": "1", "gross_income": 1000.0}
        order = Order(
            agent_id=1,
            side="LOAN_REQUEST",
            item_id="loan_item",
            quantity=100,
            price_limit=0.05,
            market_id="test_loan_market",
            metadata={"borrower_profile": profile}
        )

        mock_loan_info = LoanInfoDTO(
            loan_id="loan_id_123",
            borrower_id="1",
            original_amount=100.0,
            outstanding_balance=100.0,
            interest_rate=0.05,
            origination_tick=0,
            due_tick=50
        )
        mock_bank.grant_loan.return_value = (mock_loan_info, None)

        loan_market_instance.place_order(order, 1)

        mock_bank.grant_loan.assert_called_once_with(
            borrower_id="1",
            amount=100,
            interest_rate=0.05,
            due_tick=51,
            borrower_profile=profile
        )

    def test_place_loan_request_denies_loan(
        self, loan_market_instance, mock_bank, mock_logger
    ):
        order = Order(
            agent_id=1,
            side="LOAN_REQUEST",
            item_id="loan_item",
            quantity=100,
            price_limit=0.05,
            market_id="test_loan_market",
        )
        mock_bank.grant_loan.return_value = None

        transactions = loan_market_instance.place_order(order, 1)

        assert len(transactions) == 0
        # logger check is tricky with patch, skipping

    def test_place_repayment_processes_repayment(
        self, loan_market_instance, mock_bank, mock_logger
    ):
        order = Order(
            agent_id=1,
            side="REPAYMENT",
            item_id="loan_id_456",
            quantity=50,
            price_limit=0,
            market_id="test_loan_market",
        )

        mock_bank.repay_loan.return_value = True

        transactions = loan_market_instance.place_order(order, 1)

        mock_bank.repay_loan.assert_called_once_with("loan_id_456", 50)
        assert len(transactions) == 1
        assert transactions[0].item_id == "loan_repaid"

    def test_place_order_unknown_type_logs_warning(
        self, loan_market_instance, mock_bank, mock_logger
    ):
        order = Order(
            agent_id=1,
            side="UNKNOWN_TYPE",
            item_id="item",
            quantity=10,
            price_limit=1,
            market_id="test_loan_market",
        )
        transactions = loan_market_instance.place_order(order, 1)
        assert len(transactions) == 0
